from __future__ import annotations

import io
import os
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from preflight.api.app import app
from preflight.catalog import invalidate_catalog_cache, load_catalog
from preflight.models import LineItem, Order, Product, UOMConversion
from preflight.parsers import parse_order
from preflight.rules import analyze_order
from preflight.rules_context import RuleContext


class TestCatalogSchemaAndUOM(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.admin_headers = {"X-API-Key": "pf_dev_adm_9901"}
        self.viewer_headers = {"X-API-Key": "pf_dev_view_6604"}
        invalidate_catalog_cache()

    def test_load_full_catalog_and_legacy_backward_compat(self):
        """Full 10-column catalog loads moq/pack_size/base_uom; legacy 5-column CSV loads with defaults."""
        # 1. Full schema CSV
        full_csv = (
            "sku,name,unit_price,stock,active,base_uom,moq,pack_size,category,barcode\n"
            "CAB-01,Network Cable,50000,100,true,METER,10,5,Network,89380001\n"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write(full_csv)
            f.flush()
            temp_path = f.name

        try:
            cat = load_catalog(temp_path)
            self.assertIn("CAB-01", cat)
            prod = cat["CAB-01"]
            self.assertEqual(prod.base_uom, "METER")
            self.assertEqual(prod.moq, 10)
            self.assertEqual(prod.pack_size, 5)
            self.assertEqual(prod.category, "Network")
            self.assertEqual(prod.barcode, "89380001")
        finally:
            Path(temp_path).unlink(missing_ok=True)

        # 2. Legacy 5-column CSV
        legacy_csv = (
            "sku,name,unit_price,stock,active\n"
            "LEGACY-01,Legacy Product,100000,50,true\n"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write(legacy_csv)
            f.flush()
            temp_path = f.name

        try:
            legacy_cat = load_catalog(temp_path)
            self.assertIn("LEGACY-01", legacy_cat)
            prod = legacy_cat["LEGACY-01"]
            self.assertEqual(prod.base_uom, "PCS")
            self.assertEqual(prod.moq, 1)
            self.assertEqual(prod.pack_size, 1)
            self.assertIsNone(prod.category)
            self.assertIsNone(prod.barcode)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_uom_carton_conversion_and_missing_conversion_warning(self):
        """po-carton.json with conversion calculates stock in PCS; without conversion triggers UOM_CONVERSION_MISSING."""
        catalog = {
            "CAB-CAT6-3M": Product(
                sku="CAB-CAT6-3M",
                name="Cat6 Ethernet Cable 3m",
                unit_price=Decimal("72000"),
                stock=150,  # 150 PCS available
                active=True,
                base_uom="PCS",
                moq=1,
                pack_size=1,
            )
        }

        # Load example carton order: 10 CARTON
        carton_order_path = Path("examples/orders/po-carton.json")
        self.assertTrue(carton_order_path.exists())
        order = parse_order(carton_order_path)
        self.assertEqual(order.items[0].uom, "CARTON")

        # 1. With conversion: 1 CARTON = 20 PCS -> 10 CARTON = 200 PCS > 150 PCS stock -> INSUFFICIENT_STOCK
        conversion = UOMConversion(sku="CAB-CAT6-3M", uom_code="CARTON", base_uom="PCS", conversion_factor=Decimal("20.0"))
        ctx_with_conv = RuleContext(catalog=catalog, uom_conversions=(conversion,))
        analysis_with_conv = analyze_order(order, ctx_with_conv)
        codes_with_conv = [f.code for f in analysis_with_conv.findings]
        self.assertIn("INSUFFICIENT_STOCK", codes_with_conv)
        self.assertNotIn("UOM_CONVERSION_MISSING", codes_with_conv)

        # 2. Without conversion -> UOM_CONVERSION_MISSING warning
        ctx_without_conv = RuleContext(catalog=catalog, uom_conversions=())
        analysis_without_conv = analyze_order(order, ctx_without_conv)
        codes_without_conv = [f.code for f in analysis_without_conv.findings]
        self.assertIn("UOM_CONVERSION_MISSING", codes_without_conv)

    def test_invalid_pack_size_and_below_moq(self):
        """Qty 3 with pack_size 5 triggers INVALID_PACK_SIZE; Qty 2 with MOQ 10 triggers BELOW_MOQ."""
        catalog = {
            "PACK-ITEM": Product(
                sku="PACK-ITEM",
                name="Pack Item",
                unit_price=Decimal("10000"),
                stock=1000,
                active=True,
                base_uom="PCS",
                moq=10,
                pack_size=5,
            )
        }
        order = Order(
            po_number="PO-PACK-01",
            customer="Acme Corp",
            items=(
                LineItem(sku="PACK-ITEM", quantity=3, unit_price=Decimal("10000"), uom="PCS"),
            ),
        )
        analysis = analyze_order(order, catalog)
        codes = [f.code for f in analysis.findings]
        self.assertIn("INVALID_PACK_SIZE", codes)
        self.assertIn("BELOW_MOQ", codes)

    def test_catalog_mtime_caching(self):
        """Editing catalog file on disk automatically invalidates cache on next read without restart."""
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write(
                "sku,name,unit_price,stock,active\n"
                "CACHE-TEST,Initial Name,100000,10,true\n"
            )
            f.flush()
            temp_path = f.name

        try:
            cat1 = load_catalog(temp_path)
            self.assertEqual(cat1["CACHE-TEST"].name, "Initial Name")

            # Update file on disk
            import time
            time.sleep(0.05)  # ensure mtime advances
            Path(temp_path).write_text(
                "sku,name,unit_price,stock,active\n"
                "CACHE-TEST,Updated Name On Disk,120000,20,true\n",
                encoding="utf-8",
            )

            cat2 = load_catalog(temp_path)
            self.assertEqual(cat2["CACHE-TEST"].name, "Updated Name On Disk")
            self.assertEqual(cat2["CACHE-TEST"].unit_price, Decimal("120000"))
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_api_catalog_import_validation_and_backup(self):
        """POST /api/v1/catalog/import validates rows, returns 422 with row/column errors, and backs up valid file."""
        from unittest.mock import patch

        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write(
                "sku,name,unit_price,stock,active\n"
                "INITIAL-SKU,Initial Product,50000,10,true\n"
            )
            f.flush()
            temp_path = f.name

        try:
            with patch.dict(os.environ, {"CATALOG_PATH": temp_path}):
                # 1. Invalid CSV: bad price and non-positive MOQ
                invalid_csv = (
                    "sku,name,unit_price,stock,active,moq,pack_size\n"
                    "BAD-01,Bad Item,not_a_number,10,true,0,1\n"
                    ",Missing SKU,50000,5,true,1,1\n"
                )
                files = {"file": ("invalid_catalog.csv", io.BytesIO(invalid_csv.encode("utf-8")), "text/csv")}
                resp = self.client.post("/api/v1/catalog/import", files=files, headers=self.admin_headers)
                self.assertEqual(resp.status_code, 422)
                data = resp.json()
                self.assertEqual(data["code"], "VALIDATION_FAILED")
                self.assertTrue(len(data["errors"]) >= 2)

                # 2. Valid CSV import
                valid_csv = (
                    "sku,name,unit_price,stock,active,base_uom,moq,pack_size,category,barcode\n"
                    "LAPTOP-A14,A14 Business Laptop,18500000,25,true,PCS,1,1,Hardware,8938501234001\n"
                    "CAB-CAT6-3M,Cat6 Ethernet Patch Cable 3m,72000,150,true,PCS,5,5,Network,8938501234005\n"
                )
                files = {"file": ("new_catalog.csv", io.BytesIO(valid_csv.encode("utf-8")), "text/csv")}
                resp_ok = self.client.post("/api/v1/catalog/import", files=files, headers=self.admin_headers)
                self.assertEqual(resp_ok.status_code, 200)
                data_ok = resp_ok.json()
                self.assertTrue(data_ok["success"])
                self.assertEqual(data_ok["total_skus"], 2)
        finally:
            Path(temp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
