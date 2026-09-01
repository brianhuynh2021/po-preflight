from __future__ import annotations

import io
import re
from decimal import Decimal
from typing import Any

import openpyxl

from preflight.ingestion.schemas import (
    DocumentType,
    ExtractedLineItem,
    ExtractedOrder,
    ExtractedOrderHeader,
    ExtractorEngine,
    MathVerificationResult,
)
from preflight.ingestion.verifier import SelfReflectionVerifier
from preflight.models import LineItem, Order


class ExcelExtractor:
    """Enterprise Multi-Sheet Excel (.xlsx / .xlsm / .xls) PO Extractor.
    Features dynamic header recognition, currency normalization & math verification.
    """

    SKU_ALIASES = ["mã hàng", "mã sản phẩm", "mã sp", "mã vt", "mã vật tư", "item code", "sku", "part number", "mã"]
    DESC_ALIASES = ["tên hàng", "tên hàng hóa", "tên sản phẩm", "diễn giải", "mô tả", "description", "item name", "hàng hóa"]
    QTY_ALIASES = ["số lượng", "sl", "qty", "quantity", "so luong"]
    PRICE_ALIASES = ["đơn giá", "đơn giá trước thuế", "price", "unit price", "don gia", "giá"]
    AMOUNT_ALIASES = ["thành tiền", "tổng tiền", "amount", "total", "thanh tien", "tổng cộng", "tong cong"]
    UOM_ALIASES = ["đơn vị tính", "đvt", "dvt", "uom", "unit", "đơn vị"]

    def __init__(self):
        self.verifier = SelfReflectionVerifier()

    def extract(self, file_bytes: bytes, filename: str = "order.xlsx") -> tuple[ExtractedOrder, Order]:
        """Extract structured PO metadata and line items from Excel binary stream."""
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        sheet = self._select_primary_sheet(wb)

        po_number, customer, currency, order_date = self._extract_metadata(sheet, filename)
        header_row_idx, col_map = self._detect_table_headers(sheet)

        items: list[ExtractedLineItem] = []
        domain_items: list[LineItem] = []

        if header_row_idx is not None:
            max_r = sheet.max_row
            for r_idx in range(header_row_idx + 1, max_r + 1):
                row_vals = [sheet.cell(row=r_idx, column=c_idx).value for c_idx in range(1, sheet.max_column + 1)]
                if not any(v is not None for v in row_vals):
                    continue

                sku_val = self._get_cell_str(sheet, r_idx, col_map.get("sku"))
                desc_val = self._get_cell_str(sheet, r_idx, col_map.get("desc")) or sku_val
                qty_val = self._parse_numeric(self._get_cell_raw(sheet, r_idx, col_map.get("qty")))
                price_val = self._parse_numeric(self._get_cell_raw(sheet, r_idx, col_map.get("price")))
                uom_val = self._get_cell_str(sheet, r_idx, col_map.get("uom")) or "PCS"

                # Check if this row is a total/subtotal summary row
                combined_text = f"{sku_val} {desc_val}".lower()
                if any(k in combined_text for k in ["tổng cộng", "tong cong", "subtotal", "grand total", "thuế vat", "tax"]):
                    continue

                if not sku_val and not desc_val:
                    continue
                if qty_val <= 0 and price_val <= 0:
                    continue

                final_sku = sku_val if sku_val else desc_val
                qty_int = int(qty_val) if qty_val > 0 else 1
                amount = Decimal(str(qty_int)) * price_val

                items.append(
                    ExtractedLineItem(
                        sku=final_sku,
                        description=desc_val or final_sku,
                        quantity=qty_int,
                        unit_price=price_val,
                        amount=amount,
                        uom=uom_val.upper(),
                    )
                )
                domain_items.append(
                    LineItem(
                        sku=final_sku,
                        quantity=qty_int,
                        unit_price=price_val,
                        uom=uom_val.upper(),
                    )
                )

        # Fallback if no table items extracted
        if not items:
            items.append(
                ExtractedLineItem(
                    sku="UNKNOWN-EXCEL",
                    description="Unparsed Excel content",
                    quantity=1,
                    unit_price=Decimal("0"),
                    amount=Decimal("0"),
                )
            )
            domain_items.append(LineItem(sku="UNKNOWN-EXCEL", quantity=1, unit_price=Decimal("0")))

        subtotal = sum((it.amount for it in items), start=Decimal("0"))
        header = ExtractedOrderHeader(
            po_number=po_number,
            customer=customer,
            order_date=order_date,
            currency=currency,
            subtotal=subtotal,
            tax_amount=Decimal("0"),
            grand_total=subtotal,
            notes=f"Parsed from Excel workbook '{filename}' (Sheet: {sheet.title})",
        )

        math_res = self.verifier.verify(header, items)
        extracted = ExtractedOrder(
            header=header,
            items=items,
            raw_text=f"Excel Sheet: {sheet.title} ({len(items)} items)",
            confidence_score=0.98,
            extractor_used=ExtractorEngine.EXCEL_PARSER,
            document_type=DocumentType.SPREADSHEET_EXCEL,
            math_verification=math_res,
        )

        domain_order = Order(
            po_number=po_number,
            customer=customer,
            items=tuple(domain_items),
            currency=currency,
        )
        return extracted, domain_order

    def _select_primary_sheet(self, wb: openpyxl.Workbook) -> openpyxl.worksheet.worksheet.Worksheet:
        """Select primary PO worksheet, ignoring cover/summary tabs."""
        ignore_keywords = ["cover", "bìa", "hướng dẫn", "instruction", "tóm tắt", "summary", "notes", "config"]
        for sheetname in wb.sheetnames:
            if not any(k in sheetname.lower() for k in ignore_keywords):
                sheet = wb[sheetname]
                if sheet.max_row and sheet.max_row > 1:
                    return sheet
        return wb.active

    def _extract_metadata(self, sheet: Any, filename: str) -> tuple[str, str, str, str | None]:
        """Extract PO identifier, customer name, date and currency from top header cells."""
        po_number = re.sub(r"\.[^.]+$", "", filename)
        customer = "Excel Enterprise Customer"
        currency = "VND"
        order_date = None

        max_search_row = min(15, sheet.max_row or 1)
        max_search_col = min(10, sheet.max_column or 1)

        for r in range(1, max_search_row + 1):
            for c in range(1, max_search_col + 1):
                val = str(sheet.cell(row=r, column=c).value or "").strip()
                if not val:
                    continue
                val_lower = val.lower()

                # PO Number Detection
                if any(k in val_lower for k in ["số po", "po no", "po number", "mã đơn", "số đơn"]):
                    extracted_po = self._extract_adjacent_or_embedded(sheet, r, c, val)
                    if extracted_po:
                        po_number = extracted_po

                # Customer Detection
                if any(k in val_lower for k in ["khách hàng", "customer", "đơn vị mua", "buyer", "công ty"]):
                    extracted_cust = self._extract_adjacent_or_embedded(sheet, r, c, val)
                    if extracted_cust:
                        customer = extracted_cust

                # Currency Detection
                if "usd" in val_lower or "$" in val_lower:
                    currency = "USD"
                elif "eur" in val_lower or "€" in val_lower:
                    currency = "EUR"

        return po_number, customer, currency, order_date

    def _extract_adjacent_or_embedded(self, sheet: Any, row: int, col: int, cell_text: str) -> str | None:
        """Extract label payload either after ':' in same cell or in next adjacent cell."""
        if ":" in cell_text:
            parts = cell_text.split(":", 1)
            if len(parts) > 1 and parts[1].strip():
                return parts[1].strip()
        # Look in next column
        next_val = sheet.cell(row=row, column=col + 1).value
        if next_val:
            return str(next_val).strip()
        return None

    def _detect_table_headers(self, sheet: Any) -> tuple[int | None, dict[str, int]]:
        """Identify header row and map column indices for SKU, description, quantity, price, amount."""
        max_search_row = min(20, sheet.max_row or 1)
        for r_idx in range(1, max_search_row + 1):
            col_map: dict[str, int] = {}
            for c_idx in range(1, sheet.max_column + 1):
                raw = str(sheet.cell(row=r_idx, column=c_idx).value or "").strip().lower()
                if not raw:
                    continue

                if not col_map.get("sku") and any(k == raw or k in raw for k in self.SKU_ALIASES):
                    col_map["sku"] = c_idx
                elif not col_map.get("desc") and any(k == raw or k in raw for k in self.DESC_ALIASES):
                    col_map["desc"] = c_idx
                elif not col_map.get("qty") and any(k == raw or k in raw for k in self.QTY_ALIASES):
                    col_map["qty"] = c_idx
                elif not col_map.get("price") and any(k == raw or k in raw for k in self.PRICE_ALIASES):
                    col_map["price"] = c_idx
                elif not col_map.get("amount") and any(k == raw or k in raw for k in self.AMOUNT_ALIASES):
                    col_map["amount"] = c_idx
                elif not col_map.get("uom") and any(k == raw or k in raw for k in self.UOM_ALIASES):
                    col_map["uom"] = c_idx

            # If we matched at least 2 key columns (e.g. SKU/desc and price/qty), we found the table header!
            matched_count = len(col_map)
            if matched_count >= 2 and ("qty" in col_map or "price" in col_map or "sku" in col_map):
                return r_idx, col_map

        return None, {}

    def _get_cell_raw(self, sheet: Any, row: int, col: int | None) -> Any:
        if not col:
            return None
        return sheet.cell(row=row, column=col).value

    def _get_cell_str(self, sheet: Any, row: int, col: int | None) -> str | None:
        raw = self._get_cell_raw(sheet, row, col)
        if raw is None:
            return None
        s = str(raw).strip()
        return s if s else None

    def _parse_numeric(self, val: Any) -> Decimal:
        """Sanitize formatted currency/quantity values (e.g. '18.500.000 đ', '1,250.00')."""
        if val is None:
            return Decimal("0")
        if isinstance(val, (int, float, Decimal)):
            return Decimal(str(val))
        
        s = str(val).strip()
        # Remove currency symbols and non-numeric characters except digits, commas, dots, hyphens
        s_clean = re.sub(r"[^\d,\.\-]", "", s)
        if not s_clean:
            return Decimal("0")

        # Vietnamese/European format: 18.500.000 or 18.500.000,00
        if "." in s_clean and "," in s_clean:
            if s_clean.rfind(",") > s_clean.rfind("."):
                # 1.234,56 -> 1234.56
                s_clean = s_clean.replace(".", "").replace(",", ".")
            else:
                # 1,234.56 -> 1234.56
                s_clean = s_clean.replace(",", "")
        elif "." in s_clean and not "," in s_clean:
            # Check if dot is thousands separator (e.g. 18.500.000)
            parts = s_clean.split(".")
            if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3 and int(parts[0]) > 0):
                s_clean = s_clean.replace(".", "")
        elif "," in s_clean and not "." in s_clean:
            parts = s_clean.split(",")
            if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3 and int(parts[0]) > 0):
                s_clean = s_clean.replace(",", "")
            else:
                s_clean = s_clean.replace(",", ".")

        try:
            return Decimal(s_clean)
        except Exception:
            return Decimal("0")
