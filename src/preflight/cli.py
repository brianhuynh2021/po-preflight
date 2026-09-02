from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal

from preflight.catalog import load_catalog
from preflight.parsers import OrderParseError, parse_order
from preflight.render import render_markdown
from preflight.rules import analyze_order
from preflight.store import AuditStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="preflight")
    parser.add_argument("--catalog", required=True, help="Product catalog CSV")
    parser.add_argument("--db", required=True, help="SQLite audit database")
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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
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
                    channel="api",
                )
                res = decide_order(
                    store,
                    order_ref=args.po_number,
                    decision=args.decision,
                    note=args.note,
                    principal=principal,
                )
                print(
                    json.dumps(
                        {
                            "decision_id": res.decision_id,
                            "po_number": res.po_number,
                            "decision": res.decision,
                            "actor": res.actor,
                        },
                        ensure_ascii=False,
                    )
                )
                return 0

            if args.command == "history":
                print(json.dumps(store.history(args.po_number), ensure_ascii=False, indent=2))
                return 0
    except (OrderParseError, ValueError, OSError) as exc:
        print(f"preflight: {exc}", file=sys.stderr)
        return 1
    return 1
