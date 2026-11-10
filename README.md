# LinxSci OpenAPI

[简体中文](README.zh-CN.md)

Search academic papers, read sections and citations, explore research entities, and parse PDFs through LinxSci OpenAPI v2. Choose the interface that fits your workflow; each supports all 34 documented routes.

| Interface | Use it for | Entry point |
| --- | --- | --- |
| [AI Skill](#ai-skill) | Research with an assistant that supports local skills and scripts | `$linxsci-base` |
| [CLI](#cli) | Run commands in a terminal | `linxsci` |
| [Python SDK](#python-sdk) | Integrate the API into a Python application | `from linxsci import LinxSciClient` |

Requires **Python 3.9+** and an existing LinxSci API key for service calls. No third-party Python runtime dependencies are required. This project (`linxsci-openapi-skills`) provides the `linxsci-base` Skill from `skills/linxsci-base/` and the shared `linxsci` Python package for the CLI and SDK. The public Git repository is `LinxSci/linxsci-skills`; repository, Skill and Python package names serve different purposes.

Sign in to the [LinxSci API key page](https://linxsci.com/open-api?tab=keys) to obtain an API key. Follow the installation and configuration steps below to enter it locally; you can reuse an existing valid key and configuration.

## AI Skill

The Skill runs its bundled Python scripts independently. Installing the `linxsci` Python package is optional.

### Install and configure

Download the [Skill installation bundle](https://github.com/LinxSci/linxsci-skills/releases/download/v0.3.4/linxsci-base-0.3.4.zip), extract it fully, and double-click `Install.command` on macOS or `Install.bat` on Windows. In a terminal opened in the extracted directory, run:

```bash
python3 install.py
```

On Windows use `py -3 install.py`. The installer copies the complete Skill to `~/.agents/skills/linxsci-base` and guides you through hidden-input key setup. Use `--skills-dir <parent-directory>` for another assistant location. Refresh or restart your assistant after installation.

With Node.js/npx and a compatible Skill installer, you can also run:

```bash
npx skills add https://github.com/LinxSci/linxsci-skills --skill linxsci-base
```

If cloning times out, use the ZIP above. After installation, ask your assistant:

> Use $linxsci-base to check configuration and guide me through entering my API key locally if needed. Do not ask me to send the key in chat.

### Use the Skill

> Use $linxsci-base to find papers on graph neural networks, read their methods sections, compare the approaches, and cite the returned sources.

> Use $linxsci-base to parse /absolute/path/paper.pdf, record the task ID, and retrieve the result after the task completes.

Replace the PDF path with an accessible local file. Parsing uploads it to your configured service. Ask for the number of papers, response length and language you need; the assistant handles retrieval and presentation.

### Update and uninstall

For copies managed by the bundled installer, extract the new bundle and run from that **new** directory:

```bash
python3 install.py --update --no-config
```

For a custom destination, repeat the same `--skills-dir` option. Updating preserves settings and backs up the previous managed copy outside the assistant scan directory. Update externally managed copies with their original installer.

To uninstall, use the original installer's removal feature or remove the directory created by the bundled installer, then refresh your assistant. If you also want to clear saved settings, ask the assistant to help before removing the Skill.

See the [Skill user guide](docs/USER_GUIDE.md) for installation options, configuration, examples and troubleshooting.

## CLI

### Install and configure

Requires Python 3.9+. Activate an existing virtual environment; run the creation command below only when you need a new environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U linxsci==0.3.4
linxsci --version
linxsci setup
```

`linxsci --version` should print `0.3.4`. It requires no API key and makes no API call. The same package installs both the CLI and SDK.

PyPI installation works from any directory. The active `python` determines the installation environment; changing directories does not change virtual environments. Check the interpreter with `python -c "import sys; print(sys.executable)"`. To explicitly use Python 3.10, replace `python` in these commands with `python3.10`.

See the [CLI installation guide](docs/CLI_GUIDE.md#install-from-pypi) for SSL and proxy troubleshooting, pip version-check warnings, and verification of a fresh remote download without cached files.

Alternatively, install from source:

```bash
git clone https://github.com/LinxSci/linxsci-skills.git linxsci-openapi-skills
cd linxsci-openapi-skills
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
linxsci --version
linxsci setup
```

On Windows create the environment with `py -3 -m venv .venv` and activate it with `.venv\Scripts\activate.bat` in Command Prompt. You can instead install a downloaded wheel with `python -m pip install /path/to/linxsci-0.3.4-py3-none-any.whl`. With uv already installed, `uv tool install /path/to/linxsci-0.3.4-py3-none-any.whl` provides an isolated terminal installation.

`linxsci setup` reads your API key using hidden input. The default service root is `https://linxsci.com`, without `/openapi/v2`. `LINXSCI_BASE_URL` and `LINXSCI_OPENAPI_KEY` override saved settings; `LINXSCI_CONFIG_FILE` selects another configuration file. Default settings are stored in `~/.config/linxsci-skills/config.json` on macOS/Linux or `%LOCALAPPDATA%\linxsci-skills\config.json` on Windows.

### Search, read and parse

```bash
linxsci search "graph neural networks"
linxsci paper "<returned-paper-id>"
linxsci paper "<returned-paper-id>" --resource toc
linxsci paper "<returned-paper-id>" --resource sections --item-id "<returned-section-id>"
linxsci upload /absolute/path/paper.pdf
linxsci task "<returned-task-id>"
linxsci task "<returned-task-id>" --result
```

Use actual IDs from responses. Fetch task results only after completion. PDF commands accept `LINXSCI_MINERU_API_KEY` when the endpoint requires an additional parsing key.

Output and errors default to compact JSON. `--pretty` and `--human-errors` provide readable terminal output. Global `--select`, `--fields`, `--limit` and `--table` shape responses locally. Output over 12000 characters and binary responses are saved to files with JSON references; `read-output` reads saved responses without another API call. See [all CLI commands and parameters](docs/CLI_GUIDE.md).

`linxsci config` shows settings without exposing the key. `linxsci doctor --json` checks `/meta` and consumes a normal API call. `linxsci config --clear` removes saved settings, but leaves environment variables and server-side keys unchanged.

### Update and uninstall

For a PyPI installation, run `python -m pip install --upgrade linxsci`; for uv use `uv tool upgrade linxsci`. Update the source checkout and run `python -m pip install --upgrade .`, or install a new wheel with `python -m pip install --upgrade /path/to/linxsci-<version>-py3-none-any.whl`. For an isolated uv installation, use `uv tool install --force /path/to/linxsci-<version>-py3-none-any.whl`. Replace `<version>` with the downloaded version.

Uninstall using `python -m pip uninstall linxsci` in the installation environment, or `uv tool uninstall linxsci` for an isolated uv installation.

## Python SDK

The CLI and SDK are installed together as `linxsci`. If that package is already installed in your application's environment, no second SDK package is needed. SDK imports and API calls remain compatible with the Skill rename.

### Install

Install from PyPI in the same Python environment that runs your application:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U linxsci==0.3.4
python -c "import linxsci; print(linxsci.__version__)"
```

If your application already has an environment, activate it and run only the installation and verification commands. Verification should print `0.3.4`, confirming that the SDK imports and reports the expected version. It requires no API key and makes no API call. See the [SDK installation guide](docs/DEVELOPMENT.md#install-from-pypi) for troubleshooting and remote download verification.

On Windows use `py -3 -m venv .venv` and `.venv\Scripts\activate.bat` in Command Prompt. For a source installation, download or clone this repository and run `python -m pip install .` from its root in your application environment.

### Configure and call from Python

This example reads the key from the application's environment or prompts without echoing it during local interactive use:

```python
import os
from getpass import getpass
from linxsci import LinxSciClient, LinxSciError

client = LinxSciClient(
    base_url=os.environ.get("LINXSCI_BASE_URL", "https://linxsci.com"),
    api_key=os.environ.get("LINXSCI_OPENAPI_KEY") or getpass("LinxSci API key: "),
    timeout=60,
)

try:
    response = client.search("graph neural networks")
    print(response.json())
except LinxSciError as error:
    print(error.status, error.error_code)
    print(error.request_id, error.framework_request_id)
```

For non-interactive applications, inject the key through your deployment environment or secret manager. Constructor arguments take precedence over environment variables, existing configuration files and the release URL default. The SDK does not automatically load `.env` files. Supplying both `base_url` and `api_key` bypasses saved configuration; constructing the client does not send a request or save the key.

Reuse the configured client to read a paper or upload a PDF:

```python
paper_id = "<actual-returned-paper-id>"
print(client.paper(paper_id, "toc").json())

response = client.upload_pdf(
    "/absolute/path/paper.pdf",
    mineru_key=os.environ.get("LINXSCI_MINERU_API_KEY"),
)
print(response.json())
```

The SDK returns a `Response` with HTTP status, headers and raw `body`; use `.json()` for JSON or save `body` for binary data. The optional PDF key must be read and passed explicitly. Record the actual task ID from the response; use `client.pdf_task(task_id)` to check its state and `client.pdf_task(task_id, result=True)` only after completion. See [SDK methods, parameters and errors](docs/DEVELOPMENT.md).

### Update and uninstall

For a PyPI installation, run `python -m pip install --upgrade linxsci` in your application environment. Install a new wheel with `python -m pip install --upgrade /path/to/linxsci-<version>-py3-none-any.whl` in your application's environment, or update the source and run `python -m pip install --upgrade .`. Restart long-running Python processes after upgrading.

Check the SDK import and version with `python -c "import linxsci; print(linxsci.__version__)"`. Uninstall with `python -m pip uninstall linxsci`. Package removal does not delete application secrets or revoke API keys.

## API reference

POST fields, pagination and PDF task states follow the selected endpoint's contract. Preserve returned IDs and request trace IDs. After an uncertain execution or billing result such as `-3905`, check the operation's status before repeating uploads or task creation.

See [HTTP endpoints, authentication and errors](docs/API.md). Each linked guide includes its Chinese edition.
