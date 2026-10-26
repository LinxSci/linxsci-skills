# Website downloads and documentation

[简体中文](WEBSITE_PUBLISHING.zh-CN.md)

This repository supplies release files and Markdown documentation. The website owns page rendering, download hosting and version presentation. The paths below are integration proposals; they are not proof of deployment. Earlier inspection of the test website identified a React/TypeScript/Vite frontend with `pages/OpenApiPage.tsx` and `AppRouter.tsx`; verify those files in the website repository before implementation.

## Entry points

| Audience | Installation | Documentation source |
| --- | --- | --- |
| AI assistant users | GitHub skill installer, with ZIP fallback | [User guide](USER_GUIDE.md) |
| Terminal users | `uv tool install linxsci` after publication | [CLI guide](CLI_GUIDE.md) |
| Python developers | `python -m pip install linxsci` in the application environment after publication | [SDK guide](DEVELOPMENT.md) |

CLI and SDK share one distribution. The distribution, command and import are `linxsci`; the project and skill are `linxsci-skills`. ZIP installation provides a self-contained skill without registering the terminal command. All require Python 3.9+.

| Page or file | Suggested path |
| --- | --- |
| Overview and downloads | `/open-api?tab=guide` |
| Skill documentation | `/open-api?tab=skill` |
| CLI documentation | `/open-api?tab=cli` |
| SDK documentation | `/open-api?tab=sdk` |
| API contract | `/open-api?tab=docs` or `/open-api/docs` |
| Versioned downloads | `/downloads/linxsci-skills/0.3.0/` |

Render Markdown as readable pages with code blocks, tables and working anchors. Default to English and include a visible link to the matching Chinese edition on every page; Chinese pages should link back to English. Map relative repository links to the appropriate website pages and language. Use [API.md](API.md) for the API contract; no Postman collection is bundled, so do not show an unavailable collection download.

## Installation examples

Once the renamed package is published and registry installation has passed:

```bash
uv tool install linxsci
linxsci setup
linxsci search "graph neural networks"
```

For SDK users, show project environment installation and a runnable example:

```python
from linxsci import LinxSciClient

client = LinxSciClient()
print(client.search("graph neural networks").json())
```

Link skill users to [the official repository](https://github.com/LinxSci/linxsci-skills) and show:

```bash
npx skills add https://github.com/LinxSci/linxsci-skills --skill linxsci-skills
```

Also offer ZIP installation and `linxsci install-skill` for existing CLI users. Keep source development instructions behind the main installation steps. Do not ask website visitors to clone a private source repository. `setup` accepts the user's API key locally using hidden input; documentation pages do not need a key entry form.

## Files and version consistency

Follow [releasing](RELEASING.md) to build and verify a clean directory containing the ZIP, wheel, source archive and `SHA256SUMS`. Host those exact validated files or link to the matching release assets. Do not upload the development directory or assume a Git push uploads release files.

A proposed ZIP URL is `/downloads/linxsci-skills/0.3.0/linxsci-skills-0.3.0.zip`. Keep filenames, version badges, documents and checksums consistent across all three entry points. Published version files are immutable; publish a new version for changes.

Use the production root `https://linxsci.com` in examples. Existing saved settings and environment overrides persist across upgrades; users switching environments should run `linxsci setup --online` and inspect `LINXSCI_BASE_URL`. Test service configuration belongs in the [testing guide](TESTING.md).

Before launch, verify download links, checksums, supported-platform installation, skill discovery, CLI startup, SDK import, hidden key setup, search and section reading. Check PDF flow when supported by the deployment. Verify both language links and rendered internal links. Enable registry-based installation instructions only after publication and a fresh install check.
