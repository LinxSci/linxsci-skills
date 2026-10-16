# 测试环境验收与 Skill 调优

本地源码可以直接连接远程测试服务 `http://101.126.93.213:28888`。无需每次修改都先推送 Git 或重新生成安装包。Git 用于协作和记录版本；请求由你本地运行的脚本发往远程 Scholar。

需要分别验证：离线回归是否通过、真实接口是否能调用、助手是否能正确完成用户任务。离线测试使用模拟服务，不能证明远程服务可用；CLI 成功也不能证明助手的检索策略和回答质量合格。

## 1. 首次准备和连接测试服务

在源码根目录执行；已创建虚拟环境时不必再次创建：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -e .
linxsci --version
linxsci --help
linxsci scholar --help
linxsci scholar setup --base-url http://101.126.93.213:28888
```

Windows 激活使用 `.venv\Scripts\activate`，其余命令在对应 Python 环境中执行。Key 在向导中隐藏输入，不能发到聊天或写入 Git。`setup` 默认完成一次 `/meta` 连接检查；看到成功后，不必紧接着再运行 `doctor`。

版本与两级帮助命令不访问远程服务：确认版本为当前代码版本，根帮助包含 `scholar`，组帮助包含 `search`、`paper` 等动作。已有开发环境拉取新版代码后也需重新执行可编辑安装，才能注册新的命令入口。

如果安装提示找不到 setup.py/setup.cfg，通常是当前 pip 太旧；先执行上面的升级命令。用 `python3 -m pip --version` 确认它属于 `.venv`。指定解释器的正确格式为 `.venv/bin/python -m pip install -e .`，不要在 `-m` 后写 `python3`。

需要单独复查时运行 `linxsci scholar doctor --json`，确认 `ok` 为 true，且输出的 `base_url` 为测试地址。`doctor` 会实际调用接口，也受用量和计费策略约束。通过 `/meta` 不代表搜索、章节、上传等 action 都已经启用。

如果实际地址不对，运行 `linxsci scholar config` 检查环境变量覆盖状态。它不会显示 Key。`SCHOLAR_BASE_URL` 和 `SCHOLAR_OPENAPI_KEY` 优先于向导保存的设置；清除不需要的覆盖后再配置。

## 2. 先验证真实接口，再验证助手

第一次接入可用同一主题完成一条最小链路：

```bash
linxsci scholar search 'graph neural networks'
linxsci scholar paper '从搜索响应中选取的实际论文ID'
linxsci scholar paper '同一个实际论文ID' --resource toc
linxsci scholar paper '同一个实际论文ID' --resource sections --item-id '目录返回的实际章节ID'
```

替换中文占位参数后执行；不要直接把占位文本当作 ID。便捷命令需要带来源前缀的论文 ID（例如 `arxiv:` 或 `doi:`）。章节 ID 必须取自响应，不要用猜测的章节标题替代。

观察搜索是否返回真实论文、详情/目录能否读取、章节内容是否对应所选 ID。业务字段以当前部署的上游契约为准；遇到字段不明确时先保留原始响应，不编造解析字段或过滤参数。

发现错误时按原因处理，避免用反复重试掩盖问题：

| 现象 | 首先排查 |
| --- | --- |
| `-401` | Scholar Key 和环境变量覆盖 |
| `-3900` | 对应 action 未启用，请管理员配置并启用 |
| `-3901` | 每日调用限额 |
| `-3902` / `-3903` / `-3904` | 服务端配置、上游连接、member begin |
| `-3905` | 上游已返回但 finish 未确认，先核查执行与计费结果，不直接重复创建任务或上传 |
| CLI 成功，助手失败 | 助手是否读到正确 Skill、执行路径、命令参数和阅读策略 |

## 3. 确认助手使用的是最新本地版本

开发调优时可以不安装 Skill，直接在一个新对话中指定当前源码文件。把下面的路径替换成自己的绝对路径：

> 请读取 /你的仓库路径/skills/linxsci-scholar/SKILL.md，按它的说明执行本次任务，只调用该目录下 scripts/cli.py scholar。请搜索 graph neural networks，选出最多三篇相关论文，说明每篇与主题的关系，并提供实际返回的论文 ID 和来源。没有检索到的内容不要补写。

这种方式适合快速修改和复测，验证的是“按指定 Skill 执行”的效果。它不证明助手能自动发现或选择 Skill。

测试正式的安装和发现流程时，在当前开发虚拟环境里执行：

```bash
linxsci scholar install-skill
```

如果已经由本安装工具安装过，更新副本：

```bash
linxsci scholar install-skill --update
```

新对话中再用 `$linxsci-scholar` 提问。如果需要验证自动选择，不要在提示词中点名 Skill。检查助手工具记录中实际读取的 SKILL.md 和脚本绝对路径，避免测试到另一个目录里的同名旧副本。复制安装后，源码修改不会自动同步到副本，下一轮要先更新。不要同时安装多个会被扫描到的同名版本。

## 4. 固定的人工验收题

每轮使用相同模型与模型设置，分别开新对话，减少旧对话中已有结果的影响。对于“实际论文 ID”等参数，先从成功检索中固定一组作为样本；数据缺失时记录环境变化，不凭空替换为编造内容。

| 编号 | 提问样例 | 通过标准 |
| --- | --- | --- |
| A1 显式搜索 | 使用 $linxsci-scholar 搜索 graph neural networks，选三篇相关论文并给出 ID 和来源。 | 真正执行搜索；返回 ID/来源与工具响应一致；结果不足三篇时如实说明。 |
| A2 自动选择 | 帮我找 graph neural networks 的学术论文，说明相关性并提供来源。 | 在已安装 Skill 的新对话中选择本 Skill，并实际调用服务；只写背景知识不算检索成功。 |
| A3 按章节阅读 | 使用 $linxsci-scholar 阅读论文“实际ID”的方法部分，说明方法和依据。 | 先定位目录，使用真实章节 ID；答案可定位到返回内容。没有相关章节时说明缺失。 |
| A4 论文比较 | 使用 $linxsci-scholar 比较“实际ID一”和“实际ID二”的方法及实验结论，逐项列出来源。 | 读取两篇论文的相关证据；区分不同实验条件；没有证据的数值不补写。 |
| A5 证据不足 | 使用 $linxsci-scholar 核对论文“实际ID”是否报告了“待核对指标”的具体数值，给出原文依据。 | 找得到就引用实际章节；找不到就说明未发现，不把推断写成原文结果。 |
| A6 未定义参数 | 目前只有仓库这份接口文档，请按上游引用数过滤并搜索论文。 | 不擅自编造过滤字段；指出缺少契约，可先用已知 query 搜索，再对返回的实际字段做有说明的筛选。 |
| A7 故障解释 | 给定错误 HTTP 502、error.code=-3905，解释下一步怎么做；本题只分析错误，不调用接口。 | 说明执行与计费未确认，不声称任务未执行，不建议直接重复上传或创建任务。此题不产生服务请求。 |
| A8 PDF（按需） | 使用 $linxsci-scholar 解析 /实际路径/允许上传的样本.pdf。 | 创建任务后记录真实 task_id；不反复创建相同任务；按实际状态读取结果；未完成时不假装成功。 |

A8 会把文件发送到测试服务，只使用适合该测试的文件。真实调用按服务配置计量；先跑搜索/阅读，再按需测 PDF。A5 应固定一组经人工确认的“存在指标”和“不存在或证据不足指标”，分别核对准确性。

## 5. 如何判断好不好用

不要只看回答是否流畅。为每题记录下列证据，结果标为“通过 / 部分通过 / 失败”：

| 观察项 | 记录内容 |
| --- | --- |
| 任务完成 | 是否完成用户真正提出的检索、阅读或比较任务 |
| 调用正确 | 实际使用的源码/安装路径、接口及参数是否正确 |
| 证据准确 | ID、链接、章节、引用和数值能否回到真实响应核查 |
| 调用效率 | 接口请求次数、是否重复搜索/读全文/检查连接；结合工具记录或服务器日志统计 |
| 交互体验 | 完成耗时、是否需要人工纠正、缺失和错误解释是否清楚 |

记录模板，可复制到团队自己的测试记录中；包含真实响应的文件不要直接提交到公开仓库：

```text
日期 / 测试人：
源码 commit / 是否有未提交修改：
测试服务地址：
助手与模型设置：
实际 Skill 和脚本路径：
题号 / 原始提示词：
结果：通过 / 部分通过 / 失败
实际接口调用顺序 / 次数：
完成耗时：
选用论文 ID 与章节依据：
错误码 / 上游请求 ID / 框架请求 ID（如有）：
需要人工纠正的地方：
本轮改动与下轮要验证的问题：
```

不记录 Key、Authorization 或用户配置文件全文。先保存一轮基线，再改动和复测，避免只凭印象判断提升。

## 6. 按问题定位调优文件

| 问题 | 优先检查 |
| --- | --- |
| 不会选 Skill、流程不合适、答案缺来源、读取大量无关全文 | `skills/linxsci-scholar/SKILL.md` 的 description、工作流和证据要求，并结合模型的实际执行记录判断 |
| URL、编码、请求体、上传或错误解析有问题 | `skills/linxsci-scholar/scripts/scholar_client.py` |
| `linxsci` 下能力列表或命令转发有问题 | `skills/linxsci-scholar/scripts/cli.py` 的 `CAPABILITIES` 和分派逻辑；入口注册检查 `pyproject.toml` |
| 配置、命令参数或提示不易使用 | `skills/linxsci-scholar/scripts/scholar.py`、`scholar_config.py` |
| 测到旧代码或安装失败 | `scholar_install.py` 与助手实际读取路径 |
| 服务端 action、member、上游失败 | 服务端配置/服务日志，不能通过改提示词修复 |

每次围绕一个已观察到的问题做最小改动，复跑原失败题及相关正常题。改 Python 逻辑后运行 `python3 -m unittest discover -s tests -v`；只改 Skill 文字时优先复测真实助手行为，文字改了并不代表行为必然改善。

本地测试满意后再提交和推送 Git。需要交付安装包时，按发布指南重新构建并运行 `tools/check_release.py` 和 `tools/smoke_release.py`。无需每个调优回合都重新发版。
