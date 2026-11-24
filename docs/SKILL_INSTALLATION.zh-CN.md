# GitHub 仓库安装

[English](SKILL_INSTALLATION.md)

基础 Skill 位于 [主仓库](https://github.com/LinxSci/linxsci-skills) 的 `skills/linxsci-base/`，七个扩展各自在仓库根目录提供完整 Skill：

| Skill | 公开源码仓库 |
| --- | --- |
| `linxsci-idea` | https://github.com/LinxSci/linxsci-idea |
| `linxsci-survey` | https://github.com/LinxSci/linxsci-survey |
| `linxsci-paper-qa` | https://github.com/LinxSci/linxsci-paper-qa |
| `linxsci-paper` | https://github.com/LinxSci/linxsci-paper |
| `linxsci-ppt` | https://github.com/LinxSci/linxsci-ppt |
| `linxsci-reproduce` | https://github.com/LinxSci/linxsci-reproduce |
| `linxsci-xiaohongshu` | https://github.com/LinxSci/linxsci-xiaohongshu |

克隆主仓库不会自动取得扩展。每个扩展可独立下载、安装和更新，按自己的 README、requirements 和接口检查兼容性。

## 安装

最便捷的方式是把目标仓库 README 中的“一段话安装”交给当前 Agent，实际完成 Skill 文件、Python 依赖和发现配置。使用 Skills CLI 时，例如安装 Idea 到 Codex：

```bash
npx skills add https://github.com/LinxSci/linxsci-idea --skill linxsci-idea -g -a codex
```

此方式需要 Node.js 22.20+ 和 npx。按当前 Agent 调整 `-a`；项目级安装省略 `-g`。也可 Git 克隆或下载目标仓库源码 ZIP，将完整目录放入当前 Agent 的发现位置，根目录直接包含 `SKILL.md`。本地 Skills CLI 安装可从该根目录运行 `npx skills add . --skill linxsci-idea -g -a codex`，使用链接时保留源目录。

按目标仓库要求选择 Python：其他扩展为 Python 3.9+，小红书为 Python 3.10+。在 Skill 目录外创建或复用兼容虚拟环境，以同一解释器安装该仓库的 `requirements.txt`。当前扩展依赖 `linxsci==0.3.4`，小红书还有 PyMuPDF、Pillow 和字体要求。配置当前 Agent 的发现路径；CLI 需要时把 `LINXSCI_SKILLS_DIR` 设为包含完整 Skill 文件夹的绝对父目录。检查 SDK 版本和实际 Skill 帮助，按需在本机 `linxsci setup` 配置 API Key。

Windows 在执行 SDK/Skill 命令前，应在当前终端或 Agent 子进程环境中启用 Python UTF-8，尤其是捕获或重定向包含中文的帮助、JSON 输出时。PowerShell 使用 `$env:PYTHONUTF8 = '1'`，命令提示符使用 `set PYTHONUTF8=1`。Agent 应向子进程传入 `PYTHONUTF8=1`，并按 UTF-8 解码捕获的文本。该设置适用于现有 SDK 0.3.4，无需修改全局配置。

## 协作与更新

Idea 只有新取证或补查才需要 Survey，使用随仓库提供的 `scripts/install_survey.py` 从 Survey 的 GitHub 仓库安装；需要 Git，先检查当前解释器满足 SDK 约束。复用已有安装授权，验证后由 Agent 保留原参数、证据、输出路径和工作目录续跑。已有证据复用不要求 Survey。Paper 等扩展按实际任务选择协作者，不递归安装全套。

直接 Git 克隆的副本在保留本地修改后使用 `git pull --ff-only`。Skills CLI 管理的副本使用工具支持的更新方式；本地目录安装先更新源码再按原参数重新安装。手动副本从同一仓库获取完整新版源码后替换，保留修改和配置。更新后同步 requirements 并刷新 Agent。

CLI/SDK 的安装与发布继续见 [CLI 指南](CLI_GUIDE.zh-CN.md) 和 [维护者发布指南](RELEASING.zh-CN.md)。开发结构及提交基线见 [本地开发](LOCAL_DEVELOPMENT.zh-CN.md)。
