# Testing and skill evaluation

[简体中文](TESTING.zh-CN.md)

## Local development and remote acceptance

Install the source in one virtual environment. Local source can call the remote test service directly; pushing Git or rebuilding a wheel is not required for each change.

```bash
python -m pip install -e .
linxsci setup --base-url http://101.126.93.213:28888
linxsci doctor --json
linxsci search "graph neural networks"
```

Enter your existing key through setup's hidden input. Verify the actual base URL and `ok` result. Environment settings override the saved URL/key; inspect `linxsci config` if the wrong service is used. Connection checks consume calls, so do not repeat them unnecessarily. The test address is an explicit development setting, not the release default.

Use returned IDs to verify paper details, table of contents, and a relevant section. A successful HTTP response alone does not establish correct content. For POST endpoints beyond search, use the deployment's actual business schema. Test PDF upload/status/result only when the task requires it, with a suitable sample file.

## Verify the skill version

For rapid evaluation, give the assistant the absolute path to this repository's `skills/linxsci-skills/SKILL.md` and ask it to run that directory's `scripts/cli.py`. This tests explicit use, not automatic discovery.

To test installed discovery, run `linxsci install-skill`, or `linxsci install-skill --update` for a managed existing copy. Open a new chat and invoke `$linxsci-skills`. For automatic selection, omit the skill name from the prompt. Inspect tool traces for the actual instruction and executable paths. Copied skills do not follow source changes automatically.

## Repeatable manual acceptance

Keep model settings and prompts fixed across runs. Use actual paper IDs established by a successful baseline search. Record changes in source data instead of inventing replacements.

| Case | Prompt or task | Pass criteria |
| --- | --- | --- |
| A1 Explicit search | Use $linxsci-skills to find three relevant graph neural network papers | Real search; returned IDs and sources match; report fewer results honestly |
| A2 Automatic selection | Find academic papers on graph neural networks and explain relevance | Installed skill is selected and the service is actually called |
| A3 Section reading | Explain the methods of an actual returned paper | Inspect contents, use returned section IDs, cite section evidence |
| A4 Comparison | Compare methods and experiments in two returned papers | Read both sources; distinguish experimental conditions; do not invent numbers |
| A5 Missing evidence | Verify whether a paper reports a specified metric | Quote actual evidence or report it was not found; test known-present and absent cases |
| A6 Undefined fields | Filter by upstream citation count using only this repository contract | Identify missing field definitions; do not invent request fields |
| A7 Uncertain execution | Explain HTTP 502 with error code -3905 without making a call | Check execution/accounting before repeating writes; do not claim nothing executed |
| A8 Optional PDF | Parse a user-designated sample PDF | Upload once, retain task ID, use actual task states, fetch completed result |

A8 sends the file to the configured service. Run it only for the requested sample. Requests follow the deployment's accounting rules.

## Record results

Record pass/partial/fail, source commit and local changes, date, tester, service URL, assistant/model settings, skill/script paths, prompt, call order/count, elapsed time, paper IDs, section evidence, error codes, both trace IDs, corrections and the next hypothesis. Do not record keys, Authorization headers or complete configuration files. Keep real response data out of public commits.

Evaluate task completion, correctness of calls, traceable evidence, redundant requests and interaction clarity. Save a baseline, change one observed issue, and rerun the failing case plus relevant successful cases.

| Problem | Inspect |
| --- | --- |
| Skill selection, reading strategy or missing citations | `SKILL.md` and actual assistant traces |
| URL encoding, transport, uploads or error parsing | `scripts/client.py` |
| Root command dispatch | `scripts/cli.py` and package entry points |
| Configuration or arguments | `scripts/config.py`, `scripts/commands.py` |
| Stale installation | `scripts/installer.py` and the assistant's executable path |
| Disabled actions, member or upstream failures | Server configuration and logs |

## Automated checks

```bash
python -m unittest discover -s tests -v
python tools/build_release.py --output /tmp/linxsci-release
python tools/check_release.py /tmp/linxsci-release
python tools/smoke_release.py /tmp/linxsci-release --uv uv
```

The route coverage tests compare all 34 documented routes, then call the standalone skill against a local mock service through convenience commands and generic requests. They check authentication, raw ID encoding, repeated parameters, JSON, multipart, PDF headers, and binary output. Release smoke tests use fresh wheel and ZIP installations; optional uv checks use isolated tool/bin/cache directories and uninstall the temporary tool afterward.

These checks validate transport and packaging, not live business fields, permissions, production data, or actual assistant behavior. Run the remote acceptance cases before claiming live deployment support. See [releasing](RELEASING.md).
