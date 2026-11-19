# Install Skills from fixed Release packages

[简体中文](SKILL_INSTALLATION.zh-CN.md) · [Build guide](SKILL_RELEASES.md)

Complete single packages include `scripts/linxsci_release_install.py` to install Skills from a fixed Release manifest or local assets, without Git or private repository access. It uses the Python standard library independently of the SDK. The main repository maintains one implementation in `tools/skill_install.py`; the builder records its origin and hash when generating package copies.

The SDK/CLI dependency remains `0.3.4`; `linxsci install-skill` copies only the base Skill. For extensions, prepare the complete Skill, Python requirements and Agent discovery as described below.

First prepare the target's requirements in the same Python environment that will run the installer, outside Skill directories. The installer checks versions but does not run pip or upgrade environments. Xiaohongshu still needs PyMuPDF, Pillow and fonts; presentation, Word and LaTeX production tools remain separate.

## Fixed public downloads

Select a suite containing the manifest and target asset from [LinxSci Releases](https://github.com/LinxSci/linxsci-skills/releases). Prefer the user’s specified version; otherwise choose a stable suite meeting the Python/SDK constraints and pin its exact version. SDK tag `v0.3.4` is separate from suite tags. Run the command below from a verified single package, replacing version and path placeholders. An Agent can obtain the first package by downloading, verifying and safely extracting its manifest-listed ZIP.

```text
python scripts/linxsci_release_install.py --skill linxsci-survey --manifest-url "https://github.com/LinxSci/linxsci-skills/releases/download/suite-v<suite-version>/release-manifest.json" --suite-version "<suite-version>" --destination "/absolute/path/to/assistant/skills/linxsci-survey" --yes
```

Public mode accepts only the official fixed GitHub HTTPS manifest with consistent `status: release` / `published: true` metadata and a stable suite version. Redirects are limited to GitHub Release asset hosts. It rejects latest, branch sources, credentials in URLs and other hosts. Local assets use `--assets-dir`. `--test-allow-loopback-http` is exclusively for HTTP fixtures on literal loopback addresses; it cannot enable remote HTTP or substitute for production downloads.

The installer validates the manifest and SHA256SUMS, suite/Skill identity, source commit, ZIP size/hash, Python/SDK requirements and every file and mode. It rejects escaping paths, links and special files. Before installation it checks the real help entrypoint in a temporary directory; Survey additionally checks callable `prepare_survey`, `record` and `paper_path`. Checksums verify integrity, not publisher signatures. Users must trust the supplied local asset source.

## Local assets

Run from the root of a complete single package that you have obtained and verified, replacing the paths with real absolute paths. `--destination` is the complete Skill directory, not its parent. Use `--yes` only when installation is already authorized:

```bash
python scripts/linxsci_release_install.py --skill linxsci-survey \
  --assets-dir "/absolute/path/to/suite-assets" \
  --destination "/absolute/path/to/assistant/skills/linxsci-survey" --yes
```

The asset directory must contain the same version's `release-manifest.json`, `SHA256SUMS` and target ZIP. Add `--suite-version "<suite-version>"` to pin the selected version explicitly; a mismatch fails. Versions are never inferred from a branch tip.

Maintainers running from the main repository root use `python tools/skill_install.py` with the same arguments. If the selected package has no bundled module, follow its README to install the complete directory manually. Windows can use the selected environment’s `python` or an explicit interpreter path with the same arguments.

On Windows, enable UTF-8 for Python in the shell or Agent child-process environment before running the SDK/Skill commands, especially when capturing or redirecting Chinese help or JSON output. In PowerShell use `$env:PYTHONUTF8 = '1'`; in Command Prompt use `set PYTHONUTF8=1`. Agents should pass `PYTHONUTF8=1` to child processes and decode captured text as UTF-8. This applies to the existing SDK 0.3.4 and requires no global settings change.

Without `--destination`, the target is the Skill name under absolute `LINXSCI_SKILLS_DIR`, or `~/.agents/skills/<name>` by default. Configure and refresh the actual Agent separately; CLI discovery does not configure Agent discovery. Keep Symlink targets outside temporary directories.

## Idea → Survey and results

Idea packages use `scripts/install_survey.py` as a thin adapter to this same module. When fresh or supplemental retrieval needs missing Survey, the Agent reuses existing authorization or explains the required source, version and location first. The adapter uses Idea's `release.json` to enforce the same suite. It does not recursively install Survey's Paper collaborator.

```bash
python scripts/install_survey.py --assets-dir "/absolute/path/to/suite-assets" \
  --survey-dir "/absolute/path/to/assistant/skills/linxsci-survey" --yes
```

Run this from a complete Idea package. Maintainers using an independent Idea source checkout without the generated module explicitly add `--installer-module "/absolute/path/to/linxsci-skills/tools/skill_install.py"`. This selects trusted local development code; the adapter never searches outside its package through implicit relative imports or downloads executable helpers.

| Status | Exit | Meaning |
| --- | ---: | --- |
| `installed` | 0 | Installed and passed file, environment, help and applicable interface checks |
| `reused` | 0 | Existing same-version complete copy passed checks without another ZIP download |
| `confirmation-required` / `cancelled` | 3 | Not installed; authorization is needed or the user declined |
| `failed` | 2 | Installation incomplete; inspect the reason, existing directories are not overwritten |
| Keyboard interruption | 130 | Cancelled; not task completion |

These are installer statuses. Idea's research command still prints guidance and exits 0 when Survey is missing, without evidence output or API calls; that 0 is not installation or retrieval success. After successful installation checks, the Agent resumes the original request with its working directory, arguments, evidence and output path preserved. Existing evidence reuse does not need Survey; cancellation or failure retains previous material.

## Existing directories and updates

The installer writes `.linxsci-release-install.json` with the fixed manifest and provenance hash. An unchanged managed copy can be reused offline; a manually extracted package can be verified against its original manifest. Missing metadata, edits, incomplete files, version mismatch or a symlink destination cause a stop with existing files preserved. There is no force-overwrite option.

New installation validates a temporary directory and reserves a new destination exclusively. Concurrently created targets are preserved. POSIX uses a directory switch; Windows uses exclusive file creation with the receipt written last. Failure removes the installer's own content and preserves files introduced by another writer. Native platform acceptance must use the exact release assets, including installation, failure rollback and local-edit preservation checks.

Updates use an explicit new version and a separate destination. After validation, the user handles the old copy, edits and Agent discovery configuration. Keep backups outside discovery directories. Release copies do not use git pull, and local npx installs do not promise remote updates.
