# Python SDK and development

[简体中文](DEVELOPMENT.zh-CN.md) · [README](../README.md)

## Install from source

```bash
git clone https://github.com/LinxSci/linxsci-skills.git
cd linxsci-skills
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
linxsci --version
python -c "from linxsci import LinxSciClient; print('SDK import OK')"
```

On Windows activate with `.venv\Scripts\activate`. Use the same environment for installation and execution. For a release wheel, install `linxsci-0.3.0-py3-none-any.whl`. After publication, use `python -m pip install linxsci` inside your application environment. A CLI installed by `uv tool install` lives in a separate environment.

The project and skill are named `linxsci-skills`; the Python distribution, import and terminal command are `linxsci`. Earlier package names, client classes, environment prefixes and configuration directories have been replaced. Uninstall obsolete distributions using the original package manager, update imports to `LinxSciClient` / `LinxSciError`, configure the new `LINXSCI_*` variables or rerun setup, and remove obsolete skill copies from scan directories using their original installer. The current installer updates only its managed `linxsci-skills` directory.

## Configuration

```bash
linxsci setup --online
linxsci config
linxsci doctor --json
```

Setup hides key input. The default root is `https://linxsci.com`, without `/openapi/v2`. Existing saved URLs are retained across upgrades. Precedence is explicit constructor arguments, environment, saved configuration, then the release URL default. A key has no default. `LINXSCI_CONFIG_FILE` selects a separate configuration file.

| Variable | Purpose |
| --- | --- |
| `LINXSCI_BASE_URL` | Service root override |
| `LINXSCI_OPENAPI_KEY` | LinxSci API key override |
| `LINXSCI_CONFIG_FILE` | Configuration file override |
| `LINXSCI_MINERU_API_KEY` | Optional PDF key; SDK callers pass it explicitly |

The default configuration path is `~/.config/linxsci-skills/config.json` on macOS/Linux and `%LOCALAPPDATA%\linxsci-skills\config.json` on Windows. `config` hides keys and does not call the service. `doctor` calls `/meta` and follows normal call accounting. `config --clear` deletes saved settings; environment variables remain independent.

## First search and reading workflow

```python
from linxsci import LinxSciClient, LinxSciError

try:
    client = LinxSciClient(timeout=60)
    response = client.search("graph neural networks")
    print(response.json())
except LinxSciError as error:
    print(error.status, error.error_code)
    print(error.request_id, error.framework_request_id)
```

`python examples/research.py "graph neural networks"` runs the bundled example. Client construction loads settings without issuing an HTTP request.

```python
paper_id = "<actual-returned-paper-id>"
print(client.paper(paper_id).json())
print(client.paper(paper_id, "toc").json())
print(client.paper(paper_id, "sections", item_id="<returned-section-id>").json())
```

Keep the source prefix (`local:`, `arxiv:`, `openalex:`, `s2:`, or `doi:`). Convenience methods encode raw IDs. Obtain section/asset IDs from responses. Read relevant sections first and use full content only when needed. Keep source and section evidence for research conclusions.

## PDF parsing

```python
import os

response = client.upload_pdf(
    "/absolute/path/paper.pdf",
    mineru_key=os.environ.get("LINXSCI_MINERU_API_KEY"),
)
print(response.json())
# Use the actual returned ID, after inspecting the deployed task schema.
task_id = "<returned-task-id>"
print(client.pdf_task(task_id).json())
# Fetch only after the task has completed.
print(client.pdf_task(task_id, result=True).json())
```

The SDK does not automatically read the PDF key from the environment. `pdf_task()` does not accept `mineru_key`; use `request()` with an encoded PDF path when status/result endpoints require that header. Do not assume task ID/status fields or automatically retry task creation.

## Public signatures

```text
LinxSciClient(base_url=None, api_key=None, timeout=60, *, framework_request_id=None)
client.search(query, **options)
client.paper(paper_id, resource=None, *, item_id=None, query=None)
client.upload_pdf(file, *, fields=None, mineru_key=None)
client.pdf_task(task_id, *, result=False)
client.request(method, path, *, query=None, payload=None, file=None,
               fields=None, mineru_key=None, request_id=None, framework_request_id=None)
```

Timeout is a finite positive number of seconds. Each method returns `Response` with `status`, `headers`, and raw `body`; call `.json()` only for JSON responses. Write binary `response.body` directly to a file.

| `request()` parameter | Meaning |
| --- | --- |
| `method`, `path` | Supported GET/POST method and mapped path relative to `/openapi/v2` |
| `query` | Mapping; use lists for repeated values |
| `payload` | JSON value; not accepted for GET |
| `file` | Local PDF for POST `/pdf/parse/upload`; cannot combine with payload |
| `fields` | Additional multipart fields from the deployed contract; upload only |
| `mineru_key` | Optional PDF `X-MinerU-API-Key`, explicitly supplied |
| `request_id` | `X-Request-ID`; generated if omitted |
| `framework_request_id` | `X-ANYTHINGRIGHT-REQ-ID`; overrides the constructor value |

## All 34 SDK endpoints

Each row is independent. Prepare endpoint-specific `*_body` values using the upstream contract or read JSON from a file. `{}` is not universally valid. Paper/section/asset/task IDs below are raw; entity variables ending in `_encoded` must be encoded with `urllib.parse.quote(raw_id, safe=":")`. Supply an existing `pdf_path`, optional `pdf_fields`, and `mineru_key` as required.

| Method and path | SDK call |
| --- | --- |
| `GET /openapi/v2/meta` | `client.request("GET", "/meta")` |
| `GET /openapi/v2/usage` | `client.request("GET", "/usage")` |
| `GET /openapi/v2/health/live` | `client.request("GET", "/health/live")` |
| `GET /openapi/v2/health/ready` | `client.request("GET", "/health/ready")` |
| `POST /openapi/v2/papers/search` | `client.search("graph neural networks")` |
| `POST /openapi/v2/search/openalex` | `client.request("POST", "/search/openalex", payload=openalex_body)` |
| `POST /openapi/v2/search/semantic-scholar` | `client.request("POST", "/search/semantic-scholar", payload=semantic_scholar_body)` |
| `POST /openapi/v2/search/google-scholar` | `client.request("POST", "/search/google-scholar", payload=google_scholar_body)` |
| `POST /openapi/v2/papers/resolve` | `client.request("POST", "/papers/resolve", payload=papers_resolve_body)` |
| `POST /openapi/v2/papers:batchGet` | `client.request("POST", "/papers:batchGet", payload=papers_batch_get_body)` |
| `GET /openapi/v2/papers/{paper_id}` | `client.paper(paper_id)` |
| `GET /openapi/v2/papers/{paper_id}/content` | `client.paper(paper_id, "content")` |
| `GET /openapi/v2/papers/{paper_id}/toc` | `client.paper(paper_id, "toc")` |
| `GET /openapi/v2/papers/{paper_id}/sections/{section_id}` | `client.paper(paper_id, "sections", item_id=section_id)` |
| `GET /openapi/v2/papers/{paper_id}/figures` | `client.paper(paper_id, "figures")` |
| `GET /openapi/v2/papers/{paper_id}/assets/{asset_id}` | `client.paper(paper_id, "assets", item_id=asset_id)` |
| `GET /openapi/v2/papers/{paper_id}/references` | `client.paper(paper_id, "references")` |
| `GET /openapi/v2/papers/{paper_id}/citations` | `client.paper(paper_id, "citations")` |
| `GET /openapi/v2/papers/{paper_id}/related` | `client.paper(paper_id, "related")` |
| `GET /openapi/v2/papers/{paper_id}/graph` | `client.paper(paper_id, "graph")` |
| `GET /openapi/v2/papers/{paper_id}/citation` | `client.paper(paper_id, "citation")` |
| `POST /openapi/v2/recommendations` | `client.request("POST", "/recommendations", payload=recommendations_body)` |
| `GET /openapi/v2/recommendations/mobile-cards` | `client.request("GET", "/recommendations/mobile-cards")` |
| `GET /openapi/v2/authors/{author_id}` | `client.request("GET", f"/authors/{author_id_encoded}")` |
| `GET /openapi/v2/authors/{author_id}/papers` | `client.request("GET", f"/authors/{author_id_encoded}/papers")` |
| `GET /openapi/v2/institutions/{institution_id}` | `client.request("GET", f"/institutions/{institution_id_encoded}")` |
| `GET /openapi/v2/institutions/{institution_id}/papers` | `client.request("GET", f"/institutions/{institution_id_encoded}/papers")` |
| `GET /openapi/v2/venues/{venue_id}` | `client.request("GET", f"/venues/{venue_id_encoded}")` |
| `GET /openapi/v2/venues/{venue_id}/papers` | `client.request("GET", f"/venues/{venue_id_encoded}/papers")` |
| `POST /openapi/v2/entities:resolve` | `client.request("POST", "/entities:resolve", payload=entities_resolve_body)` |
| `POST /openapi/v2/pdf/parse` | `client.request("POST", "/pdf/parse", payload=pdf_parse_body, mineru_key=mineru_key)` |
| `POST /openapi/v2/pdf/parse/upload` | `client.upload_pdf(pdf_path, fields=pdf_fields, mineru_key=mineru_key)` |
| `GET /openapi/v2/pdf/parse/{task_id}` | `client.pdf_task(task_id)` |
| `GET /openapi/v2/pdf/parse/{task_id}/result` | `client.pdf_task(task_id, result=True)` |

For generic requests, encode each ID separately, including embedded DOI slashes:

```python
import json
from pathlib import Path
from urllib.parse import quote

entity_id = quote("<returned-author-id>", safe=":")
response = client.request("GET", f"/authors/{entity_id}/papers", query={"<contract-key>": "<value>"})
payload = json.loads(Path("resolve.json").read_text(encoding="utf-8"))
response = client.request("POST", "/papers/resolve", payload=payload)
```

## Errors and trace IDs

Local input failures raise `ValueError`, file failures may raise `OSError`, and HTTP/network failures raise `LinxSciError`. HTTP errors retain original `body` and `headers`; avoid logging sensitive response content. Diagnostic properties are `status`, `error_code`, `request_id`, `framework_request_id`, and `execution_uncertain`. Upstream business errors keep their own format; framework errors use `code/data/error/extra`. `extra.cost` measures seconds, not billing amount.

```python
response = client.request(
    "GET", "/meta",
    request_id="upstream-001",
    framework_request_id="framework-001",
)
```

The two IDs have different purposes. Framework IDs may also be set on the constructor. See [API errors and accounting](API.md) for all public codes. `-3905` means upstream returned but accounting finish is uncertain: query execution and billing before repeating a possible write. The client does not retry automatically. `Retry-After` does not resolve uncertain execution.

## CLI, skill and extensions

The CLI exposes common actions directly under `linxsci`; see [all endpoint commands](CLI_GUIDE.md). Skill installation is optional for SDK use. Run `linxsci install-skill --update` after source changes to refresh a managed assistant copy.

The package maps `linxsci` to `skills/linxsci-skills`. `scripts/cli.py` handles the root command, `commands.py` implements current actions, `client.py` handles transport, `config.py` handles settings, and `installer.py` copies the self-contained skill. Keep scripts usable without installing the SDK. New capability groups may be registered in `cli.CAPABILITIES` only when their handlers are implemented and packaged; handlers receive their own argv and a `prog` display name. Do not advertise unimplemented capabilities.

```bash
python -m unittest discover -s tests -v
python tools/build_release.py --bundle-only
```

See [testing](TESTING.md) for remote acceptance and [releasing](RELEASING.md) for artifact checks.
