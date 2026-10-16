---
name: linxsci-scholar
description: 使用 LinxSci Scholar OpenAPI v2 搜索学术论文、读取章节和引用、查询作者机构期刊以及上传 PDF 并获取解析结果。当用户需要基于 Scholar 的文献检索或论文证据分析时使用。
---

# LinxSci Scholar

使用本 Skill 的统一入口 `scripts/cli.py scholar`。所有示例中的 `<skill-dir>` 都替换为本文件所在目录的绝对路径；脚本仅依赖 Python 3.9+ 标准库，无需安装 SDK。

## 配置与发现

脚本优先读取环境变量 `SCHOLAR_BASE_URL` 和 `SCHOLAR_OPENAPI_KEY`，其次读取 `setup` 保存的用户本地配置。地址默认值是测试服务 `http://101.126.93.213:28888`，可配置为 `https://linxsci.com` 或其他部署地址；服务根地址不含 `/openapi/v2`。不要读取、展示或让用户把 Key 发到对话。缺少配置时请用户在本机运行向导，Key 通过隐藏输入保存：

```bash
python3 <skill-dir>/scripts/cli.py scholar setup
# 线上地址作为默认提示：
python3 <skill-dir>/scripts/cli.py scholar setup --online
```

不要把服务端的 `AGENT_PUBLIC_API_KEY` 当成客户端 Key。`config` 仅显示配置状态，`config --clear` 清除保存的配置；执行清除需来自用户请求。

```bash
python3 <skill-dir>/scripts/cli.py scholar doctor
# 需要元信息正文时再调用：
python3 <skill-dir>/scripts/cli.py scholar meta
python3 <skill-dir>/scripts/cli.py scholar routes
```

首次接入可用 `doctor`（调用 `/meta`）验证连接；它也经过用量检查和计费流程，已有有效连接结果时不重复探测。根据 [接口文档](references/api.md) 核对目标路由；对于未定义的业务请求模型，读取部署环境的上游契约或用户提供的请求 JSON。`meta` 不保证返回完整 schema；缺少契约时先完成已知搜索/阅读操作，明确指出缺失字段信息，不猜测字段和分页。

## 文献工作流

```bash
python3 <skill-dir>/scripts/cli.py scholar search 'graph neural networks'
python3 <skill-dir>/scripts/cli.py scholar paper 'arxiv:2301.07041'
python3 <skill-dir>/scripts/cli.py scholar paper 'arxiv:2301.07041' --resource toc
python3 <skill-dir>/scripts/cli.py scholar paper 'arxiv:2301.07041' --resource sections --item-id '<returned-section-id>'
```

从搜索结果中取实际论文 ID；先看详情、目录，再读取相关章节，需要完整文本时才读 `--resource content`。论文 ID 需要 `local:`、`arxiv:`、`openalex:`、`s2:` 或 `doi:` 前缀。便捷命令接收未经编码的 ID（例如 `doi:10.1000/example`），SDK 负责编码。章节和资源 ID 必须取自返回结果。

回答研究问题时由助手综合已读取内容，附上实际返回的论文标识、链接和章节依据。区分摘要和全文证据，说明缺失内容；不要声称存在服务端 `ask`、趋势榜或自动综述接口。

## 其他接口与 PDF

```bash
python3 <skill-dir>/scripts/cli.py scholar request POST /papers/resolve --body @resolve.json
python3 <skill-dir>/scripts/cli.py scholar request GET '/authors/<encoded-author-id>/papers' --param '<upstream-key>=<value>'
python3 <skill-dir>/scripts/cli.py scholar upload /absolute/path/paper.pdf
python3 <skill-dir>/scripts/cli.py scholar task '<returned-task-id>'
python3 <skill-dir>/scripts/cli.py scholar task '<returned-task-id>' --result
python3 <skill-dir>/scripts/cli.py scholar --output /absolute/path/asset.bin paper 'arxiv:2301.07041' --resource assets --item-id '<returned-asset-id>'
```

Scholar 组的可选参数 `--framework-request-id <id>`（放在 `scholar` 之后、具体动作之前）发送 `X-ANYTHINGRIGHT-REQ-ID`，对应 Scholar 自身错误的 `extra.request-id`；`request --request-id <id>` 发送独立的 `X-Request-ID`。两者用途不同。通用 `request` 的路径相对于 `/openapi/v2`，每个动态 ID 独立 URL 编码（包括 DOI 中的斜杠）；查询参数用重复的 `--param key=value`。JSON 通过 `--body @file.json` 原样传入。PDF 可传 `--field key=value`，仅在上游契约要求时设置 `SCHOLAR_MINERU_API_KEY`。

上传会发送本地文件到配置服务，仅在用户请求解析该文件时执行。任务状态结构未定义，使用实际返回的标识和状态；不自动无限轮询或重复创建任务，确认完成后获取结果。

## 输出与故障

stdout 输出 JSON 或原始响应；`--output`（放在 `scholar` 之后、具体动作之前）保留响应原始字节，适用于二进制资源。SDK `Response` 保留 status、headers、body。上游响应原样透传，Scholar 自身错误则使用 `code/data/error/extra` 框架结构；读取 `error.code` 和 `extra.request-id`，不把它当作上游业务模型。`extra.cost` 是请求耗时（秒），不是扣费金额。不要假定列表字段或 PDF 终态。

退出码：0 成功，1 HTTP/网络错误，2 参数/本地文件错误。SDK 异常保留原始错误体，并提供 `error_code`、`request_id`、`framework_request_id`、`execution_uncertain` 属性。CLI 默认输出中文诊断和两种请求 ID；`scholar --json-errors` 输出结构化诊断，不展示服务端错误消息全文。

按 HTTP 状态和实际 `error.code` 区分故障：

| error.code | 处理 |
| --- | --- |
| `-401` / `-404` | 检查 Scholar Key / 路径和方法 |
| `-3900` | action 已登记但未启用，联系管理员配置并启用；不要反复重试 |
| `-3901` | 每日调用限额已满，额度恢复后或管理员处理后再调用 |
| `-3902` | 服务端 Agent API 地址或 Key 缺失，联系管理员 |
| `-3903` | 上游连接/传输失败，检查连接；不要将失败等同于业务操作一定未执行 |
| `-3904` | member begin 未成功，未转发上游，交由管理员排查 |
| `-3905` | 上游已返回但 finish 未确认，先查询执行与计费结果，再决定是否重试，尤其不要直接重复上传或创建解析任务 |

上游业务错误（例如 `validation_error`、`asset_unavailable`）保留其原有格式；不要把全部 502/503 当作相同原因。脚本不自动重试；保留 `Retry-After`，但它不能替代 `-3905` 的执行/计费核查。

每次请求预计调用量为 1，Agent API 2xx 对应实际调用量 1，其他状态或连接失败对应 0，预占释放由 member finish 结果确认。不要根据 HTTP 失败自行保证扣费已经释放，尤其遇到 `-3905`。避免无目的的重复检索、诊断与轮询；查询动作也走调用限额。详细规则见 [references/api.md](references/api.md)。
