---
name: linxsci-base
description: Use LinxSci OpenAPI v2 directly for paper discovery and resources, citations, recommendations, research entities, PDF parsing, and API/CLI diagnostics. Provides supporting API guidance for task Skills; use the matching task Skill for end-to-end research and content creation.
---

# linxsci-base

[简体中文](SKILL.zh-CN.md)

Use `scripts/cli.py` from `linxsci-base`. Replace `<skill-dir>` with the absolute directory containing this file: `skills/linxsci-base/` in the source repository, or `~/.agents/skills/linxsci-base` after default installation. Scripts require only Python 3.9+ and its standard library; no SDK installation is needed. The separately installable CLI/SDK package and its Python import remain `linxsci`.

## Choose the task owner

For an end-to-end deliverable, load the matching available task Skill first: `linxsci-paper-qa` for single-paper factual questions, `linxsci-survey` for topic surveys, `linxsci-idea` for research ideas, `linxsci-reproduce` for reproduction, `linxsci-paper` for manuscript writing, `linxsci-ppt` for presentations, and `linxsci-xiaohongshu` for posts. That Skill owns the workflow and may use this Skill's API guidance for individual steps. A direct search, resource, PDF or diagnostic request remains a base operation.

Paper discovery is a prerequisite when the requested deliverable concerns a paper identified only by research clues. After identifying it, resume the requested task; PPT and post requests remain with their production Skill. Survey and Idea can start from a topic or research goal without a seed paper or a mandatory QA step. Reuse already verified identities and sufficient evidence instead of repeating discovery.

Use only Skills actually available in the current environment. If a needed extension is missing, report what is available and follow its existing installation instructions and the [extension discovery conventions](references/cli.md#discover-and-invoke-installed-skills). Reuse installation authorization already given in the session; otherwise obtain it before installing. Keep verified sources for continuation and do not claim a missing Skill ran. Base operations remain usable with this Skill alone; installing all extensions is not a prerequisite.

## Install the skill independently

This skill does not require the `linxsci` terminal command, the PyPI package, or an installed SDK. It runs its bundled Python scripts directly. You need Python 3.9+, an assistant with local skill discovery and script execution, and a LinxSci API key for service calls.

Sign in to the [LinxSci API key page](https://linxsci.com/open-api?tab=keys) to obtain an API key. Follow the installation and configuration steps below to enter it locally; you can reuse an existing valid key and configuration.

### Option 1: GitHub skill installer

If Node.js/npx is available, run:

```bash
npx skills add https://github.com/LinxSci/linxsci-skills --skill linxsci-base
```

Choose the assistant and installation scope in that installer's prompts. This installs the complete skill; it does not need `pip install linxsci` or `uv tool install linxsci`. Keep this copy updated with the same external installer.

### Option 2: Standalone ZIP or downloaded source

Extract `linxsci-base-<version>.zip`. In the extracted bundle, run `python3 install.py` (Windows: `py -3 install.py`), or double-click `Install.command` / `Install.bat`. The installer copies the complete skill and starts hidden-input key setup. No pip, SDK, or Node.js is required for this option. For installation only, run `python3 install.py --no-config`.

The ZIP's `install.py` accepts the following options (place them after `install.py`):

| Option | Default | Meaning |
| --- | --- | --- |
| `--skills-dir PATH` | `~/.agents/skills` | Assistant scan parent directory; `/linxsci-base` is appended |
| `--update` | Off | Update a managed existing copy and retain a backup |
| `--no-config` | Off | Copy the skill without starting key setup |
| `--online` | Off | Suggest the production root during setup |
| `--base-url URL` | Saved/release root | Suggest an explicit root during setup; takes precedence over `--online` |

`python3 install.py --help` shows installer help. `--online` and `--base-url` have no effect with `--no-config`. These flags belong to the ZIP installer; the standalone script uses `install-skill` for copying and a separate `setup` command for configuration.

If you downloaded the repository or only the complete skill folder, run the bundled script directly:

```bash
python3 /absolute/path/to/source/skills/linxsci-base/scripts/cli.py install-skill
```

The default destination is `~/.agents/skills/linxsci-base`. For an assistant with another scan directory, add `--skills-dir /absolute/path/to/assistant/skills` (the parent directory, without the final `linxsci-base`). Restart or refresh the assistant if discovery does not update.

### Configure and verify using only the skill

After default installation on macOS/Linux:

```bash
python3 "$HOME/.agents/skills/linxsci-base/scripts/cli.py" routes
python3 "$HOME/.agents/skills/linxsci-base/scripts/cli.py" setup
```

On Windows, invoke `py -3 "C:\absolute\path\to\linxsci-base\scripts\cli.py" setup`. For custom destinations, use the corresponding absolute script path. `routes` checks local execution without a key or network request. `setup` hides API key input, saves configuration, and performs one connection check. Then ask the assistant to use `$linxsci-base`. Setup requires an interactive terminal; never ask the user to put their key in chat.

To update a copy managed by the bundled installer, extract/download the new version and run **the new source's** `scripts/cli.py install-skill --update`, or the new ZIP's `python3 install.py --update --no-config`. Existing managed copies are backed up outside the scan directory. Manual or external-installer copies must be updated through their own installation method. Keep the complete `SKILL.md`, `scripts/`, `references/`, `agents/`, `service.json`, and supporting files together; copying `SKILL.md` alone cannot execute this skill.

For every action below, use the absolute `scripts/cli.py` path. The [command reference](references/cli.md) documents standalone invocation, all commands, parameter types, defaults, required inputs, and examples.

### Migrate an existing linxsci-skills installation

Run the **new source or installer** with `--update`. A managed `linxsci-skills` copy is backed up outside the assistant scan directory, then replaced by `linxsci-base`; a failed installation restores the old directory. Existing settings remain in `~/.config/linxsci-skills/config.json` (Windows: `%LOCALAPPDATA%\linxsci-skills\config.json`).

Without `--update`, an old installation is reported and no second copy is created. If both names exist, or a directory/installation marker is a symlink, unmanaged or mismatched, the installer stops without changing either copy. Use the original external installer to migrate its copies. For a manual installation, back it up and move it outside the scan directory before installing the new Skill. Refresh the assistant after migration.

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

`config` shows redacted settings. Clear configuration only when the user asks. `doctor` calls `/meta` and consumes a service call; reuse an existing successful connection check instead of probing repeatedly.

## Research workflow

```bash
python3 <skill-dir>/scripts/cli.py search "graph neural networks"
python3 <skill-dir>/scripts/cli.py paper "<returned-paper-id>"
python3 <skill-dir>/scripts/cli.py paper "<returned-paper-id>" --resource toc
python3 <skill-dir>/scripts/cli.py paper "<returned-paper-id>" --resource sections --item-id "<returned-section-id>"
```

Use actual returned paper IDs with `local:`, `arxiv:`, `openalex:`, `s2:` or `doi:` prefixes. Convenience commands accept raw IDs, including DOI slashes, and encode them. Get section/asset IDs from responses. Read details and contents before relevant sections; fetch full content only when needed.

Summarize retrieved resources from content actually read. Cite returned paper IDs, links and section evidence. Distinguish abstract evidence from full text, report missing content and avoid invented numbers. There is no documented server-side ask, trends or automatic-review endpoint.

### Identify a paper from research clues

Use this flow when the user describes a specific study but has no title or identifier. A supplied paper ID, DOI/arXiv identifier, title, local material or sufficient existing evidence can use its appropriate identification or reading path without restarting this discovery flow.

1. Use available web search to find candidates from distinctive experimental or methodological clues. Verify the exact title, authors/version and DOI or other available identifier against a primary bibliographic source such as the publisher, PubMed/PMC or the paper repository. Search snippets and model recall are leads, not evidence for the study's results. If several candidates still fit, ask only for the distinction needed to identify the target. In retrieval benchmarks, do not request a hidden title or DOI.
2. When a LinxSci ID is needed, use the documented search routes with the verified title or identifier, inspect the actual response, and read paper details to check the match. If title search returns no match or unrelated records, try another supported route such as `search-openalex` with the verified title or DOI. Use returned, verified IDs; do not invent an ID or assume a route searches full text unless its contract says so.
3. If web search is unavailable or unproductive, use the documented LinxSci discovery routes. If those also make no progress, another available, permitted method may propose a candidate for this stage; verify it by the same standard, then resume the original task. Preserve budget, scope, authentication, quota and error stopping rules. A service failure is not an empty search result and does not justify repeated calls. If the candidate or ID remains unresolved, name that stage and its limitation.
4. For a single-paper factual question, pass the verified title, identifiers, source links, LinxSci `paper_id`, original question and any already-read evidence to the available `linxsci-paper-qa` Skill. It must inspect the passages, tables or captions supporting the answer before responding; a search hit, loaded Skill or successful command is not proof of reading. Reuse sufficient evidence without another request. If QA is unavailable, apply the missing-extension guidance above; direct base resource retrieval remains available, but do not claim QA completion or answer experimental facts from discovery snippets.

When asked to select relevant papers:

- Screen the received candidates by topic and the user's criteria, then compare abstracts for a small shortlist before choosing. Unless the user asks specifically for the service's top-ranked results, do not simply take the first N records. Use titles and one short summary field for screening; read full abstracts only for plausible candidates. Avoid loading both abstracts and summaries for every record.
- Treat `score`, when present, as a service ranking signal unless its meaning is documented. Do not present it as a relevance percentage or paper quality measure. Resolve ties using the requested topic and evidence; citation counts alone do not establish relevance.
- Retain actual source and pagination metadata separately. State the scope actually examined (for example, the first 20 results from the local index), whether more results remain, and whether selection is based on abstracts or full text. Fetch more results only when the current candidates are insufficient or the requested coverage warrants it, using the documented pagination contract. Explain each selection against the user's criteria and cite a returned source link; do not imply an exhaustive literature review.

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

## Keep tool output small

Use the default compact JSON and structured errors; `--pretty` / `--human-errors` are for terminal reading. Once the actual schema is known, use global `--select <JSON-Pointer>`, `--fields <literal,keys>` and `--limit <N>` before the action to keep only screening fields such as actual paper IDs, titles and source links. These flags only shape the local response and do not change server pagination or requests. Do not assume a `data.items` path or field aliases; derive them from the actual contract or a saved response. If metadata such as pagination is needed, retain it separately when selecting an array. Null and false values carry information and are preserved.

For an unfamiliar saved response, inspect root keys, the result-array location, and record keys locally before projecting fields. A small Python standard-library inspection can report keys/counts without printing record values; one sample's keys need not be present in every row. A field error's `details` identifies the selected path, zero-based `item_index` when applicable, and missing/available fields for the first failing record. Correct the local view and reuse `read-output`. If a view spills again, reduce fields or shortlist size rather than repeating it unchanged or disabling the limit by default. Read only relevant metadata fields; an opaque pagination cursor need not appear in the answer or screening output.

For repeated uniform records, `--table` encodes `columns` once and returns `rows`. Get full paper content or individual sections only when needed. Endpoint output larger than 12000 characters is automatically saved as complete original bytes in a private temporary file; read the returned absolute `file` selectively using `scripts/cli.py --select <actual-pointer> --fields <actual,keys> read-output <absolute-file>`, without another API call. `truncated:true` and `preview` do not constitute full evidence. Binary assets also return file metadata. Temporary files remain available until removed. For an explicit destination use `--output /absolute/path/response.json --output-summary`. `--max-output-chars 0` disables automatic spilling for JSON/text when full output is necessary. See [all output options](references/cli.md#compact-output-and-explicit-response-views).

A `response_output_error` with `request_completed:true` and `do_not_repeat:true` means the API call succeeded but local formatting/saving failed; inspect its preserved raw response file and fix the view locally. Do not repeat task creation or upload for a formatting failure. Preserve public error codes, trace IDs, Retry-After and `execution_uncertain`, especially `-3905`.

## Output and failures

Endpoint stdout defaults to compact JSON or file metadata. Global `--output` preserves response bytes, including binary assets. Exit codes: 0 success, 1 HTTP/network failure, 2 argument/local-file failure. Errors default to structured JSON; `--json-errors` remains a compatibility flag for these diagnostics without exposing the full upstream error message. Structured HTTP/network diagnostics expose `error_code`, `request_id`, `framework_request_id`, and `execution_uncertain`.

Upstream responses and business errors keep their original format. Framework errors use `code/data/error/extra`; `extra.cost` is elapsed seconds, not a charge. Do not assume common list fields or PDF terminal states.

| Error code | Action |
| --- | --- |
| `-401` / `-404` | Check client key / method and path |
| `-3900` | Ask an administrator to enable the registered action; avoid repeated retries |
| `-3901` | Wait for daily quota reset or administrative action |
| `-3902` | Ask the administrator to configure the upstream URL/key |
| `-3903` | Inspect upstream connectivity; failure does not prove the operation did not execute |
| `-3904` | Request preparation failed before forwarding; contact the administrator |
| `-3905` | Upstream returned but accounting completion is unconfirmed; check execution and billing before retrying writes |

Do not treat all 502/503 errors identically. No automatic retries are performed. Preserve `Retry-After`, but it does not resolve `-3905` uncertainty. Expected call quantity is 1; upstream 2xx means actual 1, otherwise 0, with reserved-credit release confirmed by the service. Do not guarantee release based solely on HTTP failure. Avoid redundant search, diagnosis and polling. See [the API reference](references/api.md) for details.
