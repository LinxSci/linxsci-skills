# User guide

[简体中文](USER_GUIDE.zh-CN.md) · [README](../README.md)

## Install and configure

The Skill runs independently of the CLI and SDK: no PyPI package installation is required. Prepare Python 3.9+, your existing LinxSci API key, and an assistant with local skill/script support. Extract `linxsci-skills-0.3.0.zip`, then double-click `Install.command` on macOS or `Install.bat` on Windows. From a terminal, use:

```bash
python3 install.py
```

On Windows use `py -3 install.py`. Choose the service root and enter your key using hidden input. The default is `https://linxsci.com`; the installer saves settings and checks connectivity. Do not paste keys into a chat. The project does not provide account registration or issue API keys.

The default destination is `~/.agents/skills/linxsci-skills`. Restart your assistant if discovery does not refresh. To choose another location:

```bash
python3 install.py --skills-dir /path/to/assistant/skills
```

Installation from ZIP needs no pip or network access; setup's connection check does require access to the configured service. The ZIP does not install the `linxsci` terminal command. See the [README](../README.md) for wheel and source installation.

## Ask research questions

> Use $linxsci-skills to search for papers on graph neural networks. Select up to three relevant results and include their actual IDs and source links.

> Use $linxsci-skills to read paper "<returned-paper-id>". Inspect its table of contents, then summarize the methods with section evidence.

> Use $linxsci-skills to compare these two returned paper IDs. Cite evidence for each conclusion and identify information that was unavailable.

Replace placeholders with actual returned IDs. The assistant should call the service, read relevant content and cite it. Empty results and unavailable sections should be reported directly.

## Settings and updates

Use the installed Skill's absolute script path; replace `<skill-dir>` with its actual directory. On Windows use `py -3` instead of `python3`:

```bash
python3 "<skill-dir>/scripts/cli.py" config
python3 "<skill-dir>/scripts/cli.py" setup --online
python3 "<skill-dir>/scripts/cli.py" doctor --json
python3 "<skill-dir>/scripts/cli.py" config --clear
```

`config` hides the key. `setup --online` suggests the production service; environment overrides still take precedence. `doctor` makes a real `/meta` call, so avoid repeated checks. Clearing removes the saved URL and key, but does not unset environment variables. An update only replaces an installation managed by this installer and retains a backup outside the skill scan directory. Run updates from the new downloaded source or bundle; running an old installed script would copy its old files.

For a ZIP update, extract the new bundle and run `python3 install.py --update`. Use `--no-config` when configuration is already valid. Keep customized or externally installed copies under their original installer's management.

The current configuration uses `LINXSCI_*` variables and the `linxsci-skills` directory. After upgrading from older naming, rerun setup and update deployment variables; remove obsolete skill copies from assistant scan directories using their installation tool.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Skill is missing | Check the destination and restart the assistant |
| Terminal command is missing | Install the wheel/source, or invoke the skill script directly |
| Wrong service address | Inspect `config` and `LINXSCI_BASE_URL` |
| Authentication fails | Run setup with a valid LinxSci key |
| Search is empty | Adjust the query and report the empty result honestly |
| PDF creation has an uncertain result | Inspect task and billing status before resubmitting |

See [independent Skill installation and installer parameters](../skills/linxsci-skills/SKILL.md#install-the-skill-independently), [standalone commands and all parameters](../skills/linxsci-skills/references/cli.md), [CLI commands](CLI_GUIDE.md), [error codes](API.md), and [testing](TESTING.md).
