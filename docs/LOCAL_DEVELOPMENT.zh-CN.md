# 本地独立仓库与联调

主仓库管理 CLI、SDK、`skills/linxsci-base/`、公共文档和构建工具。其余七个扩展在 `skills/` 下各自保存完整 `.git/`，分别连接既有 Codeup 仓库，由主仓库 `.gitignore` 忽略。基础 Skill 不应另建 `.git`。

用户克隆公开主仓库可获得基础 Skill 和 CLI/SDK 源码。扩展需要独立安装；本地开发目录不随主仓库提交或 GitHub 自动源码 ZIP 分发。[固定版本构建](SKILL_RELEASES.zh-CN.md)生成包含扩展实际文件的单项包、完整套件和源码快照，各单项包随附共用安装模块。

## 目录与仓库归属

| 位置 | 管理方式 | 当前开发分支 |
| --- | --- | --- |
| 主仓库及 `skills/linxsci-base/` | 同一个主仓库 | `main` |
| `skills/linxsci-idea/` | 独立 Codeup 仓库 | `main` |
| `skills/linxsci-survey/` | 独立 Codeup 仓库 | `main` |
| `skills/linxsci-paper-qa/` | 独立 Codeup 仓库 | `main` |
| `skills/linxsci-paper/` | 独立 Codeup 仓库 | `main` |
| `skills/linxsci-ppt/` | 独立 Codeup 仓库 | `main` |
| `skills/linxsci-reproduce/` | 独立 Codeup 仓库 | `main` |
| `skills/linxsci-xiaohongshu/` | 独立 Codeup 仓库 | `main` |

公开配置不保存实际 Codeup 地址。主仓库保留既有 `github` 和 `origin` 远程；本机 `github` 对应公开 GitHub，`origin` 对应原基础工程 Codeup。向 GitHub 推送主仓库时明确使用 `git push github <分支>`。扩展各自的 `origin` 对应各自 Codeup。

## 新维护者建立工作区

普通克隆即可取得主仓库：

```bash
git clone https://github.com/LinxSci/linxsci-skills.git
cd linxsci-skills
```

维护者通过获授权的私有配置取得七个仓库地址，再分别克隆到上表目录。不要覆盖已有目录。以 Idea 为例，先在本机设置 `LINXSCI_IDEA_REPOSITORY` 为实际私有地址：

```bash
git clone "$LINXSCI_IDEA_REPOSITORY" skills/linxsci-idea
```

其他扩展同理，并核对各仓库的实际开发分支。需要复现某次联调时，按根目录 `extensions.lock.json` 的完整 `commit` 检出，不能把远端默认分支最新版本当成基线。检出固定提交后开始开发前，应明确选择或创建开发分支。

该清单是开发提交基线，只有名称、相对目录、分支和 SHA，不包含地址或凭据。它不记录未提交修改，也不是已发布的发行清单。`tools/build_skill_releases.py` 已读取它获取固定提交，结合 `release/suite.json`、显式基础提交及私有地址映射，在干净临时目录构建并生成独立发行清单；共用包安装器见 [安装指南](SKILL_INSTALLATION.zh-CN.md)，由构建输入生成到包内。

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

扩展修改应在对应 `skills/<名称>/` 中检查、提交并推送。主仓库的 `git status` 不显示这些被忽略目录中的修改；也不要用 `git add -f skills/<名称>` 把扩展纳入主仓库。

在本地准备联调基线时，先验证并提交各扩展，再将完整 SHA 写入主仓库 `extensions.lock.json`。推送主仓库更新或从 Codeup 构建之前，须先将扩展提交推送到 Codeup，并确认每个锁定提交可获取。分支只描述开发位置，固定版本以 SHA 为准。主仓库提交不会替扩展提交或推送。

固定版本构建由获授权的环境取得各独立仓库的指定提交，输出实际源码文件与可校验的清单。公开用户从 Release 资产安装，无需 Codeup 权限。依赖安装实现独立于 SDK；只有实际修改 SDK 功能或包数据时才安排相应 SDK 版本。

文档和代码在各自仓库提交；验证指定提交可获取后，更新锁定 SHA 并使用新套件版本构建。不要修改旧 ZIP 或将未提交内容标成已有源提交。单项包和完整套件不含测试，开发验收使用源码快照或完整维护者源码。候选进度、验收结果和发布待办记录在独立维护记录中，不写入用户安装提示词。
