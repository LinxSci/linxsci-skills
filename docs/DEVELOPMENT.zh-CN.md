# Python SDK 使用指南

[English](DEVELOPMENT.md)

## 从 PyPI 安装

需要 Python 3.9+。在应用实际使用的环境中安装。已有虚拟环境时直接激活，不要重新创建。新环境的 macOS/Linux 步骤：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --index-url https://pypi.org/simple linxsci==0.3.2
python -c "from linxsci import LinxSciClient; from importlib.metadata import version; print(version('linxsci'))"
```

Windows 的命令提示符使用以下两行创建并激活环境，再执行上方的 `python -m pip` 和验证命令：

```bat
py -3 -m venv .venv
.venv\Scripts\activate.bat
```

验证应输出 `0.3.2`，此检查不需要 API Key。使用 `python -m pip` 能确保安装到当前解释器对应的环境。

随后按下文在 Python 中配置 `LinxSciClient`。更新后重启长期运行的应用进程。

使用 pip 安装时，在原环境中更新：

```bash
python -m pip install --upgrade --index-url https://pypi.org/simple linxsci
python -c "from linxsci import LinxSciClient; from importlib.metadata import version; print(version('linxsci'))"
```

### 安装时出现 SSL 错误

`SSLEOFError` 表示 HTTPS 连接失败，不能仅凭它断定安装包有问题。先尝试在当前环境更新 pip；如果 pip 自身无法连接，但已安装的 [uv](https://docs.astral.sh/uv/getting-started/installation/) 可以连接，可在包含 `.venv` 的目录执行：

```bash
uv pip install --python .venv/bin/python --index-url https://pypi.org/simple --upgrade pip
.venv/bin/python -m pip install --index-url https://pypi.org/simple linxsci==0.3.2
```

环境为 `.venv-1` 时替换路径；Windows 使用 `.venv/Scripts/python.exe`。若仍失败，检查网络、代理及证书配置，保持 HTTPS 验证开启，参考 [pip 证书说明](https://pip.pypa.io/en/stable/topics/https-certificates/)。也可从下文的 GitHub 发行附件下载 wheel，在已激活的环境中离线安装：

```bash
python -m pip install --no-index --no-deps ./linxsci-0.3.2-py3-none-any.whl
```

此 wheel 没有额外运行时依赖。从文件所在目录执行，安装后运行上面的版本验证命令。

本文面向在 Python 程序中调用 LinxSci 的开发者，按当前项目的安装方式、SDK 入口和接口行为编写。首次使用按第 1 节、第 2.1 节和第 3 节操作，即可完成一次论文检索；其他章节按需阅读。

SDK 的公共 Python 入口为 `from linxsci import LinxSciClient`。SDK 将 Python 方法转换为 LinxSci API 请求，自动附带用户的 LinxSci API Key。只使用 SDK 时，完成 Python 包安装和 Key 配置即可。

## 目录

1. [安装项目](#1-安装项目)
2. [配置服务地址和 API Key](#2-配置服务地址和-api-key)
3. [完成第一次 SDK 检索](#3-完成第一次-sdk-检索)
4. [使用 SDK 阅读论文](#4-使用-sdk-阅读论文)
5. [使用 SDK 解析 PDF](#5-使用-sdk-解析-pdf)
6. [调用其他接口](#6-调用其他接口)
7. [处理响应和错误](#7-处理响应和错误)
8. [验证安装、更新与卸载](#8-验证安装更新与卸载)
9. [常见问题](#9-常见问题)

需要逐个接口调用时，直接查看 [全部 34 个接口的 SDK 对照表](#66-全部-34-个接口的-sdk-对照表)；方法签名见 [SDK 方法与参数速查](#65-sdk-方法与参数速查)。

## 1. 安装项目

### 从安装包使用 SDK

从 [GitHub 发行附件](https://github.com/LinxSci/linxsci-skills/releases/tag/v0.3.2)下载 wheel，在自己的 Python 项目环境中安装：

```bash
python -m pip install /path/to/linxsci-0.3.2-py3-none-any.whl
```

Python 安装包名和导入名均为 `linxsci`。将 SDK 安装到应用实际使用的解释器中。源码安装步骤如下。

### 1.1 获取源码

需要 Python 3.9 或以上版本。已有源码时进入项目根目录；克隆源码时执行：

```bash
git clone https://github.com/LinxSci/linxsci-skills.git
cd linxsci-skills
```

后续安装、配置和运行示例的命令均在项目根目录执行。

### 1.2 创建环境并安装

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
```

**Windows（命令提示符 CMD）**

```bat
py -3 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
```

已有 `.venv` 时跳过创建，激活后继续。`-e .` 将当前源码安装为可编辑包，适合本地开发；修改源码后，SDK 使用修改后的实现。运行时依赖 Python 标准库，安装时需要获取构建工具。

### 1.3 确认安装成功

```bash
python -c "from linxsci import LinxSciClient; print('SDK import OK')"
```

该命令应输出 `SDK import OK`，不会调用远程 API。后续 Python 程序也应使用此 `.venv` 的解释器。

## 2. 配置服务地址和 API Key

### 2.1 首次使用：在 Python 中配置

本地交互运行时，通过隐藏输入读取 Key，并传入客户端：

```python
from getpass import getpass
from linxsci import LinxSciClient

client = LinxSciClient(
    base_url="https://linxsci.com",
    api_key=getpass("请输入 LinxSci API Key："),
    timeout=60,
)
```

构造客户端不会发送请求，也不会将 Key 保存到磁盘。可在同一 Python 进程中继续使用 `client`。地址仅填写服务根地址，不添加 `/openapi/v2`。非交互应用应通过部署环境或秘密管理器提供凭据，见下一节。

已有配置文件的默认位置为 macOS/Linux 的 `~/.config/linxsci-skills/config.json`，或 Windows 的 `%LOCALAPPDATA%\linxsci-skills\config.json`。配置文件并非必需；同时显式传入 `base_url` 和 `api_key` 时不会读取该文件。不要把真实 Key 或配置文件提交到仓库。

### 2.2 按需：环境变量和显式参数

SDK 按以下顺序解析地址和 Key：

**显式构造参数 → 进程环境变量 → 本地配置文件 → 发行包内的默认地址。**

地址有发行默认值，Key 必须由调用方提供。如果通过部署系统设置了下列变量，可以直接使用 `LinxSciClient()`：

| 环境变量 | 作用 |
| --- | --- |
| `LINXSCI_BASE_URL` | 覆盖服务根地址 |
| `LINXSCI_OPENAPI_KEY` | 覆盖 LinxSci API Key |
| `LINXSCI_CONFIG_FILE` | 指定本地配置文件路径，用于隔离不同环境 |
| `LINXSCI_MINERU_API_KEY` | 可选的 PDF 解析 Key，SDK 需读取后显式传入，见第 5 节 |

项目不会自动加载 `.env`。仅将值写入 `.env` 或复制 `.env.example` 不会使其进入进程环境。

程序也可显式配置客户端。以下代码要求进程已设置 `LINXSCI_OPENAPI_KEY`：

```python
import os
from linxsci import LinxSciClient

client = LinxSciClient(
    base_url="https://linxsci.com",
    api_key=os.environ["LINXSCI_OPENAPI_KEY"],
    timeout=60,
)
```

客户端只使用用户的 LinxSci API Key。服务端转发 Agent API 所需的密钥由服务管理员配置。

### 2.3 按需：检查连接与更换凭据

复用已经配置的客户端：

```python
print("服务地址：", client.base_url)
response = client.request("GET", "/meta")
print("HTTP 状态：", response.status)
print(response.json())
```

不要输出 `client.api_key`。该检查会实际调用一次接口；检查成功不代表其他接口也已启用。更换地址或 Key 后，用新值重新构造客户端；删除应用中的凭据不会撤销服务端 Key。

下文重新创建 `LinxSciClient()` 的示例，需要当前 Python 进程已设置环境变量，或已存在有效配置文件；也可以省略重新创建步骤，复用第 2.1 节的 `client`。交互输入的 Key 只在当前进程中有效。

## 3. 完成第一次 SDK 检索

### 3.1 运行仓库自带示例

源码安装且运行环境已提供 Key 后，可运行仓库示例；wheel 用户可直接使用下一节的 Python 示例：

```bash
python examples/research.py
```

该脚本检索 `graph neural networks`，输出 HTTP 状态和实际 JSON 响应。发生错误时输出错误码和请求 ID，退出并保留诊断信息，不自动重试。

### 3.2 在自己的程序中调用

以下代码可保存为项目根目录下的 `test_sdk.py`，然后用 `python test_sdk.py` 运行：

```python
import json
import os
from getpass import getpass
from linxsci import LinxSciClient, LinxSciError

try:
    client = LinxSciClient(
        base_url=os.environ.get("LINXSCI_BASE_URL", "https://linxsci.com"),
        api_key=os.environ.get("LINXSCI_OPENAPI_KEY") or getpass("请输入 LinxSci API Key："),
        timeout=60,
    )
    response = client.search("graph neural networks")
    print("HTTP 状态：", response.status)
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))
except LinxSciError as error:
    print("HTTP 状态：", error.status)
    print("错误码：", error.error_code)
    print("上游/代理请求 ID：", error.request_id)
    print("LinxSci 框架请求 ID：", error.framework_request_id)
    if error.execution_uncertain:
        print("请先核查执行与计费结果，不要直接重复请求。")
except (ValueError, OSError):
    print("请检查服务配置、输入参数及响应是否为 JSON。")
```

将搜索词替换为自己的主题即可。中文检索同样使用 `client.search("大语言模型智能体")`。

`response.json()` 保留服务端的数据结构，具体论文列表、标识和分页字段以实际响应和部署契约为准。本项目不提供统一的列表字段映射；先查看响应，再按真实字段取值。空结果应按原样处理。

## 4. 使用 SDK 阅读论文

本节需要从搜索响应中选择真实论文 ID；章节和资源 ID 继续从对应接口响应中取得。下列示例通过终端提示输入这些 ID，不需要修改代码中的占位字符串。

### 4.1 读取详情和目录

```python
from linxsci import LinxSciClient

client = LinxSciClient()
paper_id = input("请输入搜索返回的论文 ID（保留来源前缀）：").strip()

print("论文详情：", client.paper(paper_id).json())
print("论文目录：", client.paper(paper_id, "toc").json())
```

论文 ID 需要 `local:`、`arxiv:`、`openalex:`、`s2:` 或 `doi:` 来源前缀。例如 DOI 标识采用 `doi:10.xxxx/xxxx` 形式。`paper()` 接收原始 ID 并负责路径编码，不要提前把其中的 `/` 替换成 `%2F`。

### 4.2 读取指定章节

先查看目录，再复制目录中返回的实际章节 ID：

```python
from linxsci import LinxSciClient

client = LinxSciClient()
paper_id = input("论文 ID：").strip()
section_id = input("目录返回的章节 ID：").strip()

response = client.paper(paper_id, "sections", item_id=section_id)
print(response.json())
```

章节名称不一定等于章节 ID。需要哪一节就读取哪一节；需要全文时，使用 `client.paper(paper_id, "content")`。

### 4.3 其他论文资源

以下资源值可作为 `paper()` 的第二个参数；按需选择调用：

| 资源值 | 用途 | 额外参数 |
| --- | --- | --- |
| 不传资源值 | 论文详情 | 无 |
| `toc` / `content` | 目录 / 内容 | 无 |
| `sections` | 指定章节 | `item_id=section_id` |
| `figures` / `assets` | 图表清单 / 指定资源 | `assets` 需要 `item_id=asset_id` |
| `references` / `citations` | 参考文献 / 被引论文 | 无 |
| `related` / `graph` / `citation` | 相关论文 / 引用图谱 / 引用格式 | 无 |

`paper(..., query=...)` 可传入上游实际支持的查询参数，字段需按部署契约填写。

指定资源可能返回二进制内容，使用 `body` 保存，不要强制调用 `json()`：

```python
from pathlib import Path
from linxsci import LinxSciClient

client = LinxSciClient()
paper_id = input("论文 ID：").strip()
asset_id = input("接口返回的资源 ID：").strip()

response = client.paper(paper_id, "assets", item_id=asset_id)
Path("asset.bin").write_bytes(response.body)
print("资源原始内容已保存到 asset.bin")
```

## 5. 使用 SDK 解析 PDF

PDF 解析分为“上传并创建任务 → 查询状态 → 获取结果”。上传会将指定文件发送到配置的服务；使用适合该环境的文件，创建成功后记录实际任务 ID。

### 5.1 上传一次并查看任务响应

```python
import os
from linxsci import LinxSciClient

client = LinxSciClient()
pdf_path = input("请输入本地 PDF 文件路径：").strip()

response = client.upload_pdf(
    pdf_path,
    mineru_key=os.environ.get("LINXSCI_MINERU_API_KEY"),
)
print(response.json())
```

`mineru_key` 仅在部署契约要求时提供，未设置环境变量时为 `None`。SDK 不会自动读取该变量；上面的代码显式读取后传入。附加表单字段通过 `fields={字段名: 值}` 传入，字段和文件大小限制以部署契约为准。当前客户端在内存中构建上传内容。

### 5.2 使用返回的任务 ID 查询状态

```python
from linxsci import LinxSciClient

client = LinxSciClient()
task_id = input("创建任务响应中的实际任务 ID：").strip()

print(client.pdf_task(task_id).json())
```

根据实际响应判断是否完成，当前文档没有定义统一的状态字段或终态枚举。未完成时稍后再查，不要再次上传同一文件来代替状态查询。

### 5.3 确认完成后获取结果

```python
from linxsci import LinxSciClient

client = LinxSciClient()
task_id = input("已完成任务的实际任务 ID：").strip()

print(client.pdf_task(task_id, result=True).json())
```

如果查询状态或结果时也需要 `X-MinerU-API-Key`，使用第 6 节的 `request()`，向对应 PDF 路径传入 `mineru_key`。状态和结果接口的返回类型以部署契约为准；若返回文件内容，读取 `body`。

## 6. 调用其他接口

便捷方法之外的接口统一使用 `request()`，可调用当前项目支持的全部 34 条路由。方法和路径见 [接口文档](API.zh-CN.md)。

SDK 的 `request()` 已接入全部方法与路径，常用论文操作提供便捷方法。PDF 文件上传使用 `upload_pdf()`。当前接口分布为服务与健康 4 个、搜索与解析 6 个、论文详情与引用 11 个、推荐 2 个、学术实体 7 个、PDF 解析 4 个。仅调用目标接口即可，不要求先完成其他研究工作流。

### 6.1 GET 请求

例如查询用量：

```python
from linxsci import LinxSciClient

client = LinxSciClient()
response = client.request("GET", "/usage")
print(response.json())
```

路径相对于 `/openapi/v2`，不包含服务域名或此前缀。查询参数通过 `query` 传递；JSON 请求体通过 `payload` 传递。

### 6.2 JSON POST 请求

以下请求与 `client.search()` 调用同一个综合搜索接口：

```python
from linxsci import LinxSciClient

client = LinxSciClient()
response = client.request(
    "POST",
    "/papers/search",
    payload={"query": "graph neural networks"},
)
print(response.json())
```

其他 POST 接口的业务模型依照实际部署的 Agent API 契约填写。`{}` 仅能表示一个 JSON 对象，不能当作所有 POST 接口都有效的请求模板。

### 6.3 动态路径、查询参数和 PDF 头

`request()` 中的动态 ID 需要调用方独立编码；例如作者论文接口：

```python
from urllib.parse import quote
from linxsci import LinxSciClient

client = LinxSciClient()
author_id = input("接口返回的作者 ID：").strip()
path = "/authors/" + quote(author_id, safe=":") + "/papers"

print(client.request("GET", path).json())
```

GET 查询参数可使用 `query={字段名: 值}`；多个同名值可使用列表。PDF 路径可通过 `mineru_key` 显式附加 `X-MinerU-API-Key`。SDK 不接受在非 PDF 路径上发送该头。

### 6.4 从 JSON 文件调用 POST

使用 Python 读取 JSON 文件，再将解析后的值传给 `payload`。以下示例调用推荐接口，运行前按实际上游契约准备请求文件：

```python
import json
from pathlib import Path
from linxsci import LinxSciClient

client = LinxSciClient()
request_file = input("推荐接口请求 JSON 文件路径：").strip()
recommendations_body = json.loads(Path(request_file).read_text(encoding="utf-8"))

response = client.request("POST", "/recommendations", payload=recommendations_body)
print(response.json())
```

其他 JSON POST 可使用相同的读取方式，替换目标路径和对应业务请求文件即可。SDK 的 `payload` 接收解析后的 Python JSON 值，不能直接传 `"@request.json"` 代替文件读取。

### 6.5 SDK 方法与参数速查

当前公开调用签名如下；方法返回 `Response`，构造客户端本身不发起网络请求：

```text
LinxSciClient(base_url=None, api_key=None, timeout=60, *, framework_request_id=None)
client.search(query, **options)
client.paper(paper_id, resource=None, *, item_id=None, query=None)
client.upload_pdf(file, *, fields=None, mineru_key=None)
client.pdf_task(task_id, *, result=False)
client.request(method, path, *, query=None, payload=None, file=None,
               fields=None, mineru_key=None, request_id=None, framework_request_id=None)
```

`timeout` 单位为秒，须为正的有限数值。`search()` 的 `options` 按上游契约传入，最终检索词使用 `query` 参数。`paper()` 和 `pdf_task()` 对原始 ID 编码；`request()` 接收已编码的动态路径。

| `request()` 参数 | 用法与约束 |
| --- | --- |
| `method` / `path` | 方法为 `GET` 或 `POST`，路径省略 `/openapi/v2`；仅允许当前文档中的路由 |
| `query` | 查询参数字典，同名多值使用列表，SDK 自动编码 |
| `payload` | JSON 请求值，由 SDK 序列化；GET 不接受请求体 |
| `file` | 本地文件路径，仅用于 `POST /pdf/parse/upload`，不能同时传 `payload` |
| `fields` | multipart 附加表单字段字典，仅与文件上传一起使用，字段名按上游契约 |
| `mineru_key` | PDF 接口可选的 `X-MinerU-API-Key`；SDK 需要调用方显式传入 |
| `request_id` | 可选的 `X-Request-ID`，未传时 SDK 自动生成 |
| `framework_request_id` | 可选的 `X-ANYTHINGRIGHT-REQ-ID`，覆盖客户端构造时的同名参数 |

### 6.6 全部 34 个接口的 SDK 对照表

下表每一行都是一次独立调用，返回 `Response`，不要将整张表当作必须顺序执行的流程。先创建已配置的 `client = LinxSciClient()`，再按需准备所选接口使用的变量：

| 变量 | 准备方式 |
| --- | --- |
| `paper_id`、`section_id`、`asset_id`、`task_id` | 接口实际返回的原始 ID，不提前编码；`paper_id` 保留来源前缀 |
| `author_id_encoded`、`institution_id_encoded`、`venue_id_encoded` | 对对应原始 ID 使用 `quote(raw_id, safe=":")`；需 `from urllib.parse import quote`，见第 6.3 节 |
| `*_body` | 所选 POST 接口自己的请求数据，按上游契约填写或从 JSON 文件读取；不同接口分别准备 |
| `pdf_path` | 实际存在的本地 PDF 路径 |
| `pdf_fields` | 上传接口需要的附加表单字段字典，不需要时设为 `None` |
| `mineru_key` | 上游要求时显式提供；可使用 `os.environ.get("LINXSCI_MINERU_API_KEY")` 读取，不需要时设为 `None` |

| HTTP 方法与完整路径 | SDK 调用 |
| --- | --- |
| `GET /openapi/v2/meta` | `client.request("GET", "/meta")` |
| `GET /openapi/v2/usage` | `client.request("GET", "/usage")` |
| `GET /openapi/v2/health/live` | `client.request("GET", "/health/live")` |
| `GET /openapi/v2/health/ready` | `client.request("GET", "/health/ready")` |
| `POST /openapi/v2/papers/search` | `client.search("graph neural networks")` |
| `POST /openapi/v2/search/openalex` | `client.request("POST", "/search/openalex", payload=openalex_body)` |
| `POST /openapi/v2/search/semantic-scholar` | `client.request("POST", "/search/semantic-scholar", payload=semantic_scholar_body)` |
| `POST /openapi/v2/search/google-scholar` | `client.request("POST", "/search/google-scholar", payload=google_scholar_body)` |
| `POST /openapi/v2/papers/resolve` | `client.request("POST", "/papers/resolve", payload=papers_resolve_body)` |
| `POST /openapi/v2/papers:batchGet` | `client.request("POST", "/papers:batchGet", payload=papers_batch_get_body)` |
| `GET /openapi/v2/papers/{paper_id}` | `client.paper(paper_id)` |
| `GET /openapi/v2/papers/{paper_id}/content` | `client.paper(paper_id, "content")` |
| `GET /openapi/v2/papers/{paper_id}/toc` | `client.paper(paper_id, "toc")` |
| `GET /openapi/v2/papers/{paper_id}/sections/{section_id}` | `client.paper(paper_id, "sections", item_id=section_id)` |
| `GET /openapi/v2/papers/{paper_id}/figures` | `client.paper(paper_id, "figures")` |
| `GET /openapi/v2/papers/{paper_id}/assets/{asset_id}` | `client.paper(paper_id, "assets", item_id=asset_id)` |
| `GET /openapi/v2/papers/{paper_id}/references` | `client.paper(paper_id, "references")` |
| `GET /openapi/v2/papers/{paper_id}/citations` | `client.paper(paper_id, "citations")` |
| `GET /openapi/v2/papers/{paper_id}/related` | `client.paper(paper_id, "related")` |
| `GET /openapi/v2/papers/{paper_id}/graph` | `client.paper(paper_id, "graph")` |
| `GET /openapi/v2/papers/{paper_id}/citation` | `client.paper(paper_id, "citation")` |
| `POST /openapi/v2/recommendations` | `client.request("POST", "/recommendations", payload=recommendations_body)` |
| `GET /openapi/v2/recommendations/mobile-cards` | `client.request("GET", "/recommendations/mobile-cards")` |
| `GET /openapi/v2/authors/{author_id}` | `client.request("GET", f"/authors/{author_id_encoded}")` |
| `GET /openapi/v2/authors/{author_id}/papers` | `client.request("GET", f"/authors/{author_id_encoded}/papers")` |
| `GET /openapi/v2/institutions/{institution_id}` | `client.request("GET", f"/institutions/{institution_id_encoded}")` |
| `GET /openapi/v2/institutions/{institution_id}/papers` | `client.request("GET", f"/institutions/{institution_id_encoded}/papers")` |
| `GET /openapi/v2/venues/{venue_id}` | `client.request("GET", f"/venues/{venue_id_encoded}")` |
| `GET /openapi/v2/venues/{venue_id}/papers` | `client.request("GET", f"/venues/{venue_id_encoded}/papers")` |
| `POST /openapi/v2/entities:resolve` | `client.request("POST", "/entities:resolve", payload=entities_resolve_body)` |
| `POST /openapi/v2/pdf/parse` | `client.request("POST", "/pdf/parse", payload=pdf_parse_body, mineru_key=mineru_key)` |
| `POST /openapi/v2/pdf/parse/upload` | `client.upload_pdf(pdf_path, fields=pdf_fields, mineru_key=mineru_key)` |
| `GET /openapi/v2/pdf/parse/{task_id}` | `client.pdf_task(task_id)` |
| `GET /openapi/v2/pdf/parse/{task_id}/result` | `client.pdf_task(task_id, result=True)` |

PDF 的 `pdf_task()` 便捷方法不接收 `mineru_key`。若任务查询或结果接口需要该头，改用 `client.request("GET", path, mineru_key=mineru_key)`，其中 `path` 为带已编码任务 ID 的对应 PDF 路径。二进制响应使用 `response.body`，其他响应按实际类型决定是否调用 `response.json()`；不要假定所有接口使用统一的列表或任务状态字段。

## 7. 处理响应和错误

### 7.1 成功响应

SDK 返回 `Response`，保留服务原始响应：

| 成员 | 含义 |
| --- | --- |
| `response.status` | HTTP 状态码 |
| `response.headers` | 响应头字典，例如 Content-Type、Retry-After、请求 ID |
| `response.body` | 原始响应字节，适用于文件和二进制资源 |
| `response.json()` | 将响应体解析为 Python 对象，响应不是有效 JSON 时会抛出异常 |

响应头名称可能采用不同大小写。需要按名称查找时，先将字典键统一为小写再读取。

### 7.2 异常类型

| 异常 | 含义 | 处理方式 |
| --- | --- | --- |
| `LinxSciError` | HTTP 错误或网络/传输错误 | 结合状态、错误码和请求 ID 排查 |
| `ValueError` | 配置、ID、路径、参数或 JSON 解析问题 | 检查当前配置、输入和响应类型 |
| `OSError` | 本地文件访问等问题 | 检查文件是否存在及读写权限 |

`LinxSciError` 的公共诊断属性如下。调用失败时保留这些信息，不要直接输出包含敏感业务信息的完整错误体：

| 属性 | 含义 |
| --- | --- |
| `status` | HTTP 状态；网络错误时通常为 `None` |
| `error_code` | 服务返回的数字或字符串错误码，缺失时为 `None` |
| `request_id` | 上游/代理 `X-Request-ID`；也可来自上游错误体的 `error.request_id` |
| `framework_request_id` | LinxSci 框架错误体中的 `extra.request-id` |
| `execution_uncertain` | `error_code == -3905` 时为 `True` |
| `body` / `headers` | 保留的原始错误体和响应头，供应用按需诊断 |

### 7.3 LinxSci 错误码和重试

| HTTP | 错误码 | 原因与下一步 |
| --- | --- | --- |
| 401 | `-401` | Key 无效或无法识别用户，检查 Key 和配置覆盖 |
| 404 | `-404` | 路径/方法未匹配，核对接口路径 |
| 503 | `-3900` | 接口尚未启用，请联系管理员 |
| 429 | `-3901` | 每日调用限额已满，额度恢复后再试或联系管理员 |
| 503 | `-3902` | 上游地址或服务端 Key 未配置，联系管理员 |
| 502 | `-3903` | 上游连接或传输失败，检查服务与网络；不据此保证业务没有执行 |
| 502 | `-3904` | 请求准备失败，未转发上游，联系管理员排查 |
| 502 | `-3905` | 上游已返回，但计量完成尚未确认，先核查执行与计费结果，再决定是否重试 |

上游业务错误仍使用自己的格式，例如 `validation_error`、`asset_unavailable`。SDK 保留其原始响应，不将所有错误强行转换为同一种业务结构。

LinxSci 自身框架错误采用 `code/data/error/extra` 结构，其中 `extra.cost` 是耗时（秒），不是扣费金额。包括连接检查和健康检查在内的请求都会经过调用检查；预计调用量为 1，上游 2xx 实际调用量为 1，其余状态或连接失败实际为 0，预占释放由 服务确认计量完成后确定。不能仅凭失败 HTTP 状态保证费用已释放。

SDK 不会自动重试。`Retry-After` 可供应用参考，但遇到 `-3905` 时，仍要先核查执行和计费结果，尤其不要直接重复上传 PDF 或创建解析任务。

### 7.4 指定请求追踪 ID

```python
import uuid
from linxsci import LinxSciClient

client = LinxSciClient()
response = client.request(
    "GET",
    "/meta",
    request_id=str(uuid.uuid4()),
    framework_request_id=str(uuid.uuid4()),
)
print("HTTP 状态：", response.status)
```

`request_id` 对应 `X-Request-ID`，用于上游/代理追踪；`framework_request_id` 对应 `X-ANYTHINGRIGHT-REQ-ID`，用于指定 LinxSci 框架的 `extra.request-id`。SDK 未指定 `request_id` 时会自动生成；框架 ID 也可以通过构造参数 `LinxSciClient(framework_request_id=...)` 设置，再按单次请求覆盖。

## 8. 验证安装、更新与卸载

下载新版 wheel，在应用实际使用的 Python 环境中安装，将 `<version>` 替换为实际版本号：

```bash
python -m pip install --upgrade ./linxsci-<version>-py3-none-any.whl
python -c "from importlib.metadata import version; print(version('linxsci'))"
python -c "from linxsci import LinxSciClient; print('SDK import OK')"
```

后两条命令仅验证本地版本和导入，不调用远程 API。源码安装更新源码后运行 `python -m pip install --upgrade .`。更新后重启长期运行的 Python 进程。

卸载使用同一个解释器环境：

```bash
python -m pip uninstall linxsci
```

卸载包不会删除环境变量、已有配置文件，也不会撤销服务端 Key；这些内容由应用环境和 Key 管理设置分别管理。接口方法与错误码见 [API 参考](API.zh-CN.md)。

## 9. 常见问题

| 问题 | 检查和处理 |
| --- | --- |
| 可编辑安装提示缺少 setup.py/setup.cfg | 在当前 `.venv` 内升级 pip、setuptools、wheel，再执行 `python -m pip install -e .` |
| `No module named linxsci` | 检查编辑器/终端解释器是否属于安装本项目的 `.venv` |
| `No module named python3` | `-m` 后应为模块名；使用 `python -m pip ...` |
| Key 已更新但仍然鉴权失败 | 检查当前 Python 进程的环境变量与显式 `api_key` 参数；不要打印 Key |
| 地址改了却连接到原环境 | 查看 `client.base_url`，按显式参数、环境变量、本地配置的顺序检查覆盖 |
| 本地配置文件无效 | 同时显式传入服务地址与 Key，或修复所选 JSON 配置文件 |
| 连接检查成功但搜索提示 `-3900` | 对应搜索接口尚未启用，请联系管理员 |
| `.json()` 解析失败 | 核对地址和 Content-Type；若为文件或二进制响应，读取 `body` |
| POST 返回参数校验错误 | 按部署版本的实际业务契约填写 JSON，不把空对象当作通用模板 |
