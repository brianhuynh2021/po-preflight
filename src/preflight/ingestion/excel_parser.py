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
from preflight.parsers import _decimal


class ExcelExtractor:
    """Enterprise Multi-Sheet Excel (.xlsx / .xlsm / .xls) PO Extractor.
    Features dynamic Vietnamese header recognition, VAT/Discount/Promo detection,
    declared totals extraction & self-reflection math verification.
    """

    PO_ALIASES = [
        "số po", "so po", "mã po", "ma po", "po no", "po no.", "po number", "po_number", "ponumber",
        "mã đơn", "số đơn", "số đơn hàng", "mã đơn hàng", "po #", "po#",
        "order number", "order_number", "order no", "so chung tu", "số chứng từ",
    ]
    CUSTOMER_ALIASES = [
        "khách hàng", "khach hang", "customer", "customer_name", "customer name",
        "đơn vị mua", "buyer", "công ty", "tên khách hàng", "ten khach hang",
        "khach_hang", "ten_khach_hang", "tên công ty", "ten cong ty", "khách", "khach",
        "partner", "client", "tên đơn vị", "ten don vi",
    ]
    DATE_ALIASES = [
        "ngày", "ngay", "ngày đặt", "ngay dat", "order date", "order_date", "date",
        "ngay_dat", "ngày tạo", "po_date", "ngày po", "ngay po", "order_dt",
    ]
    CURRENCY_ALIASES = [
        "tiền tệ", "tien te", "currency", "loại tiền", "loai tien", "ngoại tệ", "đơn vị tiền tệ",
    ]
    SKU_ALIASES = [
        "mã hàng", "mã sản phẩm", "mã sp", "mã vt", "mã vật tư", "item code", "sku",
        "part number", "mã", "ma hang", "ma sp", "ma vt", "product code", "product_code",
    ]
    DESC_ALIASES = [
        "tên hàng", "tên hàng hóa", "tên sản phẩm", "diễn giải", "mô tả", "description",
        "item name", "hàng hóa", "ten hang", "ten san pham", "product name", "product_name",
    ]
    QTY_ALIASES = [
        "số lượng", "sl", "qty", "quantity", "so luong", "soluong", "số lượng đặt",
    ]
    PRICE_ALIASES = [
        "đơn giá", "đơn giá trước thuế", "price", "unit price", "unit_price", "don gia",
        "giá", "gia", "đơn giá bán", "don gia ban",
    ]
    DISCOUNT_PCT_ALIASES = [
        "chiết khấu", "% chiết khấu", "ck", "% ck", "%ck", "giảm giá", "% giảm", "chiet khau",
        "% chiet khau", "discount %", "discount_percent", "disc %", "discount",
    ]
    DISCOUNT_AMT_ALIASES = [
        "tiền ck", "tiền chiết khấu", "tiền giảm", "tien chiet khau", "discount amount", "discount_amt",
    ]
    TAX_RATE_ALIASES = [
        "thuế", "vat", "thuế suất", "% thuế", "% vat", "%vat", "thue", "thue vat", "% thue",
        "tax rate", "tax %", "tax_rate",
    ]
    TAX_AMT_ALIASES = [
        "tiền thuế", "tiền vat", "tien thue", "tien vat", "tax amount", "vat amount",
    ]
    PROMO_ALIASES = [
        "khuyến mãi", "km", "tặng", "hàng tặng", "khuyen mai", "hang tang", "promo", "gift", "hàng km",
    ]
    AMOUNT_ALIASES = [
        "thành tiền", "tổng tiền", "amount", "total", "thanh tien", "line_total", "line total", "total_amount",
    ]
    UOM_ALIASES = [
        "đơn vị tính", "đvt", "dvt", "uom", "unit", "đơn vị", "don vi tinh", "don vi",
    ]

    TOTAL_KEYWORDS = [
        "tổng cộng", "tong cong", "tổng trước thuế", "tong truoc thue", "cộng tiền hàng",
        "cong tien hang", "tổng sau thuế", "tong sau thue", "tổng thanh toán", "tong thanh toan",
        "grand total", "subtotal", "total amount",
    ]

    KNOWN_HEADER_KEYWORDS = {
        "stt", "no", "no.", "sku", "mã", "mã hàng", "mã sp", "mã vt", "item", "item code",
        "description", "diễn giải", "tên hàng", "tên sản phẩm", "hàng hóa", "số lượng",
        "sl", "qty", "quantity", "đơn giá", "unit price", "price", "giá", "thành tiền",
        "amount", "total", "tổng cộng", "đvt", "dvt", "uom", "unit", "đơn vị", "ghi chú",
        "note", "notes", "khách hàng", "customer", "buyer", "po", "số po", "po number",
        "po_number", "order date", "ngày đặt", "tiền tệ", "currency", "chiết khấu", "ck",
        "thuế", "vat", "khuyến mãi", "km", "tặng",
    }

    def __init__(self):
        self.verifier = SelfReflectionVerifier()

    def extract(self, file_bytes: bytes, filename: str = "order.xlsx") -> tuple[ExtractedOrder, Order]:
        """Extract structured PO metadata, line items (with VAT/discount/promo) from Excel."""
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        sheet = self._select_primary_sheet(wb)

        header_row_idx, col_map = self._detect_table_headers(sheet)
        po_number, customer, currency, order_date = self._extract_metadata(
            sheet, filename, header_row_idx=header_row_idx, col_map=col_map
        )

        items: list[ExtractedLineItem] = []
        domain_items: list[LineItem] = []

        declared_subtotal: Decimal | None = None
        declared_tax: Decimal | None = None
        declared_total: Decimal | None = None
        header_discount_amount = Decimal("0")
        shipping_fee = Decimal("0")

        if header_row_idx is not None:
            max_r = sheet.max_row
            for r_idx in range(header_row_idx + 1, max_r + 1):
                row_vals = [sheet.cell(row=r_idx, column=c_idx).value for c_idx in range(1, sheet.max_column + 1)]
                if not any(v is not None for v in row_vals):
                    continue

                sku_val = self._get_cell_str(sheet, r_idx, col_map.get("sku"))
                desc_val = self._get_cell_str(sheet, r_idx, col_map.get("desc")) or sku_val
                qty_raw = self._get_cell_raw(sheet, r_idx, col_map.get("qty"))
                price_raw = self._get_cell_raw(sheet, r_idx, col_map.get("price"))
                uom_val = self._get_cell_str(sheet, r_idx, col_map.get("uom")) or "PCS"

                disc_pct_raw = self._get_cell_raw(sheet, r_idx, col_map.get("discount_pct"))
                disc_amt_raw = self._get_cell_raw(sheet, r_idx, col_map.get("discount_amt"))
                tax_rate_raw = self._get_cell_raw(sheet, r_idx, col_map.get("tax_rate"))
                promo_raw = self._get_cell_raw(sheet, r_idx, col_map.get("promo"))

                # Check if this row is a total/summary/footer row
                combined_text = f"{sku_val or ''} {desc_val or ''}".lower()
                if any(k in combined_text for k in self.TOTAL_KEYWORDS):
                    amt_cell = self._get_cell_raw(sheet, r_idx, col_map.get("amount") or col_map.get("price"))
                    parsed_amt = self._parse_numeric(amt_cell)
                    if parsed_amt > 0:
                        if "trước thuế" in combined_text or "cộng tiền hàng" in combined_text or "subtotal" in combined_text:
                            declared_subtotal = parsed_amt
                        elif "thuế" in combined_text or "vat" in combined_text:
                            declared_tax = parsed_amt
                        else:
                            declared_total = parsed_amt
                    continue

                if not sku_val and not desc_val:
                    continue

                qty_val = self._parse_numeric(qty_raw)
                price_val = self._parse_numeric(price_raw)
                disc_pct_val = self._parse_numeric(disc_pct_raw)
                disc_amt_val = self._parse_numeric(disc_amt_raw)
                tax_rate_val = self._parse_numeric(tax_rate_raw)

                # Promo item detection
                is_promo = False
                if promo_raw is not None:
                    is_promo = str(promo_raw).strip().lower() in {"true", "1", "yes", "km", "tặng", "hàng tặng", "promo"}
                if not is_promo:
                    combined_check = f"{sku_val or ''} {desc_val or ''}".upper()
                    if price_val == Decimal("0") or any(k in combined_check for k in ["KM", "TẶNG", "KHUYẾN MÃI", "KHUYEN MAI", "HANG TANG"]):
                        is_promo = True

                if qty_val <= 0 and price_val <= 0 and not is_promo:
                    continue

                final_sku = sku_val if sku_val else desc_val
                qty_int = int(qty_val) if qty_val > 0 else 1
                
                # Line item domain calculation
                item_obj = LineItem(
                    sku=final_sku,
                    raw_sku=final_sku,
                    description=desc_val or final_sku,
                    quantity=qty_int,
                    unit_price=price_val,
                    uom=uom_val.upper(),
                    discount_percent=disc_pct_val,
                    discount_amount=disc_amt_val,
                    tax_rate=tax_rate_val,
                    is_promo=is_promo,
                )

                items.append(
                    ExtractedLineItem(
                        sku=final_sku,
                        description=desc_val or final_sku,
                        quantity=qty_int,
                        unit_price=price_val,
                        amount=item_obj.line_total,
                        uom=uom_val.upper(),
                    )
                )
                domain_items.append(item_obj)

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

        subtotal = sum((it.line_net for it in domain_items), start=Decimal("0"))
        tax_amount = sum((it.line_tax for it in domain_items), start=Decimal("0"))
        grand_total = subtotal + tax_amount + shipping_fee

        header = ExtractedOrderHeader(
            po_number=po_number,
            customer=customer,
            order_date=order_date,
            currency=currency,
            subtotal=subtotal,
            tax_amount=tax_amount,
            grand_total=grand_total,
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
            header_discount_amount=header_discount_amount,
            shipping_fee=shipping_fee,
            declared_subtotal=declared_subtotal,
            declared_tax=declared_tax,
            declared_total=declared_total,
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

    def _extract_metadata(
        self,
        sheet: Any,
        filename: str,
        header_row_idx: int | None = None,
        col_map: dict[str, int] | None = None,
    ) -> tuple[str, str, str, str | None]:
        """Extract PO identifier, customer name, date and currency from top header cells or table columns."""
        col_map = col_map or {}
        default_po = re.sub(r"\.[^.]+$", "", filename)
        po_number = default_po
        customer = "Excel Enterprise Customer"
        currency = "VND"
        order_date = None

        # 1. First check if metadata is present in tabular columns (Flat Table Layout)
        if header_row_idx is not None and sheet.max_row and sheet.max_row > header_row_idx:
            first_data_row = header_row_idx + 1
            if col_map.get("po_number"):
                po_col_val = self._get_cell_str(sheet, first_data_row, col_map["po_number"])
                if po_col_val and not self._is_header_keyword(po_col_val):
                    po_number = po_col_val

            if col_map.get("customer"):
                cust_col_val = self._get_cell_str(sheet, first_data_row, col_map["customer"])
                if cust_col_val and not self._is_header_keyword(cust_col_val):
                    customer = cust_col_val

            if col_map.get("date"):
                date_col_val = self._get_cell_str(sheet, first_data_row, col_map["date"])
                if date_col_val:
                    order_date = str(date_col_val)

            if col_map.get("currency"):
                curr_col_val = self._get_cell_str(sheet, first_data_row, col_map["currency"])
                if curr_col_val:
                    curr_upper = curr_col_val.upper()
                    if "USD" in curr_upper or "$" in curr_upper:
                        currency = "USD"
                    elif "EUR" in curr_upper or "€" in curr_upper:
                        currency = "EUR"
                    elif "VND" in curr_upper or "VNĐ" in curr_upper:
                        currency = "VND"

        # 2. Scan form rows above table header
        form_search_row = min(15, (header_row_idx - 1) if (header_row_idx and header_row_idx > 1) else (sheet.max_row or 1))
        max_search_col = min(10, sheet.max_column or 1)

        for r in range(1, form_search_row + 1):
            for c in range(1, max_search_col + 1):
                val = str(sheet.cell(row=r, column=c).value or "").strip()
                if not val:
                    continue
                val_lower = val.lower()

                # PO Number Detection in Form Area
                if po_number == default_po and any(k in val_lower for k in self.PO_ALIASES):
                    extracted_po = self._extract_adjacent_or_embedded(sheet, r, c, val)
                    if extracted_po and not self._is_header_keyword(extracted_po):
                        po_number = extracted_po

                # Customer Detection in Form Area
                if customer == "Excel Enterprise Customer" and any(k in val_lower for k in self.CUSTOMER_ALIASES):
                    extracted_cust = self._extract_adjacent_or_embedded(sheet, r, c, val)
                    if extracted_cust and not self._is_header_keyword(extracted_cust):
                        customer = extracted_cust

                # Order Date Detection in Form Area
                if not order_date and any(k in val_lower for k in self.DATE_ALIASES):
                    extracted_date = self._extract_adjacent_or_embedded(sheet, r, c, val)
                    if extracted_date and not self._is_header_keyword(extracted_date):
                        order_date = extracted_date

                # Currency Detection
                if "usd" in val_lower or "$" in val_lower:
                    currency = "USD"
                elif "eur" in val_lower or "€" in val_lower:
                    currency = "EUR"

        return po_number, customer, currency, order_date

    def _is_header_keyword(self, text: str | None) -> bool:
        """Check if an extracted string matches a table header keyword rather than real data."""
        if not text:
            return False
        clean = text.lower().strip()
        if clean in self.KNOWN_HEADER_KEYWORDS:
            return True
        all_aliases = (
            self.PO_ALIASES + self.CUSTOMER_ALIASES + self.DATE_ALIASES +
            self.CURRENCY_ALIASES + self.SKU_ALIASES + self.DESC_ALIASES +
            self.QTY_ALIASES + self.PRICE_ALIASES + self.AMOUNT_ALIASES + self.UOM_ALIASES +
            self.DISCOUNT_PCT_ALIASES + self.TAX_RATE_ALIASES + self.PROMO_ALIASES
        )
        return clean in all_aliases

    def _extract_adjacent_or_embedded(self, sheet: Any, row: int, col: int, cell_text: str) -> str | None:
        """Extract label payload either after ':' in same cell or in next adjacent cell."""
        if ":" in cell_text:
            parts = cell_text.split(":", 1)
            if len(parts) > 1 and parts[1].strip():
                candidate = parts[1].strip()
                if not self._is_header_keyword(candidate):
                    return candidate
        next_val = sheet.cell(row=row, column=col + 1).value
        if next_val:
            candidate = str(next_val).strip()
            if not self._is_header_keyword(candidate):
                return candidate
        return None

    def _detect_table_headers(self, sheet: Any) -> tuple[int | None, dict[str, int]]:
        """Identify header row and map column indices for SKU, description, quantity, price, discount, tax, promo, etc."""
        max_search_row = min(25, sheet.max_row or 1)
        for r_idx in range(1, max_search_row + 1):
            col_map: dict[str, int] = {}
            for c_idx in range(1, sheet.max_column + 1):
                raw = str(sheet.cell(row=r_idx, column=c_idx).value or "").strip().lower()
                if not raw:
                    continue

                if not col_map.get("po_number") and any(k == raw or k in raw for k in self.PO_ALIASES):
                    col_map["po_number"] = c_idx
                elif not col_map.get("customer") and any(k == raw or k in raw for k in self.CUSTOMER_ALIASES):
                    col_map["customer"] = c_idx
                elif not col_map.get("date") and any(k == raw or k in raw for k in self.DATE_ALIASES):
                    col_map["date"] = c_idx
                elif not col_map.get("currency") and any(k == raw or k in raw for k in self.CURRENCY_ALIASES):
                    col_map["currency"] = c_idx
                elif not col_map.get("sku") and any(k == raw or k in raw for k in self.SKU_ALIASES):
                    col_map["sku"] = c_idx
                elif not col_map.get("desc") and any(k == raw or k in raw for k in self.DESC_ALIASES):
                    col_map["desc"] = c_idx
                elif not col_map.get("qty") and any(k == raw or k in raw for k in self.QTY_ALIASES):
                    col_map["qty"] = c_idx
                elif not col_map.get("price") and any(k == raw or k in raw for k in self.PRICE_ALIASES):
                    col_map["price"] = c_idx
                elif not col_map.get("discount_pct") and any(k == raw or k in raw for k in self.DISCOUNT_PCT_ALIASES):
                    col_map["discount_pct"] = c_idx
                elif not col_map.get("discount_amt") and any(k == raw or k in raw for k in self.DISCOUNT_AMT_ALIASES):
                    col_map["discount_amt"] = c_idx
                elif not col_map.get("tax_rate") and any(k == raw or k in raw for k in self.TAX_RATE_ALIASES):
                    col_map["tax_rate"] = c_idx
                elif not col_map.get("tax_amt") and any(k == raw or k in raw for k in self.TAX_AMT_ALIASES):
                    col_map["tax_amt"] = c_idx
                elif not col_map.get("promo") and any(k == raw or k in raw for k in self.PROMO_ALIASES):
                    col_map["promo"] = c_idx
                elif not col_map.get("amount") and any(k == raw or k in raw for k in self.AMOUNT_ALIASES):
                    col_map["amount"] = c_idx
                elif not col_map.get("uom") and any(k == raw or k in raw for k in self.UOM_ALIASES):
                    col_map["uom"] = c_idx

            key_cols = {"sku", "desc", "qty", "price", "amount", "po_number", "customer"}
            matched_keys = set(col_map.keys()) & key_cols
            if len(matched_keys) >= 2 and ("qty" in col_map or "price" in col_map or "sku" in col_map or "desc" in col_map):
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
        """Sanitize formatted currency/quantity values (e.g. '18.500.000 đ', '1,250.00', '1.250.000,50')."""
        return _decimal(val)
