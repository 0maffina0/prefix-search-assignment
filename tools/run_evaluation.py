from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib import parse, request, error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run evaluation against prefix-search API"
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("EVAL_BASE_URL", "http://localhost:5000"),
        help="Base URL of the API (default: http://localhost:5000)",
    )
    parser.add_argument(
        "--queries",
        default="data/prefix_queries.csv",
        help="Path to queries CSV (default: data/prefix_queries.csv)",
    )
    parser.add_argument(
        "--output",
        default="reports/eval_results.csv",
        help="Path to output CSV with results (default: reports/eval_results.csv)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="How many results to request from API (default: 5)",
    )
    return parser.parse_args()


def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    data = sorted(values)
    k = (len(data) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(data[int(k)])
    d0 = data[f] * (c - k)
    d1 = data[c] * (k - f)
    return float(d0 + d1)


def pick_first_existing(fieldnames: List[str], candidates: List[str]) -> Optional[str]:
    for cand in candidates:
        if cand in fieldnames:
            return cand
    return None


def call_search(base_url: str, query: str, top_k: int) -> Dict[str, Any]:
    params = {"q": query, "top_k": str(top_k)}
    url = base_url.rstrip("/") + "/search?" + parse.urlencode(params)
    req = request.Request(url, method="GET")

    opener = request.build_opener(request.ProxyHandler({}))

    with opener.open(req, timeout=10) as resp:
        payload = resp.read().decode("utf-8")
        return json.loads(payload)


def main() -> None:
    args = parse_args()

    queries_path = Path(args.queries)
    if not queries_path.exists():
        raise SystemExit(f"Queries file not found: {queries_path}")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with queries_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise SystemExit("No rows found in queries CSV")

    fieldnames = reader.fieldnames or []

    query_col = pick_first_existing(fieldnames, ["query", "prefix", "q", "text"])
    store_col = pick_first_existing(fieldnames, ["store", "store_id", "persona"])
    expected_cat_col = pick_first_existing(
        fieldnames, ["expected_category", "target_category", "category"]
    )

    if not query_col:
        raise SystemExit(
            f"Could not infer query column. Available columns: {fieldnames}"
        )

    print("Using columns:")
    print(f"query: {query_col}")
    print(f"store: {store_col or '(none)'}")
    print(f"target: {expected_cat_col or '(none)'}")
    print()

    result_rows: List[Dict[str, Any]] = []
    latencies_ms: List[float] = []

    total = len(rows)
    with_results = 0
    labeled = 0
    labeled_with_hit_top3 = 0

    for idx, row in enumerate(rows, start=1):
        raw_query = (row.get(query_col) or "").strip()
        if not raw_query:
            continue

        print(f"[{idx}/{total}] q={raw_query!r}", end="", flush=True)

        t0 = time.perf_counter()
        try:
            resp_json = call_search(args.base_url, raw_query, args.top_k)
            latency_ms = (time.perf_counter() - t0) * 1000.0
            latencies_ms.append(latency_ms)
        except error.HTTPError as e:
            print(f" -> HTTP {e.code}")
            continue
        except Exception as e:
            print(f" -> ERROR: {e}")
            continue

        results = resp_json.get("results", []) or []
        num_results = len(results)
        if num_results > 0:
            with_results += 1

        normalized_query = resp_json.get("normalized_query") or ""
        layout_fixed_query = resp_json.get("layout_fixed_query") or ""
        numeric_filter = resp_json.get("numeric_filter") or None

        expected_category = (
            (row.get(expected_cat_col) or "").strip().lower()
            if expected_cat_col
            else ""
        )

        hit_in_top3 = ""
        if expected_category:
            labeled += 1
            hit = any(
                (res.get("category") or "").strip().lower() == expected_category
                for res in results[:3]
            )
            if hit:
                labeled_with_hit_top3 += 1
            hit_in_top3 = "1" if hit else "0"

        flat: Dict[str, Any] = {
            "query": raw_query,
            "store": row.get(store_col, "") if store_col else "",
            "expected_category": expected_category,
            "normalized_query": normalized_query,
            "layout_fixed_query": layout_fixed_query,
            "numeric_value": numeric_filter.get("value")
            if isinstance(numeric_filter, dict)
            else "",
            "numeric_unit": numeric_filter.get("unit")
            if isinstance(numeric_filter, dict)
            else "",
            "latency_ms": round(latency_ms, 1),
            "num_results": num_results,
            "hit_in_top3_by_category": hit_in_top3,
        }

        for rank in range(3):
            prefix = f"top{rank+1}_"
            if rank < num_results:
                res = results[rank]
                flat[prefix + "id"] = res.get("id", "")
                flat[prefix + "name"] = res.get("name", "")
                flat[prefix + "category"] = res.get("category", "")
                flat[prefix + "brand"] = res.get("brand", "")
                flat[prefix + "score"] = res.get("score", "")
            else:
                flat[prefix + "id"] = ""
                flat[prefix + "name"] = ""
                flat[prefix + "category"] = ""
                flat[prefix + "brand"] = ""
                flat[prefix + "score"] = ""

        result_rows.append(flat)
        print(f" -> {num_results} hits, {latency_ms:.1f} ms")

    if not result_rows:
        raise SystemExit("No successful responses collected")

    out_fieldnames = list(result_rows[0].keys())
    with out_path.open("w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=out_fieldnames)
        writer.writeheader()
        writer.writerows(result_rows)

    coverage = with_results / total if total else 0.0
    p_at3 = (
        labeled_with_hit_top3 / labeled if labeled else None
    )

    print("\nSummary")
    print(f"Total queries: {total}")
    print(f"Queries with results:  {with_results} ({coverage*100:.1f} % coverage)")
    if labeled:
        print(
            f"Labeled queries: {labeled}, "
            f"hit in top-3: {labeled_with_hit_top3} "
            f"({p_at3*100:.1f} % precision@3 by category)"
        )
    else:
        print("No expected_category/target_category column – P@3 not computed.")

    if latencies_ms:
        print(f"Avg latency: {statistics.mean(latencies_ms):.1f} ms")
        print(f"Median latency: {statistics.median(latencies_ms):.1f} ms")
        print(f"95p latency: {percentile(latencies_ms, 95):.1f} ms")

    print(f"\nDetailed results written to: {out_path}")

if __name__ == "__main__":
    main()