# CLI command and parameter guide

[简体中文](CLI_GUIDE.zh-CN.md)

## Install the CLI

Requires Python 3.9+. Download the wheel from the [release assets](https://github.com/LinxSci/linxsci-skills/releases/tag/v0.3.1) and run from its directory:

```bash
uv tool install ./linxsci-0.3.1-py3-none-any.whl
linxsci --version
```

This option requires [uv](https://docs.astral.sh/uv/getting-started/installation/). If the command is missing, run `uv tool update-shell` and reopen the terminal. Alternatively, install from the official source in a Python environment:

```bash
git clone https://github.com/LinxSci/linxsci-skills.git
cd linxsci-skills
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
linxsci --version
```

On Windows use `py -3 -m venv .venv` and `.venv\Scripts\activate.bat`. The Python package and command are `linxsci`. Run `linxsci setup` before service calls.

## Invocation and option placement

```text
linxsci [GLOBAL_OPTIONS] COMMAND [COMMAND_ARGUMENTS]
linxsci --help
linxsci COMMAND --help
```

`linxsci` without arguments shows help. `--help` and `--version` exit without configuration or network access. Global options go **before** the command; command-specific options go **after** it. Quote values containing spaces. Relative file paths are resolved against the current working directory. Replace `<...>` placeholders before execution.

## Global options

| Option | Type / default | Meaning |
| --- | --- | --- |
| `-h`, `--help` | Flag | Show root help; after a command, show that command's help |
| `--version` | Flag | Print the version and exit |
| `--timeout SECONDS` | Number, default `60` | Positive finite network timeout in seconds; not a total timeout for a PDF task |
| `--output PATH` | File path, unset | For API responses, write original response bytes to this file instead of stdout; overwrites an existing file; the parent directory must exist |
| `--json-errors` | Flag, on by default | Write structured failure diagnostics to stderr; does not change successful API responses |
| `--pretty` | Flag, off | Indent successful JSON and local JSON reports for terminal reading |
| `--human-errors` | Flag, off | Use human-readable stderr errors; mutually exclusive with `--json-errors` |
| `--select POINTER` | JSON Pointer, unset | Select an actual response value, e.g. `/data/items`; empty string selects the root |
| `--fields KEYS` | Comma-separated literal names, unset | Keep these fields in the selected object or each array object; every requested field must exist |
| `--limit N` | Nonnegative integer, unset | Locally keep the first N selected array items; does not request server pagination |
| `--table` | Flag, off | Encode a uniform selected object array as `columns` and `rows` |
| `--max-output-chars N` | Nonnegative integer, default `12000` | If formatted endpoint output exceeds N characters, save the full original response and return file metadata plus a bounded preview; `0` disables this threshold |
| `--output-summary` | Flag, off | With `--output`, print JSON containing the saved absolute path, byte count and available content type |
| `--framework-request-id ID` | Nonempty printable ASCII, unset | Send `X-ANYTHINGRIGHT-REQ-ID`; framework errors expose it as `extra.request-id`; the server generates the framework ID when omitted |

`--output` applies to endpoint responses and `read-output`, not configuration/help output or the doctor's diagnostic report. For example:

```bash
linxsci --timeout 90 --output search.json search "graph neural networks"
linxsci --framework-request-id framework-001 meta --request-id upstream-001
```

## Compact output and explicit response views

Endpoint data and errors default to compact JSON, with Unicode characters emitted directly. `--pretty` indents successful JSON; `--human-errors` restores readable error text. `--json-errors` remains available as an explicit compatibility flag for the default error mode. Help/version and interactive setup prompts remain human-readable; setup's connection check is a JSON report. `config`, `routes`, `install-skill`, and `doctor` produce compact JSON; `doctor --text` provides a readable report.

Response views run **locally after one API request**, in this order: select a value, limit an array, project fields, then optionally encode a table. They do not change the request body, URL parameters, billing or server pagination. They apply to endpoint commands and local `read-output`; the CLI rejects using them with configuration/installation/diagnostic commands. Use actual response keys, rather than guessing a provider's schema.

For example, **if an inspected response** contains `data.items` and each item has `id`, `title`, and `url`:

```bash
linxsci --select /data/items --fields id,title,url --limit 3 search "graph neural networks"
linxsci --select /data/items --fields id,title,url --limit 3 --table search "graph neural networks"
```

`--select` follows [JSON Pointer](https://www.rfc-editor.org/rfc/rfc6901.html): `/data/items/0` selects the first item, `~1` represents `/` inside a key, and `~0` represents `~`. It supports exact keys and array indices, not wildcards. `--fields` selects literal top-level keys from the selected object(s), not dotted paths; missing keys or mismatched types produce a local output error instead of an empty result. Explicitly selected `null`, `false`, zero and empty values are preserved. Empty optional diagnostic fields are omitted from error reports; upstream business data is not silently cleaned.

When `--limit` omits items, output is wrapped as `{"data":...,"total":N,"returned":M,"truncated":true}`. Here `total` is the number of items in the **already received array**, not the service's total result count. `--limit 0` intentionally returns no items. `--table` requires objects with identical field sets; `--fields` can choose their common fields first. It emits `{"columns":[...],"rows":[...]}` and preserves nested values as JSON. Empty arrays are supported.

Large output defaults to a `12000`-character spill threshold, measured on formatted output, not tokens or network bytes. Above the threshold, the complete **original response bytes** are saved in a private system temporary directory. Stdout contains `file` (absolute path), `bytes`, available `content_type`, `reason:"output_limit"`, `raw_response:true`, `truncated:true`, `output_chars`, and `preview` (up to 500 characters, or the chosen threshold if smaller). The preview may be incomplete JSON and must not be treated as the full result. This is a spill trigger, not a strict cap on the metadata report length. Files persist for subsequent local reads; remove them when no longer needed.

Binary responses, including PDF/image/audio/video media, are saved to a temporary file with `reason:"binary_response"`; their bytes are not dumped into the model's context. Short UTF-8 non-JSON text is wrapped as `{"text":"..."}`. Use `--max-output-chars 0` to print a full JSON/text response when deliberately needed; binary responses still use file references.

For a chosen destination, the existing `--output` behavior remains: save exact response bytes and leave stdout empty. Add `--output-summary` to receive file metadata:

```bash
linxsci --output paper.json --output-summary paper "<paper-id>" --resource content
linxsci --pretty --max-output-chars 0 meta
```

`--output-summary` requires `--output`. Raw `--output` cannot be combined with `--select`, `--fields`, `--limit`, or `--table`; it always saves the original response. If local formatting or saving fails **after a successful API call**, the stderr JSON has `error_code:"response_output_error"`, `request_completed:true`, and `do_not_repeat:true`, with the original response file if recovery succeeds. Use `read-output` on that file to correct the view locally; do not repeat an upload/task creation just to fix formatting.

## Shared endpoint options

The endpoint commands below all accept these options. Local commands `setup`, `config`, `doctor`, `routes`, and `install-skill` do not accept them.

| Option | Type / default | Meaning |
| --- | --- | --- |
| `--param KEY=VALUE` | Repeatable string, unset | URL query parameter; key must be nonempty. Repeat the same key for multiple values. The script URL-encodes values. Business keys come from the upstream contract |
| `--request-id ID` | Nonempty printable ASCII, generated UUID if omitted | Send upstream/proxy `X-Request-ID`; separate from the global framework trace ID |

```bash
linxsci paper "<paper-id>" --param "<contract-key>=<value>" --request-id upstream-001
```

For a contract-defined multi-value key, repeat `--param "KEY=VALUE1" --param "KEY=VALUE2"`. Do not append query strings to a generic request path. `--param` is for URL parameters; `--body` is for JSON; `--field` is for upload form fields. They are not interchangeable. Global `--limit` only trims the received response locally; it is not an upstream pagination parameter. There are no built-in `--page` or `--year` flags. Send server-side fields through `--param` or `--body` only as defined by the upstream contract.

## Configuration and local commands

### setup

Save a service root and API key, then check `/meta` unless `--no-check` is supplied.

```bash
linxsci setup
linxsci setup --online
linxsci setup --base-url https://linxsci.com --no-check
```

| Option | Type / default | Meaning |
| --- | --- | --- |
| `--base-url URL` | Service root, optional | Explicit suggested root; takes precedence over `--online`. Must be HTTP(S), with no credentials, query, fragment or `/openapi/v1` / `/openapi/v2` suffix |
| `--online` | Flag, off | Suggest the release's online root (`https://linxsci.com`) instead of the saved URL; normal interactive input can still change it |
| `--api-key-stdin` | Flag, off | Read one line of the key from stdin instead of interactive hidden input; use a local secret manager or protected input stream, not a literal key in shell history |
| `--no-check` | Flag, off | Save settings without a network request |

Without `--api-key-stdin`, setup requires an interactive terminal, prompts for the URL, and hides key input. Blank key input retains a saved key, if present. Without an explicit URL or `--online`, the saved URL is suggested, falling back to the release default. A URL selected by flags remains editable in interactive mode. A failed connection check does not undo the saved settings. Setup's check uses the newly supplied settings; later commands can still be overridden by environment variables.

### config

```bash
linxsci config
linxsci config --clear
```

With no options, print `config_file`, `saved_base_url`, `saved_key_configured`, `environment_url_override`, and `environment_key_override`, without the key or a remote request. `--clear` is an optional flag (off by default) that deletes the saved configuration file; it does not unset environment variables. Clear only when requested.

### doctor

```bash
linxsci doctor
linxsci doctor --json
```

`--json` is retained as a compatibility flag: JSON is already the default report format. Optional `--text` (off by default) selects a readable report; the two flags are mutually exclusive. Reports go to stdout. Reports include `ok`, effective `base_url`, configuration information and, when available, status/error/trace metadata. A missing or invalid local configuration gives exit code 2; service failure gives 1; success gives 0. The check makes a real `/meta` request and requires a configured key. A 200 HTML login page does not count as a working JSON API. Avoid redundant checks because they follow normal call accounting.

### routes

```bash
linxsci routes
```

No command-specific parameters. Print all 34 supported method/path templates locally, without a key or network request.

### install-skill

```bash
linxsci install-skill
linxsci install-skill --skills-dir /absolute/path/to/assistant/skills
linxsci install-skill --update
```

| Option | Type / default | Meaning |
| --- | --- | --- |
| `--skills-dir PATH` | Directory, default `~/.agents/skills` | Parent scan directory; the installer appends `/linxsci-skills`. A leading `~` is expanded |
| `--update` | Flag, off | Replace a copy managed by this installer and keep the old version in a sibling `linxsci-skill-backups` directory outside the scan directory |

This action uses local bundled files and needs no key or network. Before using `--update`, upgrade the installed CLI so that it contains the new bundled files. The installer rejects symlink destinations and unmanaged or mismatched installation markers; use the original external installer for its copies. This action only copies the bundled assistant files; it does not configure an API key.

### read-output

Filter a saved original response locally, without a key or network request. Use it to fix a response view without calling the service again:

```bash
linxsci --select /data/items --fields id,title,url --limit 3 read-output "/absolute/path/response.json"
```

Required positional `file` is the saved local response path; a leading `~` is expanded. Replace paths and field examples with actual values. Supports global `--select`, `--fields`, `--limit`, `--table`, `--pretty`, and `--max-output-chars`; raw `--output` can save a copy but cannot be combined with selection flags. If output still exceeds the threshold, the existing input file is referenced instead of creating a duplicate. Missing/unreadable files or invalid selections are local errors and do not make an API call.

## Endpoint index: all 34 routes

Each row is an independent example, not a sequence to run in full. Detailed command parameters follow the index.

| No. | HTTP method and path | Endpoint | Example |
| --- | --- | --- | --- |
| 01 | `GET /openapi/v2/meta` | API metadata | `linxsci meta` |
| 02 | `GET /openapi/v2/usage` | Usage | `linxsci usage` |
| 03 | `GET /openapi/v2/health/live` | Liveness | `linxsci health live` |
| 04 | `GET /openapi/v2/health/ready` | Readiness | `linxsci health ready` |
| 05 | `POST /openapi/v2/papers/search` | Paper search | `linxsci search "large language models"` |
| 06 | `POST /openapi/v2/search/openalex` | OpenAlex search | `linxsci search-openalex "large language models"` |
| 07 | `POST /openapi/v2/search/semantic-scholar` | Semantic Scholar search | `linxsci search-semantic-scholar "large language models"` |
| 08 | `POST /openapi/v2/search/google-scholar` | Google Scholar search | `linxsci search-google-scholar "large language models"` |
| 09 | `POST /openapi/v2/papers/resolve` | Resolve paper identifiers | `linxsci resolve --body @papers-resolve.json` |
| 10 | `POST /openapi/v2/papers:batchGet` | Batch paper lookup | `linxsci batch-get --body @papers-batch-get.json` |
| 11 | `GET /openapi/v2/papers/{paper_id}` | Paper details | `linxsci paper "<paper-id>"` |
| 12 | `GET /openapi/v2/papers/{paper_id}/content` | Paper content | `linxsci paper "<paper-id>" --resource content` |
| 13 | `GET /openapi/v2/papers/{paper_id}/toc` | Table of contents | `linxsci paper "<paper-id>" --resource toc` |
| 14 | `GET /openapi/v2/papers/{paper_id}/sections/{section_id}` | Section | `linxsci paper "<paper-id>" --resource sections --item-id "<section-id>"` |
| 15 | `GET /openapi/v2/papers/{paper_id}/figures` | Figures | `linxsci paper "<paper-id>" --resource figures` |
| 16 | `GET /openapi/v2/papers/{paper_id}/assets/{asset_id}` | Assets | `linxsci --output asset.bin paper "<paper-id>" --resource assets --item-id "<asset-id>"` |
| 17 | `GET /openapi/v2/papers/{paper_id}/references` | References | `linxsci paper "<paper-id>" --resource references` |
| 18 | `GET /openapi/v2/papers/{paper_id}/citations` | Citing papers | `linxsci paper "<paper-id>" --resource citations` |
| 19 | `GET /openapi/v2/papers/{paper_id}/related` | Related papers | `linxsci paper "<paper-id>" --resource related` |
| 20 | `GET /openapi/v2/papers/{paper_id}/graph` | Citation graph | `linxsci paper "<paper-id>" --resource graph` |
| 21 | `GET /openapi/v2/papers/{paper_id}/citation` | Citation format | `linxsci paper "<paper-id>" --resource citation` |
| 22 | `POST /openapi/v2/recommendations` | Recommendations | `linxsci recommend --body @recommendations.json` |
| 23 | `GET /openapi/v2/recommendations/mobile-cards` | Mobile recommendation cards | `linxsci mobile-cards` |
| 24 | `GET /openapi/v2/authors/{author_id}` | Author details | `linxsci author "<author-id>"` |
| 25 | `GET /openapi/v2/authors/{author_id}/papers` | Author papers | `linxsci author "<author-id>" --papers` |
| 26 | `GET /openapi/v2/institutions/{institution_id}` | Institution details | `linxsci institution "<institution-id>"` |
| 27 | `GET /openapi/v2/institutions/{institution_id}/papers` | Institution papers | `linxsci institution "<institution-id>" --papers` |
| 28 | `GET /openapi/v2/venues/{venue_id}` | Venue details | `linxsci venue "<venue-id>"` |
| 29 | `GET /openapi/v2/venues/{venue_id}/papers` | Venue papers | `linxsci venue "<venue-id>" --papers` |
| 30 | `POST /openapi/v2/entities:resolve` | Resolve entity identifiers | `linxsci resolve-entities --body @entities-resolve.json` |
| 31 | `POST /openapi/v2/pdf/parse` | Create a PDF parsing task | `linxsci parse-pdf --body @pdf-parse.json` |
| 32 | `POST /openapi/v2/pdf/parse/upload` | Upload a PDF and create a task | `linxsci upload "/absolute/path/paper.pdf"` |
| 33 | `GET /openapi/v2/pdf/parse/{task_id}` | Task status | `linxsci task "<task-id>"` |
| 34 | `GET /openapi/v2/pdf/parse/{task_id}/result` | Task result | `linxsci task "<task-id>" --result` |

## Service information and health

### meta

`GET /openapi/v2/meta`. Get API metadata. The response is not guaranteed to be a complete business schema.

```bash
linxsci meta
```

No positional arguments or dedicated options; supports shared `--param` and `--request-id`. A configured key is required.

### usage

`GET /openapi/v2/usage`. Get request statistics for the current service process. Account balances and remaining quotas are available in the platform Usage page.

```bash
linxsci usage
```

No positional arguments or dedicated options; supports shared `--param` and `--request-id`. A configured key is required.

### mobile-cards

`GET /openapi/v2/recommendations/mobile-cards`. Get mobile recommendation cards.

```bash
linxsci mobile-cards
```

No positional arguments or dedicated options; supports shared `--param` and `--request-id`. A configured key is required.

### health

`GET /openapi/v2/health/{check}`.

```bash
linxsci health live
linxsci health ready
```

Required positional `check` is exactly `live` (liveness) or `ready` (readiness); there is no default. Both checks require a configured key and follow normal call accounting. Supports shared endpoint options.

## Search commands

### search

`POST /openapi/v2/papers/search` — integrated paper search.

```bash
linxsci search "graph neural networks"
linxsci search "graph neural networks" --body @search-options.json
```

| Argument | Required / default | Meaning |
| --- | --- | --- |
| `query` | Required positional string | Search text, sent as JSON `query`; quote multi-word text |
| `--body JSON_OR_@FILE` | Optional, default no extra fields | Additional JSON **object**, inline or UTF-8 file; a `query` inside it is replaced by the positional query |

Supports shared endpoint options. A bare query needs no request file: `"graph neural networks"` produces `{"query":"graph neural networks"}`. Extra fields must follow this provider's deployed contract; do not reuse another provider's model without checking it.

### search-openalex

`POST /openapi/v2/search/openalex` — OpenAlex.

```bash
linxsci search-openalex "graph neural networks"
linxsci search-openalex "graph neural networks" --body @search-options.json
```

| Argument | Required / default | Meaning |
| --- | --- | --- |
| `query` | Required positional string | Search text, sent as JSON `query`; quote multi-word text |
| `--body JSON_OR_@FILE` | Optional, default no extra fields | Additional JSON **object**, inline or UTF-8 file; a `query` inside it is replaced by the positional query |

Supports shared endpoint options. A bare query needs no request file: `"graph neural networks"` produces `{"query":"graph neural networks"}`. Extra fields must follow this provider's deployed contract; do not reuse another provider's model without checking it.

### search-semantic-scholar

`POST /openapi/v2/search/semantic-scholar` — Semantic Scholar.

```bash
linxsci search-semantic-scholar "graph neural networks"
linxsci search-semantic-scholar "graph neural networks" --body @search-options.json
```

| Argument | Required / default | Meaning |
| --- | --- | --- |
| `query` | Required positional string | Search text, sent as JSON `query`; quote multi-word text |
| `--body JSON_OR_@FILE` | Optional, default no extra fields | Additional JSON **object**, inline or UTF-8 file; a `query` inside it is replaced by the positional query |

Supports shared endpoint options. A bare query needs no request file: `"graph neural networks"` produces `{"query":"graph neural networks"}`. Extra fields must follow this provider's deployed contract; do not reuse another provider's model without checking it.

### search-google-scholar

`POST /openapi/v2/search/google-scholar` — Google Scholar.

```bash
linxsci search-google-scholar "graph neural networks"
linxsci search-google-scholar "graph neural networks" --body @search-options.json
```

| Argument | Required / default | Meaning |
| --- | --- | --- |
| `query` | Required positional string | Search text, sent as JSON `query`; quote multi-word text |
| `--body JSON_OR_@FILE` | Optional, default no extra fields | Additional JSON **object**, inline or UTF-8 file; a `query` inside it is replaced by the positional query |

Supports shared endpoint options. A bare query needs no request file: `"graph neural networks"` produces `{"query":"graph neural networks"}`. Extra fields must follow this provider's deployed contract; do not reuse another provider's model without checking it.

## JSON POST commands

### resolve

`POST /openapi/v2/papers/resolve`. Resolve paper identifiers.

```bash
linxsci resolve --body @papers-resolve.json
```

Required option `--body JSON_OR_@FILE` supplies this endpoint's request body as inline JSON or an existing UTF-8 JSON file. There are no positional arguments or default business fields. Supports shared endpoint options. Prepare `papers-resolve.json` using this endpoint's actual upstream schema; the repository does not define all required business fields, and `{}` is not guaranteed valid.

### batch-get

`POST /openapi/v2/papers:batchGet`. Fetch multiple papers in one request.

```bash
linxsci batch-get --body @papers-batch-get.json
```

Required option `--body JSON_OR_@FILE` supplies this endpoint's request body as inline JSON or an existing UTF-8 JSON file. There are no positional arguments or default business fields. Supports shared endpoint options. Prepare `papers-batch-get.json` using this endpoint's actual upstream schema; the repository does not define all required business fields, and `{}` is not guaranteed valid.

### recommend

`POST /openapi/v2/recommendations`. Request paper recommendations.

```bash
linxsci recommend --body @recommendations.json
```

Required option `--body JSON_OR_@FILE` supplies this endpoint's request body as inline JSON or an existing UTF-8 JSON file. There are no positional arguments or default business fields. Supports shared endpoint options. Prepare `recommendations.json` using this endpoint's actual upstream schema; the repository does not define all required business fields, and `{}` is not guaranteed valid.

### resolve-entities

`POST /openapi/v2/entities:resolve`. Resolve author, institution or venue identifiers.

```bash
linxsci resolve-entities --body @entities-resolve.json
```

Required option `--body JSON_OR_@FILE` supplies this endpoint's request body as inline JSON or an existing UTF-8 JSON file. There are no positional arguments or default business fields. Supports shared endpoint options. Prepare `entities-resolve.json` using this endpoint's actual upstream schema; the repository does not define all required business fields, and `{}` is not guaranteed valid.

### parse-pdf

`POST /openapi/v2/pdf/parse`. Create a PDF parsing task from a JSON request. This command does not upload a local file.

```bash
linxsci parse-pdf --body @pdf-parse.json
```

Required option `--body JSON_OR_@FILE` supplies this endpoint's request body as inline JSON or an existing UTF-8 JSON file. There are no positional arguments or default business fields. Supports shared endpoint options. Prepare `pdf-parse.json` using this endpoint's actual upstream schema; the repository does not define all required business fields, and `{}` is not guaranteed valid. PDF commands forward `LINXSCI_MINERU_API_KEY` when set. Retain the returned task ID and inspect its status before fetching the result.

## Paper resources

### paper

```bash
linxsci paper "<paper-id>"
linxsci paper "<paper-id>" --resource toc
linxsci paper "<paper-id>" --resource sections --item-id "<section-id>"
linxsci --output asset.bin paper "<paper-id>" --resource assets --item-id "<asset-id>"
```

| Argument | Required / default | Meaning |
| --- | --- | --- |
| `paper_id` | Required positional string | Raw returned ID with `local:`, `arxiv:`, `openalex:`, `s2:` or `doi:` prefix; the script URL-encodes it |
| `--resource NAME` | Optional, default paper details | Select one resource from the table below |
| `--item-id ID` | Required for `sections` / `assets`, otherwise forbidden | Raw section/asset ID from a real response; automatically encoded |

All resources use GET and support shared endpoint options.

| `--resource` | Path after `/openapi/v2/papers/{paper_id}` | Result |
| --- | --- | --- |
| omitted | none | Paper details |
| `content` | `/content` | Paper content |
| `toc` | `/toc` | Table of contents and actual section IDs |
| `sections` | `/sections/{section_id}` | One section; requires `--item-id` |
| `figures` | `/figures` | Figure information |
| `assets` | `/assets/{asset_id}` | One asset; requires `--item-id`; use global `--output` for binary data |
| `references` | `/references` | Referenced papers |
| `citations` | `/citations` | Papers citing this paper |
| `related` | `/related` | Related papers |
| `graph` | `/graph` | Citation graph |
| `citation` | `/citation` | Citation representation |

Use IDs returned by search, contents, or figures; do not infer an ID from a title. A raw DOI ID such as `doi:10.1000/example` is encoded automatically. Pre-encoding convenience-command IDs would encode `%` again.

## Authors, institutions and venues

### author

```bash
linxsci author "<returned-author-id>"
linxsci author "<returned-author-id>" --papers
```

Required positional `entity_id` is the actual raw author identifier, automatically URL-encoded. Optional flag `--papers` defaults to off: without it, GET `/openapi/v2/authors/{author_id}` returns details; with it, GET `/openapi/v2/authors/{author_id}/papers` returns papers. Do not add a paper-source prefix unless it is part of the actual entity ID. Supports shared `--param` and `--request-id`; pagination keys must come from the upstream contract.

### institution

```bash
linxsci institution "<returned-institution-id>"
linxsci institution "<returned-institution-id>" --papers
```

Required positional `entity_id` is the actual raw institution identifier, automatically URL-encoded. Optional flag `--papers` defaults to off: without it, GET `/openapi/v2/institutions/{institution_id}` returns details; with it, GET `/openapi/v2/institutions/{institution_id}/papers` returns papers. Do not add a paper-source prefix unless it is part of the actual entity ID. Supports shared `--param` and `--request-id`; pagination keys must come from the upstream contract.

### venue

```bash
linxsci venue "<returned-venue-id>"
linxsci venue "<returned-venue-id>" --papers
```

Required positional `entity_id` is the actual raw venue identifier, automatically URL-encoded. Optional flag `--papers` defaults to off: without it, GET `/openapi/v2/venues/{venue_id}` returns details; with it, GET `/openapi/v2/venues/{venue_id}/papers` returns papers. Do not add a paper-source prefix unless it is part of the actual entity ID. Supports shared `--param` and `--request-id`; pagination keys must come from the upstream contract.

## PDF upload and tasks

### upload

`POST /openapi/v2/pdf/parse/upload`, using multipart form data.

```bash
linxsci upload "/absolute/path/paper.pdf"
linxsci upload "/absolute/path/paper.pdf" --field "<contract-field>=<value>"
```

| Argument | Required / default | Meaning |
| --- | --- | --- |
| `file` | Required positional file path | Existing readable local PDF; sent as multipart field `file` with `application/pdf` content type |
| `--field KEY=VALUE` | Repeatable, default no extra fields | Additional multipart fields from the upstream contract; each field name must be unique and nonempty; values are strings |

Supports shared endpoint options. The script builds the multipart boundary; do not supply `--body` or manually set Content-Type. It sends the selected file to the configured service. File-size limits and business validation are determined by that service. `LINXSCI_MINERU_API_KEY`, when set, is forwarded as `X-MinerU-API-Key`. Record the returned task ID; do not automatically repeat an upload with an uncertain result.

### task

```bash
linxsci task "<returned-task-id>"
linxsci task "<returned-task-id>" --result
```

Required positional `task_id` is the actual raw returned identifier, automatically URL-encoded; it cannot be empty, `.`, `..`, or reserved `upload`. Optional flag `--result` defaults to off: without it, GET `/openapi/v2/pdf/parse/{task_id}` queries status; with it, GET `/openapi/v2/pdf/parse/{task_id}/result` fetches the result. Supports shared endpoint options and forwards `LINXSCI_MINERU_API_KEY` when set.

Inspect the actual status schema and confirm completion before requesting a result. This command makes one request; it does not poll or wait automatically. There is no documented universal terminal-state field. Use global `--output result.bin` before `task` to preserve binary results.

## Generic requests

### request

```bash
linxsci request GET /meta
linxsci request POST /papers/resolve --body @papers-resolve.json
linxsci request POST /papers/search --body '{"query":"graph neural networks"}'
linxsci request GET "/papers/doi:10.1000%2Fexample/toc"
```

| Argument | Required / default | Meaning |
| --- | --- | --- |
| `method` | Required positional, `GET` or `POST` | Uppercase HTTP method from the supported route list |
| `path` | Required positional string | Supported path beginning `/`, relative to `/openapi/v2`; not a full URL; encode each dynamic segment yourself |
| `--body JSON_OR_@FILE` | Required for JSON POST; omit for GET | Inline JSON or an existing UTF-8 JSON file matching the endpoint contract |

Supports shared endpoint options and forwards `LINXSCI_MINERU_API_KEY` for PDF paths when set. Only mapped method/path combinations are allowed. The path cannot contain `?` / `#` or unencoded segment slashes; use `--param` for queries. An encoded DOI slash is `%2F`. Generic requests do not validate the paper-source prefix as convenience `paper` does, so supply a genuine identifier yourself. GET cannot carry a non-null JSON body. Multipart `/pdf/parse/upload` must use `upload`, since generic `request` has no file argument. Inline JSON quoting above is for Bash; JSON files avoid shell-specific escaping.

## JSON files, environment and output

Search `--body` must parse to an object; other JSON bodies must follow the selected endpoint's schema. Invalid JSON or unreadable UTF-8 files are local failures. File names are examples, not bundled ready-to-run business payloads. The known minimal search body is `{"query":"graph neural networks"}`; this does not define fields for resolve, recommendations, entities or PDF creation.

| Environment variable | Default / behavior |
| --- | --- |
| `LINXSCI_BASE_URL` | Override the saved root; release fallback is `https://linxsci.com` |
| `LINXSCI_OPENAPI_KEY` | Override the saved client key; no default |
| `LINXSCI_CONFIG_FILE` | Override configuration path; otherwise `~/.config/linxsci-skills/config.json` on macOS/Linux or `%LOCALAPPDATA%\linxsci-skills\config.json` on Windows |
| `LINXSCI_MINERU_API_KEY` | Optional `X-MinerU-API-Key` on PDF commands and generic PDF requests; not sent to other endpoints |

Saved settings override release defaults; environment overrides saved settings. Use the LinxSci client key for authentication.

Successful endpoint calls use compact JSON by default, with file references for large or binary responses as described above. Global `--output` preserves original response bytes. There is no common guaranteed list, pagination or task-status schema.

| Exit code | Meaning |
| --- | --- |
| `0` | Successful action |
| `1` | HTTP/network or service diagnostic failure |
| `2` | Argument, configuration, local file or cancellation failure |

`--json-errors` reports `message`, HTTP `status`, `error_code`, `request_id`, `framework_request_id`, `execution_uncertain`, and `retry_after` when an HTTP/network error occurs. Local errors include `error_code` and `message`; `doctor --json` uses its stdout report. Argument-parser errors default to stderr JSON with `error_code:"invalid_arguments"`; local errors use `error_code:"local_error"`, and cancellation uses `error_code:"cancelled"`. `--human-errors` restores readable error text. No automatic retries occur. In particular, `-3905` requires checking execution and accounting before repeating uploads or task creation. See [API errors and accounting](API.md).

## Update and uninstall

For an isolated wheel installation, download the new wheel and run `uv tool install --force /path/to/linxsci-<version>-py3-none-any.whl`. For source installation, update the source and run `python -m pip install --upgrade .` in the same environment. Remove the isolated tool with `uv tool uninstall linxsci`, or the project package with `python -m pip uninstall linxsci`.
