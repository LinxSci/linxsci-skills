# 本地独立仓库与联调

主仓库管理 CLI、SDK、`skills/linxsci-base/`、公共文档和基础构建工具。七个扩展继续在 `skills/` 下各自保存完整 `.git/`，由主仓库忽略，各自通过 GitHub 公开源码。基础 Skill 不另建 `.git`，不使用子模块。

| 本地位置 | GitHub 仓库 |
| --- | --- |
| 主仓库及 `skills/linxsci-base/` | `LinxSci/linxsci-skills` |
| `skills/linxsci-idea/` | `LinxSci/linxsci-idea` |
| `skills/linxsci-survey/` | `LinxSci/linxsci-survey` |
| `skills/linxsci-paper-qa/` | `LinxSci/linxsci-paper-qa` |
| `skills/linxsci-paper/` | `LinxSci/linxsci-paper` |
| `skills/linxsci-ppt/` | `LinxSci/linxsci-ppt` |
| `skills/linxsci-reproduce/` | `LinxSci/linxsci-reproduce` |
| `skills/linxsci-xiaohongshu/` | `LinxSci/linxsci-xiaohongshu` |

现有 Codeup 远程可保留作为开发来源，公开用户无需 Codeup 权限。不要覆盖已有 `origin`。发布时先核对远程；既有主仓库使用 `github` 指向公开 GitHub，扩展可采用同样命名，各自推送到对应仓库。实际创建和推送按发布任务执行，配置中不保存凭据。

## 新维护者建立工作区

```bash
git clone https://github.com/LinxSci/linxsci-skills.git
cd linxsci-skills
git clone https://github.com/LinxSci/linxsci-idea.git skills/linxsci-idea
```

其他扩展按上表分别克隆，不覆盖已有目录。克隆主仓库不会自动取得扩展。公开安装见 [GitHub 安装指南](SKILL_INSTALLATION.zh-CN.md)。

## 联调环境

全部扩展共用环境时使用 Python 3.10 或更高兼容版本。在准备好所需扩展后：

```bash
python3.10 -m venv .local/dev-venv
source .local/dev-venv/bin/activate
python -m pip install -e . -r skills/linxsci-xiaohongshu/requirements.txt
export LINXSCI_SKILLS_DIR="$PWD/skills"
linxsci --help
linxsci skill survey --help
```

仅使用基础工程不要求检出七个扩展，也不需要小红书的依赖文件。各扩展依赖应以其实际 requirements 和发布约束为准。

已有工作区可使用本机 `.local/activate.sh` 和 `.local/linxsci-skills.code-workspace`。编辑器工作区显式列出七个独立仓库，便于分别提交。`.local/` 内配置不随主仓库提交。

`LINXSCI_SKILLS_DIR` 控制 CLI 扩展发现；助手的 Skill 发现需要单独配置。当前工作区 `.agents/skills/` 的链接仍指向这些目录，路径没有改变。本机 `.local/codex-dev` 仍是既有联调入口。

## 提交、版本记录与分发

在每个扩展自己的目录检查、验证和提交。主仓库的 `git status` 不显示被忽略扩展中的修改，主仓库提交也不会替扩展保存修改；不要强制添加扩展到主仓库索引。

`extensions.lock.json` 保留为 `development-baseline`，仅记录开发联调提交，不控制公开安装。需要更新基线时先产生真实提交，并确认所用远程可获取该 SHA；未提交工作区不能冒充已锁定提交。用户安装按各扩展 README 及实际 requirements 和接口要求检查兼容性。

七个扩展各自发布 GitHub 源码，仓库包含其跟踪的测试和开发工具；可从单个仓库执行开发验证。CLI/SDK 仅在实际功能或包数据变化需要时另行安排版本发布。历史构建资产和验收记录保留原字节。
