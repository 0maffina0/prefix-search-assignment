# Prefix Search Assignment

Поисковый сервис для префиксного поиска по каталогу 1000 товаров из `data/catalog_products.xml`.

Основной функционал сервиса:

- поднимает кластер `Elasticsearch` + API (FastAPI) через `docker-compose`;
- при старте сам создаёт индекс `catalog_prefix` c нужным mapping и анализаторами;
- импортирует `data/catalog_products.xml` в Elasticsearch;
- реализует префиксный поиск с учётом:
  - коротких префиксов (edge n-gram + `bool_prefix`);
  - опечаток в раскладке;
  - числовых признаков веса/объёма (`10л`, `5kg` и т.п.);
  - «защиты от мусора» по категории (`category`-пурити);
- содержит скрипт оценки качества и латентности `tools/run_evaluation.py`
  (Precision@3 по категории + latency distribution).

Эндпоинты:

- `GET /health`
  - Возвращает `{"status": "ok"}` после успешного создания индекса и загрузки каталога.
- `GET /search`
  - Параметры:
    - `q` — строка запроса (обязательный, `min_length=1`),
    - `top_k` — количество документов в ответе (по умолчанию 5, диапазон 1–50).
  - Возвращает `SearchResponse` с:
    - логами нормализации (`normalized_query`, `layout_fixed_query`),
    - распознанным числовым фильтром (`numeric_filter`),
    - top-N товарами (`results`).
---

## 1. Структура проекта

app/
  main.py                   # FastAPI-приложение, индекс, загрузка каталога, логика поиска

data/
  catalog_products.xml      # 1000 товаров (исходный каталог)
  prefix_queries.csv        # 60 префиксных запросов (open + hidden)

reports/
  eval_results.csv          # результат проверки

tools/
  run_evaluation.py         # скрипт для прогона prefix_queries.csv через /search

Dockerfile                  # контейнер с API (FastAPI + зависимости)
docker-compose.yml          # поднимает Elasticsearch + API
requirements.txt            # fastapi, uvicorn, elasticsearch


## 2. Быстрый старт

### Требования

- **Docker** и **Docker Compose**
- **Python 3.11+** 

Из корня проекта:

```bash
docker-compose up --build
```

После успешного запуска можно проверить здоровье сервиса:

```bash
curl http://localhost:5000/health
```

Ожидаемый ответ:
```json
{ "status": "ok" }
```

## 3. Проверка качества

Для оценки качества реализован скрипт tools/run_evaluation.py. Он читает CSV с запросами: data/prefix_queries.csv. Для каждого запроса вызывает GET /search с заданным top_k. Логирует количество найденных документов и время ответа.

### Как запустить проверку:

Из корня проекта, при работающем docker-compose up:

```bash
python .\tools\run_evaluation.py ^
  --base-url http://localhost:5000 ^
  --queries .\data\prefix_queries.csv ^
  --output .\reports\eval_results.csv ^
  --top-k 3
```

## 4. Выводы

По проверке можно сказать следующее:
- Поиск в целом работает устойчиво: 54 из 60 запросов вернули хотя бы один результат — это ~90% coverage, что для MVP на коротких и грязных префиксах выглядит достойно.


MVP уже даёт быструю и достаточно чистую выдачу по большинству префиксов.