# 开发者指南

以下开发与测试命令用于完整源码仓库；普通用户 ZIP 是可直接运行的安装子集，不是 editable 开发工程。

## 环境与安装

Python 3.9+，运行时只依赖标准库。源码开发：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
linxsci-scholar --version
linxsci-scholar setup
```

Windows 激活使用 `.venv\Scripts\activate`。不安装包也可运行 `python3 skills/linxsci-scholar/scripts/scholar.py`。

代码的唯一实现位于 Skill 的 `scripts`；setuptools 将完整 Skill 映射成 `linxsci_scholar` 包，wheel 包含脚本、SKILL.md、参考文档、agents 元数据和 service.json。根目录 `scholar.py`、`scholar_client.py` 保留 0.1 兼容导入。

## 配置

优先级：SDK 显式参数 > 环境变量 > 本地配置 > `service.json` 地址默认值。Key 没有发行默认值。

| 环境变量 | 用途 |
| --- | --- |
| SCHOLAR_BASE_URL | 覆盖服务根地址 |
| SCHOLAR_OPENAPI_KEY | 覆盖 Scholar Key |
| SCHOLAR_CONFIG_FILE | 指定本地配置文件路径，适用于隔离测试/多环境 |
| SCHOLAR_MINERU_API_KEY | 可选 PDF 上游 Key，只发往 PDF 路由 |

`.env.example` 仅是模板，不会自动加载。`setup --api-key-stdin --base-url URL` 可从标准输入读取 Key，便于已有秘密管理器接入；不要把真实 Key 写在 shell 命令参数中。`--no-check` 允许离线保存，`doctor --json` 提供机器可读检查结果。

## CLI

```bash
linxsci-scholar --help
linxsci-scholar routes
linxsci-scholar meta
linxsci-scholar usage
linxsci-scholar health ready
linxsci-scholar search 'graph neural networks'
linxsci-scholar paper 'arxiv:2301.07041'
linxsci-scholar paper 'arxiv:2301.07041' --resource toc
linxsci-scholar paper 'arxiv:2301.07041' --resource sections --item-id '返回的章节ID'
linxsci-scholar paper 'doi:10.1000/example' --resource references
linxsci-scholar --output content.json paper 'arxiv:2301.07041' --resource content
linxsci-scholar upload /absolute/path/paper.pdf
linxsci-scholar task '返回的任务ID'
linxsci-scholar task '返回的任务ID' --result
```

便捷命令接收未经 URL 编码的 ID；SDK 会编码 DOI 中的斜杠。全局 `--output`、`--timeout`、`--json-errors` 放在子命令前。成功输出为 JSON 或原始响应，`--output` 保留原始字节；错误提示在 stderr。退出码 0 成功、1 HTTP/网络/连接检查错误、2 输入/配置/文件错误。

通用请求支持全部已知路由。按实际上游契约准备 JSON：

```bash
linxsci-scholar request POST /papers:batchGet --body @request.json
linxsci-scholar request POST /search/openalex --body @request.json
linxsci-scholar request GET '/authors/实际且已编码的作者ID/papers'
linxsci-scholar request GET '/papers/doi:10.1000%2Fexample/citation'
```

通用请求的动态 ID 需要独立 URL 编码，路径相对于 `/openapi/v2`。重复 `--param key=value` 保留同名查询参数；`search --body @filters.json` 添加上游支持的搜索字段，位置参数搜索词优先。上传支持 `--field key=value`。不假定响应列表字段，不自动重试 POST，也不自动无限轮询 PDF 状态。当前上传在内存构建 multipart，大小限制依照部署契约。

## Python SDK

```python
from linxsci_scholar import ScholarClient, ScholarError

client = ScholarClient()  # 本地配置也可用；可显式传 base_url/api_key
try:
    response = client.search('graph neural networks')
    print(response.status)
    print(response.json())
    toc = client.paper('arxiv:2301.07041', 'toc')
except ScholarError as error:
    print(error.status)
    # error.body 和 error.headers 保留上游诊断数据；输出前检查敏感信息。
```

`Response` 保留 `status`、`headers`、`body`；资源二进制读取 `body`。通用 `client.request(method, path, payload=..., query=...)` 原样传递业务参数。HTTP 错误保留响应体、两种请求 ID 和 Retry-After；CLI 展示数字/字符串错误码及中文诊断，不回显服务端消息全文。禁止自动跟随重定向，避免泄露 Key。

## 新版框架错误与请求追踪

Scholar 自身错误为 `{code: -1, data: {}, error: {code: 数字, msg: 消息}, extra: {request-id: ID, cost: 秒}}`；Agent API 业务错误仍按上游原样返回。`extra.cost` 表示耗时，不是积分或金额。

SDK 异常提供 `error_code`、`request_id`（X-Request-ID 或上游 error.request_id）、`framework_request_id`（extra.request-id）和 `execution_uncertain`（-3905 时为 True）。需要调用方指定框架 ID：

```python
client = ScholarClient(framework_request_id="scholar-trace-001")
response = client.request("GET", "/meta", request_id="agent-trace-001")
# 单次覆盖也可传 framework_request_id="another-framework-id"
```

```bash
linxsci-scholar --framework-request-id scholar-trace-001 request GET /meta --request-id agent-trace-001
linxsci-scholar --json-errors search 'graph neural networks'
```

`X-ANYTHINGRIGHT-REQ-ID` 指定 Scholar 框架的 extra.request-id；`X-Request-ID` 用于上游/代理追踪。不要混为同一值。

错误码 -401/-404 对应鉴权/路由；-3900 为 action 待启用，-3901 为日限额，-3902 为上游配置缺失，-3903 为上游传输失败，-3904 为 member begin 失败且未转发。-3905 表示 Agent API 已返回但 member finish 未确认，先核查执行与计费结果，再决定是否重试。SDK/CLI 不自动重试，不能根据通用 502 推断业务未执行或费用已经释放。上游字符串错误码仍正常保留。

包括 meta/doctor、健康检查在内的调用均经过 Scholar Key 和用量流程。每次预计调用量 1；上游 2xx 实际为 1，否则为 0，预占释放由 member finish 结果确认。服务端使用 AgentPublicServerIp、AgentPublicAPIKey，配置为空时可回退到 AGENT_PUBLIC_API_URL、AGENT_PUBLIC_API_KEY；客户端始终只需 Scholar Key。

## 验证

```bash
python3 -m unittest discover -s tests -v
```

测试使用临时配置目录和本地 HTTP 模拟服务，不使用真实 Key。覆盖路由、鉴权、编码、上传、配置优先级、凭据不输出、诊断、安装更新和失败回滚。CI 在 Linux、macOS、Windows 上运行测试与发行包安装检查。

真实联调需要在本机配置真实 Key、正确本地端口后执行 `doctor` 和 `search`，从响应选择真实 ID 再测试目录/章节；PDF 上传使用获准发送的文件，并检查实际返回的任务状态。若缺少上游模型，不应编造参数或声称该流程已通过真实服务验证。

更新接口文档时同步根文档与 `skills/linxsci-scholar/references/api.md`，并维护 SDK 路由列表。版本同时更新 pyproject、包 __version__、CLI VERSION 和安装标记；发布检查工具会检查一致性。
