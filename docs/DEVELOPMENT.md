# 开发者指南

本文面向在 Python 程序中调用 Scholar 的开发者，按当前项目的安装方式、SDK 入口和接口行为编写。首次使用按第 1 节、第 2.1 节和第 3 节操作，即可完成一次论文检索；其他章节按需阅读。

SDK 的公共入口为 `linxsci_scholar`，命令行入口为 `linxsci`，论文相关动作放在 `scholar` 命令组。SDK 将 Python 方法转换为 Scholar API 请求，自动附带用户的 Scholar API Key。只使用 SDK 时，完成 Python 包安装和 Key 配置即可。

## 目录

1. [安装项目](#1-安装项目)
2. [配置服务地址和 API Key](#2-配置服务地址和-api-key)
3. [完成第一次 SDK 检索](#3-完成第一次-sdk-检索)
4. [使用 SDK 阅读论文](#4-使用-sdk-阅读论文)
5. [使用 SDK 解析 PDF](#5-使用-sdk-解析-pdf)
6. [调用其他接口](#6-调用其他接口)
7. [处理响应和错误](#7-处理响应和错误)
8. [使用 CLI](#8-使用-cli)
9. [本地开发与验证](#9-本地开发与验证)
10. [常见问题](#10-常见问题)

## 1. 安装项目

### 1.1 获取源码

需要 Python 3.9 或以上版本，以及仓库访问权限。如果已经有源码，直接进入项目根目录；尚未拉取时执行：

```bash
git clone git@codeup.aliyun.com:67ce5fc9e77e9167fa2fc4ca/AI/linxsci-openapi-skills.git
cd linxsci-openapi-skills
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

已有 `.venv` 时跳过创建，激活后继续。`-e .` 将当前源码安装为可编辑包，适合本地开发；修改源码后，SDK 和 CLI 使用修改后的实现。运行时依赖 Python 标准库，安装时需要获取构建工具。

### 1.3 确认安装成功

```bash
python -c "from linxsci_scholar import ScholarClient; print('SDK import OK')"
linxsci --version
```

第一条命令应输出 `SDK import OK`，第二条输出当前项目版本。两条命令均不调用远程 API。后续 Python 程序也应使用此 `.venv` 的解释器。

## 2. 配置服务地址和 API Key

### 2.1 首次使用：通过配置向导保存

```bash
linxsci scholar setup --base-url http://101.126.93.213:28888
```

1. 确认服务地址；默认提示为当前测试服务地址。
2. 输入已有的 Scholar API Key，输入内容不会显示。
3. 向导保存配置，并调用 `/meta` 检查连接。
4. 看到“连接成功”后，进入下一节运行 SDK 示例。

地址只填写服务根地址，末尾不添加 `/openapi/v2`，SDK 会自动补齐该前缀。需要切换到线上服务时，运行 `linxsci scholar setup --online`，地址提示为 `https://linxsci.com`。

配置成功后，Python 中直接使用 `ScholarClient()`，SDK 会读取已保存的地址和 Key。配置向导属于配套 CLI，SDK 开发者可以用它完成本机配置；不需要额外安装 Skill。

| 系统 | 默认配置文件 |
| --- | --- |
| macOS / Linux | `~/.config/linxsci-scholar/config.json` |
| Windows | `%LOCALAPPDATA%\linxsci-scholar\config.json` |

Key 保存在用户配置文件中，macOS/Linux 文件权限为 `600`。不要将配置文件或真实 Key 提交到仓库。

### 2.2 按需：环境变量和显式参数

SDK 按以下顺序解析地址和 Key：

**显式构造参数 → 进程环境变量 → 本地配置文件 → 发行包内的默认地址。**

地址有发行默认值，Key 必须由调用方提供。如果通过部署系统设置了下列变量，可以直接使用 `ScholarClient()`：

| 环境变量 | 作用 |
| --- | --- |
| `SCHOLAR_BASE_URL` | 覆盖服务根地址 |
| `SCHOLAR_OPENAPI_KEY` | 覆盖 Scholar API Key |
| `SCHOLAR_CONFIG_FILE` | 指定本地配置文件路径，用于隔离不同环境 |
| `SCHOLAR_MINERU_API_KEY` | 可选的 PDF 解析 Key，SDK 需读取后显式传入，见第 5 节 |

项目不会自动加载 `.env`。仅将值写入 `.env` 或复制 `.env.example` 不会使其进入进程环境。

程序也可显式配置客户端。以下代码要求进程已设置 `SCHOLAR_OPENAPI_KEY`：

```python
import os
from linxsci_scholar import ScholarClient

client = ScholarClient(
    base_url="http://101.126.93.213:28888",
    api_key=os.environ["SCHOLAR_OPENAPI_KEY"],
    timeout=60,
)
```

客户端只使用用户的 Scholar API Key。服务端转发 Agent API 所需的密钥由服务管理员配置。

### 2.3 按需：查看状态、复查连接和清除配置

```bash
# 只查看本地配置状态，不显示 Key，不调用远程接口
linxsci scholar config

# 按需检查实际使用的地址和连接状态
linxsci scholar doctor --json

# 需要移除保存的地址和 Key 时执行
linxsci scholar config --clear
```

`doctor` 输出中的 `base_url` 是实际连接地址，`ok: true` 表示本次 `/meta` 检查成功。`setup` 已检查成功时，无需紧接着重复运行 `doctor`。二者的连接检查都计入接口调用流程；某个接口检查通过，也不代表其他接口 action 已启用。

环境变量优先于保存的配置。若切换地址后仍连接到原服务，先用 `config` 检查环境变量覆盖状态。清除本地配置不会清除环境变量，也不会撤销服务端 Key。

## 3. 完成第一次 SDK 检索

### 3.1 运行仓库自带示例

安装并配置成功后，执行：

```bash
python examples/research.py
```

该脚本检索 `graph neural networks`，输出 HTTP 状态和实际 JSON 响应。发生错误时输出错误码和请求 ID，退出并保留诊断信息，不自动重试。

### 3.2 在自己的程序中调用

以下代码可保存为项目根目录下的 `test_sdk.py`，然后用 `python test_sdk.py` 运行：

```python
import json
from linxsci_scholar import ScholarClient, ScholarError

try:
    client = ScholarClient(timeout=60)
    response = client.search("graph neural networks")
    print("HTTP 状态：", response.status)
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))
except ScholarError as error:
    print("HTTP 状态：", error.status)
    print("错误码：", error.error_code)
    print("上游/代理请求 ID：", error.request_id)
    print("Scholar 框架请求 ID：", error.framework_request_id)
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
from linxsci_scholar import ScholarClient

client = ScholarClient()
paper_id = input("请输入搜索返回的论文 ID（保留来源前缀）：").strip()

print("论文详情：", client.paper(paper_id).json())
print("论文目录：", client.paper(paper_id, "toc").json())
```

论文 ID 需要 `local:`、`arxiv:`、`openalex:`、`s2:` 或 `doi:` 来源前缀。例如 DOI 标识采用 `doi:10.xxxx/xxxx` 形式。`paper()` 接收原始 ID 并负责路径编码，不要提前把其中的 `/` 替换成 `%2F`。

### 4.2 读取指定章节

先查看目录，再复制目录中返回的实际章节 ID：

```python
from linxsci_scholar import ScholarClient

client = ScholarClient()
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
from linxsci_scholar import ScholarClient

client = ScholarClient()
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
from linxsci_scholar import ScholarClient

client = ScholarClient()
pdf_path = input("请输入本地 PDF 文件路径：").strip()

response = client.upload_pdf(
    pdf_path,
    mineru_key=os.environ.get("SCHOLAR_MINERU_API_KEY"),
)
print(response.json())
```

`mineru_key` 仅在部署契约要求时提供，未设置环境变量时为 `None`。SDK 不会自动读取该变量；上面的代码显式读取后传入。附加表单字段通过 `fields={字段名: 值}` 传入，字段和文件大小限制以部署契约为准。当前客户端在内存中构建上传内容。

### 5.2 使用返回的任务 ID 查询状态

```python
from linxsci_scholar import ScholarClient

client = ScholarClient()
task_id = input("创建任务响应中的实际任务 ID：").strip()

print(client.pdf_task(task_id).json())
```

根据实际响应判断是否完成，当前文档没有定义统一的状态字段或终态枚举。未完成时稍后再查，不要再次上传同一文件来代替状态查询。

### 5.3 确认完成后获取结果

```python
from linxsci_scholar import ScholarClient

client = ScholarClient()
task_id = input("已完成任务的实际任务 ID：").strip()

print(client.pdf_task(task_id, result=True).json())
```

如果查询状态或结果时也需要 `X-MinerU-API-Key`，使用第 6 节的 `request()`，向对应 PDF 路径传入 `mineru_key`。状态和结果接口的返回类型以部署契约为准；若返回文件内容，读取 `body`。

## 6. 调用其他接口

便捷方法之外的接口统一使用 `request()`，可调用当前项目支持的全部 34 条路由。方法和路径见 [接口文档](../Scholar-OpenAPI-v2-使用文档.md)。

### 6.1 GET 请求

例如查询用量：

```python
from linxsci_scholar import ScholarClient

client = ScholarClient()
response = client.request("GET", "/usage")
print(response.json())
```

路径相对于 `/openapi/v2`，不包含服务域名或此前缀。查询参数通过 `query` 传递；JSON 请求体通过 `payload` 传递。

### 6.2 JSON POST 请求

以下请求与 `client.search()` 调用同一个综合搜索接口：

```python
from linxsci_scholar import ScholarClient

client = ScholarClient()
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
from linxsci_scholar import ScholarClient

client = ScholarClient()
author_id = input("接口返回的作者 ID：").strip()
path = "/authors/" + quote(author_id, safe=":") + "/papers"

print(client.request("GET", path).json())
```

GET 查询参数可使用 `query={字段名: 值}`；多个同名值可使用列表。PDF 路径可通过 `mineru_key` 显式附加 `X-MinerU-API-Key`。SDK 不接受在非 PDF 路径上发送该头。

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
| `ScholarError` | HTTP 错误或网络/传输错误 | 结合状态、错误码和请求 ID 排查 |
| `ValueError` | 配置、ID、路径、参数或 JSON 解析问题 | 检查当前配置、输入和响应类型 |
| `OSError` | 本地文件访问等问题 | 检查文件是否存在及读写权限 |

`ScholarError` 的公共诊断属性如下。调用失败时保留这些信息，不要直接输出包含敏感业务信息的完整错误体：

| 属性 | 含义 |
| --- | --- |
| `status` | HTTP 状态；网络错误时通常为 `None` |
| `error_code` | 服务返回的数字或字符串错误码，缺失时为 `None` |
| `request_id` | 上游/代理 `X-Request-ID`；也可来自上游错误体的 `error.request_id` |
| `framework_request_id` | Scholar 框架错误体中的 `extra.request-id` |
| `execution_uncertain` | `error_code == -3905` 时为 `True` |
| `body` / `headers` | 保留的原始错误体和响应头，供应用按需诊断 |

### 7.3 Scholar 错误码和重试

| HTTP | 错误码 | 原因与下一步 |
| --- | --- | --- |
| 401 | `-401` | Key 无效或无法识别用户，检查 Key 和配置覆盖 |
| 404 | `-404` | 路径/方法未匹配，核对接口路径 |
| 503 | `-3900` | action 已登记但未启用，联系管理员配置并启用 |
| 429 | `-3901` | 每日调用限额已满，额度恢复后再试或联系管理员 |
| 503 | `-3902` | 上游地址或服务端 Key 未配置，联系管理员 |
| 502 | `-3903` | 上游连接或传输失败，检查服务与网络；不据此保证业务没有执行 |
| 502 | `-3904` | member begin 未成功，未转发上游，联系管理员排查 |
| 502 | `-3905` | 上游已返回，但 member finish 未确认，先核查执行与计费结果，再决定是否重试 |

上游业务错误仍使用自己的格式，例如 `validation_error`、`asset_unavailable`。SDK 保留其原始响应，不将所有错误强行转换为同一种业务结构。

Scholar 自身框架错误采用 `code/data/error/extra` 结构，其中 `extra.cost` 是耗时（秒），不是扣费金额。包括连接检查和健康检查在内的请求都会经过调用检查；预计调用量为 1，上游 2xx 实际调用量为 1，其余状态或连接失败实际为 0，预占释放由 member finish 结果确认。不能仅凭失败 HTTP 状态保证费用已释放。

SDK 和 CLI 都不会自动重试。`Retry-After` 可供应用参考，但遇到 `-3905` 时，仍要先核查执行和计费结果，尤其不要直接重复上传 PDF 或创建解析任务。

### 7.4 指定请求追踪 ID

```python
import uuid
from linxsci_scholar import ScholarClient

client = ScholarClient()
response = client.request(
    "GET",
    "/meta",
    request_id=str(uuid.uuid4()),
    framework_request_id=str(uuid.uuid4()),
)
print("HTTP 状态：", response.status)
```

`request_id` 对应 `X-Request-ID`，用于上游/代理追踪；`framework_request_id` 对应 `X-ANYTHINGRIGHT-REQ-ID`，用于指定 Scholar 框架的 `extra.request-id`。SDK 未指定 `request_id` 时会自动生成；框架 ID 也可以通过构造参数 `ScholarClient(framework_request_id=...)` 设置，再按单次请求覆盖。

## 8. 使用 CLI

CLI 与 SDK 共用配置和请求实现。以下是终端调用方式；在 Python 程序里则使用前面的 SDK 方法。

命令格式为 `linxsci scholar [组内选项] <动作> [动作参数]`。`linxsci --help` 列出当前能力，`linxsci scholar --help` 列出论文相关动作。安装包名称仍为 `linxsci-scholar-sdk`，Python 中继续导入 `linxsci_scholar`。

从已有开发版本更新时，在安装本项目的虚拟环境重新执行 `python -m pip install -e .`，再运行 `linxsci --version` 确认入口已注册。已有环境变量和 `~/.config/linxsci-scholar/config.json` 等本地配置继续生效。若还需要在助手中使用更新后的 Skill，执行 `linxsci scholar install-skill --update`。

### 8.1 搜索、阅读和保存内容

```bash
linxsci scholar search "graph neural networks"
linxsci scholar --output search.json search "graph neural networks"
```

从结果中取得 ID 后，替换下列中文占位参数再执行：

```bash
linxsci scholar paper "实际论文ID"
linxsci scholar paper "实际论文ID" --resource toc
linxsci scholar paper "实际论文ID" --resource sections --item-id "实际章节ID"
```

### 8.2 通用调用和诊断

```bash
# 查看全部支持路由，无需 Key，不调用远程服务
linxsci scholar routes

# 查看帮助
linxsci scholar --help

# 查询用量
linxsci scholar request GET /usage

# 发生错误时，将结构化诊断写到 stderr
linxsci scholar --json-errors search "graph neural networks"
```

JSON POST 请求用 `--body @request.json` 从文件读取，或用 `--body` 传入 JSON 文本；请求字段按目标接口契约准备。查询参数用 `--param key=value`，可重复；动态路径与 SDK 的 `request()` 一样需要编码。

### 8.3 PDF 和组选项

以下路径和任务 ID 需要替换为实际值；确认任务完成后才执行结果命令：

```bash
linxsci scholar upload /实际路径/paper.pdf
linxsci scholar task "实际任务ID"
linxsci scholar task "实际任务ID" --result
```

CLI 在 PDF 命令中按其实现读取 `SCHOLAR_MINERU_API_KEY`：`upload` 和通用 PDF `request` 会发送该头，`task` 便捷命令不附加该头；需要时改用通用 `request`。

`--output`、`--timeout`、`--json-errors`、`--framework-request-id` 属于 Scholar 组，放在 `scholar` 之后、具体动作之前。例如：

```bash
linxsci scholar --timeout 90 --framework-request-id scholar-trace-001 request GET /meta --request-id agent-trace-001
```

成功输出为格式化 JSON 或原始数据；`--output` 保存原始响应字节。错误写入 stderr。退出码 `0` 表示成功，`1` 表示 HTTP/网络或连接检查错误，`2` 表示输入、配置或本地文件错误。

## 9. 本地开发与验证

每次打开新的终端，先激活 `.venv`。修改 SDK/CLI 逻辑后运行：

```bash
python -m unittest discover -s tests -v
```

这些测试使用本地模拟 HTTP 服务和临时配置，不需要真实 Key，不访问远程测试环境。真实联调可依次验证：搜索 → 真实论文 ID → 目录 → 真实章节 ID；PDF 按需验证一次创建、查询和结果流程。

只使用 SDK 时无需安装 Skill。需要验证 AI 助手调用效果时，再按 [测试环境验收与 Skill 调优](TESTING.md) 安装或更新 Skill，并核对助手实际使用的源码路径。

交付安装包、上传制品和版本维护见 [发布指南](RELEASING.md)。接口方法、路由和代理约定见 [接口文档](../Scholar-OpenAPI-v2-使用文档.md)。

### 9.1 新增其他 Skill 的命名与入口

统一采用下列结构：

| 内容 | 规则 | 将来新增专利能力的命名示例 |
| --- | --- | --- |
| CLI | `linxsci <能力名> <动作>` | `linxsci patents search` |
| Skill 名称 | `linxsci-<能力名>` | `linxsci-patents` |
| Skill 目录 | `skills/linxsci-<能力名>/` | `skills/linxsci-patents/SKILL.md` |
| Python 模块 | 使用合法的 Python 模块名 | `linxsci_patents` |

当前只实现 Scholar。新的能力实现后，在 `skills/linxsci-scholar/scripts/cli.py` 的 `CAPABILITIES` 中注册处理函数，处理函数接收 `argv` 和 `prog`；将对应实现纳入发行包配置，并补充命令与安装测试。由统一入口分派到各能力，不要让多个发行包分别注册并覆盖同一个 `linxsci` 可执行文件。

新增能力按以下步骤落地：

1. 在独立的 `skills/linxsci-<能力名>/` 中编写 `SKILL.md` 和所需脚本、参考资料，明确任务范围及使用流程。
2. 实现命令处理函数并注册能力名，验证 `linxsci <能力名> --help` 和具体动作。
3. 更新 `pyproject.toml` 的模块和资源配置、`tools/build_release.py` 的 ZIP 白名单，以及 Skill 复制安装逻辑。当前 `linxsci scholar install-skill` 只安装 Scholar，添加命令组不会自动安装新 Skill。
4. 补充测试及 README、用户指南、开发者指南和发布指南，并验证新环境安装的 wheel、ZIP 都包含新能力所需文件。

当前发行包仍叫 `linxsci-scholar-sdk`，ZIP 仍叫 `linxsci-scholar-<版本>.zip`。未来真正发布多能力合集时，再统一决定合集的发行包和 ZIP 名称，并同步调整构建与安装逻辑；新增能力的命名示例不表示当前安装包已包含它。

## 10. 常见问题

| 问题 | 检查和处理 |
| --- | --- |
| 可编辑安装提示缺少 setup.py/setup.cfg | 在当前 `.venv` 内升级 pip、setuptools、wheel，再执行 `python -m pip install -e .` |
| `No module named linxsci_scholar` | 检查编辑器/终端解释器是否属于安装本项目的 `.venv` |
| `No module named python3` | `-m` 后应为模块名；使用 `python -m pip ...` |
| 找不到 `linxsci` 命令 | 激活安装本项目的虚拟环境；更新源码后重新执行 `python -m pip install -e .` 注册入口 |
| Key 已更新但仍然鉴权失败 | 用 `config` 检查进程环境变量是否覆盖本地配置；SDK 显式参数优先级更高 |
| 地址改了却连接到原环境 | 按显式参数、环境变量、本地配置的顺序检查覆盖 |
| 连接检查成功但搜索提示 `-3900` | 不同接口有独立 action，需要管理员启用对应搜索接口 |
| `.json()` 解析失败 | 核对地址和 Content-Type；若为文件或二进制响应，读取 `body` |
| POST 返回参数校验错误 | 按部署版本的实际业务契约填写 JSON，不把空对象当作通用模板 |
