# Prefix Search Assignment Assets

This repository packages everything needed to run the "prefix-search ranking" test assignment:

- synthetic catalog with 1 000 multilingual products (`data/catalog_products.xml`),
- curated query set with 30 open and 30 hidden prefixes (`data/prefix_queries.csv`),
- whitelist/quality exports from the production audit (see `data/*.csv` / `.json`),
- investigative reports and spellchecker notes (`docs/`),
- candidate-facing brief plus delivery instructions.

## Directory map
| Path | Description |
| --- | --- |
| `assignment/PREFIX_TEST_ASSIGNMENT.md` | Основное описание задания (на русском). |
| `docs/FINAL_COMPREHENSIVE_REPORT.md` | Итоговый отчёт по текущим проблемам префиксного поиска. |
| `docs/PREFIX_SEARCH_SORT_ANALYSIS_20251027.md` | Детальный анализ сортировки по префиксам. |
| `docs/PREFIX_SEARCH_REMEDIATION_PLAN.md` | План работ по улучшению поиска. |
| `docs/PREFIX_WL_DEBUG_CHECK_20251027.md` | Замечания по whitelist-правилам. |
| `docs/SPELLCHECKER_AUTOFILL_ANALYSIS.md` | Сравнение двух версий spellchecker/autofill. |
| `docs/CANDIDATE_DELIVERY_GUIDE.md` | Инструкция для кандидатов (Docker + Git требования). |
| `data/catalog_products.xml` | Каталог товаров (~1 000 SKU). |
| `data/prefix_queries.csv` | 60 префиксных запросов (open/hidden). |
| `data/PREFIX_*.{csv,json}` | Реальные метрики whitelist/zero-queries (анонимизированы). |
| `reports/PREFIX_REPORT_20251027.html` | HTML-дашборд с графиками за 7 дней. |
| `tools/generate_catalog.py` | Скрипт генерации каталога (детерминированный). |
| `tools/load_catalog.py` | Быстрая проверка каталога (категории/бренды). |
| `tools/evaluate.py` | Заготовка для собственного evaluation pipeline. |

## Data refresh
```bash
# regenerate the synthetic catalog (1 000 rows by default)
python tools/generate_catalog.py --output data/catalog_products.xml --total 1000 --seed 42

# take a quick look at category/brand distribution
python tools/load_catalog.py data/catalog_products.xml

# create an empty evaluation template for your ranking results
python tools/evaluate.py --queries data/prefix_queries.csv --output reports/evaluation_template.csv
```

All store names are anonymized as `Store A…F` and product URLs/prices are fictional. Please do not add real merchant identifiers before sharing the assignment publicly.

## Candidate workflow
1. Прочитайте `assignment/PREFIX_TEST_ASSIGNMENT.md` и `docs/CANDIDATE_DELIVERY_GUIDE.md`.
2. Импортируйте каталог и запросы в выбранный вами движок поиска.
3. Реализуйте поддержку коротких префиксов, опечаток, транслитерации и числовых атрибутов.
4. Используйте `tools/evaluate.py` как каркас для отчёта и дополните README результатами.
5. Упакуйте решение в Docker и пришлите ссылку на приватный репозиторий + образ.
6. Дайте доступ на просмотр решения (репозиторий и артефакты) адресу `artem.kruglov@diginetica.com`.

## Maintainer notes
- Все артефакты из внутреннего расследования находятся в `docs/` и `data/` (см. суффиксы `20251027`).
- Если нужно обновить статистику whitelist, положите новые выгрузки в `data/` и ссылку добавьте в README.
- Перед публикацией убедитесь, что новые файлы не содержат PII или названий реальных магазинов.
