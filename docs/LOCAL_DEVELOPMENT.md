# Independent repositories and local development

The main repository owns the CLI, SDK, `skills/linxsci-base/`, shared documentation and base build tools. The seven extensions retain their own complete `.git/` directories under `skills/`, ignored by the main repository, and publish their own GitHub source. The base Skill has no separate `.git`; no submodules are used.

| Local location | GitHub repository |
| --- | --- |
| Main repository and `skills/linxsci-base/` | `LinxSci/linxsci-skills` |
| `skills/linxsci-idea/` | `LinxSci/linxsci-idea` |
| `skills/linxsci-survey/` | `LinxSci/linxsci-survey` |
| `skills/linxsci-paper-qa/` | `LinxSci/linxsci-paper-qa` |
| `skills/linxsci-paper/` | `LinxSci/linxsci-paper` |
| `skills/linxsci-ppt/` | `LinxSci/linxsci-ppt` |
| `skills/linxsci-reproduce/` | `LinxSci/linxsci-reproduce` |
| `skills/linxsci-xiaohongshu/` | `LinxSci/linxsci-xiaohongshu` |

Existing Codeup remotes may remain for development; public users need no Codeup access. Preserve existing `origin` remotes. Verify the destination when publishing: the established main repository uses `github` for public GitHub, and extensions can use the same name for their respective repositories. Repository creation and pushes belong to the publication task. Never store credentials in public configuration.

## Set up a workspace

```bash
git clone https://github.com/LinxSci/linxsci-skills.git
cd linxsci-skills
git clone https://github.com/LinxSci/linxsci-idea.git skills/linxsci-idea
```

Clone the other extensions separately using the table; preserve existing directories. Cloning the main repository does not retrieve extensions. Public installation is covered in the [GitHub installation guide](SKILL_INSTALLATION.md).

## Local environment

Use Python 3.10 or a later compatible version for all extensions together. After checking out the required extensions:

```bash
python3.10 -m venv .local/dev-venv
source .local/dev-venv/bin/activate
python -m pip install -e . -r skills/linxsci-xiaohongshu/requirements.txt
export LINXSCI_SKILLS_DIR="$PWD/skills"
linxsci --help
linxsci skill survey --help
```

The base project alone does not require extension checkouts or Xiaohongshu dependencies. Follow the actual requirements and published compatibility constraints of each extension.

Existing local checkouts can use `.local/activate.sh` and `.local/linxsci-skills.code-workspace`. The editor workspace explicitly lists the seven independent repositories for separate commits. Files under `.local/` are not committed.

`LINXSCI_SKILLS_DIR` controls CLI discovery; assistant Skill discovery is configured separately. Existing `.agents/skills/` links still target the same directories, and `.local/codex-dev` remains the established local development launcher.

## Commits, version records and distribution

Inspect, verify and commit each extension from its own directory. The main repository’s status omits ignored extensions, and its commits do not save their changes. Do not force-add extensions to the main index.

`extensions.lock.json` remains a `development-baseline` for integration commits, without controlling public installation. Update it only after real commits exist and are retrievable from the relevant remote; uncommitted work cannot be attributed to a pinned commit. Users check compatibility through each extension’s README, actual requirements and workflow interfaces.

Each extension publishes GitHub source including its tracked tests and development tools, so development verification can run from an individual repository. Schedule CLI/SDK releases only when their functionality or package data requires it. Preserve historical build assets and acceptance evidence unchanged.
