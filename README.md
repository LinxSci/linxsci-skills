# linxsci-skills

[简体中文](README.zh-CN.md)

Search academic papers, read sections and citations, explore research entities, and parse PDFs through LinxSci OpenAPI v2. The project includes a standalone AI Skill, a CLI, and a Python SDK covering all 34 documented routes.

Requires **Python 3.9+** and a LinxSci API key. The Skill also requires an assistant that can execute local scripts. No third-party Python runtime dependencies are required.

| Component | Name |
| --- | --- |
| Project and AI Skill | `linxsci-skills` (`$linxsci-skills`) |
| CLI / SDK Python package | `linxsci` |
| Terminal command | `linxsci` |
| Python import | `from linxsci import LinxSciClient, LinxSciError` |

## Install the Skill

The Skill runs its bundled scripts independently. Choose one installation method.

With Node.js/npx and a compatible Skill installer:

```bash
npx skills add https://github.com/LinxSci/linxsci-skills --skill linxsci-skills
```

Alternatively, download and extract the [repository source](https://github.com/LinxSci/linxsci-skills), or a standalone `linxsci-skills-0.3.0.zip` bundle. From the extracted directory, run:

```bash
python3 install.py
```

On Windows use `py -3 install.py`. The standalone bundle also includes `Install.command` and `Install.bat`. The installer copies the Skill to `~/.agents/skills/linxsci-skills` and starts hidden-input key setup. Use `--skills-dir <parent-directory>` for another assistant location. See [independent installation and installer parameters](skills/linxsci-skills/SKILL.md#install-the-skill-independently).

> Use $linxsci-skills to find papers on graph neural networks, read their methods sections, compare the approaches, and cite the returned sources.

## Install the CLI or SDK

Download or clone the source, then install it in your Python environment:

```bash
git clone https://github.com/LinxSci/linxsci-skills.git
cd linxsci-skills
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
linxsci setup
linxsci search "graph neural networks"
```

On Windows activate with `.venv\Scripts\activate`. You can also install a local wheel with `python -m pip install /path/to/linxsci-0.3.0-py3-none-any.whl`. For an isolated CLI environment, use `uv tool install /path/to/linxsci-0.3.0-py3-none-any.whl`. SDK applications must install the package in their own Python environment.

## Configure

The default service root is `https://linxsci.com`; do not append `/openapi/v2`. Run setup locally and enter your API key using hidden input. Environment variables override saved settings; upgrades retain your saved service URL.

| Variable | Purpose |
| --- | --- |
| `LINXSCI_BASE_URL` | Service root override |
| `LINXSCI_OPENAPI_KEY` | Client API key override |
| `LINXSCI_CONFIG_FILE` | Configuration file override |
| `LINXSCI_MINERU_API_KEY` | Optional PDF parsing key |

Settings are saved under `~/.config/linxsci-skills/config.json` on macOS/Linux or `%LOCALAPPDATA%\linxsci-skills\config.json` on Windows. `linxsci config` reports settings without revealing the key. `linxsci doctor --json` checks `/meta` and consumes a normal API call. `linxsci config --clear` removes saved settings.

For Skill-only installations, replace `linxsci` in command examples with `python3 "/absolute/path/to/linxsci-skills/scripts/cli.py"` (Windows: `py -3` with the actual path).

## Search, read and parse

```bash
linxsci search "graph neural networks"
linxsci paper "<returned-paper-id>"
linxsci paper "<returned-paper-id>" --resource toc
linxsci paper "<returned-paper-id>" --resource sections --item-id "<returned-section-id>"
linxsci upload /absolute/path/paper.pdf
linxsci task "<returned-task-id>"
linxsci task "<returned-task-id>" --result
```

Use actual paper IDs from search and section IDs from the table of contents. All 34 routes have convenience commands; `request` provides a generic interface. POST fields, pagination and PDF task states follow the selected endpoint's contract.

```python
from linxsci import LinxSciClient

client = LinxSciClient()
print(client.search("graph neural networks").json())
```

## Output and updates

Endpoint output and errors default to compact JSON. Use `--pretty` or `--human-errors` for terminal reading. Global `--select`, `--fields`, and `--limit` shape known response data locally; `--table` packs uniform records. Large output (over 12000 characters) and binary responses are saved to private temporary files with JSON references. `read-output` filters those files locally. Use `--output PATH --output-summary` to save exact response bytes at a chosen path and print file metadata. See [all output options](docs/CLI_GUIDE.md#compact-output-and-explicit-response-views).

Update the Python package from the new source or wheel. To update a managed Skill copy, run `linxsci install-skill --update` from the updated package, or `python3 install.py --update --no-config` in the new source/bundle. The installer retains a backup outside the assistant scan directory. Copies installed by external tools should be updated with those tools.

## Documentation

- [Skill user guide](docs/USER_GUIDE.md)
- [CLI commands and parameters](docs/CLI_GUIDE.md)
- [Python SDK guide](docs/DEVELOPMENT.md)
- [API reference and errors](docs/API.md)
- [Skill instructions](skills/linxsci-skills/SKILL.md)

Each guide links to its Chinese edition.
