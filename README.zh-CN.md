# LinxSci OpenAPI

[English](README.md)

通过 LinxSci OpenAPI v2 检索学术论文、阅读章节与引用、查询学术实体并解析 PDF。选择适合自己工作方式的入口，每种方式均支持文档中的全部 34 条接口。

| 使用方式 | 适用场景 | 入口 |
| --- | --- | --- |
| [AI Skill](#ai-skill) | 在支持本地 Skill 和脚本执行的助手中研究论文 | `$linxsci-base` |
| [CLI](#cli) | 在终端执行命令 | `linxsci` |
| [Python SDK](#python-sdk) | 在 Python 应用中集成接口 | `from linxsci import LinxSciClient` |

需要 **Python 3.9+**；调用服务时需要已有的 LinxSci API Key。Python 运行时无需第三方依赖。本项目（`linxsci-openapi-skills`）在 `skills/linxsci-base/` 中提供基础 Skill `linxsci-base`，CLI 和 SDK 则由同一个 `linxsci` Python 包提供。公开 Git 仓库为 `LinxSci/linxsci-skills`；仓库名、Skill 名和 Python 包名分别用于不同入口。

登录 [LinxSci API Key 管理页](https://linxsci.com/open-api?tab=keys) 获取 API Key。随后按下方安装与配置说明，在本机输入 Key；已有有效 Key 和配置可直接复用。

## AI Skill

Skill 可独立运行随附的 Python 脚本，无需先安装 `linxsci` Python 包。

### 发现和选装任务 Skill

base 也能引导你像选装插件一样添加任务 Skill：文献综述、研究构思、论文问答、论文写作、演示文稿、代码复现和小红书图文。各扩展按需从自己的 GitHub 仓库安装；[扩展指南](skills/linxsci-base/references/extensions.zh-CN.md) 提供能力目录、安装检查和任务续跑说明。

复制下面任一请求给当前 Agent：

```text
使用 $linxsci-base 列出 LinxSci 可选扩展，说明各自用途，并检查哪些已安装、哪些还需要配置。
```

```text
请使用 $linxsci-base 帮我从 https://github.com/LinxSci/linxsci-paper 安装 linxsci-paper。保留已有修改和配置，用兼容的 Python 环境实际安装 requirements.txt，配置 Agent 与 CLI 的发现路径，运行 linxsci skill paper --help 验证，并告诉我如何使用。
```

```text
请使用 $linxsci-base 帮我把这些研究材料做成 PPT；如果缺少 linxsci-ppt，授权你按其 GitHub README 安装并验证，随后继续原任务，保留已有材料和输出位置。
```

列目录不需要 API Key 或下载扩展。Agent 检查真实可用状态，只安装选中的 Skill，验证后继续任务。克隆主仓库不会自动取得扩展，更新 base 也不会更新扩展文件。

### 安装与配置

下载 [Skill 安装包](https://github.com/LinxSci/linxsci-skills/releases/download/v0.3.5/linxsci-base-0.3.5.zip)，完整解压后，在 macOS 双击 `Install.command`，Windows 双击 `Install.bat`。也可以在解压目录打开终端并运行：

```bash
python3 install.py
```

Windows 使用 `py -3 install.py`。安装器将完整 Skill 复制到 `~/.agents/skills/linxsci-base`，并引导你在本机隐藏输入 Key。其他助手目录可使用 `--skills-dir <父目录>` 指定。安装后刷新或重启助手。

已发布的 `v0.3.5` 安装包包含扩展安装引导，但包内指南仍描述当时的扩展 0.3.4 基线；安装时以目标仓库实际 requirements 为准。下方更新后的源码指南需要未来新的 base 版本才会进入下载包，已有 0.3.5 发布文件保持不变。

### 通过 Skills CLI 安装到 Codex 或其他 Agent

[Skills CLI](https://github.com/vercel-labs/skills#readme) 需要 Node.js 22.20+ 和 npx。从公开仓库安装为 Codex 用户级 Skill：

```bash
npx skills add https://github.com/LinxSci/linxsci-skills --skill linxsci-base -g -a codex
```

从已下载的本项目根目录安装：

```bash
npx skills add ./skills/linxsci-base --skill linxsci-base -g -a codex
```

`-g` 表示跨项目的用户级安装，去掉后安装到当前项目。可替换或同时指定多个 Agent：

| Agent | 参数 |
| --- | --- |
| Codex | `-a codex` |
| Claude Code | `-a claude-code` |
| Cursor | `-a cursor` |
| Gemini CLI | `-a gemini-cli` |

```bash
npx skills add https://github.com/LinxSci/linxsci-skills --skill linxsci-base -g -a codex claude-code cursor
```

多 Agent 安装时可选择 Symlink 方式，共用一份 Skill，以安装器显示的目录为准；本地目标须长期保留，不使用会被删除的临时解压目录。也可以在具备终端权限的 Agent 中发送：

```text
请使用 npx skills add https://github.com/LinxSci/linxsci-skills --skill linxsci-base -g -a codex 安装基础 Skill。检查同名安装并保留已有修改；完成后使用 Skill 随附脚本检查配置，API Key 在本机交互输入。
```

`linxsci-base` 使用随附脚本，不需要安装 Python 包；需要终端短命令时，按下方 CLI 部分安装 `linxsci==0.3.5`。已适配的扩展源码锁定 SDK `0.3.5`，可共用符合依赖的环境（全部七个共用时为 Python 3.10+）。以下载仓库实际 requirements 为准：公开副本可能尚未包含本轮修改，仍固定 `0.3.4` 的旧副本使用独立兼容环境。源码和依赖的协调更新见[扩展指南](skills/linxsci-base/references/extensions.zh-CN.md)。安装后重新加载助手。

克隆超时时可改用上方 ZIP。安装后向助手提出：

> 使用 $linxsci-base 检查配置；如需配置，请引导我在本机安全输入 API Key，不要让我把 Key 发到聊天中。

### 使用 Skill

> 使用 $linxsci-base 检索图神经网络论文，返回核实后的题名、标识和来源链接。

> 我只记得论文比较了对比学习与掩码预训练在图像分类上的效果。请使用 $linxsci-base 定位候选，核实题名、标识和来源。

需要回答单篇论文事实时，助手将核实后的论文和原问题交给可用的 `linxsci-paper-qa`，实际检查相关原文后作答。主题综述、研究构思、论文写作和演示文稿由对应任务 Skill 负责，基础接口支持其中的子步骤。缺少扩展时说明安装方式；基础检索和资源读取仍可独立使用。

> 使用 $linxsci-base 解析 /absolute/path/paper.pdf，记录任务 ID，完成后获取结果。

将 PDF 路径替换为助手可以访问的实际文件。解析会将文件上传至配置的服务。说明所需论文数量、回答长度和语言，助手负责检索与整理。

### 更新与卸载

从仓库通过 Skills CLI 安装的用户级副本，使用：

```bash
npx skills update linxsci-base -g
```

本地目录安装的副本，先更新源项目，再从源项目根目录重新执行原安装命令，并沿用 Agent 和安装范围。替换前保留安装目标中的本地修改。

对于自带安装器管理的副本，解压新版安装包，在**新版**目录执行：

```bash
python3 install.py --update --no-config
```

自定义安装目录时，补充原来使用的 `--skills-dir`。更新保留配置，并将旧副本备份到助手扫描目录之外。其他安装器管理的副本请使用原安装器更新。

卸载时使用原安装器的移除功能，或删除自带安装器创建的目录，然后刷新助手。如需清除保存的配置，请在删除 Skill 前让助手协助处理。

安装参数、配置、使用示例和故障排查见 [Skill 使用指南](docs/USER_GUIDE.zh-CN.md)。

## CLI

### 安装与配置

需要 Python 3.9+。已有虚拟环境时直接激活；仅在需要新环境时执行下面的创建命令：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U linxsci==0.3.5
linxsci --version
linxsci setup
```

`linxsci --version` 应输出 `0.3.5`，不需要 API Key，也不调用 API。CLI 和 SDK 随同一个包安装。

从 PyPI 安装可在任意目录执行，安装目标由当前 `python` 对应的环境决定，切换目录不会切换虚拟环境。使用 `python -c "import sys; print(sys.executable)"` 查看解释器；要明确使用 Python 3.10，可将命令中的 `python` 替换为 `python3.10`。

SSL 或代理错误、pip 自身版本检查警告的处理方式，以及禁用缓存验证远程下载的步骤，见 [CLI 安装指南](docs/CLI_GUIDE.zh-CN.md#从-pypi-安装)。

也可以从源码安装：

```bash
git clone https://github.com/LinxSci/linxsci-skills.git linxsci-openapi-skills
cd linxsci-openapi-skills
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
linxsci --version
linxsci setup
```

Windows 使用 `py -3 -m venv .venv` 创建环境，在命令提示符 CMD 中运行 `.venv\Scripts\activate.bat` 激活。也可通过 `python -m pip install /path/to/linxsci-0.3.5-py3-none-any.whl` 安装已下载的 wheel。已安装 uv 时，可用 `uv tool install /path/to/linxsci-0.3.5-py3-none-any.whl` 创建隔离的终端工具安装。

`linxsci setup` 通过隐藏输入读取 API Key。默认服务根地址为 `https://linxsci.com`，不添加 `/openapi/v2`。`LINXSCI_BASE_URL` 和 `LINXSCI_OPENAPI_KEY` 优先于保存的设置；`LINXSCI_CONFIG_FILE` 可指定其他配置文件。默认配置位于 macOS/Linux 的 `~/.config/linxsci-skills/config.json`，或 Windows 的 `%LOCALAPPDATA%\linxsci-skills\config.json`。

### 检索、阅读与解析

```bash
linxsci search "graph neural networks"
linxsci paper "<returned-paper-id>"
linxsci paper "<returned-paper-id>" --resource toc
linxsci paper "<returned-paper-id>" --resource sections --item-id "<returned-section-id>"
linxsci upload /absolute/path/paper.pdf
linxsci task "<returned-task-id>"
linxsci task "<returned-task-id>" --result
```

使用响应返回的实际 ID，确认任务完成后才获取结果。PDF 接口需要额外解析 Key 时，相关命令读取 `LINXSCI_MINERU_API_KEY`。

接口输出和错误默认使用紧凑 JSON；`--pretty` 和 `--human-errors` 提供便于人工阅读的终端输出。全局 `--select`、`--fields`、`--limit` 和 `--table` 在本地筛选响应。超过 12000 字符的输出及二进制内容保存到文件并返回 JSON 引用；`read-output` 读取已保存的响应，不再请求接口。详见 [CLI 全部命令与参数](docs/CLI_GUIDE.zh-CN.md)。

`linxsci config` 查看设置而不展示 Key；`linxsci doctor --json` 请求 `/meta` 检查连接，计入正常接口调用；`linxsci config --clear` 删除保存的设置，不清除环境变量或撤销服务端 Key。

### 更新与卸载

PyPI 安装使用 `python -m pip install --upgrade linxsci` 更新；通过 uv 从 PyPI 安装的副本使用 `uv tool upgrade linxsci`。更新源码后执行 `python -m pip install --upgrade .`，或运行 `python -m pip install --upgrade /path/to/linxsci-<version>-py3-none-any.whl` 安装新版 wheel。uv 隔离安装使用 `uv tool install --force /path/to/linxsci-<version>-py3-none-any.whl`。将 `<version>` 替换为下载的实际版本号。

在安装环境中运行 `python -m pip uninstall linxsci` 卸载；uv 隔离安装使用 `uv tool uninstall linxsci`。

## Python SDK

CLI 与 SDK 通过 `linxsci` 一起安装。应用环境中已有该包时，无需另外安装 SDK 包；Skill 改名后，SDK 导入及 API 调用方式保持兼容。

### 安装

从 PyPI 安装到应用实际使用的 Python 环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U linxsci==0.3.5
python -c "import linxsci; print(linxsci.__version__)"
```

已有应用环境时，激活后直接执行安装和验证两条命令。验证应输出 `0.3.5`，确认 SDK 可导入及其版本；此检查不需要 API Key，也不调用 API。安装排查与远程下载验证见 [SDK 安装指南](docs/DEVELOPMENT.zh-CN.md#从-pypi-安装)。

Windows 使用 `py -3 -m venv .venv`，并在命令提示符 CMD 中运行 `.venv\Scripts\activate.bat`。从源码安装时，下载或克隆本仓库，在仓库根目录使用应用的 Python 环境执行 `python -m pip install .`。

### 使用 Python 配置与调用

下面的示例优先读取应用环境中的 Key，本地交互使用时也可隐藏输入：

```python
import os
from getpass import getpass
from linxsci import LinxSciClient, LinxSciError

client = LinxSciClient(
    base_url=os.environ.get("LINXSCI_BASE_URL", "https://linxsci.com"),
    api_key=os.environ.get("LINXSCI_OPENAPI_KEY") or getpass("请输入 LinxSci API Key："),
    timeout=60,
)

try:
    response = client.search("graph neural networks")
    print(response.json())
except LinxSciError as error:
    print(error.status, error.error_code)
    print(error.request_id, error.framework_request_id)
```

非交互应用通过部署环境或秘密管理器注入 Key。构造参数优先于环境变量、已有配置文件和发行默认地址。SDK 不会自动加载 `.env` 文件。同时传入 `base_url` 与 `api_key` 时跳过本地配置文件；构造客户端不会发送请求或保存 Key。

复用已配置的客户端读取论文或上传 PDF：

```python
paper_id = "<actual-returned-paper-id>"
print(client.paper(paper_id, "toc").json())

response = client.upload_pdf(
    "/absolute/path/paper.pdf",
    mineru_key=os.environ.get("LINXSCI_MINERU_API_KEY"),
)
print(response.json())
```

SDK 返回包含 HTTP 状态、响应头和原始 `body` 的 `Response`；JSON 使用 `.json()`，二进制内容直接保存 `body`。可选的 PDF Key 需要在 Python 中读取并显式传入。记录响应返回的实际任务 ID，用 `client.pdf_task(task_id)` 查询状态，确认完成后再调用 `client.pdf_task(task_id, result=True)`。详见 [SDK 方法、参数与错误处理](docs/DEVELOPMENT.zh-CN.md)。

### 更新与卸载

PyPI 安装使用 `python -m pip install --upgrade linxsci` 更新。也可在应用环境中运行 `python -m pip install --upgrade /path/to/linxsci-<version>-py3-none-any.whl` 安装新版 wheel，或更新源码后运行 `python -m pip install --upgrade .`。升级后重启长期运行的 Python 进程。

使用 `python -c "import linxsci; print(linxsci.__version__)"` 检查 SDK 导入和版本。卸载执行 `python -m pip uninstall linxsci`。删除安装包不会删除应用凭据或撤销 API Key。

## API 参考

POST 字段、分页及 PDF 任务状态应按所选接口的契约使用，保留返回的实际 ID 和请求追踪 ID。遇到 `-3905` 等执行或计费结果未确认的情况，先核查操作状态，再决定是否重复上传或创建任务。

详见 [HTTP 接口、认证与错误处理](docs/API.zh-CN.md)。各链接指南均可切换至英文版。

## 许可

代码与 Skill 指令采用 [MIT 许可证](LICENSE)，允许使用、修改、商业使用和再分发。再分发时须保留版权声明和许可文本。

访问 LinxSci API 仍需有效的 API Key，并遵守相应服务访问规则；软件许可证不改变 API 鉴权、配额或计费。第三方依赖及获取的论文、图片等材料仍适用各自的许可。
