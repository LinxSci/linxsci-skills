# Releasing linxsci-skills

[简体中文](RELEASING.zh-CN.md)

The CLI and SDK share the `linxsci` Python distribution. The project and AI skill are named `linxsci-skills`. The terminal command and Python import remain `linxsci`. The build backend is setuptools (64+), Python 3.9+ is required, and runtime dependencies are empty. The complete self-contained skill is included in the wheel.

## Build and verify

Use a clean output directory for each version. Synchronize the version in `pyproject.toml`, SDK `__version__`, CLI `VERSION`, and installer marker metadata. The current version is 0.3.0. Never replace files already published under a version; choose a new version when needed.

```bash
python -m pip install build twine
python -m unittest discover -s tests -v
python tools/build_release.py --output /tmp/linxsci-release
python tools/check_release.py /tmp/linxsci-release
python tools/smoke_release.py /tmp/linxsci-release --uv uv
```

The optional uv argument requires an installed uv executable. Alternatively, build wheel/sdist with `uv build --no-sources --out-dir /tmp/linxsci-release --no-create-gitignore`, then create the ZIP with `python tools/build_release.py --bundle-only --output /tmp/linxsci-release` and run the same checks.

| Artifact | Purpose |
| --- | --- |
| `linxsci-skills-0.3.0.zip` | Standalone installer, complete skill, and English/Chinese guides |
| `linxsci-0.3.0-py3-none-any.whl` | CLI, SDK, and complete skill |
| `linxsci-0.3.0.tar.gz` | Source distribution |
| `SHA256SUMS` | SHA-256 for the artifacts |

ZIP construction uses an allowlist that excludes keys, configuration, caches, virtual environments and installation markers. Production defaults in `service.json` are `https://linxsci.com`. Test environments must be selected explicitly. Saved configuration and environment overrides take precedence over release defaults.

Release checks verify versions, contents, metadata, and hashes. Smoke checks install into fresh temporary environments and exercise all 34 convenience routes from wheel and ZIP against a local mock server. Optional uv checks also install offline from the local wheel, install/update the bundled skill, and uninstall the temporary tool without changing the user's tool environment. Manually check desktop launcher behavior on macOS and Windows, as well as actual service search/section/PDF workflows. Mock tests do not prove live business behavior.

## Distribution

An authorized maintainer should confirm distribution-name ownership and release licensing before publishing. This repository does not choose a license on the owner's behalf. Building does not publish artifacts or create a Git tag, release, or website deployment.

For a manual upload, use separate TestPyPI and PyPI accounts/credentials as applicable. In a Bash terminal, read the appropriate publishing token locally without echoing it:

```bash
read -r -s UV_PUBLISH_TOKEN
export UV_PUBLISH_TOKEN
```

Then select the intended registry and explicit wheel/sdist files; ZIP files do not go to PyPI:

```bash
uv publish --publish-url https://test.pypi.org/legacy/ /tmp/linxsci-release/linxsci-0.3.0-py3-none-any.whl /tmp/linxsci-release/linxsci-0.3.0.tar.gz
```

With production credentials and release authorization:

```bash
uv publish /tmp/linxsci-release/linxsci-0.3.0-py3-none-any.whl /tmp/linxsci-release/linxsci-0.3.0.tar.gz
unset UV_PUBLISH_TOKEN
```

Do not put tokens into Git, chat, or reusable commands. Publishing credentials are separate from users' LinxSci API keys. Prefer project-scoped tokens once the project exists. Verify registry installation in fresh CLI and application environments before advertising `uv tool install linxsci` and `python -m pip install linxsci` as available.

For future GitHub Trusted Publishing, register the exact owner, repository, publishing workflow filename and optional environment with PyPI. The publishing job needs `id-token: write` and should publish the same validated artifacts. The current CI workflow builds and tests; it does not upload.

## Skill and website synchronization

Maintain the complete `skills/linxsci-skills/` in [LinxSci/linxsci-skills](https://github.com/LinxSci/linxsci-skills), using the same files as the wheel. A compatible installer can use:

```bash
npx skills add https://github.com/LinxSci/linxsci-skills --skill linxsci-skills
```

Keep external installer copies under that installer's management. The built-in installer updates only its managed copy and backs up the previous version outside the scan directory. ZIP users run `python3 install.py --update`; CLI users update the package then run `linxsci install-skill --update`. For earlier naming, update SDK imports and environment variables and rerun setup for the new configuration directory.

Publish matching English and Chinese guides, version labels, downloads and checksums on the website. See [website publishing](WEBSITE_PUBLISHING.md).
