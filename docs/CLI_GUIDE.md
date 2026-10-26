# CLI guide: all 34 endpoints

[简体中文](CLI_GUIDE.zh-CN.md) · [README](../README.md)

## Installation and setup

Install a release wheel or install this repository with `python -m pip install -e .`. Once published under its new name, the distribution can be installed with `uv tool install linxsci` for CLI use, or `python -m pip install linxsci` for SDK use.

```bash
linxsci setup
linxsci search "graph neural networks"
```

Setup hides key input and saves configuration locally. The production root is `https://linxsci.com`, without `/openapi/v2`. `LINXSCI_BASE_URL` and `LINXSCI_OPENAPI_KEY` override saved settings. Use `linxsci config` to inspect redacted configuration and `linxsci doctor --json` to perform a real connection check.

For ZIP-only installations, replace `linxsci` with `python3 /absolute/path/to/skill/scripts/cli.py`. On Windows use the installed Python 3 interpreter. No SDK installation is required for that script.

## Inputs

Convenience commands accept raw IDs, including DOI slashes, and encode them. Keep source prefixes such as `arxiv:` or `doi:`. Section, asset and task IDs must come from actual responses. Generic `request` accepts pre-encoded paths relative to `/openapi/v2`.

The four search commands accept a query directly. An optional `--body @search-options.json` supplies contract-defined extra fields; the positional query takes precedence over a `query` field in that file. Other JSON POST commands require `--body`, either inline JSON or `@file.json`. Prepare each file for that endpoint's deployed upstream schema. Do not assume an empty JSON object is valid. PDF upload constructs multipart automatically.

## Endpoint commands

Each row is an independent example; replace placeholder IDs and paths before running it.

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

## Global options and tracing

```bash
linxsci --output search.json search "graph neural networks"
linxsci --timeout 90 --framework-request-id framework-001 meta --request-id upstream-001
linxsci --json-errors usage
linxsci author "<returned-author-id>" --papers --param "<contract-key>=<value>"
linxsci request GET /meta
linxsci request POST /papers/resolve --body @papers-resolve.json
linxsci routes
linxsci paper --help
```

Place `--output`, `--timeout`, `--framework-request-id`, and `--json-errors` before the action. `--output` preserves raw response bytes, including binary assets. Standard output otherwise contains JSON or the raw response. Endpoint-specific `--request-id` sends `X-Request-ID`; `--framework-request-id` sends `X-ANYTHINGRIGHT-REQ-ID`, corresponding to framework `extra.request-id`.

Repeat `--param key=value` for query parameters, including repeated keys. Upload supports repeated `--field key=value`. PDF convenience commands and generic PDF requests read `LINXSCI_MINERU_API_KEY` for `X-MinerU-API-Key` when required.

## PDF tasks and failures

Upload/create only once per intended operation, record the returned ID and inspect the actual task status schema. Fetch `--result` after completion. No universal terminal state or response list field is assumed. Do not poll indefinitely or automatically recreate tasks.

Exit codes are 0 for success, 1 for HTTP/network errors, and 2 for argument/local-file errors. `--json-errors` writes structured diagnostics to stderr without printing the entire upstream error body. Check HTTP status, `error_code`, both trace IDs, `execution_uncertain` and `retry_after`. In particular, `-3905` requires execution and billing verification before retrying uploads or creation. See [API errors and accounting](API.md).
