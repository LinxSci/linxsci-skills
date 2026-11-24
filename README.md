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

### Discover and add task Skills

Base also helps you discover and add task Skills: literature surveys, research ideas, paper Q&A, manuscript writing, presentations, reproduction and Xiaohongshu posts. Each is installed on demand from its own GitHub repository. The [extension guide](skills/linxsci-base/references/extensions.md) includes the capability directory, installation checks and task continuation.

Copy one of these requests to your Agent:

```text
Use $linxsci-base to list optional LinxSci Skills, explain their uses, and check which are installed or still need configuration.
```

```text
Use $linxsci-base to install linxsci-paper from https://github.com/LinxSci/linxsci-paper. Preserve existing edits and configuration, install requirements.txt in a compatible Python environment, configure Agent and CLI discovery, verify linxsci skill paper --help, and explain how to use it.
```

```text
Use $linxsci-base to turn these research materials into a presentation. If linxsci-ppt is missing, you are authorized to install and verify it using its GitHub README, then continue the original task with its materials and output location.
```

Listing capabilities needs no API key or extension download. The Agent checks actual availability, installs only selected Skills and resumes the task after verification. Cloning the main repository does not retrieve extensions. Base updates do not update their files.

### Install and configure

Download the [Skill installation bundle](https://github.com/LinxSci/linxsci-skills/releases/download/v0.3.5/linxsci-base-0.3.5.zip), extract it fully, and double-click `Install.command` on macOS or `Install.bat` on Windows. In a terminal opened in the extracted directory, run:

```bash
python3 install.py
```

On Windows use `py -3 install.py`. The installer copies the complete Skill to `~/.agents/skills/linxsci-base` and guides you through hidden-input key setup. Use `--skills-dir <parent-directory>` for another assistant location. Refresh or restart your assistant after installation.

The published `v0.3.5` bundle includes extension onboarding, but its bundled guide still describes the earlier 0.3.4 extension baseline. Follow the target repository’s actual requirements. The revised source guidance below will reach download bundles in a future base release; existing 0.3.5 assets remain unchanged.

### Install into Codex or another agent with Skills CLI

The [Skills CLI](https://github.com/vercel-labs/skills#readme) requires Node.js 22.20+ and npx. Install from the public repository for your Codex user:

```bash
npx skills add https://github.com/LinxSci/linxsci-skills --skill linxsci-base -g -a codex
```

To install from a downloaded copy of this project, run from its root:

```bash
npx skills add ./skills/linxsci-base --skill linxsci-base -g -a codex
```

`-g` makes the Skill available across projects. Omit it for installation into the current project. Replace the agent or specify several:

| Agent | Option |
| --- | --- |
| Codex | `-a codex` |
| Claude Code | `-a claude-code` |
| Cursor | `-a cursor` |
| Gemini CLI | `-a gemini-cli` |

```bash
npx skills add https://github.com/LinxSci/linxsci-skills --skill linxsci-base -g -a codex claude-code cursor
```

For multiple agents, Symlink can share one Skill copy. Use the directories reported by the installer and retain any local target permanently; do not link to a temporary extraction directory. You can also send this request to an agent with terminal access:

```text
Install the base Skill using npx skills add https://github.com/LinxSci/linxsci-skills --skill linxsci-base -g -a codex. Check for an existing installation and preserve local changes. Then use the bundled scripts to check configuration; enter the API key interactively on this machine.
```

`linxsci-base` runs its bundled scripts without installing the Python package. For terminal commands, install `linxsci==0.3.5` using the CLI instructions below. Adapted extension source pins SDK `0.3.5` and can share a compatible environment (Python 3.10+ for all seven). Read the downloaded repository’s actual requirements: public copies may not yet include these changes, and old copies pinned to `0.3.4` need their own compatible environment. See the [extension guide](skills/linxsci-base/references/extensions.md) for coordinated source and dependency updates. Reload the assistant after installation.

If cloning times out, use the ZIP above. After installation, ask your assistant:

> Use $linxsci-base to check configuration and guide me through entering my API key locally if needed. Do not ask me to send the key in chat.

### Use the Skill

> Use $linxsci-base to find papers on graph neural networks and return their verified titles, identifiers and source links.

> I remember a paper comparing contrastive and masked pretraining for image classification. Use $linxsci-base to find candidates and verify their titles, identifiers and sources.

For a single-paper factual answer, the assistant hands the verified paper and original question to an available `linxsci-paper-qa` Skill to inspect the relevant source passages. Topic surveys, research ideas, manuscripts and presentations follow their matching task Skill, with base operations supporting individual steps. Missing extensions are reported with installation guidance; base searches and resource retrieval remain available independently.

> Use $linxsci-base to parse /absolute/path/paper.pdf, record the task ID, and retrieve the result after the task completes.

Replace the PDF path with an accessible local file. Parsing uploads it to your configured service. Ask for the number of papers, response length and language you need; the assistant handles retrieval and presentation.

### Update and uninstall

For a user installation managed by Skills CLI from the repository:

```bash
npx skills update linxsci-base -g
```

For a local installation, update the source project, then repeat the original install command from its root with the same agents and scope. Preserve local changes in the installed copy before replacement.

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
python -m pip install -U linxsci==0.3.5
linxsci --version
linxsci setup
```

`linxsci --version` should print `0.3.5`. It requires no API key and makes no API call. The same package installs both the CLI and SDK.

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

On Windows create the environment with `py -3 -m venv .venv` and activate it with `.venv\Scripts\activate.bat` in Command Prompt. You can instead install a downloaded wheel with `python -m pip install /path/to/linxsci-0.3.5-py3-none-any.whl`. With uv already installed, `uv tool install /path/to/linxsci-0.3.5-py3-none-any.whl` provides an isolated terminal installation.

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
python -m pip install -U linxsci==0.3.5
python -c "import linxsci; print(linxsci.__version__)"
```

If your application already has an environment, activate it and run only the installation and verification commands. Verification should print `0.3.5`, confirming that the SDK imports and reports the expected version. It requires no API key and makes no API call. See the [SDK installation guide](docs/DEVELOPMENT.md#install-from-pypi) for troubleshooting and remote download verification.

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

## License

The code and Skill instructions are licensed under the [MIT License](LICENSE), allowing use, modification, commercial use and redistribution. Retain the copyright and permission notice when redistributing.

LinxSci API access requires a valid API key and remains subject to the service's access rules; this software license does not change API authorization, quotas or billing. Third-party dependencies and retrieved papers, images and other materials retain their own licenses.
