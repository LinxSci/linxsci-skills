# 发现和选装 LinxSci Skill

[English](extensions.md)

需要查看可选能力、安装指定 Skill，或在任务中补装协作者时使用本指南，由当前 Agent 执行安装。base 可仅用 Python 3.9+ 和标准库独立运行；查看能力目录不需要 API Key、SDK、Git、npx 或联网请求。

## 选择能力

每个扩展都在自己的 GitHub 仓库提供完整 Skill。以下是可选能力，不代表当前电脑已经安装。

| Skill | 适用任务 | GitHub 来源 | 验证入口 |
| --- | --- | --- | --- |
| `linxsci-survey` | 主题文献调研、综述取证 | https://github.com/LinxSci/linxsci-survey | `linxsci survey --help` |
| `linxsci-idea` | 研究问题、方向与可验证方案构思 | https://github.com/LinxSci/linxsci-idea | `linxsci idea --help` |
| `linxsci-paper-qa` | 单篇论文阅读、基于原文的事实问答 | https://github.com/LinxSci/linxsci-paper-qa | `linxsci paper-qa --help` |
| `linxsci-paper` | 论文大纲、章节、初稿与修改 | https://github.com/LinxSci/linxsci-paper | `linxsci skill paper --help` |
| `linxsci-ppt` | 论文或研究材料的演示文稿 | https://github.com/LinxSci/linxsci-ppt | `linxsci ppt --help` |
| `linxsci-reproduce` | 研究代码检查、环境准备与复现 | https://github.com/LinxSci/linxsci-reproduce | `linxsci reproduce --help` |
| `linxsci-xiaohongshu` | 论文解读与小红书图文制作 | https://github.com/LinxSci/linxsci-xiaohongshu | `linxsci xiaohongshu --help` |

`linxsci paper` 查询基础论文资源，写作入口为 `linxsci skill paper`。安装主仓库或 Python 包不会安装这些扩展；`install-skill` 仅复制 base，不接受扩展名，也不下载扩展。

## 直接对 Agent 说

```text
使用 $linxsci-base 列出 LinxSci 可选扩展，说明各自用途，并检查当前环境中哪些已安装、哪些还需要配置。
```

```text
请使用 $linxsci-base 帮我从 https://github.com/LinxSci/linxsci-paper 安装 linxsci-paper。保留已有修改和配置，用兼容的 Python 环境实际安装 requirements.txt，配置当前 Agent 与 CLI 的发现路径，运行 linxsci skill paper --help 验证，并告诉我如何使用。
```

```text
请使用 $linxsci-base 帮我把这些研究材料做成 PPT；如果缺少 linxsci-ppt，授权你按其 GitHub README 安装并验证，随后继续完成当前任务，保留已有材料和输出位置。
```

## 检查当前安装

识别当前 Agent 及其实际发现目录。另行检查 CLI 的配置：默认是 `~/.agents/skills`，`LINXSCI_SKILLS_DIR` 会替换默认位置，指向包含完整 Skill 文件夹的绝对父目录。安装前核对相关已有副本、依赖和可执行文件路径。开发目录中有源码不代表 Agent 已发现，CLI 已发现也不代表所有 Agent 都已发现。详见 [CLI 发现约定](cli.zh-CN.md#自动发现与调用扩展-skill)。

展示能力时说明检查范围，区分已验证可用、文件存在但依赖或发现配置待处理、在已检查位置未找到，以及未检查。列目录不调用研究 API。完整兼容安装直接复用，保留修改和配置；冲突处理后再替换，备份放在发现目录之外。

## 安装所选 Skill

明确要求安装某项就是对应的安装授权。复用会话已有授权，需要补充授权时再确认；只安装所选扩展及任务确需的协作者，沿用用户要求的项目级或用户级范围。安装 Skill 不等于授权执行复现实验或发布内容。

读取目标 GitHub 仓库的 README、SKILL 和 requirements，按当前工具及 Agent 选择获取方式：

- **Skills CLI** 需要 Node.js 22.20+ 和 npx。例如为 Codex 用户级安装 Paper：`npx skills add https://github.com/LinxSci/linxsci-paper --skill linxsci-paper -g -a codex`。按实际情况替换仓库、Skill 与 Agent；项目级安装在项目目录执行并省略 `-g`。已有长期保留的本地源码时，在含 SKILL.md 的根目录运行 `npx skills add . --skill linxsci-paper -g -a codex`，记录工具报告的真实安装位置。
- **Git**：从所选公开 HTTPS 仓库克隆到新的暂存目录，检查后将完整 Skill 放到实际发现位置。例如：`git clone https://github.com/LinxSci/linxsci-paper.git /absolute/new/staging/linxsci-paper`。不把新源码直接混入已有安装。
- **源码 ZIP**：下载目标仓库的源码归档，检查并解压，放入以 Skill 命名的目录。SKILL.md 应直接位于该目录内，不多套一层归档名；保留 scripts、references、agents、requirements 和许可文件。

符号链接的目标必须长期保留。手动安装源码归档不要求 Git 或 Skills CLI。公开仓库不可访问或下载失败时报告具体步骤并保留已有材料，不自动换成 Codeup、旧 Release 包或镜像。

### Python 依赖与制作工具

已适配的扩展源码依赖 `linxsci==0.3.5`。Survey、Idea、Paper QA、Paper、PPT 和 Reproduce 使用 Python 3.9+；小红书要求 Python 3.10+、PyMuPDF、Pillow 和支持内容语言的字体。实际操作先读目标仓库当时的 requirements。Word/LaTeX、演示文稿制作和复现实验的额外工具按各自 Skill 检查。

base `0.3.5` 的随附脚本可独立运行，无需 SDK。已适配的扩展可复用符合依赖的 CLI/SDK 0.3.5 环境，七个扩展全部共用时使用 Python 3.10+。公开仓库副本可能尚未完成适配，以实际 requirements 为准；仍固定 0.3.4 的旧副本保留独立兼容环境。已发布 0.3.5 ZIP/wheel 仍包含原指南，本修订指南需未来新的 base 版本才会进入正式包。

复用兼容环境，或在 Skill 目录之外创建虚拟环境。依赖安装与执行使用同一解释器，将路径换成实际位置：

```bash
python -m pip install -r "/absolute/path/to/linxsci-paper/requirements.txt"
python -m pip check
linxsci --version
linxsci skill paper --help
```

激活该环境或使用明确的可执行文件路径，确保 `python` 和 `linxsci` 属于同一环境。复用已满足约束的依赖，处理版本冲突时保护其他任务环境。只安装 Skill 文件不等于安装 requirements；不根据本目录说明擅自升级 SDK 或放宽约束。

配置当前 Agent 的发现位置。CLI 使用其他父目录时，在实际执行 CLI 的环境中设置：

```bash
export LINXSCI_SKILLS_DIR="/absolute/path/to/assistant/skills"
```

Windows PowerShell：

```powershell
$env:LINXSCI_SKILLS_DIR = "C:\path\to\assistant\skills"
$env:PYTHONUTF8 = '1'
```

Windows 命令提示符使用 `set PYTHONUTF8=1`。Agent 捕获输出时向子进程传入 `PYTHONUTF8=1` 并按 UTF-8 解码；这些都是当前会话设置。按需刷新或重启 Agent，无法核实发现状态时标记待验证。需要服务调用时才在本机运行 `linxsci setup`，复用有效配置，不要求用户在聊天中提供 Key。

## 完成安装或继续原任务

报告源码来源及可获取的提交、安装目录、Python 解释器、依赖版本、发现状态、验证结果和调用示例。区分成功、失败、取消和待处理；帮助通过只说明入口可运行，不等于研究或制作任务完成。

纯安装请求以使用说明结束。任务中补装后读取目标 Skill，以原目标、工作目录、输入材料、已核实证据、参数和输出位置继续；不丢弃上下文或重复已完成的研究。选装 Paper 后先验证 `linxsci skill paper --help`，再交接写作；缺少 PPT 时安装并验证，检查其制作工具，然后继续制作用户要求的演示文稿。

Idea 只有新取证或补查才需要 Survey；沿用 Idea 已有的 `scripts/install_survey.py`、同一 Python 环境及其结果判断规则。离线证据复用不需要 Survey。其他协作按各 Skill 指令处理，不递归安装全套。拒绝或失败时保留有效材料并明确未完成部分，base 基础能力仍可使用。

## 更新扩展

先保留本地修改。Git 克隆使用 `git pull --ff-only`；Skills CLI 从仓库安装的用户级副本，例如使用 `npx skills update linxsci-paper -g`。本地目录安装先更新长期保留的源码，再重新执行安装；手动副本从同一仓库获取完整源码更新。协调更新共用环境的扩展源码，Idea 与 Survey 配对更新，并用同一解释器安装各自实际 requirements。保留配置及任务/证据文件。只更新 Python 包会留下旧 Skill 的检查，只更新源码则会留下旧依赖。核对 Python/CLI 路径、SDK 版本、发现目录和实际入口后刷新 Agent。base 更新不会更新扩展文件。
