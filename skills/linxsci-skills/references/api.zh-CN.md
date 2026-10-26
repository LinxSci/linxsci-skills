# LinxSci OpenAPI v2 使用文档

[English](api.md)

LinxSci 的 `/openapi/v2` 将请求转发给独立 Agent API。客户端只需使用 LinxSci API Key；服务端负责向 Agent API 提供自己的 Key。接口路径、业务请求参数和上游业务响应以 Agent API 的 `/openapi/v1` 契约为准。健康检查分别转发到 Agent API 的 `/health/live` 和 `/health/ready`。

可直接导入 Postman 集合（当前仓库未包含该文件） 调用下表中的接口。

## 认证和配置

| 请求头 | 提供方 | 用途 |
| --- | --- | --- |
| `Authorization: Bearer <LinxSci OpenAPI Key>` | 客户端 | LinxSci 校验 API Key，所有 v2 接口都需要。 |
| `X-Request-ID` | 客户端，可选 | 转发给 Agent API；LinxSci 自身返回错误时也会在响应头回传。 |
| `X-ANYTHINGRIGHT-REQ-ID` | 客户端，可选 | 指定 LinxSci 框架响应中的 `extra.request-id`；未提供时由框架生成。 |
| `X-MinerU-API-Key` | 客户端，按需 | PDF 解析相关请求转发给 Agent API。 |

LinxSci 服务端配置 `AgentPublicServerIp` 和 `AgentPublicAPIKey`；相应环境变量 `AGENT_PUBLIC_API_URL`、`AGENT_PUBLIC_API_KEY` 可在配置项为空时使用。转发到 Agent API `/openapi/v1` 的请求会由服务端附加 `X-API-Key`，客户端无需提供第二把 Key。v2 的这组配置与旧版 Agent API 配置独立。

## 接口目录

以下为 LinxSci 对外路径。除健康检查外，上游使用相同的 HTTP 方法及 `/openapi/v1` 路径前缀。

| Postman 分类 | 方法 | LinxSci 路径 | 接口 |
| --- | --- | --- | --- |
| 服务信息与健康检查 | GET | `/openapi/v2/meta` | 接口元信息 |
| 服务信息与健康检查 | GET | `/openapi/v2/usage` | 用量信息 |
| 服务信息与健康检查 | GET | `/openapi/v2/health/live` | 存活检查 |
| 服务信息与健康检查 | GET | `/openapi/v2/health/ready` | 就绪检查 |
| 论文搜索与解析 | POST | `/openapi/v2/papers/search` | 综合论文搜索 |
| 论文搜索与解析 | POST | `/openapi/v2/search/openalex` | OpenAlex 搜索 |
| 论文搜索与解析 | POST | `/openapi/v2/search/semantic-scholar` | Semantic Scholar 搜索 |
| 论文搜索与解析 | POST | `/openapi/v2/search/google-scholar` | Google Scholar 搜索 |
| 论文搜索与解析 | POST | `/openapi/v2/papers/resolve` | 论文标识解析 |
| 论文搜索与解析 | POST | `/openapi/v2/papers:batchGet` | 批量获取论文 |
| 论文详情与引用 | GET | `/openapi/v2/papers/{paper_id}` | 论文详情 |
| 论文详情与引用 | GET | `/openapi/v2/papers/{paper_id}/content` | 论文内容 |
| 论文详情与引用 | GET | `/openapi/v2/papers/{paper_id}/toc` | 论文目录 |
| 论文详情与引用 | GET | `/openapi/v2/papers/{paper_id}/sections/{section_id}` | 论文章节 |
| 论文详情与引用 | GET | `/openapi/v2/papers/{paper_id}/figures` | 论文图表 |
| 论文详情与引用 | GET | `/openapi/v2/papers/{paper_id}/assets/{asset_id}` | 论文资源 |
| 论文详情与引用 | GET | `/openapi/v2/papers/{paper_id}/references` | 参考文献 |
| 论文详情与引用 | GET | `/openapi/v2/papers/{paper_id}/citations` | 被引论文 |
| 论文详情与引用 | GET | `/openapi/v2/papers/{paper_id}/related` | 相关论文 |
| 论文详情与引用 | GET | `/openapi/v2/papers/{paper_id}/graph` | 引用图谱 |
| 论文详情与引用 | GET | `/openapi/v2/papers/{paper_id}/citation` | 论文引用格式 |
| 论文推荐 | POST | `/openapi/v2/recommendations` | 论文推荐 |
| 论文推荐 | GET | `/openapi/v2/recommendations/mobile-cards` | 移动端推荐卡片 |
| 作者、机构与期刊 | GET | `/openapi/v2/authors/{author_id}` | 作者详情 |
| 作者、机构与期刊 | GET | `/openapi/v2/authors/{author_id}/papers` | 作者论文 |
| 作者、机构与期刊 | GET | `/openapi/v2/institutions/{institution_id}` | 机构详情 |
| 作者、机构与期刊 | GET | `/openapi/v2/institutions/{institution_id}/papers` | 机构论文 |
| 作者、机构与期刊 | GET | `/openapi/v2/venues/{venue_id}` | 期刊或会议详情 |
| 作者、机构与期刊 | GET | `/openapi/v2/venues/{venue_id}/papers` | 期刊或会议论文 |
| 作者、机构与期刊 | POST | `/openapi/v2/entities:resolve` | 实体标识解析 |
| PDF 解析 | POST | `/openapi/v2/pdf/parse` | 创建 PDF 解析任务 |
| PDF 解析 | POST | `/openapi/v2/pdf/parse/upload` | 上传 PDF 并创建解析任务 |
| PDF 解析 | GET | `/openapi/v2/pdf/parse/{task_id}` | 查询 PDF 解析任务 |
| PDF 解析 | GET | `/openapi/v2/pdf/parse/{task_id}/result` | 获取 PDF 解析结果 |

`paper_id` 支持 `local:`、`arxiv:`、`openalex:`、`s2:`、`doi:` 前缀。ID 中的 `/` 需要 URL 编码，例如 `doi:10.1000%2Fexample`。`POST` 接口的 JSON 字段按 Agent API 契约填写；Postman 中的 `{}` 只是待编辑模板。PDF 上传使用 `multipart/form-data` 的 `file` 字段，具体参数与文件大小限制以 Agent API 配置为准。

## API Key 调用与计费流程

正常调用依次经过 LinxSci 的 API Key 校验、member 的 `/internal/openapi/calls/begin`、Agent API 转发和 member 的 `/internal/openapi/calls/finish`。若服务端 Agent API 配置缺失，请求会在 `begin` 前返回；若 `begin` 拒绝请求，则不会转发上游或调用 `finish`。路由映射生成固定的 `openapi_v2_*` action，例如论文资源接口的 action 为 `openapi_v2_paper_asset`。

首次调用尚未登记的 action 时，member 会在 `openapi_register` 创建**待启用**记录；该次请求返回 HTTP 503，且不会转发给 Agent API。管理员按免费或计费策略配置并启用对应 action 后，才能继续调用。

每次请求预计调用量为 1。Agent API 返回 2xx 时，实际调用量为 1；返回其他状态或发生连接失败时，实际调用量为 0，member 根据 `finish` 结果释放预占积分。每日调用限额由 member 检查。

## 响应与错误

Agent API 已返回且 `finish` 成功时，LinxSci 保留上游 HTTP 状态码和响应体，并透传 `Content-Type`、`X-Request-ID`、`Retry-After`、`Cache-Control`。这也适用于 Agent API 的业务错误，例如 `validation_error` 或 `asset_unavailable`；其错误体仍使用 Agent API 的格式。

LinxSci 自身产生的鉴权、配置、用量和连接错误使用统一框架结构：

```json
{
  "code": -1,
  "data": {},
  "error": {
    "code": -3900,
    "msg": "OpenAPI action openapi_v2_paper_asset has been registered but is not enabled. Ask an administrator to configure and enable it before retrying."
  },
  "extra": {
    "request-id": "example-request-id",
    "cost": 0.01
  }
}
```

示例中的 HTTP 状态为 503；`extra.cost` 是本次请求耗时，单位为秒。这里的 `extra.request-id` 来自 `X-ANYTHINGRIGHT-REQ-ID` 或由框架生成。member 内部使用的 `-3501`、`-3500` 会分别转换为下表的对外错误码。

| HTTP | `error.code` | 原因与处理 |
| --- | --- | --- |
| 401 | `-401` | LinxSci API Key 缺失、无效或无法识别用户；检查 `Authorization`。 |
| 404 | `-404` | 未匹配到 v2 接口映射；检查路径和 HTTP 方法。 |
| 503 | `-3900` | 接口 action 已登记但未启用；联系管理员配置、启用后重试。 |
| 429 | `-3901` | 已达到每日调用限额；额度恢复后重试或联系管理员。 |
| 503 | `-3902` | Agent API 地址或服务端 Key 未配置；联系服务端管理员。 |
| 502 | `-3903` | Agent API 连接或传输失败；LinxSci 会尝试以失败结果调用 `finish`。 |
| 502 | `-3904` | member 的 `begin` 未成功，尚未转发上游；检查 member 服务和内部鉴权配置。 |
| 502 | `-3905` | Agent API 已返回，但 member 的 `finish` 未确认；先查询执行与计费结果，再决定是否重试可能产生写入的请求。 |

## Postman 调用

在 Postman 中设置 LinxSci 服务根地址和 Bearer API Key。GET 请求可直接按路径变量调用；POST 请求先按 Agent API 契约填写 JSON。调用 `/openapi/v2/pdf/parse/upload` 时，在 Postman 的 `file` 字段中选择本地 PDF。
