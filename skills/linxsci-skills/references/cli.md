# CLI quick reference

[简体中文](cli.zh-CN.md)

All 34 endpoints have convenience commands. With only the skill installed, replace `linxsci` with `python3 <skill-dir>/scripts/cli.py`, using the skill's absolute path.

Replace placeholders with actual returned, unencoded IDs. Convenience commands encode IDs automatically. Prepare JSON files using the deployed Agent API contract. All four search commands send the positional query as `query`; optional `--body` supplies additional fields and cannot override that query. `{}` is not a universally valid request.

| No. | Endpoint | Command |
| --- | --- | --- |
| 01 | API metadata | `linxsci meta` |
| 02 | Usage | `linxsci usage` |
| 03 | Liveness | `linxsci health live` |
| 04 | Readiness | `linxsci health ready` |
| 05 | Paper search | `linxsci search "large language models"` |
| 06 | OpenAlex search | `linxsci search-openalex "large language models"` |
| 07 | Semantic Scholar search | `linxsci search-semantic-scholar "large language models"` |
| 08 | Google Scholar search | `linxsci search-google-scholar "large language models"` |
| 09 | Resolve paper identifiers | `linxsci resolve --body @papers-resolve.json` |
| 10 | Batch paper lookup | `linxsci batch-get --body @papers-batch-get.json` |
| 11 | Paper details | `linxsci paper "<paper-id>"` |
| 12 | Paper content | `linxsci paper "<paper-id>" --resource content` |
| 13 | Table of contents | `linxsci paper "<paper-id>" --resource toc` |
| 14 | Section | `linxsci paper "<paper-id>" --resource sections --item-id "<section-id>"` |
| 15 | Figures | `linxsci paper "<paper-id>" --resource figures` |
| 16 | Assets | `linxsci --output asset.bin paper "<paper-id>" --resource assets --item-id "<asset-id>"` |
| 17 | References | `linxsci paper "<paper-id>" --resource references` |
| 18 | Citing papers | `linxsci paper "<paper-id>" --resource citations` |
| 19 | Related papers | `linxsci paper "<paper-id>" --resource related` |
| 20 | Citation graph | `linxsci paper "<paper-id>" --resource graph` |
| 21 | Citation format | `linxsci paper "<paper-id>" --resource citation` |
| 22 | Recommendations | `linxsci recommend --body @recommendations.json` |
| 23 | Mobile recommendation cards | `linxsci mobile-cards` |
| 24 | Author details | `linxsci author "<author-id>"` |
| 25 | Author papers | `linxsci author "<author-id>" --papers` |
| 26 | Institution details | `linxsci institution "<institution-id>"` |
| 27 | Institution papers | `linxsci institution "<institution-id>" --papers` |
| 28 | Venue details | `linxsci venue "<venue-id>"` |
| 29 | Venue papers | `linxsci venue "<venue-id>" --papers` |
| 30 | Resolve entity identifiers | `linxsci resolve-entities --body @entities-resolve.json` |
| 31 | Create a PDF parsing task | `linxsci parse-pdf --body @pdf-parse.json` |
| 32 | Upload a PDF and create a task | `linxsci upload "/absolute/path/paper.pdf"` |
| 33 | Task status | `linxsci task "<task-id>"` |
| 34 | Task result | `linxsci task "<task-id>" --result` |

All endpoint commands accept repeatable `--param key=value` and `--request-id`. Put global `--output`, `--timeout`, `--framework-request-id`, and `--json-errors` before the action. PDF commands read `LINXSCI_MINERU_API_KEY` when needed. Record the returned task ID; do not recreate tasks or poll indefinitely.

Use `linxsci <action> --help` for parameters. Generic `request` expects a path relative to `/openapi/v2` with dynamic IDs already encoded. See [API contract and errors](api.md).
