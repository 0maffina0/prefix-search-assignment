#!/usr/bin/env python3
"""Quick helper to inspect the synthetic catalog."""
from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


def summarize_catalog(path: Path) -> None:
    tree = ET.parse(path)
    root = tree.getroot()
    products = root.findall("product")
    categories = Counter(prod.findtext("category", default="unknown") for prod in products)
    brands = Counter(prod.findtext("brand", default="unknown") for prod in products)

    print(f"Loaded {len(products)} products from {path}")
    print("Top categories:")
    for category, count in categories.most_common(10):
        print(f"  • {category}: {count}")

    print("\nTop brands:")
    for brand, count in brands.most_common(10):
        print(f"  • {brand}: {count}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect catalog_products.xml")
    parser.add_argument("catalog", nargs="?", default="data/catalog_products.xml", help="Path to the XML catalog")
    args = parser.parse_args()

    path = Path(args.catalog)
    if not path.exists():
        raise SystemExit(f"Catalog not found: {path}")

    summarize_catalog(path)


if __name__ == "__main__":
    main()
