---
name: linxsci-skills
description: Use LinxSci OpenAPI v2 for academic paper search, content and citations, recommendations, research entities, PDF parsing, and explicit API health or usage queries.
---

# linxsci-skills

[简体中文](SKILL.zh-CN.md)

Use `scripts/cli.py` from this skill. Replace `<skill-dir>` with the absolute directory containing this file. Scripts require only Python 3.9+ and its standard library; no SDK installation is needed.

## Choose the requested action

All 34 routes in [the API reference](references/api.md) have [convenience commands](references/cli.md). Follow the user's requested endpoint and parameters directly. A usage query does not require paper search; a recommendation request does not require section reading. Read the relevant contract when needed. `routes` lists supported methods and paths without network access.

```bash
python3 <skill-dir>/scripts/cli.py usage
python3 <skill-dir>/scripts/cli.py health ready
python3 <skill-dir>/scripts/cli.py search-openalex "large language models"
python3 <skill-dir>/scripts/cli.py recommend --body @recommendations.json
```

Prepare JSON files from the deployed Agent API contract or user-provided request data. The four search commands accept a positional query; optional `--body` adds fields without overriding it. Do not invent POST fields, filters, pagination or task states. `{}` is not a universally valid request. `meta` does not guarantee a complete schema. If required business parameters are missing, identify the missing contract or request data.

## Configuration

`LINXSCI_BASE_URL` and `LINXSCI_OPENAPI_KEY` override setup's saved configuration. The default service is `https://linxsci.com`; supply a root without `/openapi/v2`. Saved settings override release defaults and persist across upgrades.

Do not read or display keys, or ask users to send them in chat. If configuration is missing, have the user run setup locally with hidden key input:

```bash
python3 <skill-dir>/scripts/cli.py setup
python3 <skill-dir>/scripts/cli.py setup --online
```

The server's `AGENT_PUBLIC_API_KEY` is not a client key. `config` shows redacted settings. Clear configuration only when the user asks. `doctor` calls `/meta` and consumes a service call; reuse an existing successful connection check instead of probing repeatedly.

## Research workflow

```bash
python3 <skill-dir>/scripts/cli.py search "graph neural networks"
python3 <skill-dir>/scripts/cli.py paper "<returned-paper-id>"
python3 <skill-dir>/scripts/cli.py paper "<returned-paper-id>" --resource toc
python3 <skill-dir>/scripts/cli.py paper "<returned-paper-id>" --resource sections --item-id "<returned-section-id>"
```

Use actual returned paper IDs with `local:`, `arxiv:`, `openalex:`, `s2:` or `doi:` prefixes. Convenience commands accept raw IDs, including DOI slashes, and encode them. Get section/asset IDs from responses. Read details and contents before relevant sections; fetch full content only when needed.

Synthesize research answers from content actually read. Cite returned paper IDs, links and section evidence. Distinguish abstract evidence from full text, report missing content and avoid invented numbers. There is no documented server-side ask, trends or automatic-review endpoint.

## PDF and transport

```bash
python3 <skill-dir>/scripts/cli.py upload /absolute/path/paper.pdf
python3 <skill-dir>/scripts/cli.py task "<returned-task-id>"
python3 <skill-dir>/scripts/cli.py task "<returned-task-id>" --result
python3 <skill-dir>/scripts/cli.py --output /absolute/path/asset.bin paper "<returned-paper-id>" --resource assets --item-id "<returned-asset-id>"
```

Upload sends the local file to the configured service; perform it when the user requests parsing that file. Record the returned task ID, inspect actual statuses and fetch results after completion. Do not recreate tasks or poll indefinitely.

Global `--framework-request-id` goes before the action and sends `X-ANYTHINGRIGHT-REQ-ID` for framework `extra.request-id`. Endpoint `--request-id` sends the separate upstream/proxy `X-Request-ID`. Repeat `--param key=value` for query parameters and `--field key=value` for upload fields. Generic `request` paths are relative to `/openapi/v2` and require separately encoded dynamic segments, including DOI slashes.

When the upstream contract needs `X-MinerU-API-Key`, the user can set `LINXSCI_MINERU_API_KEY` locally. PDF create/upload/status/result commands and generic PDF requests read it.

## Output and failures

Stdout contains JSON or the raw response. Global `--output` preserves response bytes, including binary assets. Exit codes: 0 success, 1 HTTP/network failure, 2 argument/local-file failure. `--json-errors` produces structured diagnostics without exposing the full upstream error message. SDK responses preserve status, headers and body; errors expose `error_code`, `request_id`, `framework_request_id`, and `execution_uncertain`.

Upstream responses and business errors keep their original format. Framework errors use `code/data/error/extra`; `extra.cost` is elapsed seconds, not a charge. Do not assume common list fields or PDF terminal states.

| Error code | Action |
| --- | --- |
| `-401` / `-404` | Check client key / method and path |
| `-3900` | Ask an administrator to enable the registered action; avoid repeated retries |
| `-3901` | Wait for daily quota reset or administrative action |
| `-3902` | Ask the administrator to configure the upstream URL/key |
| `-3903` | Inspect upstream connectivity; failure does not prove the operation did not execute |
| `-3904` | Member begin failed before forwarding; administrator investigation is needed |
| `-3905` | Upstream returned but finish is unconfirmed; check execution and billing before retrying writes |

Do not treat all 502/503 errors identically. No automatic retries are performed. Preserve `Retry-After`, but it does not resolve `-3905` uncertainty. Expected call quantity is 1; upstream 2xx means actual 1, otherwise 0, with reserved-credit release confirmed by member finish. Do not guarantee release based solely on HTTP failure. Avoid redundant search, diagnosis and polling. See [the API reference](references/api.md) for details.
