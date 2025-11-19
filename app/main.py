from __future__ import annotations

import os
import time
import re
from collections import Counter
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from elasticsearch import Elasticsearch, helpers

ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
INDEX_NAME = os.getenv("ES_INDEX", "catalog_prefix")
CATALOG_PATH = Path("data/catalog_products.xml")

app = FastAPI(title="Prefix Search Assignment API")

class Product(BaseModel):
    id: str
    name: str
    category: str
    brand: str
    price: float
    weight_value: Optional[float] = None
    weight_unit: Optional[str] = None
    image_url: Optional[str] = None
    score: Optional[float] = None

class NumericFilter(BaseModel):
    value: float
    unit: str

class SearchResponse(BaseModel):
    query: str
    normalized_query: str
    layout_fixed_query: Optional[str]
    numeric_filter: Optional[NumericFilter] = None
    results: List[Product]

def get_es() -> Elasticsearch:
    return Elasticsearch(ES_HOST)

INDEX_SETTINGS: Dict[str, Any] = {
    "settings": {
        "analysis": {
            "filter": {
                "ru_stop": {"type": "stop", "stopwords": "_russian_"},
                "ru_stemmer": {"type": "stemmer", "language": "russian"},
                "edge_ngram_filter": {
                    "type": "edge_ngram",
                    "min_gram": 1,
                    "max_gram": 15,
                },
            },
            "analyzer": {
                "ru_en_search": {
                    "tokenizer": "standard",
                    "filter": ["lowercase", "ru_stop", "ru_stemmer"],
                },
                "ru_en_edge_ngram": {
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "ru_stop",
                        "ru_stemmer",
                        "edge_ngram_filter",
                    ],
                },
            },
        }
    },
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "name": {
                "type": "text",
                "analyzer": "ru_en_search",
                "search_analyzer": "ru_en_search",
                "fields": {
                    "prefix": {
                        "type": "text",
                        "analyzer": "ru_en_edge_ngram",
                        "search_analyzer": "ru_en_search",
                    }
                },
            },
            "category": {"type": "keyword"},
            "brand": {"type": "keyword"},
            "keywords": {
                "type": "text",
                "analyzer": "ru_en_search",
                "search_analyzer": "ru_en_search",
                "fields": {
                    "prefix": {
                        "type": "text",
                        "analyzer": "ru_en_edge_ngram",
                        "search_analyzer": "ru_en_search",
                    }
                },
            },
            "description": {
                "type": "text",
                "analyzer": "ru_en_search",
                "search_analyzer": "ru_en_search",
            },
            "weight_value": {"type": "float"},
            "weight_unit": {"type": "keyword"},
            "package_size": {"type": "integer"},
            "price": {"type": "float"},
            "image_url": {"type": "keyword"},
        }
    },
}

def ensure_index() -> None:
    es = get_es()

    for _ in range(10):
        if es.ping():
            break
        time.sleep(1)
    else:
        raise RuntimeError("Elasticsearch is not responding on ping()")

    if not es.indices.exists(index=INDEX_NAME):
        es.indices.create(index=INDEX_NAME, body=INDEX_SETTINGS)

    count = es.count(index=INDEX_NAME)["count"]
    if count == 0:
        bulk_load_catalog(es)

def bulk_load_catalog(es: Elasticsearch) -> None:
    if not CATALOG_PATH.exists():
        raise RuntimeError(f"Catalog file not found: {CATALOG_PATH}")

    tree = ET.parse(str(CATALOG_PATH))
    root = tree.getroot()
    actions = []

    for product in root.findall("product"):
        pid = product.get("id")
        name = product.findtext("name", default="")
        category = product.findtext("category", default="")
        brand = product.findtext("brand", default="")

        weight_node = product.find("weight")
        weight_value = (
            float(weight_node.text) if (weight_node is not None and weight_node.text) else None
        )
        weight_unit = weight_node.get("unit") if weight_node is not None else None

        package_size_text = product.findtext("package_size")
        package_size = int(package_size_text) if package_size_text else None

        keywords = product.findtext("keywords", default="")
        description = product.findtext("description", default="")

        price_text = product.findtext("price", default="0") or "0"
        price = float(price_text.replace(",", "."))

        image_url = product.findtext("image_url", default="")

        doc = {
            "id": pid,
            "name": name,
            "category": category,
            "brand": brand,
            "weight_value": weight_value,
            "weight_unit": weight_unit,
            "package_size": package_size,
            "keywords": keywords,
            "description": description,
            "price": price,
            "image_url": image_url,
        }

        actions.append(
            {
                "_index": INDEX_NAME,
                "_id": pid,
                "_source": doc,
            }
        )

    if actions:
        helpers.bulk(es, actions)
        es.indices.refresh(index=INDEX_NAME)

RU_TO_EN = dict(
    zip(
        "йцукенгшщзхъфывапролджэячсмитьбю",
        "qwertyuiop[]asdfghjkl;'zxcvbnm,.",
    )
)
EN_TO_RU = {v: k for k, v in RU_TO_EN.items()}

def convert_layout(text: str, mapping: Dict[str, str]) -> str:
    return "".join(mapping.get(ch, mapping.get(ch.lower(), ch)) for ch in text)

def normalize_query(raw: str) -> Dict[str, Optional[str]]:
    q = (raw or "").strip()
    if not q:
        return {"original": raw, "normalized": "", "layout_fixed": None}

    q_norm = q.lower()
    to_ru = convert_layout(q_norm, EN_TO_RU)
    to_en = convert_layout(q_norm, RU_TO_EN)

    layout_fixed = None
    if to_ru != q_norm and any("а" <= ch <= "я" for ch in to_ru):
        layout_fixed = to_ru
    elif to_en != q_norm and any("a" <= ch <= "z" for ch in to_en):
        layout_fixed = to_en

    return {"original": raw, "normalized": q_norm, "layout_fixed": layout_fixed}

NUMERIC_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(кг|kg|г|гр|g|л|l|мл|ml)",
    re.IGNORECASE,
)

UNIT_ALIASES = {
    "кг": "kg",
    "kg": "kg",
    "г": "g",
    "гр": "g",
    "g": "g",
    "л": "l",
    "l": "l",
    "мл": "ml",
    "ml": "ml",
}

def extract_numeric_filter(text: str) -> Optional[Dict[str, Any]]:
    m = NUMERIC_RE.search(text)
    if not m:
        return None

    raw_value, raw_unit = m.groups()
    try:
        value = float(raw_value.replace(",", "."))
    except ValueError:
        return None

    unit = UNIT_ALIASES.get(raw_unit.lower())
    if not unit:
        return None

    return {"value": value, "unit": unit}

@app.on_event("startup")
def on_startup() -> None:
    ensure_index()

@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}

@app.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1, description="Raw user query"),
    top_k: int = Query(5, ge=1, le=50),
):
    es = get_es()
    norm = normalize_query(q)

    numeric = extract_numeric_filter(norm["normalized"])
    numeric_filter_debug: Optional[Dict[str, Any]] = None

    should_queries: List[Dict[str, Any]] = []

    should_queries.append(
        {
            "multi_match": {
                "query": norm["normalized"],
                "type": "bool_prefix",
                "fields": [
                    "name.prefix^4",
                    "name^3",
                    "brand^3",
                    "category^2",
                    "keywords.prefix^2",
                    "description",
                ],
            }
        }
    )

    if norm["layout_fixed"] and norm["layout_fixed"] != norm["normalized"]:
        should_queries.append(
            {
                "multi_match": {
                    "query": norm["layout_fixed"],
                    "type": "bool_prefix",
                    "fields": [
                        "name.prefix^4",
                        "name^3",
                        "brand^3",
                        "category^2",
                        "keywords.prefix^2",
                        "description",
                    ],
                }
            }
        )

    if numeric:
        numeric_filter_debug = numeric
        value = numeric["value"]
        unit = numeric["unit"]

        should_queries.append(
            {
                "constant_score": {
                    "filter": {
                        "bool": {
                            "must": [
                                {"term": {"weight_unit": unit}},
                                {
                                    "range": {
                                        "weight_value": {
                                            "gte": value * 0.8,
                                            "lte": value * 1.2,
                                        }
                                    }
                                },
                            ]
                        }
                    },
                    "boost": 3.0,
                }
            }
        )

    if not should_queries:
        raise HTTPException(status_code=400, detail="Empty query")

    body = {
        "size": top_k * 5,
        "query": {
            "bool": {
                "should": should_queries,
                "minimum_should_match": 1,
            }
        },
        "_source": [
            "id",
            "name",
            "category",
            "brand",
            "price",
            "weight_value",
            "weight_unit",
            "image_url",
        ],
    }

    try:
        resp = es.search(index=INDEX_NAME, body=body)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Search error: {exc}")

    hits = resp.get("hits", {}).get("hits", [])

    if hits:
        top_score = hits[0].get("_score") or 0.0

        score_threshold = top_score * 0.3
        filtered_hits = [
            h for h in hits
            if (h.get("_score") or 0.0) >= score_threshold
        ]

        categories = [
            h.get("_source", {}).get("category")
            for h in filtered_hits
            if h.get("_source", {}).get("category")
        ]

        if categories:
            dominant_category, _ = Counter(categories).most_common(1)[0]
            filtered_hits2: List[Dict[str, Any]] = []
            for h in filtered_hits:
                cat = h.get("_source", {}).get("category")
                sc = h.get("_score") or 0.0
                if cat == dominant_category or sc >= top_score * 0.8:
                    filtered_hits2.append(h)
            hits = filtered_hits2
        else:
            hits = filtered_hits

        hits = hits[:top_k]

    results: List[Product] = []
    for h in hits:
        src = h.get("_source", {})
        results.append(
            Product(
                id=src.get("id", ""),
                name=src.get("name", ""),
                category=src.get("category", ""),
                brand=src.get("brand", ""),
                price=float(src.get("price", 0.0)),
                weight_value=src.get("weight_value"),
                weight_unit=src.get("weight_unit"),
                image_url=src.get("image_url"),
                score=h.get("_score"),
            )
        )

    return SearchResponse(
        query=norm["original"],
        normalized_query=norm["normalized"],
        layout_fixed_query=norm["layout_fixed"],
        numeric_filter=NumericFilter(**numeric_filter_debug) if numeric_filter_debug else None,
        results=results,
    )