#!/usr/bin/env python3
"""Skeleton evaluation script for prefix queries.

This script does **not** run a search engine. It just prepares a CSV template
that you can fill with actual ranking results. Replace it with your real
evaluation pipeline when implementing the assignment.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

TEMPLATE_COLUMNS = [
    "query",
    "site",
    "type",
    "notes",
    "top_1",
    "top_1_score",
    "top_2",
    "top_2_score",
    "top_3",
    "top_3_score",
    "latency_ms",
    "judgement",
]


def build_template(queries_path: Path, output_path: Path) -> None:
    with queries_path.open(newline="", encoding="utf-8") as src, output_path.open("w", newline="", encoding="utf-8") as dst:
        reader = csv.DictReader(src)
        writer = csv.DictWriter(dst, fieldnames=TEMPLATE_COLUMNS)
        writer.writeheader()
        for row in reader:
            writer.writerow({
                "query": row.get("query"),
                "site": row.get("site"),
                "type": row.get("type"),
                "notes": row.get("notes"),
                "top_1": "",
                "top_1_score": "",
                "top_2": "",
                "top_2_score": "",
                "top_3": "",
                "top_3_score": "",
                "latency_ms": "",
                "judgement": "",
            })
    print(f"Template written to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an evaluation template for prefix queries")
    parser.add_argument("--queries", default="data/prefix_queries.csv", help="CSV with open/hidden queries")
    parser.add_argument("--output", default="reports/evaluation_template.csv", help="Where to store the template")
    args = parser.parse_args()

    queries_path = Path(args.queries)
    if not queries_path.exists():
        raise SystemExit(f"Queries file not found: {queries_path}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    build_template(queries_path, output_path)


if __name__ == "__main__":
    main()
