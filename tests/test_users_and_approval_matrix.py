from __future__ import annotations

import os
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from preflight.api.app import app
from preflight.models import ApprovalTier, LineItem, Order, RulePolicy, User
from preflight.rules import Finding
from preflight.security.password import (
    hash_password,
    needs_rehash,
    validate_password_strength,
    verify_password,
)
from preflight.security.rbac import Role, UserPrincipal
from preflight.services.decisions import DecisionError, Principal, decide_order
from preflight.store import AuditStore


class TestPasswordSecurity(unittest.TestCase):
    def test_argon2_hashing_and_verification(self):
        pwd = "SecurePassword@123"
        hashed = hash_password(pwd)
        self.assertTrue(hashed.startswith("$argon2id$"))
        self.assertTrue(verify_password(pwd, hashed))
        self.assertFalse(verify_password("WrongPassword123", hashed))
        self.assertFalse(needs_rehash(hashed))

    def test_password_strength_validator(self):
        self.assertFalse(validate_password_strength("short")[0])
        self.assertFalse(validate_password_strength("alllowercaseletters")[0])
        self.assertTrue(validate_password_strength("StrongPass@1234")[0])


class TestUserStoreAndLockout(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_users.db"
        self.store = AuditStore(self.db_path)

    def tearDown(self):
        self.store.close()
        self.temp_dir.cleanup()

    def test_default_seeded_users(self):
        admin = self.store.get_user("admin")
        self.assertIsNotNone(admin)
        self.assertEqual(admin.role, "admin")
        self.assertTrue(verify_password("Admin@123456", admin.password_hash))

        director = self.store.get_user("director")
        self.assertIsNotNone(director)
        self.assertEqual(director.role, "director")

        manager = self.store.get_user("manager")
        self.assertIsNotNone(manager)
        self.assertEqual(manager.role, "manager")

    def test_user_crud(self):
        u = User(
            username="testuser",
            display_name="Nguyen Van A",
            email="test@preflight.vn",
            role="sales_admin",
            password_hash=hash_password("MySecretPass@123"),
        )
        saved = self.store.create_user(u)
        self.assertEqual(saved.username, "testuser")

        fetched = self.store.get_user("testuser")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.display_name, "Nguyen Van A")

        updated = self.store.update_user("testuser", display_name="Nguyen Van B", role="manager")
        self.assertEqual(updated.display_name, "Nguyen Van B")
        self.assertEqual(updated.role, "manager")

        deleted = self.store.delete_user("testuser")
        self.assertTrue(deleted)
        self.assertIsNone(self.store.get_user("testuser"))

    def test_failed_attempts_and_lockout(self):
        username = "admin"
        self.assertFalse(self.store.is_user_locked(username))

        for i in range(1, 5):
            attempts = self.store.record_failed_login(username)
            self.assertEqual(attempts, i)
            self.assertFalse(self.store.is_user_locked(username))

        # 5th attempt locks account
        attempts = self.store.record_failed_login(username)
        self.assertEqual(attempts, 5)
        self.assertTrue(self.store.is_user_locked(username))

        # Reset unlocks
        self.store.reset_failed_logins(username)
        self.assertFalse(self.store.is_user_locked(username))


class TestApprovalMatrixAndSeparationOfDuties(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_governance.db"
        self.store = AuditStore(self.db_path)

        # Set standard approval policy
        self.policy = RulePolicy(
            approval_tiers=[
                ApprovalTier(max_amount=Decimal("50000000"), required_role="manager", description="Dưới 50 triệu"),
                ApprovalTier(max_amount=None, required_role="director", description="Trên 50 triệu"),
            ],
            credit_exception_min_role="director",
            enforce_separation_of_duties=True,
        )
        self.store.set_policy(self.policy)

    def tearDown(self):
        self.store.close()
        self.temp_dir.cleanup()

    def _create_sample_order(self, po_num: str, total_amount: Decimal, created_by: str = "sales_user", findings=None):
        order = Order(
            po_number=po_num,
            customer="CUST-001",
            items=(
                LineItem(sku="SKU-001", quantity=10, unit_price=total_amount / Decimal("10")),
            ),
            created_by=created_by,
            last_modified_by=created_by,
        )
        from preflight.models import Analysis
        analysis = Analysis(
            order=order,
            findings=findings or [],
            status="ready_for_approval" if not findings else "review_required",
        )
        order_id = self.store.record_analysis(analysis, "test_order.json")
        return order_id, order

    def test_manager_can_approve_order_below_threshold(self):
        order_id, _ = self._create_sample_order("PO-SMALL-01", Decimal("30000000"), created_by="sales_admin")
        mgr_principal = Principal(user_id="mgr_01", display_name="Manager One", role=Role.MANAGER, channel="api")

        res = decide_order(self.store, order_ref=order_id, decision="approved", note="Approve small order", principal=mgr_principal)
        self.assertEqual(res.decision, "approved")
        self.assertEqual(res.new_status, "approved")

    def test_manager_cannot_approve_order_above_threshold(self):
        order_id, _ = self._create_sample_order("PO-LARGE-01", Decimal("80000000"), created_by="sales_admin")
        mgr_principal = Principal(user_id="mgr_01", display_name="Manager One", role=Role.MANAGER, channel="api")

        with self.assertRaises(DecisionError) as ctx:
            decide_order(self.store, order_ref=order_id, decision="approved", note="Approve large order", principal=mgr_principal)
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.code, "APPROVAL_LEVEL_INSUFFICIENT")

        # Director can approve
        dir_principal = Principal(user_id="dir_01", display_name="Director One", role=Role.DIRECTOR, channel="api")
        res = decide_order(self.store, order_ref=order_id, decision="approved", note="Director approved large order", principal=dir_principal)
        self.assertEqual(res.decision, "approved")

    def test_credit_exception_elevates_required_role_to_director(self):
        credit_finding = Finding(
            code="CREDIT_LIMIT_EXCEEDED",
            severity="warning",
            message="Vượt hạn mức công nợ",
        )
        order_id, _ = self._create_sample_order("PO-CREDIT-01", Decimal("20000000"), created_by="sales_admin", findings=[credit_finding])
        mgr_principal = Principal(user_id="mgr_01", display_name="Manager One", role=Role.MANAGER, channel="api")

        # Manager rejected due to credit exception elevation
        with self.assertRaises(DecisionError) as ctx:
            decide_order(self.store, order_ref=order_id, decision="approved", note="Ghi chú ngoại lệ công nợ hợp lệ", principal=mgr_principal)
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.code, "APPROVAL_LEVEL_INSUFFICIENT")

        # Director can approve with required note
        dir_principal = Principal(user_id="dir_01", display_name="Director One", role=Role.DIRECTOR, channel="api")
        res = decide_order(self.store, order_ref=order_id, decision="approved", note="Director chấp thuận ngoại lệ công nợ", principal=dir_principal)
        self.assertEqual(res.decision, "approved")

    def test_separation_of_duties_prevents_self_approval(self):
        order_id, _ = self._create_sample_order("PO-SOD-01", Decimal("30000000"), created_by="manager_john")
        self_principal = Principal(user_id="manager_john", display_name="Manager John", role=Role.MANAGER, channel="api")

        with self.assertRaises(DecisionError) as ctx:
            decide_order(self.store, order_ref=order_id, decision="approved", note="Self approving my own order", principal=self_principal)
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.code, "SOD_VIOLATION")

        # Another manager can approve
        other_principal = Principal(user_id="manager_alice", display_name="Manager Alice", role=Role.MANAGER, channel="api")
        res = decide_order(self.store, order_ref=order_id, decision="approved", note="Alice approving John order", principal=other_principal)
        self.assertEqual(res.decision, "approved")


class TestAuthAndUserAPIRoutes(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_auth_login_with_valid_and_invalid_password(self):
        # Valid login
        res = self.client.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin@123456"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["user"], "admin")
        self.assertEqual(data["role"], "ADMIN")

        # Invalid password
        res_bad = self.client.post("/api/v1/auth/login", json={"username": "admin", "password": "WrongPassword"})
        self.assertEqual(res_bad.status_code, 401)

    def test_user_management_api(self):
        admin_headers = {"X-API-Key": "pf_dev_adm_9901"}

        # List users
        res = self.client.get("/api/v1/users", headers=admin_headers)
        self.assertEqual(res.status_code, 200)
        users = res.json()
        self.assertTrue(len(users) >= 4)

        # Create user
        new_user_payload = {
            "username": "sales_lead_1",
            "display_name": "Sales Leader 1",
            "email": "lead1@preflight.vn",
            "password": "SalesPass@123456",
            "role": "sales_admin",
        }
        res_create = self.client.post("/api/v1/users", json=new_user_payload, headers=admin_headers)
        self.assertEqual(res_create.status_code, 201)
        created = res_create.json()
        self.assertEqual(created["username"], "sales_lead_1")
        self.assertEqual(created["role"], "sales_admin")

        # Reset password
        res_reset = self.client.post(
            "/api/v1/users/sales_lead_1/reset-password",
            json={"new_password": "NewSecretPass@999"},
            headers=admin_headers,
        )
        self.assertEqual(res_reset.status_code, 200)

        # Delete user
        res_del = self.client.delete("/api/v1/users/sales_lead_1", headers=admin_headers)
        self.assertEqual(res_del.status_code, 200)


class TestUserCLI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test_cli.db")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cli_users_commands(self):
        from preflight.cli import main

        # 1. Users list
        code = main(["--db", self.db_path, "users", "list"])
        self.assertEqual(code, 0)

        # 2. Users create
        code = main([
            "--db", self.db_path,
            "users", "create",
            "cli_user_1", "CLI User Name", "cli@preflight.vn",
            "--role", "manager",
            "--password", "CLIPassword@123",
        ])
        self.assertEqual(code, 0)

        # 3. Users reset-password
        code = main([
            "--db", self.db_path,
            "users", "reset-password",
            "cli_user_1",
            "--password", "NewCLIPassword@456",
        ])
        self.assertEqual(code, 0)

        # 4. Users unlock
        code = main([
            "--db", self.db_path,
            "users", "unlock",
            "cli_user_1",
        ])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
