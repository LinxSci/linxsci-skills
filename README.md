# linxsci-skills

[简体中文](README.zh-CN.md)

Endpoint output now defaults to compact JSON, and errors default to structured JSON on stderr. Use `--pretty` or `--human-errors` for terminal reading. Global `--select`, `--fields`, and `--limit` shape known response data locally; `--table` packs uniform records. Large responses (over 12000 output characters) and binary assets are saved to private temporary files with JSON references. `--output PATH --output-summary` saves raw bytes at a chosen path and reports metadata. See [output options](docs/CLI_GUIDE.md#compact-output-and-explicit-response-views).

Search academic papers, read sections and citations, explore research entities, and parse PDFs through LinxSci OpenAPI v2. The project includes an AI skill, a CLI, and a Python SDK covering all 34 documented routes.

Requires **Python 3.9+**, an existing LinxSci API key, and an assistant that can execute local scripts when using the skill. No third-party Python runtime dependencies are required.

## Names

| Component | Name |
| --- | --- |
| Project | `linxsci-skills` |
| CLI / SDK Python distribution | `linxsci` |
| AI skill | `linxsci-skills` (`$linxsci-skills`) |
| Terminal command | `linxsci` |
| Python import | `from linxsci import LinxSciClient, LinxSciError` |

Semantic Scholar and Google Scholar retain their provider names and upstream route identifiers.

## Install

From a release wheel:

```bash
python -m pip install /path/to/linxsci-0.3.0-py3-none-any.whl
linxsci setup
linxsci search "graph neural networks"
```

After the renamed distribution is published to PyPI, use `uv tool install linxsci` for the CLI or `python -m pip install linxsci` inside your application environment for the SDK. A uv tool environment does not install the SDK into your application environment. Upgrade with `uv tool upgrade linxsci`.

For the self-contained skill, use a compatible GitHub skill installer:

```bash
npx skills add https://github.com/LinxSci/linxsci-skills --skill linxsci-skills
```

Alternatively, download and extract `linxsci-skills-0.3.0.zip`, then run `python3 install.py` (Windows: `py -3 install.py`), or open `Install.command` / `Install.bat`. The installer copies the skill to `~/.agents/skills/linxsci-skills` and starts configuration. Use `--skills-dir <directory>` for another assistant location. The ZIP installer does not register the terminal command.

With the CLI already installed:

```bash
linxsci install-skill
linxsci setup --online
```

Enter your API key locally using hidden input. The default service is `https://linxsci.com`; do not append `/openapi/v2`. Environment variables override saved configuration. Upgrading does not replace a saved service URL.

## Use the skill

> Use $linxsci-skills to find papers on graph neural networks, read their methods sections, compare the approaches, and cite the returned sources.

Use actual paper IDs from search results and section IDs from the table of contents. The assistant should distinguish abstract evidence from full-text evidence and report missing information.

## Use the CLI and SDK

```bash
linxsci search "graph neural networks"
linxsci --output search.json search "graph neural networks"
linxsci paper "<returned-paper-id>"
linxsci paper "<returned-paper-id>" --resource toc
linxsci paper "<returned-paper-id>" --resource sections --item-id "<returned-section-id>"
linxsci upload /absolute/path/paper.pdf
linxsci task "<returned-task-id>"
linxsci task "<returned-task-id>" --result
```

```python
from linxsci import LinxSciClient

client = LinxSciClient()
response = client.search("graph neural networks")
print(response.json())
```

Global flags such as `--output`, `--timeout`, and `--framework-request-id` go before the action. All 34 routes have convenience commands; `request` provides a generic interface. POST fields, pagination and PDF task states follow the deployed upstream contract, so do not assume `{}` is valid or invent response fields.

## Configuration and updates

`linxsci config` reports settings without revealing the key. `linxsci doctor --json` checks connectivity through `/meta`; it counts as an API call. `linxsci config --clear` removes saved settings. `linxsci install-skill --update` updates a managed skill and retains a backup outside the assistant scan directory.

Use `LINXSCI_BASE_URL`, `LINXSCI_OPENAPI_KEY`, `LINXSCI_CONFIG_FILE`, and optionally `LINXSCI_MINERU_API_KEY`. Settings are saved under `~/.config/linxsci-skills/config.json` on macOS/Linux or `%LOCALAPPDATA%\linxsci-skills\config.json` on Windows. This rename changes the Python distribution, client/error class names, environment variables and configuration directory. Reconfigure with `linxsci setup` and update application imports and deployment settings when moving from an earlier release. Remove obsolete packages and skill copies using their original installation tools to avoid duplicate command ownership and discovery.

## Develop and verify

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
python -m unittest discover -s tests -v
python tools/build_release.py --bundle-only
```

On Windows activate with `.venv\Scripts\activate`. Changes to a copied skill require `linxsci install-skill --update`.

## Documentation

Every English guide links to its Chinese edition.

- [User guide](docs/USER_GUIDE.md)
- [Python SDK and development](docs/DEVELOPMENT.md)
- [All 34 CLI endpoints](docs/CLI_GUIDE.md)
- [API contract](docs/API.md)
- [Testing and skill evaluation](docs/TESTING.md)
- [Releasing](docs/RELEASING.md)
- [Website publishing](docs/WEBSITE_PUBLISHING.md)
- [Skill instructions](skills/linxsci-skills/SKILL.md)
