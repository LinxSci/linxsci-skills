# Build and publish Skill suites from fixed commits

[简体中文](SKILL_RELEASES.zh-CN.md) · [Local development](LOCAL_DEVELOPMENT.md)

The builder creates local candidate or final assets without committing or uploading. The separate publication tool defaults to an offline plan; explicit flags perform GitHub operations. Seven extensions remain independent, ignored repositories; no submodules are used. Public users download actual files from Release assets without private source access.

## Inputs and versions

`extensions.lock.json` pins seven complete extension SHAs; branch names are descriptive only. `release/suite.json` defines the suite version, entrypoints, Python/SDK constraints and conditional collaboration. `--base-commit` pins the main project, including `skills/linxsci-base/`. Staged and unstaged source changes are excluded.

The private `--sources` JSON object must have eight keys: `linxsci-base`, `linxsci-idea`, `linxsci-survey`, `linxsci-paper-qa`, `linxsci-paper`, `linxsci-ppt`, `linxsci-reproduce`, and `linxsci-xiaohongshu`. Values are authorized source repository URLs; the base entry points to the main repository. Store it in ignored `.local/release-sources.json` or external private configuration. Never commit it or embed passwords/tokens in URLs.

`--sdk-wheel` supplies the existing `linxsci-0.3.4-py3-none-any.whl`. Its checksum, metadata and packaged `linxsci/` files must match the recipe and pinned base source. The CLI/SDK is not rebuilt. The suite has its own version under the `suite-v<suite-version>` tag namespace. This guide uses `0.1.0-rc.1` to illustrate asset naming; actual builds use the new version selected in the recipe and an unused output directory. All eight package identities use this suite version while preserving each source SHA; source version declarations are not rewritten. Internal Skill dependencies resolve to the named package version in the same suite manifest.

## Build and verify

Use Python 3.10+ for the complete acceptance run. Building and static checking require only Python 3.9+ standard library and Git. Maintainers must already have read access to private sources. From the main repository, after preparing the private mapping and existing wheel, set `BASE_COMMIT` to the complete main-project SHA selected for this build and verified against that wheel:

```bash
python tools/build_skill_releases.py \
  --sources .local/release-sources.json \
  --base-commit "$BASE_COMMIT" \
  --sdk-wheel dist/0.3.4/linxsci-0.3.4-py3-none-any.whl \
  --output dist/suite-0.1.0-rc.1

python tools/check_skill_releases.py dist/suite-0.1.0-rc.1
python tools/smoke_skill_releases.py dist/suite-0.1.0-rc.1 \
  --report .local/release-checks/smoke.json
```

`--lock` and `--recipe` override the default configuration paths. Existing output directories are rejected; choose a new directory rather than replacing release bytes. Run focused tests with `python -m unittest discover -s tests -p test_skill_releases.py -v`.

The builder fetches and checks out each complete SHA in a fresh temporary repository and verifies a clean checkout. It reads Git blobs directly so checkout line-ending conversions cannot alter the packaged source. Servers rejecting an old unadvertised SHA are retried using advertised branch/tag objects; the exact pin is still required. Missing commits fail the build. Local absolute paths and `file://` sources are supported, but non-bare repositories with uncommitted/untracked files are rejected without altering their indexes.

If the development checkout retains changes deferred from this release, use a clean checkout of the selected commit or a remote source in the private mapping. Preserve the deferred changes; they are excluded from the fixed commit.

ZIP ordering, timestamps, modes and compression settings are fixed. Identical inputs reproduce identical bytes with the same Python/zlib toolchain; cross-toolchain compression equivalence has not been verified. Intermediate failures leave no candidate directory. Only a completely validated set is moved into the output location.

## Output: 13 files

| Asset | Contents |
| --- | --- |
| `linxsci-base-skill-0.1.0-rc.1.zip` | Flat base package with root `SKILL.md` |
| Seven `linxsci-<extension>-0.1.0-rc.1.zip` files | Flat extension packages with instructions, entrypoints and required resources |
| `linxsci-skills-0.1.0-rc.1-full.zip` | Eight expanded directories under `skills/`, identical ZIPs under `packages/`, SDK under `wheels/`, and manifest |
| `linxsci-skills-0.1.0-rc.1-source.zip` | One root directory containing the eight pinned source trees, allowed tests/tools and a separate build-input snapshot |
| `linxsci-0.3.4-py3-none-any.whl` | Existing SDK/CLI, unchanged |
| `release-manifest.json` | Public version, commits, dependency conditions, asset sizes, planned URLs and individual checksums |
| `SHA256SUMS` | SHA256 of the other 12 assets |

Single packages explicitly select root instructions, READMEs, requirements, licenses and related files, plus `scripts/`, `references/`, `agents/`, `assets/` and `tools/`. Tests are source-snapshot only. Snapshots select tracked Git files and exclude Git metadata, local configuration, environments, caches, build output and `docs/local/`. Links, nested repositories and unsafe/conflicting archive paths are rejected; actual private source addresses are scanned. `.env.example` is allowed, real environment files are excluded.

`release/build-inputs/` in the source snapshot preserves the exact lock, recipe, build, check, smoke, package-installation acceptance and publication tools plus shared `tools/skill_install.py`, with hashes in manifest `build_inputs`. These are explicitly separate from the pinned main commit, allowing review of a candidate built with uncommitted new tooling. To rebuild, use that builder with explicit `--lock`, `--recipe` and all other inputs. Private-source access remains necessary for rebuilding. Git history and uncommitted developer changes are absent.

## Metadata and verification

The public manifest and each package's `release.json` use schema 1. They record source commits, package identity, Python/SDK requirements and conditional Skill dependencies. Idea's `feature / fresh-evidence` dependency on Survey applies when fresh evidence is needed. `workflow` relationships apply to the specified collaboration, rather than making every collaborator an unconditional installation dependency.

The manifest hashes the eight individual ZIPs and wheel, and names both bundles. Because bundles embed the manifest, their final hashes live in outer `SHA256SUMS` to avoid circular hashes. The checker verifies the complete asset set, individual inventories, embedded packages, expanded directories, source files, build-input snapshots and SDK consistency. Markdown relative file targets are checked; anchor names and public network availability are not. Checksums are integrity checks, not publisher signatures.

Candidate recipes use `status: candidate` and produce `published: false`. Final recipes use `status: release`, a stable suite version and an explicit `--release` build flag; all final assets consistently use `status: release` / `published: true`. This describes the payload prepared for publication: build output still reports `uploaded: false` and does not claim remote availability. The checker and installer reject contradictory states; public installation requires final metadata. Package identities, embedded manifests and checksums are produced together, never by manually changing only the outer JSON.

## Scope and next stage

The smoke runner extracts all formats outside the source checkout, creates a temporary venv, installs only the bundled SDK wheel offline, clears inherited LinxSci/Python/Pip configuration and excludes Git from PATH. It checks direct entrypoints, SDK dispatch, discovery and base routes without business API calls. It does not validate research/content production or install third-party rendering tools.

The builder generates the [shared installer and Idea → Survey adapter support](SKILL_INSTALLATION.md) at `scripts/linxsci_release_install.py` in all eight packages and source snapshots. `generated_files` records its build-input path and SHA256; the checker requires byte-for-byte equality with `release/build-inputs/tools/skill_install.py`. Generated files are not attributed to the pinned source commit; their hashes enter both inventories, and the SDK wheel is reused unchanged. The installer handles explicit selections without recursive collaborator installation. Documentation and code updates require retrievable new commits, updated versions and pins, and a new output directory; existing assets remain unchanged. The full bundle is not a complete offline Python/font/experiment environment. Record anonymous download, SkillHub and production acceptance for each release separately.

The tools do not change source repositories. To undo local build work, preserve or move the candidate output and new tooling. Back up subsequent changes before restoring individual files; do not reset unrelated staged work.

## Final packaging and installation acceptance

Commit each source repository separately and confirm that every pin is retrievable. Select an unused stable suite version and set `SUITE_VERSION` and `BASE_COMMIT` to that version and the real complete main-project SHA. All SDK package data at that commit must match the existing wheel, including both base SKILL files. Preserving worktree changes does not include them in a pinned release.

Copy the recipe to `.local/suite.release.json`, set `status` to `release` and `suite_version` to the selected version, and maintain constraints, SDK hash and entrypoints from actual verification. From the main repository, with those variables already set and new output/report paths:

```bash
python tools/build_skill_releases.py --release \
  --recipe .local/suite.release.json --lock extensions.lock.json \
  --sources .local/release-sources.json --base-commit "$BASE_COMMIT" \
  --sdk-wheel dist/0.3.4/linxsci-0.3.4-py3-none-any.whl \
  --output "dist/suite-$SUITE_VERSION"
python tools/check_skill_releases.py "dist/suite-$SUITE_VERSION"
python tools/verify_skill_installation.py "dist/suite-$SUITE_VERSION" \
  --report ".local/release-checks/install-$SUITE_VERSION.json"
```

The installation verifier also accepts newly built candidates. It first runs all eight Skills' help/discovery checks in single packages, the full bundle and source snapshot. It then starts outside the source tree from the single Idea ZIP, installs the bundled SDK offline and obtains Survey through the explicit loopback HTTP test entry. It checks refusal, suite identity, 404/timeouts/interruption, corrupt/unsafe ZIPs, rollback, local edits, download-free reuse, original-task continuation and follow-up using a local mock API. Existing evidence must remain reusable without Survey or downloads. Required scenarios fail instead of skipping. The report binds the manifest and all 13 asset hashes.

Production HTTPS source selection is exercised with local transport substitution, not anonymous network downloads. User subprocesses need no Git, private credentials or development source. Reports must be new files outside the assets directory. Running the verifier requires Python 3.10+, venv and loopback listeners. Run it from the main project or source snapshot; single packages omit tests.

## Suite publication entrypoint

Prepare actual suite release notes and complete licensing, supported-platform and source review. `publish_skill_releases.py` operates on already built assets and a matching installation report. It does not use the SDK `v*` workflow or Codeup credentials.

By default it generates an offline plan with no network access:

```bash
python tools/publish_skill_releases.py "dist/suite-$SUITE_VERSION" \
  --installation-report ".local/release-checks/install-$SUITE_VERSION.json" \
  --notes-file "docs/releases/suite-v$SUITE_VERSION.md"
```

Once publication is authorized, push the real main-project commit and matching `suite-v<version>` tag to the public repository. The tag must resolve to the manifest's base source commit. With GitHub CLI installed and maintainer authentication configured, append `--upload-draft` to the command: it creates a new draft, uploads 13 files, downloads them and verifies the complete asset set and bytes. Existing releases are not overwritten. If an upload fails, inspect the remaining draft; the tool does not delete or replace it.

After draft review, append `--publish` to the same command. It rechecks the tag and remote draft bytes before making it public. Already public releases are rejected, and SDK latest is not moved. The two write flags are mutually exclusive; without either, the command only plans locally.

After publication, verify anonymous fixed HTTPS downloads, installation and SkillHub separately. Authenticated draft downloads, mock research results and substituted HTTPS transport do not prove public availability. A local publication plan does not complete licensing or native-platform acceptance.
