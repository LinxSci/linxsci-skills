# Skill user guide

[简体中文](USER_GUIDE.zh-CN.md)

LinxSci Skill lets you search, read and compare papers in an AI assistant using natural language. You can also submit PDFs for parsing. After installation, use `$linxsci-skills` to select this Skill.

## Before you start

- Python 3.9 or newer.
- An AI assistant that supports local skills and tool execution.
- An existing LinxSci API key.

## Install the Skill

### Option 1: Download the installation bundle

Download the [complete Skill bundle](https://github.com/LinxSci/linxsci-skills/releases/download/v0.3.2/linxsci-skills-0.3.2.zip) and extract it fully before installing.

**macOS**: double-click `Install.command` in the extracted directory. If it cannot be opened that way, open a terminal in that directory and run:

```bash
python3 install.py
```

**Windows**: double-click `Install.bat`, or open a terminal in the extracted directory and run:

```bat
py -3 install.py
```

**Linux**: run `python3 install.py` in the extracted directory.

The installer copies the Skill, guides you through hidden-input API key setup on your computer, and checks the connection once. The default destination is `~/.agents/skills/linxsci-skills`. Refresh or restart your assistant, then open a new conversation.

If your assistant scans a different location, specify its parent skills directory:

```bash
python3 install.py --skills-dir /path/to/assistant/skills
```

Do not include the final `linxsci-skills` directory in `--skills-dir`; the installer appends it. Keep the complete installation bundle. Downloading only `SKILL.md` is insufficient.

### Option 2: Use a Skill installer

If Node.js/npx is already available, you can also run:

```bash
npx skills add https://github.com/LinxSci/linxsci-skills --skill linxsci-skills
```

Choose your assistant and installation scope when prompted. After installation, refresh or restart the assistant and follow “Configure and verify” below.

If installation stops at `Cloning repository` with `Clone timed out`, the repository download timed out. Use the ZIP installation method above, which does not require cloning the repository.

### Installation options

These options apply only to the bundle's `install.py`; place them after the filename:

| Option | Default | Purpose |
| --- | --- | --- |
| `--skills-dir PATH` | `~/.agents/skills` | Parent skills directory scanned by your assistant |
| `--update` | Off | Update a copy managed by this installer and retain a backup |
| `--no-config` | Off | Install without starting API key setup |
| `--online` | Off | Suggest the production service root during setup |
| `--base-url URL` | Saved or release default | Suggest a specific service root; takes precedence over `--online` |

`--online` and `--base-url` have no effect with `--no-config`. Run `python3 install.py --help` for installer help. On Windows, replace `python3` with `py -3`.

## Configure and verify

The ZIP installer guides you through configuration. If you used another installer or skipped setup, ask your assistant:

> Use $linxsci-skills to check whether configuration exists. If it is missing, guide me through entering my API key safely on my computer. Do not ask me to send the key in chat.

The default service root is `https://linxsci.com`, without `/openapi/v2`. Enter the API key only during local configuration, not in the conversation.

Once configured, you can ask:

> Use $linxsci-skills to check the service connection once and tell me whether I can start searching for papers.

A connection check makes a real service request. If installation already confirmed the connection, proceed directly to your research question.

Settings default to `~/.config/linxsci-skills/config.json` on macOS/Linux or `%LOCALAPPDATA%\linxsci-skills\config.json` on Windows. If the assistant's environment defines `LINXSCI_BASE_URL` or `LINXSCI_OPENAPI_KEY`, they override saved settings; `LINXSCI_CONFIG_FILE` selects another configuration file. If the assistant still connects to an old address, ask it to check these overrides without showing the key.

## Use it in your assistant

### Find papers

> Use $linxsci-skills to find papers on graph neural networks. Select the three most relevant papers, explain why you chose them, and include source links.

You can specify a topic, filtering criteria and the number of results. The assistant will use the capabilities supported by the service.

### Read a paper

> Use $linxsci-skills to read the first paper we just found. Start with its table of contents, then explain the methods and experiments with source references.

Use actual paper IDs from search results or an existing paper identifier. Section names are not necessarily section IDs.

### Compare papers

> Use $linxsci-skills to compare the methods, experimental settings and limitations of those two papers. Present a table and cite the evidence.

### Parse a PDF

> Use $linxsci-skills to parse /absolute/path/paper.pdf. Record the task ID, retrieve the result after completion, and summarize the main findings.

Replace the path with a real PDF that the assistant can access. Parsing uploads the file to your configured service. While a task is pending, ask the assistant to check that task rather than upload the file again.

### Check usage

> Use $linxsci-skills to check my API usage and briefly explain the result.

### Choose the response format

> Return only three paper titles, short summaries and source links. Read the details only when needed.

> Save the complete result to a file and tell me its location. Keep the conversation response to conclusions and references.

Specify your preferred language, number of papers, length and format. The assistant handles retrieval and presentation. Large responses may be saved locally; you can ask it to read the relevant parts later.

## Update the Skill

**Installed with the ZIP's bundled installer**: download and extract the new release, then run from the **new release's extracted directory**:

```bash
python3 install.py --update --no-config
```

On Windows, use `py -3 install.py --update --no-config`. For a custom destination, also pass the same `--skills-dir PATH` used during installation. Updating preserves existing settings and backs up the previous managed copy outside the assistant's scan directory. Refresh or restart the assistant afterward.

**Installed with another Skill installer**: use that installer's update feature. Do not overwrite its managed copy with a different installation method or keep duplicate copies in locations scanned by the same assistant.

To change settings, ask:

> Use $linxsci-skills to guide me through changing my service address or API key locally. Do not show the key in chat.

## Uninstall the Skill

For a copy managed by an external installer, use its removal feature. For a copy installed by the bundled installer, remove the `linxsci-skills` directory reported during installation, then refresh or restart your assistant.

If you also want to remove saved local settings, ask the assistant to help clear them before uninstalling. Clearing local settings does not revoke the server-side key or remove environment variables.

## Troubleshooting

| Symptom | What to do |
| --- | --- |
| Repository download timed out | Download the complete Skill ZIP from this page and install after extracting it |
| Python is missing | Install Python 3.9+; on Windows you can use `py -3` |
| Assistant cannot find the Skill | Check that the destination is scanned by your assistant, refresh or restart it, and open a new conversation |
| Installer reports an existing copy | Use the update option for a managed copy; update externally managed copies with their original installer |
| API key is invalid | Reconfigure the key locally and check whether the assistant's environment overrides saved settings |
| PDF cannot be read | Check that the file exists and the assistant can access its path |
| `-3900` | The requested endpoint is not enabled; contact the service administrator |
| `-3905` | Execution and accounting are unconfirmed; check the existing task and usage before repeating an upload or task creation |
| Result formatting or saving failed | Ask the assistant to inspect the saved response instead of submitting the original task again just to format its result |

When reporting a problem, include the steps, error code and request trace IDs. Do not include your API key or the full configuration file.
