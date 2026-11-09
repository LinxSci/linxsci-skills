# LinxSci documentation

[简体中文](README.zh-CN.md) · [Project overview](../README.md)

Choose the guide for the interface you use. In this `linxsci-openapi-skills` project, the standalone Skill is `linxsci-base`, with source at `skills/linxsci-base/`. The CLI and SDK share the Python distribution `linxsci`, the terminal command `linxsci`, and imports such as `from linxsci import LinxSciClient`.

| Task | Guide |
| --- | --- |
| Install, configure, update and remove the standalone Skill | [Skill user guide](USER_GUIDE.md) |
| Install the command-line tool and use its commands and parameters | [CLI guide](CLI_GUIDE.md) |
| Install the SDK, configure a Python client, call methods and handle errors | [Python SDK guide](DEVELOPMENT.md) |
| Look up HTTP routes, authentication and errors shared by all interfaces | [API reference](API.md) |
| Build packages, publish GitHub/PyPI releases and verify installations | [Maintainer release guide](RELEASING.md) |
| Run regression and integration checks | [Testing guide](TESTING.md) |

The Skill guide uses its standalone installer and assistant workflow. The CLI guide uses terminal commands. The SDK guide uses Python installation and code. Each user guide includes its own update instructions. Publishing credentials are needed only by maintainers, not by users installing packages.

The release guide describes public file exclusions, package contents, build validation, GitHub publication and PyPI uploads. Installation examples use `0.3.3`, which includes the renamed `linxsci-base` Skill. CLI and SDK users upgrade the `linxsci` package; copied Skill installations require a separate update using their original installer.
