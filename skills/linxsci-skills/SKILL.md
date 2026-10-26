---
name: linxsci-skills
description: Use LinxSci OpenAPI v2 for academic paper search, content and citations, recommendations, research entities, PDF parsing, and explicit API health or usage queries.
---

# linxsci-skills

[简体中文](SKILL.zh-CN.md)

Use `scripts/cli.py` from this skill. Replace `<skill-dir>` with the absolute directory containing this file. Scripts require only Python 3.9+ and its standard library; no SDK installation is needed.

## Install the skill independently

This skill does not require the `linxsci` terminal command, the PyPI package, or an installed SDK. It runs its bundled Python scripts directly. You need Python 3.9+, an assistant with local skill discovery and script execution, and a LinxSci API key for service calls.

### Option 1: GitHub skill installer

If Node.js/npx is available, run:

```bash
npx skills add https://github.com/LinxSci/linxsci-skills --skill linxsci-skills
```

Choose the assistant and installation scope in that installer's prompts. This installs the complete skill; it does not need `pip install linxsci` or `uv tool install linxsci`. Keep this copy updated with the same external installer.

### Option 2: Standalone ZIP or downloaded source

Extract `linxsci-skills-0.3.0.zip`. In the extracted bundle, run `python3 install.py` (Windows: `py -3 install.py`), or double-click `Install.command` / `Install.bat`. The installer copies the complete skill and starts hidden-input key setup. No pip, SDK, or Node.js is required for this option. For installation only, run `python3 install.py --no-config`.

The ZIP's `install.py` accepts the following options (place them after `install.py`):

| Option | Default | Meaning |
| --- | --- | --- |
| `--skills-dir PATH` | `~/.agents/skills` | Assistant scan parent directory; `/linxsci-skills` is appended |
| `--update` | Off | Update a managed existing copy and retain a backup |
| `--no-config` | Off | Copy the skill without starting key setup |
| `--online` | Off | Suggest the production root during setup |
| `--base-url URL` | Saved/release root | Suggest an explicit root during setup; takes precedence over `--online` |

`python3 install.py --help` shows installer help. `--online` and `--base-url` have no effect with `--no-config`. These flags belong to the ZIP installer; the standalone script uses `install-skill` for copying and a separate `setup` command for configuration.

If you downloaded the repository or only the complete skill folder, run the bundled script directly:

```bash
python3 /absolute/path/to/source/skills/linxsci-skills/scripts/cli.py install-skill
```

The default destination is `~/.agents/skills/linxsci-skills`. For an assistant with another scan directory, add `--skills-dir /absolute/path/to/assistant/skills` (the parent directory, without the final `linxsci-skills`). Restart or refresh the assistant if discovery does not update.

### Configure and verify using only the skill

After default installation on macOS/Linux:

```bash
python3 "$HOME/.agents/skills/linxsci-skills/scripts/cli.py" routes
python3 "$HOME/.agents/skills/linxsci-skills/scripts/cli.py" setup
```

On Windows, invoke `py -3 "C:\absolute\path\to\linxsci-skills\scripts\cli.py" setup`. For custom destinations, use the corresponding absolute script path. `routes` checks local execution without a key or network request. `setup` hides API key input, saves configuration, and performs one connection check. Then ask the assistant to use `$linxsci-skills`. Setup requires an interactive terminal; never ask the user to put their key in chat.

To update a copy managed by the bundled installer, extract/download the new version and run **the new source's** `scripts/cli.py install-skill --update`, or the new ZIP's `python3 install.py --update --no-config`. Existing managed copies are backed up outside the scan directory. Manual or external-installer copies must be updated through their own installation method. Keep the complete `SKILL.md`, `scripts/`, `references/`, `agents/`, `service.json`, and supporting files together; copying `SKILL.md` alone cannot execute this skill.

For every action below, use the absolute `scripts/cli.py` path. The [command reference](references/cli.md) documents standalone invocation, all commands, parameter types, defaults, required inputs, and examples.

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

Stdout contains JSON or the raw response. Global `--output` preserves response bytes, including binary assets. Exit codes: 0 success, 1 HTTP/network failure, 2 argument/local-file failure. `--json-errors` produces structured diagnostics without exposing the full upstream error message. Structured HTTP/network diagnostics expose `error_code`, `request_id`, `framework_request_id`, and `execution_uncertain`.

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
