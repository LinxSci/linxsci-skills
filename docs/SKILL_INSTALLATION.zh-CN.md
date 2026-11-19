# 从固定 Release 包安装 Skill

[English](SKILL_INSTALLATION.md) · [构建指南](SKILL_RELEASES.zh-CN.md)

完整单项包随附 `scripts/linxsci_release_install.py`，可从固定版本 Release 清单或本地资产目录安装 Skill，不需要 Git 或私有仓库权限。它是独立于 SDK 的 Python 标准库模块；主工程在 `tools/skill_install.py` 维护一份实现，构建时按来源哈希生成到各包。

SDK/CLI 依赖仍为 `0.3.4`，`linxsci install-skill` 只复制基础 Skill。使用扩展包时，按下述方式准备完整 Skill、Python 依赖与助手发现路径。

先按照目标 Skill 的 requirements，在运行安装器的同一 Python 环境中准备依赖。环境放在 Skill 目录外。安装器只检查版本，不运行 pip、不升级现有环境；小红书的 PyMuPDF、Pillow 和字体，PPT/Word/LaTeX 制作工具仍需另行准备。

## 固定版本公开下载

从 [LinxSci Releases](https://github.com/LinxSci/linxsci-skills/releases) 选择包含发行清单和目标资产的套件。优先采用用户指定版本，否则选择满足 Python/SDK 约束的稳定套件并固定版本。SDK 标签 `v0.3.4` 与套件标签不同。以下命令从已核验的单项包根目录执行；将占位符替换为实际版本和路径，首次获取包可由 Agent 按清单下载、核验并安全解压。

```text
python scripts/linxsci_release_install.py --skill linxsci-survey --manifest-url "https://github.com/LinxSci/linxsci-skills/releases/download/suite-v<套件版本>/release-manifest.json" --suite-version "<套件版本>" --destination "/absolute/path/to/assistant/skills/linxsci-survey" --yes
```

公开模式限定官方 GitHub HTTPS 固定清单，要求清单为一致的 `status: release` / `published: true` 且使用稳定套件版本；下载重定向只允许 GitHub 的发行资产域名。拒绝 latest、分支来源、URL 凭据或其他主机。本地资产可用 `--assets-dir`；`--test-allow-loopback-http` 仅用于本机测试服务的 HTTP 地址，不能用于正式下载，不能扩大到远程 HTTP。

安装器核对清单与 SHA256SUMS、套件/Skill 身份、来源提交、ZIP 大小和 SHA256、Python/SDK 约束、所有包内文件及模式，拒绝越界路径、链接和特殊文件。在临时目录检查真实帮助入口；Survey 额外检查 `prepare_survey`、`record`、`paper_path` 接口，再安装。校验和用于完整性验证，不是发布者数字签名；本地资产来源须由使用者确认。

## 本地资产安装

以下命令在已获取并核验的完整单项包根目录执行；将路径换成真实绝对路径。`--destination` 是完整 Skill 目录，不能写成其父目录。`--yes` 仅用于已有明确安装授权的场景：

```bash
python scripts/linxsci_release_install.py --skill linxsci-survey \
  --assets-dir "/absolute/path/to/suite-assets" \
  --destination "/absolute/path/to/assistant/skills/linxsci-survey" --yes
```

资产目录须包含同版本 `release-manifest.json`、`SHA256SUMS` 和目标单项 ZIP。可加 `--suite-version "<套件版本>"` 明确限定所选版本；版本不匹配会停止。包和清单不由分支最新提交推断。

维护者在主工程根目录使用相同参数，将入口换为 `python tools/skill_install.py`。若所选包没有随附模块，按该包 README 手动安装完整目录。Windows 可使用所选环境的 `python` 或明确的 Python 可执行文件；命令参数相同。

省略 `--destination` 时，目标为绝对 `LINXSCI_SKILLS_DIR` 下的 Skill 名称目录，未设置则为 `~/.agents/skills/<名称>`。它只控制 CLI 发现；助手的实际扫描位置需单独配置并刷新。不要把临时目录作为持久 Symlink 目标。

## Idea → Survey 与结果判断

Idea 的 `scripts/install_survey.py` 是同一安装模块的薄适配入口。需要新取证或补查且 Survey 缺失时，Agent 沿用已有安装授权，否则先说明所需来源、版本和目录。单项 Idea 从自己的 `release.json` 限定 Survey 的同套件版本；它不会自动递归安装 Survey 的 Paper 协作者。

```bash
python scripts/install_survey.py --assets-dir "/absolute/path/to/suite-assets" \
  --survey-dir "/absolute/path/to/assistant/skills/linxsci-survey" --yes
```

上述命令从完整 Idea 包根目录执行。维护者直接使用独立 Idea 源码、还没有生成模块时，显式添加 `--installer-module "/absolute/path/to/linxsci-skills/tools/skill_install.py"`；这是可信本地开发模块，不会从包外相对路径自动寻找或下载代码。

| 状态 | 退出码 | 含义 |
| --- | ---: | --- |
| `installed` | 0 | 目标已安装并通过文件、环境、帮助及相应接口检查 |
| `reused` | 0 | 已有同版本完整副本通过检查，未重新下载 ZIP |
| `confirmation-required` / `cancelled` | 3 | 未安装；需授权或用户已取消 |
| `failed` | 2 | 安装未完成；查看具体原因，已有目录不覆盖 |
| 键盘中断 | 130 | 已取消，不代表任务完成 |

这些是安装器状态。Idea 的研究入口缺 Survey 时仍只输出引导、退出 0，不生成证据文件、不调用 API；这个 0 不等于安装或取证成功。安装器通过后，Agent 保留原工作目录、原参数、已有证据和输出位置，再执行原 Idea 请求。已有证据复用不要求安装 Survey，取消或失败仍保留原材料。

## 已有目录与更新

安装器记录 `.linxsci-release-install.json`，保存固定清单和来源哈希；受管、未修改的同版本副本可离线复用。手动展开的包可提供原清单后核验复用。缺少元数据、内容有修改、文件残缺、版本不符或目标为符号链接时保留目录并停止，不提供强制覆盖参数。

新装先验证临时目录，再排他预留目标；并发出现的目标不会被覆盖。POSIX 使用目录切换，Windows 使用排他文件写入并最后写入安装记录；失败清理自身创建的内容，保留其他进程新增的文件。Windows 分支有故障注入检查，尚需实际 Windows 平台验收。

更新使用明确的新版本包和独立目标目录，核验后由使用者处理旧目录、本地修改与助手发现配置。备份放在助手扫描目录外；不对 Release 副本执行 git pull，不承诺本地 npx 安装自动跟踪远程更新。
