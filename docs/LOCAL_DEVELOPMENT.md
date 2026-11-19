# Independent repositories and local development

The main repository owns the CLI, SDK, `skills/linxsci-base/`, public documentation and build tools. Seven extension repositories live under `skills/`, each with its own complete `.git/` and existing Codeup remote. The main repository ignores those directories. The base Skill must not have a separate `.git` directory.

Cloning the public repository provides the base Skill and CLI/SDK source. Extensions require separate installation; ignored local checkouts are not included in main-repository commits or GitHub’s automatic source ZIPs. [Fixed-commit builds](SKILL_RELEASES.md) produce single packages, a full suite and a source snapshot with actual extension files. Each single package includes the shared installer.

## Repository ownership

| Location | Repository | Current development branch |
| --- | --- | --- |
| Main project and `skills/linxsci-base/` | Main repository | `main` |
| `skills/linxsci-idea/` | Independent Codeup repository | `main` |
| `skills/linxsci-survey/` | Independent Codeup repository | `main` |
| `skills/linxsci-paper-qa/` | Independent Codeup repository | `main` |
| `skills/linxsci-paper/` | Independent Codeup repository | `main` |
| `skills/linxsci-ppt/` | Independent Codeup repository | `main` |
| `skills/linxsci-reproduce/` | Independent Codeup repository | `main` |
| `skills/linxsci-xiaohongshu/` | Independent Codeup repository | `main` |

Public configuration contains no actual Codeup addresses. The existing main checkout retains its `github` and `origin` remotes: `github` points to public GitHub and `origin` to the original base project's Codeup repository. Explicitly use `git push github <branch>` to publish main-repository changes to GitHub. Each extension retains its own Codeup `origin`.

## Set up a maintainer checkout

Clone the main repository normally:

```bash
git clone https://github.com/LinxSci/linxsci-skills.git
cd linxsci-skills
```

Authorized maintainers obtain extension URLs through private configuration and clone each repository into its directory above. Do not overwrite existing directories. For example, after setting `LINXSCI_IDEA_REPOSITORY` locally to the private Idea repository URL:

```bash
git clone "$LINXSCI_IDEA_REPOSITORY" skills/linxsci-idea
```

Repeat for the other extensions and check each repository's branch. To reproduce the development baseline, check out the complete `commit` values in `extensions.lock.json`; a remote default branch's latest commit is not the baseline. Select or create an appropriate branch before starting development from a pinned checkout.

This file records development commits using names, relative paths, branches and SHAs, without addresses or credentials. It does not capture uncommitted changes and is not a published release manifest. `tools/build_skill_releases.py` now consumes it together with `release/suite.json`, an explicit base commit and a private source mapping. It builds in clean temporary repositories and generates a separate release manifest. See the [package installer guide](SKILL_INSTALLATION.md); the shared module is generated into packages from build inputs.

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

Inspect, commit and push extension changes from their own `skills/<name>/` directories. The main repository's `git status` does not report changes inside these ignored directories. Do not use `git add -f skills/<name>` to add extension repositories to the parent.

When preparing the development baseline locally, validate and commit each extension, then record its complete SHA in the main repository's `extensions.lock.json`. Before pushing the main-repository update or building from Codeup, push the extension commits to Codeup and confirm that every pinned commit is retrievable. Branches describe development locations; SHAs identify fixed versions. A main-repository commit does not commit or push extension changes.

Authorized build environments acquire specified commits from independent repositories and produce actual source files with verifiable manifests. Public users install Release assets without Codeup access. Dependency installation is independent of the SDK; schedule an SDK version only when its functionality or package data changes.

Commit documentation and code in their owning repositories, verify that the selected commits are retrievable, update pins and build a new suite version. Do not edit old ZIPs or attribute uncommitted content to an existing source SHA. Development checks require a source snapshot or complete maintainer source; single packages and the full suite omit tests. Record candidate progress, acceptance results and publication work separately from user installation prompts.
