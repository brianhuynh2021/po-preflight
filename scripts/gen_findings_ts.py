#!/usr/bin/env python3
"""Generate TypeScript definitions for findings from findings_registry.py."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to sys.path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

from preflight.findings_registry import FINDING_SPECS


def generate_ts() -> str:
    lines = [
        "/**",
        " * Auto-generated from src/preflight/findings_registry.py.",
        " * DO NOT EDIT MANUALLY. Run `python scripts/gen_findings_ts.py` to regenerate.",
        " */",
        "",
        "export type FindingCode =",
    ]
    for spec in FINDING_SPECS:
        lines.append(f'  | "{spec.code}"')
    lines[-1] += ";"
    lines.append("")

    lines.append('export type FindingSeverity = "Info" | "Warning" | "Error";')
    lines.append("")
    lines.append(
        'export type FindingCategory = "catalog" | "price" | "stock" | "credit" | "document" | "duplicate" | "fx";'
    )
    lines.append("")

    lines.append("export interface FindingMetadata {")
    lines.append("  code: FindingCode;")
    lines.append("  defaultSeverity: FindingSeverity;")
    lines.append("  titleVi: string;")
    lines.append("  descriptionVi: string;")
    lines.append("  category: FindingCategory;")
    lines.append("}")
    lines.append("")

    lines.append("export const FINDINGS_REGISTRY: Record<FindingCode, FindingMetadata> = {")
    for spec in FINDING_SPECS:
        sev_cap = spec.default_severity.capitalize()
        lines.append(f'  "{spec.code}": {{')
        lines.append(f'    code: "{spec.code}",')
        lines.append(f'    defaultSeverity: "{sev_cap}",')
        lines.append(f'    titleVi: {repr(spec.title_vi)},')
        lines.append(f'    descriptionVi: {repr(spec.description_vi)},')
        lines.append(f'    category: "{spec.category}",')
        lines.append("  },")
    lines.append("};")
    lines.append("")

    lines.append("export const FINDING_TITLE: Record<FindingCode, string> = {")
    for spec in FINDING_SPECS:
        lines.append(f'  "{spec.code}": {repr(spec.title_vi)},')
    lines.append("};")
    lines.append("")

    lines.append("export const SEVERITY_BY_CODE: Record<FindingCode, FindingSeverity> = {")
    for spec in FINDING_SPECS:
        sev_cap = spec.default_severity.capitalize()
        lines.append(f'  "{spec.code}": "{sev_cap}",')
    lines.append("};")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate findings.generated.ts from Python findings registry.")
    parser.add_argument("--check", action="store_true", help="Check if generated file is up to date without writing.")
    args = parser.parse_args()

    content = generate_ts()
    target_file = repo_root / "apps" / "web" / "app" / "lib" / "findings.generated.ts"

    if args.check:
        if not target_file.exists():
            print(f"Error: {target_file} does not exist. Run without --check to generate it.", file=sys.stderr)
            return 1
        existing = target_file.read_text(encoding="utf-8")
        if existing != content:
            print(f"Error: {target_file} is out of date with findings_registry.py.", file=sys.stderr)
            print("Run `python scripts/gen_findings_ts.py` to regenerate.", file=sys.stderr)
            return 1
        print("✔ findings.generated.ts is up to date.")
        return 0

    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text(content, encoding="utf-8")
    print(f"✔ Generated {target_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
