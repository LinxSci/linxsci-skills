# Standalone Skill commands and parameters

[简体中文](cli.zh-CN.md)

Use only the scripts bundled in this Skill. No installed CLI, PyPI package or SDK is required. In every command below, replace `<skill-dir>` with the absolute directory containing `SKILL.md`. Windows users can replace `python3` with `py -3`. See [Skill installation](../SKILL.md#install-the-skill-independently).

## Invocation and option placement

```text
python3 "<skill-dir>/scripts/cli.py" [GLOBAL_OPTIONS] COMMAND [COMMAND_ARGUMENTS]
python3 "<skill-dir>/scripts/cli.py" --help
python3 "<skill-dir>/scripts/cli.py" COMMAND --help
```

`python3 "<skill-dir>/scripts/cli.py"` without arguments shows help. `--help` and `--version` exit without configuration or network access. Global options go **before** the command; command-specific options go **after** it. Quote values containing spaces. Relative file paths are resolved against the current working directory, not the skill directory. Replace `<...>` placeholders before execution.

## Global options

| Option | Type / default | Meaning |
| --- | --- | --- |
| `-h`, `--help` | Flag | Show root help; after a command, show that command's help |
| `--version` | Flag | Print the version and exit |
| `--timeout SECONDS` | Number, default `60` | Positive finite network timeout in seconds; not a total timeout for a PDF task |
| `--output PATH` | File path, unset | For API responses, write original response bytes to this file instead of stdout; overwrites an existing file; the parent directory must exist |
| `--json-errors` | Flag, off | Write structured failure diagnostics to stderr; does not change successful API responses |
| `--framework-request-id ID` | Nonempty printable ASCII, unset | Send `X-ANYTHINGRIGHT-REQ-ID`; framework errors expose it as `extra.request-id`; the server generates the framework ID when omitted |

`--output` applies to endpoint responses, not local configuration/help output or the doctor's diagnostic report. For example:

```bash
python3 "<skill-dir>/scripts/cli.py" --timeout 90 --output search.json search "graph neural networks"
python3 "<skill-dir>/scripts/cli.py" --framework-request-id framework-001 meta --request-id upstream-001
```

## Shared endpoint options

The endpoint commands below all accept these options. Local commands `setup`, `config`, `doctor`, `routes`, and `install-skill` do not accept them.

| Option | Type / default | Meaning |
| --- | --- | --- |
| `--param KEY=VALUE` | Repeatable string, unset | URL query parameter; key must be nonempty. Repeat the same key for multiple values. The script URL-encodes values. Business keys come from the upstream contract |
| `--request-id ID` | Nonempty printable ASCII, generated UUID if omitted | Send upstream/proxy `X-Request-ID`; separate from the global framework trace ID |

```bash
python3 "<skill-dir>/scripts/cli.py" paper "<paper-id>" --param "<contract-key>=<value>" --request-id upstream-001
```

For a contract-defined multi-value key, repeat `--param "KEY=VALUE1" --param "KEY=VALUE2"`. Do not append query strings to a generic request path. `--param` is for URL parameters; `--body` is for JSON; `--field` is for upload form fields. They are not interchangeable. There are no built-in `--limit`, `--page`, or `--year` flags; pass such fields only if the deployed upstream contract defines them.

## Configuration and local commands

### setup

Save a service root and API key, then check `/meta` unless `--no-check` is supplied.

```bash
python3 "<skill-dir>/scripts/cli.py" setup
python3 "<skill-dir>/scripts/cli.py" setup --online
python3 "<skill-dir>/scripts/cli.py" setup --base-url https://linxsci.com --no-check
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
python3 "<skill-dir>/scripts/cli.py" config
python3 "<skill-dir>/scripts/cli.py" config --clear
```

With no options, print `config_file`, `saved_base_url`, `saved_key_configured`, `environment_url_override`, and `environment_key_override`, without the key or a remote request. `--clear` is an optional flag (off by default) that deletes the saved configuration file; it does not unset environment variables. Clear only when requested.

### doctor

```bash
python3 "<skill-dir>/scripts/cli.py" doctor
python3 "<skill-dir>/scripts/cli.py" doctor --json
```

`--json` is an optional flag (off by default) that prints the diagnostic report as JSON on stdout. Reports include `ok`, effective `base_url`, configuration information and, when available, status/error/trace metadata. A missing or invalid local configuration gives exit code 2; service failure gives 1; success gives 0. The check makes a real `/meta` request and requires a configured key. A 200 HTML login page does not count as a working JSON API. Avoid redundant checks because they follow normal call accounting.

### routes

```bash
python3 "<skill-dir>/scripts/cli.py" routes
```

No command-specific parameters. Print all 34 supported method/path templates locally, without a key or network request.

### install-skill

```bash
python3 "<skill-dir>/scripts/cli.py" install-skill
python3 "<skill-dir>/scripts/cli.py" install-skill --skills-dir /absolute/path/to/assistant/skills
python3 "<skill-dir>/scripts/cli.py" install-skill --update
```

| Option | Type / default | Meaning |
| --- | --- | --- |
| `--skills-dir PATH` | Directory, default `~/.agents/skills` | Parent scan directory; the installer appends `/linxsci-skills`. A leading `~` is expanded |
| `--update` | Flag, off | Replace a copy managed by this installer and keep the old version in a sibling `linxsci-skill-backups` directory outside the scan directory |

This action uses local bundled files and needs no key or network. It also works through the standalone skill script without an installed CLI/SDK. When updating, run the command from the **new** downloaded source/bundle so that the new files are copied. The installer rejects symlink destinations and unmanaged or mismatched installation markers; use the original external installer for its copies. This action does not configure a key or register a terminal command.

## Endpoint index: all 34 routes

Each row is an independent example, not a sequence to run in full. Detailed command parameters follow the index.

| No. | Endpoint | Example |
| --- | --- | --- |
| 01 | API metadata | `python3 "<skill-dir>/scripts/cli.py" meta` |
| 02 | Usage | `python3 "<skill-dir>/scripts/cli.py" usage` |
| 03 | Liveness | `python3 "<skill-dir>/scripts/cli.py" health live` |
| 04 | Readiness | `python3 "<skill-dir>/scripts/cli.py" health ready` |
| 05 | Paper search | `python3 "<skill-dir>/scripts/cli.py" search "large language models"` |
| 06 | OpenAlex search | `python3 "<skill-dir>/scripts/cli.py" search-openalex "large language models"` |
| 07 | Semantic Scholar search | `python3 "<skill-dir>/scripts/cli.py" search-semantic-scholar "large language models"` |
| 08 | Google Scholar search | `python3 "<skill-dir>/scripts/cli.py" search-google-scholar "large language models"` |
| 09 | Resolve paper identifiers | `python3 "<skill-dir>/scripts/cli.py" resolve --body @papers-resolve.json` |
| 10 | Batch paper lookup | `python3 "<skill-dir>/scripts/cli.py" batch-get --body @papers-batch-get.json` |
| 11 | Paper details | `python3 "<skill-dir>/scripts/cli.py" paper "<paper-id>"` |
| 12 | Paper content | `python3 "<skill-dir>/scripts/cli.py" paper "<paper-id>" --resource content` |
| 13 | Table of contents | `python3 "<skill-dir>/scripts/cli.py" paper "<paper-id>" --resource toc` |
| 14 | Section | `python3 "<skill-dir>/scripts/cli.py" paper "<paper-id>" --resource sections --item-id "<section-id>"` |
| 15 | Figures | `python3 "<skill-dir>/scripts/cli.py" paper "<paper-id>" --resource figures` |
| 16 | Assets | `python3 "<skill-dir>/scripts/cli.py" --output asset.bin paper "<paper-id>" --resource assets --item-id "<asset-id>"` |
| 17 | References | `python3 "<skill-dir>/scripts/cli.py" paper "<paper-id>" --resource references` |
| 18 | Citing papers | `python3 "<skill-dir>/scripts/cli.py" paper "<paper-id>" --resource citations` |
| 19 | Related papers | `python3 "<skill-dir>/scripts/cli.py" paper "<paper-id>" --resource related` |
| 20 | Citation graph | `python3 "<skill-dir>/scripts/cli.py" paper "<paper-id>" --resource graph` |
| 21 | Citation format | `python3 "<skill-dir>/scripts/cli.py" paper "<paper-id>" --resource citation` |
| 22 | Recommendations | `python3 "<skill-dir>/scripts/cli.py" recommend --body @recommendations.json` |
| 23 | Mobile recommendation cards | `python3 "<skill-dir>/scripts/cli.py" mobile-cards` |
| 24 | Author details | `python3 "<skill-dir>/scripts/cli.py" author "<author-id>"` |
| 25 | Author papers | `python3 "<skill-dir>/scripts/cli.py" author "<author-id>" --papers` |
| 26 | Institution details | `python3 "<skill-dir>/scripts/cli.py" institution "<institution-id>"` |
| 27 | Institution papers | `python3 "<skill-dir>/scripts/cli.py" institution "<institution-id>" --papers` |
| 28 | Venue details | `python3 "<skill-dir>/scripts/cli.py" venue "<venue-id>"` |
| 29 | Venue papers | `python3 "<skill-dir>/scripts/cli.py" venue "<venue-id>" --papers` |
| 30 | Resolve entity identifiers | `python3 "<skill-dir>/scripts/cli.py" resolve-entities --body @entities-resolve.json` |
| 31 | Create a PDF parsing task | `python3 "<skill-dir>/scripts/cli.py" parse-pdf --body @pdf-parse.json` |
| 32 | Upload a PDF and create a task | `python3 "<skill-dir>/scripts/cli.py" upload "/absolute/path/paper.pdf"` |
| 33 | Task status | `python3 "<skill-dir>/scripts/cli.py" task "<task-id>"` |
| 34 | Task result | `python3 "<skill-dir>/scripts/cli.py" task "<task-id>" --result` |

## Service information and health

### meta

`GET /openapi/v2/meta`. Get API metadata. The response is not guaranteed to be a complete business schema.

```bash
python3 "<skill-dir>/scripts/cli.py" meta
```

No positional arguments or dedicated options; supports shared `--param` and `--request-id`. A configured key is required.

### usage

`GET /openapi/v2/usage`. Get account usage information.

```bash
python3 "<skill-dir>/scripts/cli.py" usage
```

No positional arguments or dedicated options; supports shared `--param` and `--request-id`. A configured key is required.

### mobile-cards

`GET /openapi/v2/recommendations/mobile-cards`. Get mobile recommendation cards.

```bash
python3 "<skill-dir>/scripts/cli.py" mobile-cards
```

No positional arguments or dedicated options; supports shared `--param` and `--request-id`. A configured key is required.

### health

`GET /openapi/v2/health/{check}`.

```bash
python3 "<skill-dir>/scripts/cli.py" health live
python3 "<skill-dir>/scripts/cli.py" health ready
```

Required positional `check` is exactly `live` (liveness) or `ready` (readiness); there is no default. Both checks require a configured key and follow normal call accounting. Supports shared endpoint options.

## Search commands

### search

`POST /openapi/v2/papers/search` — integrated paper search.

```bash
python3 "<skill-dir>/scripts/cli.py" search "graph neural networks"
python3 "<skill-dir>/scripts/cli.py" search "graph neural networks" --body @search-options.json
```

| Argument | Required / default | Meaning |
| --- | --- | --- |
| `query` | Required positional string | Search text, sent as JSON `query`; quote multi-word text |
| `--body JSON_OR_@FILE` | Optional, default no extra fields | Additional JSON **object**, inline or UTF-8 file; a `query` inside it is replaced by the positional query |

Supports shared endpoint options. A bare query needs no request file: `"graph neural networks"` produces `{"query":"graph neural networks"}`. Extra fields must follow this provider's deployed contract; do not reuse another provider's model without checking it.

### search-openalex

`POST /openapi/v2/search/openalex` — OpenAlex.

```bash
python3 "<skill-dir>/scripts/cli.py" search-openalex "graph neural networks"
python3 "<skill-dir>/scripts/cli.py" search-openalex "graph neural networks" --body @search-options.json
```

| Argument | Required / default | Meaning |
| --- | --- | --- |
| `query` | Required positional string | Search text, sent as JSON `query`; quote multi-word text |
| `--body JSON_OR_@FILE` | Optional, default no extra fields | Additional JSON **object**, inline or UTF-8 file; a `query` inside it is replaced by the positional query |

Supports shared endpoint options. A bare query needs no request file: `"graph neural networks"` produces `{"query":"graph neural networks"}`. Extra fields must follow this provider's deployed contract; do not reuse another provider's model without checking it.

### search-semantic-scholar

`POST /openapi/v2/search/semantic-scholar` — Semantic Scholar.

```bash
python3 "<skill-dir>/scripts/cli.py" search-semantic-scholar "graph neural networks"
python3 "<skill-dir>/scripts/cli.py" search-semantic-scholar "graph neural networks" --body @search-options.json
```

| Argument | Required / default | Meaning |
| --- | --- | --- |
| `query` | Required positional string | Search text, sent as JSON `query`; quote multi-word text |
| `--body JSON_OR_@FILE` | Optional, default no extra fields | Additional JSON **object**, inline or UTF-8 file; a `query` inside it is replaced by the positional query |

Supports shared endpoint options. A bare query needs no request file: `"graph neural networks"` produces `{"query":"graph neural networks"}`. Extra fields must follow this provider's deployed contract; do not reuse another provider's model without checking it.

### search-google-scholar

`POST /openapi/v2/search/google-scholar` — Google Scholar.

```bash
python3 "<skill-dir>/scripts/cli.py" search-google-scholar "graph neural networks"
python3 "<skill-dir>/scripts/cli.py" search-google-scholar "graph neural networks" --body @search-options.json
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
python3 "<skill-dir>/scripts/cli.py" resolve --body @papers-resolve.json
```

Required option `--body JSON_OR_@FILE` supplies this endpoint's request body as inline JSON or an existing UTF-8 JSON file. There are no positional arguments or default business fields. Supports shared endpoint options. Prepare `papers-resolve.json` using this endpoint's actual upstream schema; the repository does not define all required business fields, and `{}` is not guaranteed valid.

### batch-get

`POST /openapi/v2/papers:batchGet`. Fetch multiple papers in one request.

```bash
python3 "<skill-dir>/scripts/cli.py" batch-get --body @papers-batch-get.json
```

Required option `--body JSON_OR_@FILE` supplies this endpoint's request body as inline JSON or an existing UTF-8 JSON file. There are no positional arguments or default business fields. Supports shared endpoint options. Prepare `papers-batch-get.json` using this endpoint's actual upstream schema; the repository does not define all required business fields, and `{}` is not guaranteed valid.

### recommend

`POST /openapi/v2/recommendations`. Request paper recommendations.

```bash
python3 "<skill-dir>/scripts/cli.py" recommend --body @recommendations.json
```

Required option `--body JSON_OR_@FILE` supplies this endpoint's request body as inline JSON or an existing UTF-8 JSON file. There are no positional arguments or default business fields. Supports shared endpoint options. Prepare `recommendations.json` using this endpoint's actual upstream schema; the repository does not define all required business fields, and `{}` is not guaranteed valid.

### resolve-entities

`POST /openapi/v2/entities:resolve`. Resolve author, institution or venue identifiers.

```bash
python3 "<skill-dir>/scripts/cli.py" resolve-entities --body @entities-resolve.json
```

Required option `--body JSON_OR_@FILE` supplies this endpoint's request body as inline JSON or an existing UTF-8 JSON file. There are no positional arguments or default business fields. Supports shared endpoint options. Prepare `entities-resolve.json` using this endpoint's actual upstream schema; the repository does not define all required business fields, and `{}` is not guaranteed valid.

### parse-pdf

`POST /openapi/v2/pdf/parse`. Create a PDF parsing task from a JSON request. This command does not upload a local file.

```bash
python3 "<skill-dir>/scripts/cli.py" parse-pdf --body @pdf-parse.json
```

Required option `--body JSON_OR_@FILE` supplies this endpoint's request body as inline JSON or an existing UTF-8 JSON file. There are no positional arguments or default business fields. Supports shared endpoint options. Prepare `pdf-parse.json` using this endpoint's actual upstream schema; the repository does not define all required business fields, and `{}` is not guaranteed valid. PDF commands forward `LINXSCI_MINERU_API_KEY` when set. Retain the returned task ID and inspect its status before fetching the result.

## Paper resources

### paper

```bash
python3 "<skill-dir>/scripts/cli.py" paper "<paper-id>"
python3 "<skill-dir>/scripts/cli.py" paper "<paper-id>" --resource toc
python3 "<skill-dir>/scripts/cli.py" paper "<paper-id>" --resource sections --item-id "<section-id>"
python3 "<skill-dir>/scripts/cli.py" --output asset.bin paper "<paper-id>" --resource assets --item-id "<asset-id>"
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
python3 "<skill-dir>/scripts/cli.py" author "<returned-author-id>"
python3 "<skill-dir>/scripts/cli.py" author "<returned-author-id>" --papers
```

Required positional `entity_id` is the actual raw author identifier, automatically URL-encoded. Optional flag `--papers` defaults to off: without it, GET `/openapi/v2/authors/{author_id}` returns details; with it, GET `/openapi/v2/authors/{author_id}/papers` returns papers. Do not add a paper-source prefix unless it is part of the actual entity ID. Supports shared `--param` and `--request-id`; pagination keys must come from the upstream contract.

### institution

```bash
python3 "<skill-dir>/scripts/cli.py" institution "<returned-institution-id>"
python3 "<skill-dir>/scripts/cli.py" institution "<returned-institution-id>" --papers
```

Required positional `entity_id` is the actual raw institution identifier, automatically URL-encoded. Optional flag `--papers` defaults to off: without it, GET `/openapi/v2/institutions/{institution_id}` returns details; with it, GET `/openapi/v2/institutions/{institution_id}/papers` returns papers. Do not add a paper-source prefix unless it is part of the actual entity ID. Supports shared `--param` and `--request-id`; pagination keys must come from the upstream contract.

### venue

```bash
python3 "<skill-dir>/scripts/cli.py" venue "<returned-venue-id>"
python3 "<skill-dir>/scripts/cli.py" venue "<returned-venue-id>" --papers
```

Required positional `entity_id` is the actual raw venue identifier, automatically URL-encoded. Optional flag `--papers` defaults to off: without it, GET `/openapi/v2/venues/{venue_id}` returns details; with it, GET `/openapi/v2/venues/{venue_id}/papers` returns papers. Do not add a paper-source prefix unless it is part of the actual entity ID. Supports shared `--param` and `--request-id`; pagination keys must come from the upstream contract.

## PDF upload and tasks

### upload

`POST /openapi/v2/pdf/parse/upload`, using multipart form data.

```bash
python3 "<skill-dir>/scripts/cli.py" upload "/absolute/path/paper.pdf"
python3 "<skill-dir>/scripts/cli.py" upload "/absolute/path/paper.pdf" --field "<contract-field>=<value>"
```

| Argument | Required / default | Meaning |
| --- | --- | --- |
| `file` | Required positional file path | Existing readable local PDF; sent as multipart field `file` with `application/pdf` content type |
| `--field KEY=VALUE` | Repeatable, default no extra fields | Additional multipart fields from the upstream contract; each field name must be unique and nonempty; values are strings |

Supports shared endpoint options. The script builds the multipart boundary; do not supply `--body` or manually set Content-Type. It sends the selected file to the configured service. File-size limits and business validation are determined by that service. `LINXSCI_MINERU_API_KEY`, when set, is forwarded as `X-MinerU-API-Key`. Record the returned task ID; do not automatically repeat an upload with an uncertain result.

### task

```bash
python3 "<skill-dir>/scripts/cli.py" task "<returned-task-id>"
python3 "<skill-dir>/scripts/cli.py" task "<returned-task-id>" --result
```

Required positional `task_id` is the actual raw returned identifier, automatically URL-encoded; it cannot be empty, `.`, `..`, or reserved `upload`. Optional flag `--result` defaults to off: without it, GET `/openapi/v2/pdf/parse/{task_id}` queries status; with it, GET `/openapi/v2/pdf/parse/{task_id}/result` fetches the result. Supports shared endpoint options and forwards `LINXSCI_MINERU_API_KEY` when set.

Inspect the actual status schema and confirm completion before requesting a result. This command makes one request; it does not poll or wait automatically. There is no documented universal terminal-state field. Use global `--output result.bin` before `task` to preserve binary results.

## Generic requests

### request

```bash
python3 "<skill-dir>/scripts/cli.py" request GET /meta
python3 "<skill-dir>/scripts/cli.py" request POST /papers/resolve --body @papers-resolve.json
python3 "<skill-dir>/scripts/cli.py" request POST /papers/search --body '{"query":"graph neural networks"}'
python3 "<skill-dir>/scripts/cli.py" request GET "/papers/doi:10.1000%2Fexample/toc"
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

Saved settings override release defaults; environment overrides saved settings. Do not confuse the client's key with the server's `AGENT_PUBLIC_API_KEY`.

For successful endpoint calls, JSON is pretty-printed on stdout; non-JSON data is written as raw bytes. Global `--output` saves the original bytes, so the saved JSON need not have stdout's formatting. There is no common guaranteed list, pagination or task-status schema.

| Exit code | Meaning |
| --- | --- |
| `0` | Successful action |
| `1` | HTTP/network or service diagnostic failure |
| `2` | Argument, configuration, local file or cancellation failure |

`--json-errors` reports `message`, HTTP `status`, `error_code`, `request_id`, `framework_request_id`, `execution_uncertain`, and `retry_after` when an HTTP/network error occurs. Local errors may contain only `message`; `doctor --json` uses its stdout report. Argument-parser errors still use argparse's normal stderr help/error format. No automatic retries occur. In particular, `-3905` requires checking execution and accounting before repeating uploads or task creation. See [API errors and accounting](api.md).
