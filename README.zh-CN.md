# linxsci-skills

[English](README.md)

通过 LinxSci OpenAPI v2 检索学术论文、阅读章节与引用、查询学术实体并解析 PDF。选择适合自己工作方式的入口，每种方式均支持文档中的全部 34 条接口。

| 使用方式 | 适用场景 | 入口 |
| --- | --- | --- |
| [AI Skill](#ai-skill) | 在支持本地 Skill 和脚本执行的助手中研究论文 | `$linxsci-skills` |
| [CLI](#cli) | 在终端执行命令 | `linxsci` |
| [Python SDK](#python-sdk) | 在 Python 应用中集成接口 | `from linxsci import LinxSciClient` |

需要 **Python 3.9+**；调用服务时需要已有的 LinxSci API Key。Python 运行时无需第三方依赖。项目与 Skill 名为 `linxsci-skills`，Python 安装包名为 `linxsci`。

## AI Skill

### 安装与配置

Skill 独立运行随附脚本，选择一种安装方式即可。

本机有 Node.js / npx，且使用兼容的 Skill 安装器时：

```bash
npx skills add https://github.com/LinxSci/linxsci-skills --skill linxsci-skills
```

安装后，使用安装器输出的实际 Skill 目录配置 Key：

```bash
python3 "/absolute/path/to/installed/linxsci-skills/scripts/cli.py" setup
```

也可以下载并解压 [仓库源码](https://github.com/LinxSci/linxsci-skills)，或独立的 `linxsci-skills-0.3.0.zip` 安装包。在解压目录执行：

```bash
python3 install.py
```

Windows 将 `python3` 替换为 `py -3`。独立安装包还包含 `Install.command` 和 `Install.bat`。该安装器默认复制到 `~/.agents/skills/linxsci-skills`，随后通过隐藏输入配置 Key。其他助手位置可使用 `--skills-dir <安装父目录>`。安装后刷新或重启助手。

### 在助手中使用

在助手中输入：

> 使用 $linxsci-skills 搜索图神经网络相关论文，阅读方法章节，比较主要方法并附上来源。

> 使用 $linxsci-skills 解析 /absolute/path/paper.pdf，记录任务 ID，任务完成后读取结果。

将 PDF 路径替换为实际本地文件。上传会将该文件发送到配置的服务。查看本机设置或检查连接时，使用已安装脚本的绝对路径：

```bash
python3 "/absolute/path/to/installed/linxsci-skills/scripts/cli.py" config
python3 "/absolute/path/to/installed/linxsci-skills/scripts/cli.py" doctor --json
```

脚本默认输出紧凑 JSON，大型响应和二进制内容返回文件引用。响应筛选、文件读取和错误处理见 [Skill 自身的命令与参数参考](skills/linxsci-skills/references/cli.zh-CN.md)。`doctor` 会实际请求 `/meta`，需要检查连接时再执行。

### 更新与卸载

通过随附安装器管理的副本，下载并解压新版源码或安装包，在该**新版本目录**运行：

```bash
python3 install.py --update --no-config
```

安装器保留已有配置，并将旧托管副本备份到助手扫描目录之外。外部工具管理的副本使用原安装器更新。卸载时删除已安装的 `linxsci-skills` 目录。如需同时删除保存的配置，在删除目录前运行已安装脚本的 `config --clear`；这不会撤销服务端 Key。

详见 [Skill 独立安装与安装器参数](skills/linxsci-skills/SKILL.zh-CN.md#独立安装-skill) 和 [Skill 用户指南](docs/USER_GUIDE.zh-CN.md)。

## CLI

### 安装与配置

从源码安装到 Python 环境：

```bash
git clone https://github.com/LinxSci/linxsci-skills.git
cd linxsci-skills
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
linxsci --version
linxsci setup
```

Windows 使用 `py -3 -m venv .venv` 创建环境，在命令提示符 CMD 中运行 `.venv\Scripts\activate.bat` 激活。也可通过 `python -m pip install /path/to/linxsci-0.3.0-py3-none-any.whl` 安装已下载的 wheel。已安装 uv 时，可用 `uv tool install /path/to/linxsci-0.3.0-py3-none-any.whl` 创建隔离的终端工具安装。

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

更新源码后执行 `python -m pip install --upgrade .`，或运行 `python -m pip install --upgrade /path/to/linxsci-<version>-py3-none-any.whl` 安装新版 wheel。uv 隔离安装使用 `uv tool install --force /path/to/linxsci-<version>-py3-none-any.whl`。将 `<version>` 替换为下载的实际版本号。

在安装环境中运行 `python -m pip uninstall linxsci` 卸载；uv 隔离安装使用 `uv tool uninstall linxsci`。

## Python SDK

### 安装

将 wheel 安装到应用实际使用的 Python 环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install /path/to/linxsci-0.3.0-py3-none-any.whl
python -c "from linxsci import LinxSciClient; print('SDK import OK')"
```

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

在应用环境中运行 `python -m pip install --upgrade /path/to/linxsci-<version>-py3-none-any.whl` 安装新版 wheel，或更新源码后运行 `python -m pip install --upgrade .`。升级后重启长期运行的 Python 进程。

使用 `python -c "from importlib.metadata import version; print(version('linxsci'))"` 检查已安装版本。卸载执行 `python -m pip uninstall linxsci`。删除安装包不会删除应用凭据或撤销 API Key。

## API 参考

POST 字段、分页及 PDF 任务状态应按所选接口的契约使用，保留返回的实际 ID 和请求追踪 ID。遇到 `-3905` 等执行或计费结果未确认的情况，先核查操作状态，再决定是否重复上传或创建任务。

详见 [HTTP 接口、认证与错误处理](docs/API.zh-CN.md)。各链接指南均可切换至英文版。
