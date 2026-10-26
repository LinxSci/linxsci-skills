# Skill 独立脚本命令与参数

[English](cli.md)

直接使用本 Skill 随附脚本，无需安装 CLI、PyPI 包或 SDK。执行下文命令前，将 `<skill-dir>` 替换为 `SKILL.md` 所在目录的绝对路径；Windows 可将 `python3` 改为 `py -3`。安装方式见 [Skill 安装说明](../SKILL.zh-CN.md#独立安装-skill)。

## 调用格式与参数位置

```text
python3 "<skill-dir>/scripts/cli.py" [全局选项] 命令 [命令参数]
python3 "<skill-dir>/scripts/cli.py" --help
python3 "<skill-dir>/scripts/cli.py" 命令 --help
```

不带参数运行 `python3 "<skill-dir>/scripts/cli.py"` 显示帮助。`--help` 和 `--version` 无需配置、不联网。全局选项必须放在**命令之前**，命令专用参数放在**命令之后**。含空格的值使用引号。相对文件路径以当前工作目录为基准，不以 Skill 目录为基准。执行前将 `<...>` 占位参数替换成实际值。

## 全局选项

| 参数 | 类型 / 默认值 | 说明 |
| --- | --- | --- |
| `-h`、`--help` | 开关 | 查看总帮助；放在命令后查看该命令帮助 |
| `--version` | 开关 | 输出版本号并退出 |
| `--timeout SECONDS` | 数值，默认 `60` | 网络超时秒数，必须为正的有限数；不是 PDF 任务的整体完成时限 |
| `--output PATH` | 文件路径，默认不设置 | 将接口原始响应字节写入文件而不输出到 stdout；覆盖同名文件，父目录需已存在 |
| `--json-errors` | 开关，默认开启 | 将结构化错误写入 stderr，不改变成功响应格式 |
| `--pretty` | 开关，默认关闭 | 将成功 JSON 和本地 JSON 报告缩进排版，方便终端阅读 |
| `--human-errors` | 开关，默认关闭 | 使用面向人的 stderr 错误提示，与 `--json-errors` 互斥 |
| `--select POINTER` | JSON Pointer，默认不设置 | 选择真实响应中的数据位置，如 `/data/items`；空字符串选择根值 |
| `--fields KEYS` | 逗号分隔的字面字段名，默认不设置 | 保留选中对象或数组各对象的指定字段；每个请求字段都必须存在 |
| `--limit N` | 非负整数，默认不设置 | 在本地仅保留选中数组的前 N 项，不向服务端请求分页 |
| `--table` | 开关，默认关闭 | 将字段一致的对象数组编码为 `columns` 与 `rows` |
| `--max-output-chars N` | 非负整数，默认 `12000` | 格式化后的接口输出超过 N 字符时，将完整原始响应保存为文件，返回文件元信息及有长度上限的预览；`0` 关闭此阈值 |
| `--output-summary` | 开关，默认关闭 | 配合 `--output`，额外输出包含文件绝对路径、字节数及可用内容类型的 JSON |
| `--framework-request-id ID` | 非空可打印 ASCII，默认不设置 | 发送 `X-ANYTHINGRIGHT-REQ-ID`，对应框架错误的 `extra.request-id`；未设置时由服务端生成框架 ID |

`--output` 用于接口响应及 `read-output`，不用于配置/帮助输出或 doctor 的诊断报告。例如：

```bash
python3 "<skill-dir>/scripts/cli.py" --timeout 90 --output search.json search "graph neural networks"
python3 "<skill-dir>/scripts/cli.py" --framework-request-id framework-001 meta --request-id upstream-001
```

## 紧凑输出与显式响应筛选

接口数据和错误默认使用紧凑 JSON，直接输出中文等 Unicode 字符。`--pretty` 将成功 JSON 缩进排版，`--human-errors` 切换为面向人的错误文本。`--json-errors` 保留为显式选择默认错误模式的兼容参数。帮助、版本和交互 setup 提示仍方便人工阅读，setup 的连接检查输出 JSON 报告。`config`、`routes`、`install-skill`、`doctor` 输出紧凑 JSON；`doctor --text` 可查看可读报告。

响应筛选在**一次接口请求完成后于本地执行**，顺序为：选择数据位置、限制数组条数、保留字段、按需转换表格。不会改变请求体、URL 参数、计费或服务端分页。适用于接口命令及本地 `read-output`，不能与配置、安装、诊断命令混用。必须根据真实响应选择字段，不能猜测不同来源的返回模型。

例如，**已查看的真实响应**包含 `data.items`，且每项都有 `id`、`title`、`url` 时：

```bash
python3 "<skill-dir>/scripts/cli.py" --select /data/items --fields id,title,url --limit 3 search "graph neural networks"
python3 "<skill-dir>/scripts/cli.py" --select /data/items --fields id,title,url --limit 3 --table search "graph neural networks"
```

`--select` 使用 [JSON Pointer](https://www.rfc-editor.org/rfc/rfc6901.html)：`/data/items/0` 选择第一项，键中的 `/` 写为 `~1`，`~` 写为 `~0`。支持精确键和数组下标，不支持通配符。`--fields` 选择选中对象或数组各对象的顶层字面键，不解析点号路径；字段缺失或类型不匹配时返回本地输出错误，避免误报为空结果。显式选中的 `null`、`false`、零和空值均保留。错误报告省略缺失的可选诊断字段，不会自动清理上游业务数据。

`--limit` 实际省略了项目时，输出包装为 `{"data":...,"total":N,"returned":M,"truncated":true}`。`total` 仅指**已经收到的数组**的长度，不代表服务端全部结果数。`--limit 0` 明确返回零项。`--table` 要求数组各对象字段集合一致，可先用 `--fields` 选择共有字段；输出 `{"columns":[...],"rows":[...]}`，嵌套值仍保持 JSON，支持空数组。

大响应默认使用 `12000` 字符的转存阈值，按格式化后的输出计算，不是 token 数或网络字节数。超过阈值时，将**完整原始响应字节**保存在私有系统临时目录，stdout 返回 `file`（绝对路径）、`bytes`、可用的 `content_type`、`reason:"output_limit"`、`raw_response:true`、`truncated:true`、`output_chars` 和 `preview`（最多 500 字符，阈值更小时不超过该阈值）。预览可能是未完整闭合的 JSON，不能当作完整结果。阈值用于触发转存，不是对元信息总长度的严格限制。文件在命令结束后保留供本地按需读取，用完后可删除。

PDF、图像、音视频等二进制响应自动保存文件，并返回 `reason:"binary_response"`，不将原始字节输出到模型上下文。短的 UTF-8 非 JSON 文本包装为 `{"text":"..."}`。确需完整 JSON/文本时可使用 `--max-output-chars 0`；二进制内容仍返回文件引用。

需要自行选择保存路径时，`--output` 继续保留原有行为：保存原始字节、stdout 留空。增加 `--output-summary` 可获取文件元信息：

```bash
python3 "<skill-dir>/scripts/cli.py" --output paper.json --output-summary paper "<paper-id>" --resource content
python3 "<skill-dir>/scripts/cli.py" --pretty --max-output-chars 0 meta
```

`--output-summary` 必须配合 `--output`，保存原始响应的 `--output` 不可与 `--select`、`--fields`、`--limit`、`--table` 混用。如果**接口已成功执行后**本地格式化或保存失败，stderr JSON 返回 `error_code:"response_output_error"`、`request_completed:true`、`do_not_repeat:true`，恢复保存成功时还会返回完整原始响应的文件。应读取文件在本地修正展示，不能为修正格式而重复上传或创建任务。

## 接口命令共有参数

下文所有接口命令均支持以下参数。`setup`、`config`、`doctor`、`routes`、`install-skill` 这些本地/管理命令不支持它们。

| 参数 | 类型 / 默认值 | 说明 |
| --- | --- | --- |
| `--param KEY=VALUE` | 可重复字符串，默认不设置 | URL 查询参数，键不能为空；同一键重复传入会保留多个值，脚本负责 URL 编码。业务字段名以部署环境的上游契约为准 |
| `--request-id ID` | 非空可打印 ASCII，未设置时自动生成 UUID | 发送上游/代理追踪头 `X-Request-ID`，与全局框架请求 ID 不同 |

```bash
python3 "<skill-dir>/scripts/cli.py" paper "<paper-id>" --param "<contract-key>=<value>" --request-id upstream-001
```

契约支持多值查询键时，使用 `--param "KEY=VALUE1" --param "KEY=VALUE2"`。通用请求的路径中不要附加查询字符串。`--param` 是 URL 查询参数，`--body` 是 JSON 请求体，`--field` 是上传表单字段，三者不能相互替代。全局 `--limit` 仅在本地裁剪响应，不是上游分页参数；没有内置的 `--page`、`--year` 选项。服务端字段应按上游契约通过 `--param` 或 `--body` 传递。

## 配置与本地命令

### setup

保存服务根地址和 API Key，默认随后调用一次 `/meta` 检查连接，使用 `--no-check` 可跳过。

```bash
python3 "<skill-dir>/scripts/cli.py" setup
python3 "<skill-dir>/scripts/cli.py" setup --online
python3 "<skill-dir>/scripts/cli.py" setup --base-url https://linxsci.com --no-check
```

| 参数 | 类型 / 默认值 | 说明 |
| --- | --- | --- |
| `--base-url URL` | 服务根地址，可选 | 明确指定向导建议的地址，优先于 `--online`；必须为 HTTP(S)，不能包含账号、查询串、片段或 `/openapi/v1`、`/openapi/v2` 后缀 |
| `--online` | 开关，默认关闭 | 使用发行配置中的线上地址 `https://linxsci.com` 作为建议值，代替保存的地址；交互时仍可修改 |
| `--api-key-stdin` | 开关，默认关闭 | 从 stdin 读取一行 Key，替代交互式隐藏输入；用于本机秘密管理器或受保护输入流，不应将真实 Key 写成 shell 历史中的字面量 |
| `--no-check` | 开关，默认关闭 | 仅保存配置，不发起连接检查 |

不使用 `--api-key-stdin` 时必须在交互终端运行；向导询问地址并隐藏输入 Key。已有保存的 Key 时，留空会保留它。未指定地址和 `--online` 时，优先建议保存的地址，否则使用发行默认值；通过参数选择的地址在交互中仍可改写。连接检查失败不会撤销已保存的配置。向导检查使用刚提供的配置，但后续命令仍可能受环境变量覆盖。

### config

```bash
python3 "<skill-dir>/scripts/cli.py" config
python3 "<skill-dir>/scripts/cli.py" config --clear
```

不带参数时输出 `config_file`、`saved_base_url`、`saved_key_configured`、`environment_url_override`、`environment_key_override`，不输出 Key、不调用服务。`--clear` 为可选开关，默认关闭；指定后删除保存的配置文件，不会清除环境变量。仅在用户要求时清除配置。

### doctor

```bash
python3 "<skill-dir>/scripts/cli.py" doctor
python3 "<skill-dir>/scripts/cli.py" doctor --json
```

`--json` 保留为兼容开关，JSON 已是默认格式；使用 `--text`（默认关闭）可切换人工可读报告，二者互斥。报告输出到 stdout。报告包含 `ok`、实际 `base_url`、配置信息，以及可用时的状态、错误和请求追踪信息。本地配置缺失/无效退出码为 2，服务失败为 1，成功为 0。此操作需要已配置 Key，会实际请求 `/meta`；200 状态的 HTML 登录页不算 JSON API 连接成功。请求计入正常调用流程，已有有效检查结果时不要重复探测。

### routes

```bash
python3 "<skill-dir>/scripts/cli.py" routes
```

没有命令专用参数；本地输出全部 34 条支持的方法及路径模板，不需要 Key、不联网。

### install-skill

```bash
python3 "<skill-dir>/scripts/cli.py" install-skill
python3 "<skill-dir>/scripts/cli.py" install-skill --skills-dir /absolute/path/to/assistant/skills
python3 "<skill-dir>/scripts/cli.py" install-skill --update
```

| 参数 | 类型 / 默认值 | 说明 |
| --- | --- | --- |
| `--skills-dir PATH` | 目录，默认 `~/.agents/skills` | 助手扫描父目录，安装器自动追加 `/linxsci-skills`；支持展开开头的 `~` |
| `--update` | 开关，默认关闭 | 更新由本安装器管理的副本，并将旧版备份到扫描父目录旁的 `linxsci-skill-backups`，避免被助手重复扫描 |

此操作复制随包文件，不需要 Key 或网络；可通过 Skill 独立脚本运行，无需安装 CLI/SDK。更新时必须从**新版本**下载源码或安装包运行命令，确保复制的是新文件。安装器拒绝符号链接目标、不受其管理或标记不匹配的目录；外部安装器的副本请用原工具更新。此命令不配置 Key，也不注册终端命令。

### read-output

从已保存的响应文件进行本地筛选，不需要 Key、不联网，可避免为调整输出再次请求远程服务：

```bash
python3 "<skill-dir>/scripts/cli.py" --select /data/items --fields id,title,url --limit 3 read-output "/absolute/path/response.json"
```

位置参数 `file` 必填，指定本地原始响应文件，支持展开开头的 `~`。路径和字段示例需替换为实际值。支持全局 `--select`、`--fields`、`--limit`、`--table`、`--pretty`、`--max-output-chars`，也可用 `--output`（与筛选选项互斥）另存原始字节。响应仍超过阈值时复用原文件引用，不重复生成副本。文件缺失、无法读取或字段选择错误返回本地错误，不会发起接口请求。

## 全部 34 条接口索引

每行都是独立示例，不应将整表当作必须依次执行的操作。各命令详细参数见下文。

| 编号 | 接口 | 示例 |
| --- | --- | --- |


## 服务信息与健康检查

### meta

`GET /openapi/v2/meta`。查询接口元信息，响应不保证包含完整业务 schema。

```bash
python3 "<skill-dir>/scripts/cli.py" meta
```

没有位置参数或专用选项，支持共有的 `--param` 和 `--request-id`，需要已配置的 Key。

### usage

`GET /openapi/v2/usage`。查询账号用量信息。

```bash
python3 "<skill-dir>/scripts/cli.py" usage
```

没有位置参数或专用选项，支持共有的 `--param` 和 `--request-id`，需要已配置的 Key。

### mobile-cards

`GET /openapi/v2/recommendations/mobile-cards`。获取移动端推荐卡片。

```bash
python3 "<skill-dir>/scripts/cli.py" mobile-cards
```

没有位置参数或专用选项，支持共有的 `--param` 和 `--request-id`，需要已配置的 Key。

### health

`GET /openapi/v2/health/{check}`。

```bash
python3 "<skill-dir>/scripts/cli.py" health live
python3 "<skill-dir>/scripts/cli.py" health ready
```

位置参数 `check` 必填，只能为 `live`（存活）或 `ready`（就绪），没有默认值。两者均需要已配置 Key，并经过正常调用检查和计量，支持接口共有参数。

## 搜索命令

### search

`POST /openapi/v2/papers/search`，用于综合论文搜索。

```bash
python3 "<skill-dir>/scripts/cli.py" search "graph neural networks"
python3 "<skill-dir>/scripts/cli.py" search "graph neural networks" --body @search-options.json
```

| 参数 | 必填 / 默认值 | 说明 |
| --- | --- | --- |
| `query` | 必填位置字符串 | 检索词，以 JSON 的 `query` 字段发送，多词内容用引号括起 |
| `--body JSON_OR_@FILE` | 可选，默认无附加字段 | 附加 JSON **对象**，可内联或从 UTF-8 文件读取；其中的 `query` 会被位置检索词覆盖 |

支持接口共有参数。仅传检索词无需请求文件，例如 `"graph neural networks"` 生成 `{"query":"graph neural networks"}`。附加字段必须符合当前来源的部署契约，不应未经核对直接复用其他来源的请求模型。

### search-openalex

`POST /openapi/v2/search/openalex`，用于OpenAlex 搜索。

```bash
python3 "<skill-dir>/scripts/cli.py" search-openalex "graph neural networks"
python3 "<skill-dir>/scripts/cli.py" search-openalex "graph neural networks" --body @search-options.json
```

| 参数 | 必填 / 默认值 | 说明 |
| --- | --- | --- |
| `query` | 必填位置字符串 | 检索词，以 JSON 的 `query` 字段发送，多词内容用引号括起 |
| `--body JSON_OR_@FILE` | 可选，默认无附加字段 | 附加 JSON **对象**，可内联或从 UTF-8 文件读取；其中的 `query` 会被位置检索词覆盖 |

支持接口共有参数。仅传检索词无需请求文件，例如 `"graph neural networks"` 生成 `{"query":"graph neural networks"}`。附加字段必须符合当前来源的部署契约，不应未经核对直接复用其他来源的请求模型。

### search-semantic-scholar

`POST /openapi/v2/search/semantic-scholar`，用于Semantic Scholar 搜索。

```bash
python3 "<skill-dir>/scripts/cli.py" search-semantic-scholar "graph neural networks"
python3 "<skill-dir>/scripts/cli.py" search-semantic-scholar "graph neural networks" --body @search-options.json
```

| 参数 | 必填 / 默认值 | 说明 |
| --- | --- | --- |
| `query` | 必填位置字符串 | 检索词，以 JSON 的 `query` 字段发送，多词内容用引号括起 |
| `--body JSON_OR_@FILE` | 可选，默认无附加字段 | 附加 JSON **对象**，可内联或从 UTF-8 文件读取；其中的 `query` 会被位置检索词覆盖 |

支持接口共有参数。仅传检索词无需请求文件，例如 `"graph neural networks"` 生成 `{"query":"graph neural networks"}`。附加字段必须符合当前来源的部署契约，不应未经核对直接复用其他来源的请求模型。

### search-google-scholar

`POST /openapi/v2/search/google-scholar`，用于Google Scholar 搜索。

```bash
python3 "<skill-dir>/scripts/cli.py" search-google-scholar "graph neural networks"
python3 "<skill-dir>/scripts/cli.py" search-google-scholar "graph neural networks" --body @search-options.json
```

| 参数 | 必填 / 默认值 | 说明 |
| --- | --- | --- |
| `query` | 必填位置字符串 | 检索词，以 JSON 的 `query` 字段发送，多词内容用引号括起 |
| `--body JSON_OR_@FILE` | 可选，默认无附加字段 | 附加 JSON **对象**，可内联或从 UTF-8 文件读取；其中的 `query` 会被位置检索词覆盖 |

支持接口共有参数。仅传检索词无需请求文件，例如 `"graph neural networks"` 生成 `{"query":"graph neural networks"}`。附加字段必须符合当前来源的部署契约，不应未经核对直接复用其他来源的请求模型。

## JSON POST 命令

### resolve

`POST /openapi/v2/papers/resolve`。解析论文标识。

```bash
python3 "<skill-dir>/scripts/cli.py" resolve --body @papers-resolve.json
```

`--body JSON_OR_@FILE` 为必填选项，接收内联 JSON 或已存在的 UTF-8 JSON 文件。没有位置参数，也没有默认业务字段，支持接口共有参数。应按当前接口实际的上游 schema 准备 `papers-resolve.json`；仓库没有定义全部业务必填字段，不能假定 `{}` 有效。

### batch-get

`POST /openapi/v2/papers:batchGet`。批量获取论文。

```bash
python3 "<skill-dir>/scripts/cli.py" batch-get --body @papers-batch-get.json
```

`--body JSON_OR_@FILE` 为必填选项，接收内联 JSON 或已存在的 UTF-8 JSON 文件。没有位置参数，也没有默认业务字段，支持接口共有参数。应按当前接口实际的上游 schema 准备 `papers-batch-get.json`；仓库没有定义全部业务必填字段，不能假定 `{}` 有效。

### recommend

`POST /openapi/v2/recommendations`。请求论文推荐。

```bash
python3 "<skill-dir>/scripts/cli.py" recommend --body @recommendations.json
```

`--body JSON_OR_@FILE` 为必填选项，接收内联 JSON 或已存在的 UTF-8 JSON 文件。没有位置参数，也没有默认业务字段，支持接口共有参数。应按当前接口实际的上游 schema 准备 `recommendations.json`；仓库没有定义全部业务必填字段，不能假定 `{}` 有效。

### resolve-entities

`POST /openapi/v2/entities:resolve`。解析作者、机构或期刊/会议标识。

```bash
python3 "<skill-dir>/scripts/cli.py" resolve-entities --body @entities-resolve.json
```

`--body JSON_OR_@FILE` 为必填选项，接收内联 JSON 或已存在的 UTF-8 JSON 文件。没有位置参数，也没有默认业务字段，支持接口共有参数。应按当前接口实际的上游 schema 准备 `entities-resolve.json`；仓库没有定义全部业务必填字段，不能假定 `{}` 有效。

### parse-pdf

`POST /openapi/v2/pdf/parse`。根据 JSON 请求创建 PDF 解析任务，此命令不上传本地文件。

```bash
python3 "<skill-dir>/scripts/cli.py" parse-pdf --body @pdf-parse.json
```

`--body JSON_OR_@FILE` 为必填选项，接收内联 JSON 或已存在的 UTF-8 JSON 文件。没有位置参数，也没有默认业务字段，支持接口共有参数。应按当前接口实际的上游 schema 准备 `pdf-parse.json`；仓库没有定义全部业务必填字段，不能假定 `{}` 有效。 设置 `LINXSCI_MINERU_API_KEY` 后会转发该 PDF Key；创建后保存真实任务 ID，按返回状态确认完成后再获取结果。

## 论文资源

### paper

```bash
python3 "<skill-dir>/scripts/cli.py" paper "<paper-id>"
python3 "<skill-dir>/scripts/cli.py" paper "<paper-id>" --resource toc
python3 "<skill-dir>/scripts/cli.py" paper "<paper-id>" --resource sections --item-id "<section-id>"
python3 "<skill-dir>/scripts/cli.py" --output asset.bin paper "<paper-id>" --resource assets --item-id "<asset-id>"
```

| 参数 | 必填 / 默认值 | 说明 |
| --- | --- | --- |
| `paper_id` | 必填位置字符串 | 真实返回的原始论文 ID，带 `local:`、`arxiv:`、`openalex:`、`s2:` 或 `doi:` 前缀，由脚本编码 |
| `--resource NAME` | 可选，默认论文详情 | 从下表选择资源类型 |
| `--item-id ID` | `sections` / `assets` 必填，其他情况禁止 | 真实响应返回的原始章节/资源 ID，自动编码 |

所有资源均使用 GET，支持接口共有参数。

| `--resource` | `/openapi/v2/papers/{paper_id}` 后的路径 | 返回内容 |
| --- | --- | --- |
| 不传 | 无 | 论文详情 |
| `content` | `/content` | 论文正文内容 |
| `toc` | `/toc` | 目录及真实章节 ID |
| `sections` | `/sections/{section_id}` | 指定章节，必须传 `--item-id` |
| `figures` | `/figures` | 图表信息 |
| `assets` | `/assets/{asset_id}` | 指定资源，必须传 `--item-id`；二进制内容用全局 `--output` 保存 |
| `references` | `/references` | 参考文献 |
| `citations` | `/citations` | 引用本论文的论文 |
| `related` | `/related` | 相关论文 |
| `graph` | `/graph` | 引用图谱 |
| `citation` | `/citation` | 引用格式内容 |

论文、章节和资源 ID 必须来自检索、目录或图表响应，不能根据标题猜测。`doi:10.1000/example` 这样的原始 DOI ID 会自动编码；提前编码会导致 `%` 再次被编码。

## 作者、机构与期刊/会议

### author

```bash
python3 "<skill-dir>/scripts/cli.py" author "<returned-author-id>"
python3 "<skill-dir>/scripts/cli.py" author "<returned-author-id>" --papers
```

位置参数 `entity_id` 必填，使用真实的原始作者标识，由脚本自动 URL 编码。可选开关 `--papers` 默认关闭：不传时 GET `/openapi/v2/authors/{author_id}` 获取详情，传入后 GET `/openapi/v2/authors/{author_id}/papers` 获取论文。除非真实实体 ID 本身包含，否则不要自行添加论文来源前缀。支持共有的 `--param` 和 `--request-id`，分页字段以实际契约为准。

### institution

```bash
python3 "<skill-dir>/scripts/cli.py" institution "<returned-institution-id>"
python3 "<skill-dir>/scripts/cli.py" institution "<returned-institution-id>" --papers
```

位置参数 `entity_id` 必填，使用真实的原始机构标识，由脚本自动 URL 编码。可选开关 `--papers` 默认关闭：不传时 GET `/openapi/v2/institutions/{institution_id}` 获取详情，传入后 GET `/openapi/v2/institutions/{institution_id}/papers` 获取论文。除非真实实体 ID 本身包含，否则不要自行添加论文来源前缀。支持共有的 `--param` 和 `--request-id`，分页字段以实际契约为准。

### venue

```bash
python3 "<skill-dir>/scripts/cli.py" venue "<returned-venue-id>"
python3 "<skill-dir>/scripts/cli.py" venue "<returned-venue-id>" --papers
```

位置参数 `entity_id` 必填，使用真实的原始期刊或会议标识，由脚本自动 URL 编码。可选开关 `--papers` 默认关闭：不传时 GET `/openapi/v2/venues/{venue_id}` 获取详情，传入后 GET `/openapi/v2/venues/{venue_id}/papers` 获取论文。除非真实实体 ID 本身包含，否则不要自行添加论文来源前缀。支持共有的 `--param` 和 `--request-id`，分页字段以实际契约为准。

## PDF 上传与任务

### upload

`POST /openapi/v2/pdf/parse/upload`，使用 multipart 表单。

```bash
python3 "<skill-dir>/scripts/cli.py" upload "/absolute/path/paper.pdf"
python3 "<skill-dir>/scripts/cli.py" upload "/absolute/path/paper.pdf" --field "<contract-field>=<value>"
```

| 参数 | 必填 / 默认值 | 说明 |
| --- | --- | --- |
| `file` | 必填位置文件路径 | 已存在且可读的本地 PDF，以 multipart 的 `file` 字段发送，内容类型为 `application/pdf` |
| `--field KEY=VALUE` | 可重复，默认无附加字段 | 契约定义的附加 multipart 字段，各字段名必须非空且唯一，值为字符串 |

支持接口共有参数。脚本自动生成 multipart 边界，不接受 `--body`，无需手动设置 Content-Type。操作会将所选文件发送到已配置服务，文件大小及业务校验限制由服务端决定。设置了 `LINXSCI_MINERU_API_KEY` 时，会转发为 `X-MinerU-API-Key`。创建后记录实际任务 ID，结果不确定时不要自动重复上传。

### task

```bash
python3 "<skill-dir>/scripts/cli.py" task "<returned-task-id>"
python3 "<skill-dir>/scripts/cli.py" task "<returned-task-id>" --result
```

位置参数 `task_id` 必填，使用真实响应中的原始标识，由脚本自动编码；不能为空、`.`、`..` 或保留值 `upload`。可选开关 `--result` 默认关闭：不传时 GET `/openapi/v2/pdf/parse/{task_id}` 查询状态，传入时 GET `/openapi/v2/pdf/parse/{task_id}/result` 获取结果。支持接口共有参数，设置后会转发 `LINXSCI_MINERU_API_KEY`。

根据实际状态模型确认完成后再获取结果。此命令只发起一次请求，不自动轮询或等待完成；文档未定义统一的终态字段。保存二进制结果时，将全局 `--output result.bin` 放在 `task` 之前。

## 通用请求

### request

```bash
python3 "<skill-dir>/scripts/cli.py" request GET /meta
python3 "<skill-dir>/scripts/cli.py" request POST /papers/resolve --body @papers-resolve.json
python3 "<skill-dir>/scripts/cli.py" request POST /papers/search --body '{"query":"graph neural networks"}'
python3 "<skill-dir>/scripts/cli.py" request GET "/papers/doi:10.1000%2Fexample/toc"
```

| 参数 | 必填 / 默认值 | 说明 |
| --- | --- | --- |
| `method` | 必填位置参数，只能为 `GET` / `POST` | 支持路由对应的大写 HTTP 方法 |
| `path` | 必填位置字符串 | 以 `/` 开头、相对于 `/openapi/v2` 的已支持路径，不是完整 URL；动态路径段需自行编码 |
| `--body JSON_OR_@FILE` | JSON POST 必填，GET 应省略 | 符合接口契约的内联 JSON 或已存在的 UTF-8 JSON 文件 |

支持接口共有参数；PDF 路径会按需转发环境变量 `LINXSCI_MINERU_API_KEY`。仅允许文档列出的映射方法和路径。路径不能含 `?`、`#` 或未编码的动态 ID 斜杠，查询通过 `--param` 传递。DOI 中的斜杠编码为 `%2F`。通用请求不像便捷 `paper` 命令那样校验论文来源前缀，调用方必须自行提供真实标识。GET 不可携带非 null JSON 请求体。通用命令没有文件参数，因此 multipart `/pdf/parse/upload` 必须使用 `upload`。上述内联 JSON 引号示例适用于 Bash；使用 JSON 文件可避免不同 shell 的转义差异。

## JSON 文件、环境变量和输出

搜索 `--body` 必须解析为对象，其他 JSON 请求体应符合所选接口的 schema。JSON 语法错误、无法读取或非 UTF-8 文件属于本地失败。示例文件名不是仓库自带的业务请求文件。已知最小搜索请求为 `{"query":"graph neural networks"}`，不能据此推断解析标识、推荐、实体或 PDF 创建任务的字段。

| 环境变量 | 默认值 / 行为 |
| --- | --- |
| `LINXSCI_BASE_URL` | 覆盖保存的服务根地址；发行回退值为 `https://linxsci.com` |
| `LINXSCI_OPENAPI_KEY` | 覆盖保存的客户端 Key，无默认值 |
| `LINXSCI_CONFIG_FILE` | 覆盖配置文件路径；默认 macOS/Linux 为 `~/.config/linxsci-skills/config.json`，Windows 为 `%LOCALAPPDATA%\linxsci-skills\config.json` |
| `LINXSCI_MINERU_API_KEY` | PDF 命令及通用 PDF 请求可选的 `X-MinerU-API-Key`，不会发送到其他接口 |

保存的配置优先于发行默认值，环境变量优先于保存的配置。使用 LinxSci 客户端 Key 完成鉴权。

接口成功后默认输出紧凑 JSON，大响应和二进制使用上文的文件引用规则。全局 `--output` 保留原始响应字节。不要假定接口拥有统一的列表、分页或任务状态字段。

| 退出码 | 含义 |
| --- | --- |
| `0` | 操作成功 |
| `1` | HTTP/网络或服务诊断失败 |
| `2` | 参数、配置、本地文件或取消操作错误 |

HTTP/网络失败时，`--json-errors` 提供 `message`、HTTP `status`、`error_code`、`request_id`、`framework_request_id`、`execution_uncertain` 和 `retry_after`。本地错误包含 `error_code` 和 `message`，`doctor --json` 则使用 stdout 的诊断报告。参数解析错误默认以 `error_code:"invalid_arguments"` 的 JSON 写入 stderr，本地错误使用 `error_code:"local_error"`，取消使用 `error_code:"cancelled"`；`--human-errors` 恢复文本错误。工具不自动重试，尤其 `-3905` 时应先查询执行及计费结果，再决定是否重复上传或创建任务。详见 [API 错误与计量规则](api.zh-CN.md)。
