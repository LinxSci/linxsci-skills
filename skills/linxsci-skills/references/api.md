# LinxSci OpenAPI v2

[简体中文](api.zh-CN.md)

LinxSci forwards `/openapi/v2` requests to an independent Agent API. Clients supply their LinxSci API key; the server supplies its own upstream key. Business request fields and upstream response schemas follow the deployed Agent API `/openapi/v1` contract. Health checks forward to `/health/live` and `/health/ready`.

## Authentication and server settings

| Header | Supplied by | Purpose |
| --- | --- | --- |
| `Authorization: Bearer <LinxSci OpenAPI Key>` | Client | Required on every v2 endpoint |
| `X-Request-ID` | Client, optional | Upstream/proxy trace ID; also returned on framework errors |
| `X-ANYTHINGRIGHT-REQ-ID` | Client, optional | Framework `extra.request-id`; generated if omitted |
| `X-MinerU-API-Key` | Client, when required | Forwarded for PDF parsing |

The server configures `AgentPublicServerIp` and `AgentPublicAPIKey`, with `AGENT_PUBLIC_API_URL` and `AGENT_PUBLIC_API_KEY` as fallbacks for empty configuration. The server adds `X-API-Key` when forwarding to Agent API. Clients do not need that second key. These v2 settings are independent of older Agent API settings.

## Routes

Except for health checks, upstream routes use the same method and an `/openapi/v1` prefix.

| Category | Method | LinxSci path | Endpoint |
| --- | --- | --- | --- |
| Service and health | GET | `/openapi/v2/meta` | API metadata |
| Service and health | GET | `/openapi/v2/usage` | Usage |
| Service and health | GET | `/openapi/v2/health/live` | Liveness |
| Service and health | GET | `/openapi/v2/health/ready` | Readiness |
| Search and resolution | POST | `/openapi/v2/papers/search` | Paper search |
| Search and resolution | POST | `/openapi/v2/search/openalex` | OpenAlex search |
| Search and resolution | POST | `/openapi/v2/search/semantic-scholar` | Semantic Scholar search |
| Search and resolution | POST | `/openapi/v2/search/google-scholar` | Google Scholar search |
| Search and resolution | POST | `/openapi/v2/papers/resolve` | Resolve paper identifiers |
| Search and resolution | POST | `/openapi/v2/papers:batchGet` | Batch paper lookup |
| Papers and citations | GET | `/openapi/v2/papers/{paper_id}` | Paper details |
| Papers and citations | GET | `/openapi/v2/papers/{paper_id}/content` | Paper content |
| Papers and citations | GET | `/openapi/v2/papers/{paper_id}/toc` | Table of contents |
| Papers and citations | GET | `/openapi/v2/papers/{paper_id}/sections/{section_id}` | Section |
| Papers and citations | GET | `/openapi/v2/papers/{paper_id}/figures` | Figures |
| Papers and citations | GET | `/openapi/v2/papers/{paper_id}/assets/{asset_id}` | Assets |
| Papers and citations | GET | `/openapi/v2/papers/{paper_id}/references` | References |
| Papers and citations | GET | `/openapi/v2/papers/{paper_id}/citations` | Citing papers |
| Papers and citations | GET | `/openapi/v2/papers/{paper_id}/related` | Related papers |
| Papers and citations | GET | `/openapi/v2/papers/{paper_id}/graph` | Citation graph |
| Papers and citations | GET | `/openapi/v2/papers/{paper_id}/citation` | Citation format |
| Recommendations | POST | `/openapi/v2/recommendations` | Recommendations |
| Recommendations | GET | `/openapi/v2/recommendations/mobile-cards` | Mobile recommendation cards |
| Authors, institutions and venues | GET | `/openapi/v2/authors/{author_id}` | Author details |
| Authors, institutions and venues | GET | `/openapi/v2/authors/{author_id}/papers` | Author papers |
| Authors, institutions and venues | GET | `/openapi/v2/institutions/{institution_id}` | Institution details |
| Authors, institutions and venues | GET | `/openapi/v2/institutions/{institution_id}/papers` | Institution papers |
| Authors, institutions and venues | GET | `/openapi/v2/venues/{venue_id}` | Venue details |
| Authors, institutions and venues | GET | `/openapi/v2/venues/{venue_id}/papers` | Venue papers |
| Authors, institutions and venues | POST | `/openapi/v2/entities:resolve` | Resolve entity identifiers |
| PDF parsing | POST | `/openapi/v2/pdf/parse` | Create a PDF parsing task |
| PDF parsing | POST | `/openapi/v2/pdf/parse/upload` | Upload a PDF and create a task |
| PDF parsing | GET | `/openapi/v2/pdf/parse/{task_id}` | Task status |
| PDF parsing | GET | `/openapi/v2/pdf/parse/{task_id}/result` | Task result |

Paper IDs support `local:`, `arxiv:`, `openalex:`, `s2:`, and `doi:` prefixes. Encode each dynamic path segment, including slashes in DOIs, for example `doi:10.1000%2Fexample`. Convenience SDK/CLI methods accept raw IDs and encode them. Generic requests require pre-encoded paths. POST JSON fields follow the upstream contract; `{}` is only a template. PDF upload uses the multipart `file` field, with limits and other fields determined by the upstream deployment.

## Call accounting

A request passes through API key validation, member `/internal/openapi/calls/begin`, Agent API forwarding, and member `/internal/openapi/calls/finish`. Missing server-side upstream configuration fails before begin. A rejected begin does not forward upstream or call finish. Routes map to fixed `openapi_v2_*` actions, such as `openapi_v2_paper_asset`.

The first call to an unregistered action creates a disabled record in `openapi_register` and returns HTTP 503 without forwarding. An administrator must configure and enable that action.

Expected call quantity is 1. Upstream 2xx means actual quantity 1; other statuses or connection failures mean 0. Member releases reserved credits according to finish. Member also enforces daily limits. A failed HTTP response alone does not establish that credits were released.

## Responses and errors

When upstream returns and finish succeeds, LinxSci preserves upstream status and body, plus `Content-Type`, `X-Request-ID`, `Retry-After`, and `Cache-Control`. Upstream business errors such as `validation_error` and `asset_unavailable` retain their original schemas.

Framework authentication, configuration, accounting and connection errors use:

```json
{
  "code": -1,
  "data": {},
  "error": {
    "code": -3900,
    "msg": "OpenAPI action openapi_v2_paper_asset has been registered but is not enabled. Ask an administrator to configure and enable it before retrying."
  },
  "extra": {"request-id": "example-request-id", "cost": 0.01}
}
```

This example has HTTP status 503. `extra.cost` is elapsed time in seconds, not a monetary charge. `extra.request-id` comes from `X-ANYTHINGRIGHT-REQ-ID` or is generated. Internal member codes `-3501` and `-3500` are translated to public codes.

| HTTP | `error.code` | Meaning and action |
| --- | --- | --- |
| 401 | `-401` | Missing/invalid key or unidentified user; check Authorization |
| 404 | `-404` | No mapped v2 route; check method and path |
| 503 | `-3900` | Registered but disabled action; ask an administrator to enable it |
| 429 | `-3901` | Daily limit reached; wait for reset or contact an administrator |
| 503 | `-3902` | Upstream URL or server key missing; contact an administrator |
| 502 | `-3903` | Upstream transport failed; the server attempts finish with a failure result |
| 502 | `-3904` | Member begin failed; request was not forwarded upstream |
| 502 | `-3905` | Upstream returned but member finish was not confirmed; check execution and billing before retrying |

## Manual clients

In Postman or another HTTP client, configure the service root and bearer key, then use the routes above. Prepare POST JSON according to the deployed contract. For `/openapi/v2/pdf/parse/upload`, choose a local PDF in the multipart `file` field. A Postman collection is not bundled in this repository.
