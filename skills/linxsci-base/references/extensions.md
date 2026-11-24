# Discover and add LinxSci Skills

[简体中文](extensions.zh-CN.md)

Use this guide to list optional capabilities, install a selected Skill, or add a missing collaborator while continuing a task. The current Agent performs the installation. Base remains usable on its own with Python 3.9+ and the standard library. Reading this directory needs no API key, SDK, Git, npx or network requests.

## Choose a capability

Each extension is a complete Skill in its own GitHub repository. These are available choices, not a list of what is installed on this computer.

| Skill | Use it for | GitHub source | Verify its entrypoint |
| --- | --- | --- | --- |
| `linxsci-survey` | Topic surveys and literature evidence | https://github.com/LinxSci/linxsci-survey | `linxsci survey --help` |
| `linxsci-idea` | Research questions, directions and testable plans | https://github.com/LinxSci/linxsci-idea | `linxsci idea --help` |
| `linxsci-paper-qa` | Single-paper reading and evidence-based factual answers | https://github.com/LinxSci/linxsci-paper-qa | `linxsci paper-qa --help` |
| `linxsci-paper` | Manuscript outlines, sections, drafts and revisions | https://github.com/LinxSci/linxsci-paper | `linxsci skill paper --help` |
| `linxsci-ppt` | Presentations from papers or research materials | https://github.com/LinxSci/linxsci-ppt | `linxsci ppt --help` |
| `linxsci-reproduce` | Research code inspection, environments and reproduction | https://github.com/LinxSci/linxsci-reproduce | `linxsci reproduce --help` |
| `linxsci-xiaohongshu` | Paper explanations and Xiaohongshu text/image posts | https://github.com/LinxSci/linxsci-xiaohongshu | `linxsci xiaohongshu --help` |

`linxsci paper` queries base paper resources; manuscript work uses `linxsci skill paper`. Installing the main repository or Python package does not install these extensions. `install-skill` copies only base; it does not accept an extension name or download extensions.

## Ask the Agent

```text
Use $linxsci-base to list optional LinxSci Skills, explain their uses, and check which are installed or still need configuration in the current environment.
```

```text
Use $linxsci-base to install linxsci-paper from https://github.com/LinxSci/linxsci-paper. Preserve existing edits and configuration, install requirements.txt in a compatible Python environment, configure discovery for this Agent and the CLI, verify linxsci skill paper --help, and explain how to use it.
```

```text
Use $linxsci-base to turn these research materials into a presentation. If linxsci-ppt is missing, you are authorized to install and verify it using its GitHub README, then continue this task with the original materials and output location.
```

## Check the current installation

Identify the current Agent and its actual discovery directories. Check the CLI's separate configuration: it defaults to `~/.agents/skills`; `LINXSCI_SKILLS_DIR` replaces that location with an absolute parent containing complete Skill folders. Inspect any relevant existing copies, dependencies and executable paths before installing. A development checkout alone does not establish Agent discovery, and CLI discovery does not establish discovery by every Agent. See [CLI discovery](cli.md#discover-and-invoke-installed-skills).

When listing capabilities, report the scope you checked and distinguish verified usable installations, files present but dependencies/discovery needing work, absent copies in the checked location, and unchecked status. Do not run research APIs to list Skills. Reuse complete compatible copies. Preserve existing edits and configuration; handle conflicts before replacement and keep backups outside discovery directories.

## Install the selected Skill

An explicit request to install a selected Skill authorizes that installation. Reuse installation authorization already given in the session; obtain missing authorization only when needed. Choose only the requested extension and collaborators required by the task. Preserve the requested project/user scope. Skill installation does not authorize experiments or content publication.

Read the selected repository's README, SKILL and requirements. Choose a supported acquisition method for the available tools and Agent:

- **Skills CLI** needs Node.js 22.20+ and npx. For a user-level Codex installation of Paper, run `npx skills add https://github.com/LinxSci/linxsci-paper --skill linxsci-paper -g -a codex`. Replace the repository, Skill and Agent as appropriate. For project scope run in the project and omit `-g`. From a persistent local source root containing SKILL.md, use `npx skills add . --skill linxsci-paper -g -a codex`. Record the actual destination reported by the tool.
- **Git**: clone the chosen public HTTPS repository into a new staging directory, inspect it, then place the complete Skill in the actual discovery directory. For example, `git clone https://github.com/LinxSci/linxsci-paper.git /absolute/new/staging/linxsci-paper`. Do not merge it over an existing installation.
- **Source ZIP**: download the selected repository's source archive, inspect and extract it, and place its contents in a directory named for the Skill. SKILL.md must be directly inside that directory, without an extra archive-name layer. Retain scripts, references, agents, requirements and license files.

Keep symlink targets in persistent locations. Git or Skills CLI is not required when manually installing a source archive. If the public repository is unavailable or a download fails, report the failed step and preserve existing materials; do not silently substitute Codeup, old Release packages or a mirror.

### Python dependencies and tools

Current extensions require `linxsci==0.3.4`. Survey, Idea, Paper QA, Paper, PPT and Reproduce use Python 3.9+; Xiaohongshu requires Python 3.10+, PyMuPDF, Pillow and fonts supporting the content language. Read the current target requirements before acting. Word/LaTeX production, presentation production and reproduction experiments have additional tools described by their respective Skills.

Base `0.3.5` runs its bundled scripts independently and does not require extensions to upgrade their SDK. If an existing CLI/SDK environment uses `0.3.5`, reuse or create a separate environment for extensions still pinned to `0.3.4`, and run them with that environment's Python and CLI. Do not downgrade the existing environment by installing those requirements into it or bypass the dependency constraints.

Reuse a compatible environment or create a virtual environment outside Skill folders. Install dependencies with the same interpreter used for execution, substituting the real requirements path:

```bash
python -m pip install -r "/absolute/path/to/linxsci-paper/requirements.txt"
python -m pip check
linxsci --version
linxsci skill paper --help
```

Activate that environment or use its explicit executable paths so `python` and `linxsci` belong to it. Reuse compatible installed dependencies; resolve version conflicts without overwriting other task environments. Installing Skill files alone does not install requirements. Do not upgrade the SDK or loosen version pins based only on this catalog.

Configure the current Agent's discovery path. If the CLI uses another parent, set it in the environment used to invoke the CLI:

```bash
export LINXSCI_SKILLS_DIR="/absolute/path/to/assistant/skills"
```

Windows PowerShell:

```powershell
$env:LINXSCI_SKILLS_DIR = "C:\path\to\assistant\skills"
$env:PYTHONUTF8 = '1'
```

For Windows Command Prompt, use `set PYTHONUTF8=1`. Agents capturing output should pass `PYTHONUTF8=1` to child processes and decode UTF-8. These are per-session settings. Refresh or restart the Agent when required; report discovery as pending until it can be checked. Configure API access locally with `linxsci setup` only when service calls are needed, reusing valid settings and never requesting a key in chat.

## Finish installation or resume the task

Report the source and available commit, installation directory, Python interpreter, dependency versions, discovery status, verification results and a usage example. Distinguish success, failure, cancellation and steps still pending. Passing help verifies an entrypoint, not completion of a research or production task.

For an installation-only request, finish with usage guidance. When adding a Skill during a task, load that Skill and continue with the original goal, working directory, inputs, verified evidence, arguments and output location. Do not discard context or restart completed research. For Paper installation, verify `linxsci skill paper --help` before handing off writing; for a missing PPT Skill, install and verify it, check its production tools, then continue preparing the requested presentation.

Idea needs Survey only for fresh retrieval or supplementary searches; use Idea's existing `scripts/install_survey.py` and its documented result checks with the same Python environment. Offline evidence reuse does not require Survey. Follow each Skill's collaboration instructions without recursively installing the whole collection. On refusal or failure, retain useful materials and identify what remains incomplete; base operations remain available.

## Update an extension

Preserve local changes first. For Git clones use `git pull --ff-only`; for user-level Skills CLI repository installs use, for example, `npx skills update linxsci-paper -g`. Update persistent local sources before repeating local installation; update manual copies from complete source from the same repository. Recheck requirements and the actual Skill entrypoint, then refresh discovery. Python package updates and base updates do not update extension files.
