# LinxSci OpenAPI v2 使用文档

[English](api.md)

服务根地址为 `https://linxsci.com`，接口前缀为 `/openapi/v2`，所有接口均需要 LinxSci API Key。业务 JSON 字段、分页及任务状态字段按对应接口的 API 契约使用。

## 认证与请求追踪

| 请求头 | 是否必填 | 用途 |
| --- | --- | --- |
| `Authorization: Bearer <LinxSci OpenAPI Key>` | 是 | 客户端鉴权 |
| `X-Request-ID` | 否 | 上游/代理请求追踪；未提供时 SDK 自动生成 |
| `X-ANYTHINGRIGHT-REQ-ID` | 否 | 框架请求追踪，对应框架错误的 `extra.request-id`；未提供时由服务生成 |
| `X-MinerU-API-Key` | 按需 | PDF 解析接口所需的附加 Key |

客户端 Key 可通过本机配置向导或 `LINXSCI_OPENAPI_KEY` 设置。上游服务鉴权由 LinxSci 管理，客户端仅需按要求提供上述请求头。

## 接口目录

| 分类 | 方法 | LinxSci 路径 | 接口 |
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

论文 ID 支持 `local:`、`arxiv:`、`openalex:`、`s2:`、`doi:` 前缀。动态路径段需分别 URL 编码，包含 DOI 中的斜杠，例如 `doi:10.1000%2Fexample`。SDK/CLI 便捷方法接收原始 ID 并自动编码；通用请求接收已编码路径。POST JSON 按接口契约准备，不能假定 `{}` 通用有效。PDF 上传使用 multipart 的 `file` 字段，文件大小限制及附加字段由服务决定。

## 用量与限额

每次请求的预计调用量为 1。上游返回 2xx 时实际调用量为 1，其他状态或连接失败时为 0。预占积分在服务确认计量完成后释放，不能仅根据 HTTP 失败保证已经释放。每日限额及接口可用性由服务检查，需要时通过 `usage` 和下表错误码排查。

## 响应与错误

成功的上游响应保留其状态、响应体及相关响应头（`Content-Type`、`X-Request-ID`、`Retry-After`、`Cache-Control`）。`validation_error`、`asset_unavailable` 等业务错误保留原有响应模型。SDK 保留原始响应字节；CLI 的显示、字段筛选及文件输出见 [命令指南](cli.zh-CN.md#紧凑输出与显式响应筛选)。

鉴权、服务配置、用量及连接等框架错误采用：

```json
{
  "code": -1,
  "data": {},
  "error": {
    "code": -3900,
    "msg": "This endpoint is not enabled. Contact the service administrator."
  },
  "extra": {"request-id": "example-request-id", "cost": 0.01}
}
```

该示例的 HTTP 状态为 503。`extra.cost` 是耗时，单位为秒，不是扣费金额。`extra.request-id` 来自 `X-ANYTHINGRIGHT-REQ-ID`，或由服务生成。

| HTTP | `error.code` | 含义与处理 |
| --- | --- | --- |
| 401 | `-401` | 客户端 Key 缺失或无效，检查 Authorization 或重新运行配置向导 |
| 404 | `-404` | 方法或路径不支持，核对接口目录 |
| 503 | `-3900` | 接口未启用，联系服务管理员 |
| 429 | `-3901` | 达到每日限额，等待额度恢复或联系管理员 |
| 503 | `-3902` | 上游服务连接配置缺失，联系管理员 |
| 502 | `-3903` | 上游连接或传输失败，检查服务连接后再决定是否重试 |
| 502 | `-3904` | 请求准备失败，尚未转发，联系管理员 |
| 502 | `-3905` | 上游已返回，但计量完成尚未确认，先核查执行和计费结果再决定是否重试 |

排查问题时保留两种请求 ID 和 `Retry-After`（如有）。结果不确定时，不自动重复上传或创建任务。尤其 `-3905` 不代表操作未执行，`Retry-After` 也不能替代执行结果核查。

## 手动调用

在 Postman 或其他 HTTP 客户端中设置服务根地址和 Bearer Key，再按上表选择方法和路径。POST 使用对应接口要求的 JSON。调用 `/openapi/v2/pdf/parse/upload` 时，在 multipart 的 `file` 字段选择本地 PDF。
