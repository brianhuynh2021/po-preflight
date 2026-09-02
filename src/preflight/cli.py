from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

from preflight.catalog import load_catalog
from preflight.config import get_settings
from preflight.db.engine import create_db_engine
from preflight.db.models import metadata, organizations, customers, products
from preflight.models import LineItem, Order, OrderAnalysis
from preflight.parsers import OrderParseError, parse_order
from preflight.render import render_markdown
from preflight.repositories.orders import OrderRepository
from preflight.rules import analyze_order
from preflight.security.rbac import Role
from preflight.store import AuditStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="preflight")
    parser.add_argument("--catalog", default="examples/catalog.csv", help="Product catalog CSV")
    parser.add_argument("--db", default="runtime/preflight.db", help="SQLite/Postgres audit database URL or path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analyze an order file")
    analyze.add_argument("order_file")
    analyze.add_argument("--format", choices=("markdown", "json"), default="markdown")
    analyze.add_argument("--price-tolerance", type=Decimal, default=Decimal("0"))

    decide = subparsers.add_parser("decide", help="Record a human decision")
    decide.add_argument("po_number")
    decide.add_argument("decision", choices=("approved", "rejected", "needs_changes"))
    decide.add_argument("--by", required=True, dest="actor")
    decide.add_argument("--note", default="")

    history = subparsers.add_parser("history", help="Show audit history")
    history.add_argument("po_number")

    # Database Subcommands
    db_cmd = subparsers.add_parser("db", help="Database management & migrations")
    db_sub = db_cmd.add_subparsers(dest="db_command", required=True)
    db_sub.add_parser("upgrade", help="Run Alembic migrations to head")
    db_sub.add_parser("check", help="Verify schema alignment and connectivity")

    # Users Subcommands
    users_cmd = subparsers.add_parser("users", help="User and RBAC security management")
    users_sub = users_cmd.add_subparsers(dest="users_command", required=True)
    
    u_list = users_sub.add_parser("list", help="List all users")
    
    u_create = users_sub.add_parser("create", help="Create a new user")
    u_create.add_argument("username", help="Username")
    u_create.add_argument("display_name", help="Full name")
    u_create.add_argument("email", help="Email address")
    u_create.add_argument("--role", default="viewer", choices=("admin", "director", "manager", "sales_admin", "auditor", "viewer"), help="User role")
    u_create.add_argument("--password", default=None, help="Password (prompted if omitted)")
    
    u_reset = users_sub.add_parser("reset-password", help="Reset user password")
    u_reset.add_argument("username", help="Username to reset")
    u_reset.add_argument("--password", default=None, help="New password (prompted if omitted)")
    
    u_unlock = users_sub.add_parser("unlock", help="Unlock a locked user account")
    u_unlock.add_argument("username", help="Username to unlock")

    # Inventory Subcommands
    inv_cmd = subparsers.add_parser("inventory", help="Inventory snapshots and ATP management")
    inv_sub = inv_cmd.add_subparsers(dest="inventory_command", required=True)
    inv_sync = inv_sub.add_parser("sync", help="Sync stock balances from ERP")
    inv_sync.add_argument("--adapter", default=None, choices=("odoo", "sap", "misa_amis", "mock_odoo", "mock_sap"), help="ERP adapter")
    inv_sync.add_argument("--sku", nargs="*", help="Specific SKUs to sync")
    inv_list = inv_sub.add_parser("list", help="List inventory snapshots and ATP")
    inv_list.add_argument("--sku", help="Filter by specific SKU")

    # Intake Subcommands
    intake_cmd = subparsers.add_parser("intake", help="Multi-channel PO ingestion (email, etc.)")
    intake_sub = intake_cmd.add_subparsers(dest="intake_command", required=True)
    email_cmd = intake_sub.add_parser("email", help="Email IMAP PO intake")
    email_cmd.add_argument("--once", action="store_true", default=True, help="Poll once and exit")
    email_cmd.add_argument("--loop", action="store_true", help="Continuously poll every interval")
    email_cmd.add_argument(
        "--max-messages",
        type=int,
        default=None,
        help="Max messages to process per poll (default 20)",
    )

    # Seed Demo Subcommand
    subparsers.add_parser("seed-demo", help="Seed demo organization, catalog, customers, and sample orders")

    return parser


def run_db_upgrade() -> int:
    """Runs Alembic upgrade to head."""
    print("⚡ Running Alembic database migrations to head...")
    res = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"])
    if res.returncode == 0:
        print("✔ Database schema is up to date.")
    return res.returncode


def run_db_check() -> int:
    """Verifies database connectivity and table presence."""
    engine = create_db_engine()
    with engine.connect() as conn:
        print(f"✔ Successfully connected to database dialect: {engine.dialect.name}")
        from sqlalchemy import inspect
        insp = inspect(conn)
        tables = insp.get_table_names()
        print(f"✔ Found {len(tables)} tables: {', '.join(sorted(tables))}")
    return 0


def run_seed_demo() -> int:
    """Seeds demo organization, customers, catalog, and sample orders into DB."""
    print("🌱 Seeding demo workspace data...")
    engine = create_db_engine()
    with engine.begin() as conn:
        metadata.create_all(conn)

        # 1. Organization
        org = conn.execute(organizations.select().where(organizations.c.code == "demo")).fetchone()
        if not org:
            conn.execute(organizations.insert().values(code="demo", name="Công ty Phân phối Demo Nhật Minh"))
            org = conn.execute(organizations.select().where(organizations.c.code == "demo")).fetchone()
        org_id = org[0]

        # 2. Customers
        demo_custs = [
            ("CUST-001", "Công ty Cổ phần Bán lẻ FPT", "fpt retail"),
            ("CUST-002", "Tập đoàn Vingroup (WinMart)", "winmart vingroup"),
            ("CUST-003", "Hệ thống Bách Hóa Xanh", "bach hoa xanh"),
        ]
        for c_code, c_name, c_norm in demo_custs:
            if not conn.execute(customers.select().where(customers.c.org_id == org_id, customers.c.code == c_code)).fetchone():
                conn.execute(customers.insert().values(org_id=org_id, code=c_code, name=c_name, normalized_name=c_norm))

        # 3. Catalog Products
        cat_map = load_catalog(Path("examples/catalog.csv"))
        for sku, p in cat_map.items():
            if not conn.execute(products.select().where(products.c.org_id == org_id, products.c.sku == sku)).fetchone():
                conn.execute(products.insert().values(
                    org_id=org_id,
                    sku=sku,
                    name=p.name,
                    unit_price=float(p.unit_price),
                    stock=p.stock,
                    active=p.active,
                    base_uom=p.base_uom,
                    moq=p.moq,
                    pack_size=p.pack_size,
                    category=p.category,
                    barcode=p.barcode,
                ))

        # 4. Sample Orders
        order_repo = OrderRepository(conn)
        sample_orders = [
            Order(
                po_number="PO-DEMO-101",
                customer="Công ty Cổ phần Bán lẻ FPT",
                items=(LineItem(sku="LAPTOP-A14", quantity=2, unit_price=Decimal("18500000")),),
            ),
            Order(
                po_number="PO-DEMO-102",
                customer="Tập đoàn Vingroup (WinMart)",
                items=(
                    LineItem(sku="MONITOR-27", quantity=10, unit_price=Decimal("6200000")),
                    LineItem(sku="CAB-CAT6-3M", quantity=20, unit_price=Decimal("72000")),
                ),
            ),
            Order(
                po_number="PO-DEMO-103",
                customer="Hệ thống Bách Hóa Xanh",
                items=(LineItem(sku="HEADSET-PRO", quantity=5, unit_price=Decimal("1450000")),),
            ),
        ]
        for ord_obj in sample_orders:
            analysis = analyze_order(ord_obj, cat_map)
            order_repo.record_analysis(analysis, f"{ord_obj.po_number}.json", org_id=org_id)

    print("✔ Demo workspace seeded successfully with 1 org, 3 customers, catalog SKUs, and 3 orders.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "db":
        if args.db_command == "upgrade":
            return run_db_upgrade()
        if args.db_command == "check":
            return run_db_check()

    if args.command == "seed-demo":
        return run_seed_demo()

    if args.command == "users":
        from preflight.models import User
        from preflight.security.password import hash_password, validate_password_strength
        from preflight.security.rbac import role_from_str
        import getpass

        store = AuditStore(args.db)
        try:
            if args.users_command == "list":
                users = store.list_users()
                print(f"{'ID':<4} {'USERNAME':<16} {'ROLE':<12} {'ACTIVE':<8} {'LOCKED':<8} {'NAME':<24} {'EMAIL'}")
                print("-" * 88)
                for u in users:
                    locked_str = "YES" if store.is_user_locked(u.username) else "NO"
                    print(f"{u.id or '-':<4} {u.username:<16} {u.role:<12} {'YES' if u.is_active else 'NO':<8} {locked_str:<8} {u.display_name:<24} {u.email}")
                return 0

            if args.users_command == "create":
                pwd = args.password
                if not pwd:
                    pwd = getpass.getpass(f"Enter password for '{args.username}': ")
                valid_pwd, pwd_err = validate_password_strength(pwd)
                if not valid_pwd:
                    print(f"Error: {pwd_err}", file=sys.stderr)
                    return 1
                role_val = role_from_str(args.role).name.lower()
                new_u = User(
                    username=args.username.strip().lower(),
                    display_name=args.display_name.strip(),
                    email=args.email.strip().lower(),
                    role=role_val,
                    password_hash=hash_password(pwd),
                    is_active=True,
                )
                created = store.create_user(new_u)
                print(f"✔ User '{created.username}' created successfully with role '{created.role}'.")
                return 0

            if args.users_command == "reset-password":
                pwd = args.password
                if not pwd:
                    pwd = getpass.getpass(f"Enter new password for '{args.username}': ")
                valid_pwd, pwd_err = validate_password_strength(pwd)
                if not valid_pwd:
                    print(f"Error: {pwd_err}", file=sys.stderr)
                    return 1
                u = store.get_user(args.username.strip().lower())
                if not u:
                    print(f"Error: User '{args.username}' not found.", file=sys.stderr)
                    return 1
                store.update_user(args.username.strip().lower(), password_hash=hash_password(pwd))
                store.reset_failed_logins(args.username.strip().lower())
                print(f"✔ Password reset successfully for user '{args.username}'.")
                return 0

            if args.users_command == "unlock":
                u = store.get_user(args.username.strip().lower())
                if not u:
                    print(f"Error: User '{args.username}' not found.", file=sys.stderr)
                    return 1
                store.reset_failed_logins(args.username.strip().lower())
                print(f"✔ Account '{args.username}' unlocked successfully.")
                return 0
        finally:
            store.close()

    if args.command == "inventory":
        from preflight.erp import get_erp_adapter
        from preflight.store import create_audit_store
        store = create_audit_store(args.db)
        try:
            if args.inventory_command == "sync":
                adapter = get_erp_adapter(args.adapter)
                target_skus = args.sku if args.sku else list(load_catalog(args.catalog).keys())
                snaps = adapter.fetch_inventory(skus=target_skus)
                count = store.record_inventory_snapshots(snaps)
                print(f"✔ Synced {count} inventory snapshot(s) from ERP adapter '{adapter.adapter_type.value}'.")
                for s in snaps:
                    print(f"   • {s.sku}: on_hand={s.on_hand}, reserved={s.reserved} (warehouse: {s.warehouse})")
                return 0
            if args.inventory_command == "list":
                catalog = load_catalog(args.catalog)
                target_skus = [args.sku] if args.sku else list(catalog.keys())
                print(f"📦 Inventory Snapshots & ATP (Total SKUs: {len(target_skus)}):")
                for s in target_skus:
                    prod = catalog.get(s)
                    stock_cat = prod.stock if prod else 0
                    atp = store.calculate_atp(s, catalog_stock=stock_cat)
                    stale_flag = " [STALE]" if atp.get("is_stale") else ""
                    print(
                        f"   • {s}: on_hand={atp['on_hand']}, reserved_erp={atp['reserved_erp']}, "
                        f"allocated_local={atp['allocated_local']}, ATP={atp['atp']}{stale_flag} (src: {atp['source']})"
                    )
                return 0
        finally:
            store.close()

    if args.command == "intake":
        from datetime import datetime, UTC
        from preflight.intake.email import EmailIntakeService
        from preflight.store import create_audit_store
        store = create_audit_store(args.db)
        try:
            service = EmailIntakeService(store=store)
            if getattr(args, "loop", False):
                import time
                interval = service.config.poll_interval_seconds
                print(f"📧 Starting continuous Email Intake polling (interval: {interval}s)...")
                try:
                    while True:
                        results = service.poll_once(
                            catalog_path=args.catalog, max_messages=args.max_messages
                        )
                        print(f"[{datetime.now(UTC).isoformat()}] Polled inbox: {len(results)} message(s) processed.")
                        time.sleep(interval)
                except KeyboardInterrupt:
                    print("\n🛑 Stopped email polling.")
                    return 0
            else:
                print("📧 Polling email intake mailbox once...")
                results = service.poll_once(
                    catalog_path=args.catalog, max_messages=args.max_messages
                )
                print(f"✔ Completed email intake poll: {len(results)} message(s) processed.")
                for r in results:
                    print(f"   • [{r.status}] MsgID: {r.message_id} | Sender: {r.sender_email} | Subject: {r.subject} | Orders: {r.orders_created}")
                    for name, reason in r.failed_attachments:
                        print(f"       ✗ {name}: {reason}")
                return 0
        finally:
            store.close()

    try:
        with AuditStore(args.db) as store:
            if args.command == "analyze":
                order = parse_order(args.order_file)
                analysis = analyze_order(
                    order,
                    load_catalog(args.catalog),
                    duplicate=store.has_po(order.po_number),
                    price_tolerance_percent=args.price_tolerance,
                )
                store.record_analysis(analysis, args.order_file)
                if args.format == "json":
                    print(json.dumps(analysis.to_dict(), ensure_ascii=False, indent=2))
                else:
                    print(render_markdown(analysis))
                return 2 if analysis.status == "blocked" else 0
            if args.command == "decide":
                from preflight.services.decisions import Principal, decide_order
                principal = Principal(
                    user_id=args.actor,
                    display_name=args.actor,
                    role=Role.MANAGER,
                    channel="cli",
                )
                res = decide_order(
                    po_number=args.po_number,
                    decision=args.decision,
                    actor=principal,
                    note=args.note,
                    store=store,
                )
                print(f"✔ Decision '{res.decision}' recorded for PO '{res.po_number}'.")
                return 0
            if args.command == "history":
                history = store.get_history(args.po_number)
                print(json.dumps(history, ensure_ascii=False, indent=2))
                return 0
    except OrderParseError as err:
        print(f"Parse error: {err}", file=sys.stderr)
        return 1
    except Exception as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
