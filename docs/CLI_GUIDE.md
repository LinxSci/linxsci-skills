# Scholar 全接口 CLI 使用指南

本文逐一列出当前 [Scholar OpenAPI v2 接口文档](../Scholar-OpenAPI-v2-使用文档.md) 中的 **34 个接口**及其 CLI 调用命令。先完成安装和配置，再选择需要的接口执行。

接口按以下类别排列：

| 分类 | 接口编号 | 数量 |
| --- | --- | --- |
| [服务信息与健康检查](#服务信息与健康检查) | 01–04 | 4 |
| [论文搜索与解析](#论文搜索与解析) | 05–10 | 6 |
| [论文详情与引用](#论文详情与引用) | 11–21 | 11 |
| [论文推荐](#论文推荐) | 22–23 | 2 |
| [作者、机构与期刊](#作者机构与期刊) | 24–30 | 7 |
| [PDF 解析](#pdf-解析) | 31–34 | 4 |

## 安装和配置

### 从项目源码安装 CLI

在项目根目录执行；已有虚拟环境时只需激活并安装。

**macOS / Linux：**

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -e .
linxsci --version
linxsci scholar --help
```

**Windows CMD：**

```bat
py -3 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
linxsci --version
linxsci scholar --help
```

后续调用均在安装了本项目的同一个虚拟环境中执行。

如果拿到的是 wheel，在自己的虚拟环境中安装它：

```bash
python -m pip install /实际路径/linxsci_scholar_sdk-0.3.0-py3-none-any.whl
```

当前尚未上传 PyPI，不能假定 `pip install linxsci` 可以安装本项目。命令名为 `linxsci`，Python 包名为 `linxsci-scholar-sdk`。

### 配置服务地址和 Key

```bash
linxsci scholar setup --base-url http://101.126.93.213:28888
```

按提示输入自己的 Scholar API Key，输入不会显示。地址只填服务根地址，不附加 `/openapi/v2`；所有接口，包括健康检查，都自动携带 `Authorization: Bearer ...`。`setup` 默认执行一次连接检查，成功后即可调用其他接口。

已有配置时无需再次输入 Key。检查实际配置状态可运行 `linxsci scholar config`，不会显示 Key；`SCHOLAR_BASE_URL` 和 `SCHOLAR_OPENAPI_KEY` 环境变量优先于保存的配置。保存位置及配置优先级见 [开发者指南](DEVELOPMENT.md#2-配置服务地址和-api-key)。

### 只使用 ZIP 时

ZIP 安装器不注册 `linxsci` 命令。在解压目录中，把下文所有命令开头的 `linxsci scholar` 替换为：

```bash
python3 skills/linxsci-scholar/scripts/cli.py scholar
```

例如：

```bash
python3 skills/linxsci-scholar/scripts/cli.py scholar request GET /usage
```

Windows 使用 `py -3` 替换 `python3`。完整安装流程见 [普通用户指南](USER_GUIDE.md)。

## 调用前的参数准备

### 通用语法

```text
linxsci scholar [组选项] request GET  <接口路径> [--param 字段=值]
linxsci scholar [组选项] request POST <接口路径> --body @请求文件.json
linxsci scholar [组选项] upload <本地PDF路径> [--field 字段=值]
```

下文通用命令中的路径均省略 `/openapi/v2`，CLI 会自动添加。尖括号内容均为占位参数，须替换为真实值后执行，不要保留尖括号。

### 动态 ID 与 URL 编码

| 占位参数 | 替换值来源 |
| --- | --- |
| `<paper-id-encoded>` | 搜索、解析或其他响应返回的论文 ID，按单个路径段编码 |
| `<section-id-encoded>` | 论文目录返回的真实章节 ID，按单个路径段编码 |
| `<asset-id-encoded>` | 接口响应返回的真实资源 ID，按单个路径段编码 |
| `<author-id-encoded>` | 接口响应或部署契约提供的作者 ID，按单个路径段编码 |
| `<institution-id-encoded>` | 接口响应或部署契约提供的机构 ID，按单个路径段编码 |
| `<venue-id-encoded>` | 接口响应或部署契约提供的期刊/会议 ID，按单个路径段编码 |
| `<task-id-encoded>` | PDF 创建/上传响应中的真实任务 ID，按单个路径段编码 |

`paper_id` 保留 `local:`、`arxiv:`、`openalex:`、`s2:` 或 `doi:` 来源前缀。通用 `request` 接收已编码路径，只编码各个 ID，不要编码整个接口路径，也不要对已编码 ID 再编码。

可用以下命令编码单个原始 ID；运行后粘贴 ID 并按回车：

```bash
python3 -c "from urllib.parse import quote; print(quote(input('原始 ID: '), safe=':'))"
```

仅作编码演示：`doi:10.1000/example` 会变为 `doi:10.1000%2Fexample`，该示例不代表真实可用论文。`paper` 便捷命令接收原始 ID 并自动编码：

```bash
linxsci scholar paper "实际论文ID"
linxsci scholar paper "实际论文ID" --resource sections --item-id "实际章节ID"
```

### JSON 请求文件

`--body @文件名.json` 从当前工作目录读取请求文件；也可以使用绝对路径，例如 `--body "@/实际路径/request.json"`。文件使用 UTF-8 编码。

当前项目的综合论文搜索支持以下最小请求，保存为 `papers-search.json`：

```json
{
  "query": "graph neural networks"
}
```

其他 POST 接口的具体业务字段未在当前代理接口文档中展开，需要依照实际部署的 Agent API 契约准备下列文件。文件名由本文约定，方便区分不同接口；CLI 不会自动生成这些文件。

| 请求文件 | 用于接口 | 内容要求 |
| --- | --- | --- |
| `papers-search.json` | 综合论文搜索 | 可使用上方 `query` 示例，其他选项按上游契约添加 |
| `openalex-search.json` | OpenAlex 搜索 | 按 OpenAlex 搜索接口的上游请求模型填写 |
| `semantic-scholar-search.json` | Semantic Scholar 搜索 | 按对应上游请求模型填写 |
| `google-scholar-search.json` | Google Scholar 搜索 | 按对应上游请求模型填写 |
| `papers-resolve.json` | 论文标识解析 | 按对应上游请求模型填写 |
| `papers-batch-get.json` | 批量获取论文 | 按对应上游请求模型填写 |
| `recommendations.json` | 论文推荐 | 按对应上游请求模型填写 |
| `entities-resolve.json` | 实体标识解析 | 按对应上游请求模型填写 |
| `pdf-parse.json` | JSON 创建 PDF 解析任务 | 按对应上游请求模型填写 |

不要把 `{}` 或检索响应当成通用有效请求，也不要推断不存在的 `ids`、`limit`、`page` 等字段。认证由 CLI 读取本机配置，无需在业务 JSON 中写入 Scholar API Key。

## 服务信息与健康检查

### 01. 接口元信息

**接口：** `GET /openapi/v2/meta`

```bash
linxsci scholar request GET /meta
```

便捷命令为 `linxsci scholar meta`。返回内容以服务实际响应为准，不保证包含完整请求 schema。

### 02. 用量信息

**接口：** `GET /openapi/v2/usage`

```bash
linxsci scholar request GET /usage
```

便捷命令为 `linxsci scholar usage`。

### 03. 存活检查

**接口：** `GET /openapi/v2/health/live`

```bash
linxsci scholar request GET /health/live
```

便捷命令为 `linxsci scholar health live`。

### 04. 就绪检查

**接口：** `GET /openapi/v2/health/ready`

```bash
linxsci scholar request GET /health/ready
```

便捷命令为 `linxsci scholar health ready`。

## 论文搜索与解析

### 05. 综合论文搜索

**接口：** `POST /openapi/v2/papers/search`

先按上文准备 `papers-search.json`：

```bash
linxsci scholar request POST /papers/search --body @papers-search.json
```

只传检索词时也可以运行 `linxsci scholar search "graph neural networks"`。从响应中选择真实论文 ID，用于后续详情和阅读接口。

### 06. OpenAlex 搜索

**接口：** `POST /openapi/v2/search/openalex`

```bash
linxsci scholar request POST /search/openalex --body @openalex-search.json
```

### 07. Semantic Scholar 搜索

**接口：** `POST /openapi/v2/search/semantic-scholar`

```bash
linxsci scholar request POST /search/semantic-scholar --body @semantic-scholar-search.json
```

### 08. Google Scholar 搜索

**接口：** `POST /openapi/v2/search/google-scholar`

```bash
linxsci scholar request POST /search/google-scholar --body @google-scholar-search.json
```

### 09. 论文标识解析

**接口：** `POST /openapi/v2/papers/resolve`

```bash
linxsci scholar request POST /papers/resolve --body @papers-resolve.json
```

### 10. 批量获取论文

**接口：** `POST /openapi/v2/papers:batchGet`

```bash
linxsci scholar request POST /papers:batchGet --body @papers-batch-get.json
```

路径中的冒号和 `batchGet` 大小写须保持原样。

## 论文详情与引用

以下命令使用真实且已编码的论文 ID；章节和资源 ID 分别从目录或资源响应中取得。

### 11. 论文详情

**接口：** `GET /openapi/v2/papers/{paper_id}`

```bash
linxsci scholar request GET "/papers/<paper-id-encoded>"
```

### 12. 论文内容

**接口：** `GET /openapi/v2/papers/{paper_id}/content`

```bash
linxsci scholar request GET "/papers/<paper-id-encoded>/content"
```

### 13. 论文目录

**接口：** `GET /openapi/v2/papers/{paper_id}/toc`

```bash
linxsci scholar request GET "/papers/<paper-id-encoded>/toc"
```

### 14. 论文章节

**接口：** `GET /openapi/v2/papers/{paper_id}/sections/{section_id}`

```bash
linxsci scholar request GET "/papers/<paper-id-encoded>/sections/<section-id-encoded>"
```

### 15. 论文图表

**接口：** `GET /openapi/v2/papers/{paper_id}/figures`

```bash
linxsci scholar request GET "/papers/<paper-id-encoded>/figures"
```

### 16. 论文资源

**接口：** `GET /openapi/v2/papers/{paper_id}/assets/{asset_id}`

```bash
linxsci scholar --output asset.bin request GET "/papers/<paper-id-encoded>/assets/<asset-id-encoded>"
```

响应原始字节保存到当前目录的 `asset.bin`。实际文件格式取决于返回资源，可按真实格式选择文件名和扩展名。

### 17. 参考文献

**接口：** `GET /openapi/v2/papers/{paper_id}/references`

```bash
linxsci scholar request GET "/papers/<paper-id-encoded>/references"
```

### 18. 被引论文

**接口：** `GET /openapi/v2/papers/{paper_id}/citations`

```bash
linxsci scholar request GET "/papers/<paper-id-encoded>/citations"
```

### 19. 相关论文

**接口：** `GET /openapi/v2/papers/{paper_id}/related`

```bash
linxsci scholar request GET "/papers/<paper-id-encoded>/related"
```

### 20. 引用图谱

**接口：** `GET /openapi/v2/papers/{paper_id}/graph`

```bash
linxsci scholar request GET "/papers/<paper-id-encoded>/graph"
```

### 21. 论文引用格式

**接口：** `GET /openapi/v2/papers/{paper_id}/citation`

```bash
linxsci scholar request GET "/papers/<paper-id-encoded>/citation"
```

若需要指定格式等查询条件，按实际契约使用 `--param 字段名=值`，不要猜测参数名称。

## 论文推荐

### 22. 论文推荐

**接口：** `POST /openapi/v2/recommendations`

```bash
linxsci scholar request POST /recommendations --body @recommendations.json
```

### 23. 移动端推荐卡片

**接口：** `GET /openapi/v2/recommendations/mobile-cards`

```bash
linxsci scholar request GET /recommendations/mobile-cards
```

## 作者、机构与期刊

### 24. 作者详情

**接口：** `GET /openapi/v2/authors/{author_id}`

```bash
linxsci scholar request GET "/authors/<author-id-encoded>"
```

### 25. 作者论文

**接口：** `GET /openapi/v2/authors/{author_id}/papers`

```bash
linxsci scholar request GET "/authors/<author-id-encoded>/papers"
```

### 26. 机构详情

**接口：** `GET /openapi/v2/institutions/{institution_id}`

```bash
linxsci scholar request GET "/institutions/<institution-id-encoded>"
```

### 27. 机构论文

**接口：** `GET /openapi/v2/institutions/{institution_id}/papers`

```bash
linxsci scholar request GET "/institutions/<institution-id-encoded>/papers"
```

### 28. 期刊或会议详情

**接口：** `GET /openapi/v2/venues/{venue_id}`

```bash
linxsci scholar request GET "/venues/<venue-id-encoded>"
```

### 29. 期刊或会议论文

**接口：** `GET /openapi/v2/venues/{venue_id}/papers`

```bash
linxsci scholar request GET "/venues/<venue-id-encoded>/papers"
```

### 30. 实体标识解析

**接口：** `POST /openapi/v2/entities:resolve`

```bash
linxsci scholar request POST /entities:resolve --body @entities-resolve.json
```

## PDF 解析

### 31. 创建 PDF 解析任务

**接口：** `POST /openapi/v2/pdf/parse`

先按实际契约准备 `pdf-parse.json`：

```bash
linxsci scholar request POST /pdf/parse --body @pdf-parse.json
```

记录响应中的真实任务 ID。不要自行假定 JSON 中的 PDF 地址字段或任务 ID 的响应字段名。

### 32. 上传 PDF 并创建解析任务

**接口：** `POST /openapi/v2/pdf/parse/upload`

```bash
linxsci scholar upload "/实际路径/paper.pdf"
```

这是文件上传接口，使用 `upload` 而不是 JSON `request POST`。CLI 自动构造 `multipart/form-data` 的 `file` 字段，无需手动填写 Content-Type。其他表单字段仅在上游要求时添加，例如：

```bash
linxsci scholar upload "/实际路径/paper.pdf" --field "实际字段名=实际字段值"
```

每个字段名只能出现一次。文件大小限制以服务配置为准；调用会上传文件并创建任务，避免对同一个文件无意重复提交。

### 33. 查询 PDF 解析任务

**接口：** `GET /openapi/v2/pdf/parse/{task_id}`

```bash
linxsci scholar request GET "/pdf/parse/<task-id-encoded>"
```

便捷命令为 `linxsci scholar task "实际任务ID"`，由 CLI 编码原始 ID。任务状态以实际响应为准，不假定状态字段名和终态值。

### 34. 获取 PDF 解析结果

**接口：** `GET /openapi/v2/pdf/parse/{task_id}/result`

确认任务完成后执行：

```bash
linxsci scholar request GET "/pdf/parse/<task-id-encoded>/result"
```

便捷命令为 `linxsci scholar task "实际任务ID" --result`。如果接口返回文件，使用 `linxsci scholar --output result.bin request GET "/pdf/parse/<task-id-encoded>/result"` 保存原始数据。

PDF 接口按需使用 `X-MinerU-API-Key`。在运行 CLI 的本机环境中设置 `SCHOLAR_MINERU_API_KEY` 后，`upload` 和通用 PDF `request` 会自动附带该头；`task` 便捷命令不会附带，需要时使用上文通用命令。无需向 CLI 提供服务端 `AGENT_PUBLIC_API_KEY`。

## 通用选项与输出

### 查询参数

`request` 和 `paper` 通过 `--param 字段名=值` 传递查询参数，同名参数可以重复。字段名和值以实际接口契约为准；CLI 自动编码查询参数，无需预先 URL 编码：

```bash
linxsci scholar request GET "/authors/<author-id-encoded>/papers" --param "实际字段名=实际值"
```

当前文档未定义通用分页模型，不能假定所有列表接口都使用相同的分页字段。

### 保存响应、超时和请求追踪

`--output`、`--timeout`、`--json-errors` 和 `--framework-request-id` 是 Scholar 组选项，放在 `scholar` 之后、具体动作之前：

```bash
linxsci scholar --output search-result.json request POST /papers/search --body @papers-search.json
linxsci scholar --timeout 90 request GET /meta
linxsci scholar --framework-request-id scholar-trace-001 request GET /meta --request-id upstream-trace-001
linxsci scholar --json-errors request GET /usage
```

`--timeout` 单位为秒，默认 60；`--output` 保存响应原始字节，并覆盖同名文件，父目录须已存在。未指定输出文件时，JSON 格式化输出到终端，其他内容原样输出。请求文件与响应文件请使用不同文件名。

`--request-id` 是 `request` 动作的参数，对应 `X-Request-ID`；不传时自动生成。`--framework-request-id` 对应 Scholar 框架的 `X-ANYTHINGRIGHT-REQ-ID`。CLI 不提供任意请求头参数，认证头自动添加。

### 错误与退出码

| 退出码 | 含义 |
| --- | --- |
| `0` | CLI 调用成功 |
| `1` | HTTP、网络或连接检查失败 |
| `2` | 配置、参数、请求文件或本地文件错误 |

错误输出到 stderr，可用 `--json-errors` 获取结构化诊断。`-3900` 表示接口尚未启用，需管理员处理；`-3905` 表示上游已返回但执行与计费确认未完成，先核查结果再决定是否重试，尤其不要直接重复上传或创建任务。其他错误码见 [接口文档](../Scholar-OpenAPI-v2-使用文档.md#响应与错误)。

本指南的命令已核对当前 CLI 的参数和路由。接口调用会经过服务端权限、用量及业务参数校验；全部路径可调用不代表所有接口已在你的部署中启用。

### 查看完整路由和帮助

```bash
linxsci scholar routes
linxsci scholar request --help
linxsci scholar upload --help
```

以上三条命令不调用远程服务。Python SDK 的安装、配置、方法签名及全接口对照见 [SDK 开发者指南](DEVELOPMENT.md)，测试和联调见 [测试指南](TESTING.md)。
