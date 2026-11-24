# GitHub repository installation

[简体中文](SKILL_INSTALLATION.zh-CN.md)

The [main repository](https://github.com/LinxSci/linxsci-skills) provides `skills/linxsci-base/`. Each extension provides a complete Skill at the root of its own repository:

| Skill | Public source repository |
| --- | --- |
| `linxsci-idea` | https://github.com/LinxSci/linxsci-idea |
| `linxsci-survey` | https://github.com/LinxSci/linxsci-survey |
| `linxsci-paper-qa` | https://github.com/LinxSci/linxsci-paper-qa |
| `linxsci-paper` | https://github.com/LinxSci/linxsci-paper |
| `linxsci-ppt` | https://github.com/LinxSci/linxsci-ppt |
| `linxsci-reproduce` | https://github.com/LinxSci/linxsci-reproduce |
| `linxsci-xiaohongshu` | https://github.com/LinxSci/linxsci-xiaohongshu |

Cloning the main repository does not retrieve extensions. Download, install and update each independently, checking its README, requirements and workflow interfaces for compatibility.

## Installation

Give the one-paragraph installation request in the target repository’s README to the current Agent to install Skill files, Python dependencies and discovery configuration. For Skills CLI, install Idea for Codex with:

```bash
npx skills add https://github.com/LinxSci/linxsci-idea --skill linxsci-idea -g -a codex
```

This method needs Node.js 22.20+ and npx. Adjust `-a` for the current Agent and omit `-g` for project scope. Alternatively clone the target repository or download its source ZIP and put the complete directory in the Agent’s discovery location, with `SKILL.md` directly inside it. From a local source root, use `npx skills add . --skill linxsci-idea -g -a codex`; retain the source when using links.

Create or reuse a Python environment that meets the target repository’s requirements: Python 3.9+ for most extensions, and Python 3.10+ for Xiaohongshu. Keep the environment outside the Skill directory and install that repository’s `requirements.txt` with the same interpreter used to run it. Current extensions require `linxsci==0.3.4`; Xiaohongshu also needs PyMuPDF, Pillow and fonts. Configure the current Agent’s discovery path and, when needed, set CLI `LINXSCI_SKILLS_DIR` to the absolute parent containing complete Skill folders. Check the SDK version and actual Skill help, and configure API access locally with `linxsci setup` when needed.

On Windows, enable Python UTF-8 in the current shell or Agent subprocess environment before running SDK/Skill commands, especially when capturing or redirecting Chinese help or JSON output. In PowerShell use `$env:PYTHONUTF8 = '1'`; in Command Prompt use `set PYTHONUTF8=1`. Agents should pass `PYTHONUTF8=1` to child processes and decode captured text as UTF-8. This applies to SDK 0.3.4 and requires no global settings change.

## Collaboration and updates

Idea needs Survey only for fresh retrieval or supplementary searches. Its bundled `scripts/install_survey.py` installs from Survey’s GitHub repository using Git; first prepare the compatible SDK in the same interpreter. Reuse existing installation authorization and resume the task with its original arguments, evidence, output paths and working directory after verification. Existing evidence reuse does not need Survey. Paper and other extensions select collaborators as needed without recursively installing the entire collection.

For Git clones, preserve local changes before `git pull --ff-only`. Use the supported update method for Skills CLI copies; update local source before repeating local installation. Replace manual copies with complete source from the same repository while preserving configuration and edits. Synchronize requirements and refresh the Agent afterward.

CLI/SDK installation and publication remain in the [CLI guide](CLI_GUIDE.md) and [release guide](RELEASING.md). See [local development](LOCAL_DEVELOPMENT.md) for repository layout and development baselines.
