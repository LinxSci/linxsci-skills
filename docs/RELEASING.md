# Maintainer build and release guide

[简体中文](RELEASING.zh-CN.md)

This guide covers source builds, artifact validation and package uploads. User installation and usage are documented in the [README](../README.md).

## Versions and artifacts

Keep the version in `pyproject.toml`, SDK `__version__`, CLI `VERSION`, and installer marker metadata consistent. Use a separate output directory for each version and preserve published artifact files unchanged.

| Artifact | Contents |
| --- | --- |
| `linxsci-skills-0.3.2.zip` | Standalone installer, complete Skill and bilingual user guides |
| `linxsci-0.3.2-py3-none-any.whl` | CLI, Python SDK and complete Skill |
| `linxsci-0.3.2.tar.gz` | Source, tests, build tools and maintainer documentation |
| `SHA256SUMS` | SHA-256 digests of the artifacts |

The build backend is setuptools, Python 3.9+ is required, and runtime dependencies are empty. The Skill's scripts run without installing the SDK.

## Build and validate

From a Python environment with build tools installed:

```bash
python -m pip install build twine
python -m unittest discover -s tests -v
python tools/build_release.py --output dist/0.3.2
python tools/check_release.py dist/0.3.2
python tools/smoke_release.py dist/0.3.2
```

With uv installed, add `--uv uv` to the smoke command to verify an isolated CLI tool installation. The checks use a local mock API and temporary settings; no production API key is needed. Checksum, metadata and file checks cover the wheel, source archive and ZIP. The smoke test installs fresh copies, calls all 34 convenience routes, and checks Skill installation/update, SDK access and local response views. Desktop launchers can be checked on their respective platforms.

`python tools/build_release.py --bundle-only --output dist/0.3.2` creates just the standalone ZIP and checksums. The ZIP uses the bilingual Skill user guide as its README and includes the installer and complete Skill with agent references. CLI, SDK and maintainer guides remain in the source repository/archive. Configuration files, credentials, caches and existing installation markers are excluded. All Markdown links in the ZIP must resolve within that bundle.

Use the [testing guide](TESTING.md) for regression and assistant behavior checks. Live integration tests should use an explicitly configured service root and suitable sample data.

## Package upload

Upload the validated wheel and source archive to the selected registry using the maintainer's publishing credentials. ZIP bundles are separate download artifacts. For example, with uv and `UV_PUBLISH_TOKEN` configured locally:

```bash
uv publish dist/0.3.2/linxsci-0.3.2-py3-none-any.whl dist/0.3.2/linxsci-0.3.2.tar.gz
```

Keep tokens in local secret storage or the CI credential mechanism. Publishing credentials and users' LinxSci API keys are separate. Validate installation from the selected registry after uploading.

## Source and documentation consistency

The wheel and standalone bundle use the same `skills/linxsci-skills/` source. Keep both language editions and the command examples aligned with the packaged version. `.github/workflows/ci.yml` runs tests, builds artifacts and verifies installation on the supported Python/platform matrix.

## GitHub and PyPI publication

The `publish.yml` workflow runs from a version tag such as `v0.3.2`. It runs the platform/Python test matrix, builds and validates the packages, then publishes a GitHub Release. Existing release assets are reused on a rerun, not replaced. Push the matching version tag only after reviewing the source and release notes and passing local checks.

To publish to PyPI, download the GitHub Release's wheel, source archive and `SHA256SUMS`, verify their hashes, and upload those exact files. With Twine and a compatible keyring backend installed, store a publishing token locally using hidden input:

```bash
python -m keyring set https://upload.pypi.org/legacy/ __token__
python -m twine upload --non-interactive --username __token__ --repository-url https://upload.pypi.org/legacy/ dist/0.3.2/linxsci-0.3.2-py3-none-any.whl dist/0.3.2/linxsci-0.3.2.tar.gz
```

Do not put the token in a command argument, source file or chat. Keep the API key used for LinxSci service calls separate. For a first upload, the token must permit creating this PyPI project; use a project-scoped token once the project exists. See [PyPI's publishing guide](https://docs.pypi.org/project-management/publishing/).

After uploading, compare PyPI's file hashes with the GitHub Release and verify installation from PyPI in a fresh environment. If an upload is interrupted, inspect which files already exist and upload only missing files; never replace a published version with different bytes.
