---
name: linxsci-base
description: 直接使用 LinxSci OpenAPI v2 发现论文、获取论文资源与引用、查询推荐和学术实体、解析 PDF，以及诊断 API/CLI。为任务 Skill 提供基础接口指导；完整研究和内容制作由匹配的任务 Skill 负责。
---

# linxsci-base

[English](SKILL.md)

使用 `linxsci-base` 的统一入口 `scripts/cli.py`。所有示例中的 `<skill-dir>` 都替换为本文件所在目录的绝对路径：源码中为 `skills/linxsci-base/`，默认安装后为 `~/.agents/skills/linxsci-base`。脚本仅依赖 Python 3.9+ 标准库，无需安装 SDK。可单独安装的 CLI/SDK 包名及 Python 导入名仍为 `linxsci`。

## 确定主任务

用户需要完整交付物时，先读取当前可用的对应任务 Skill：单篇论文事实问答用 `linxsci-paper-qa`，主题综述用 `linxsci-survey`，研究构思用 `linxsci-idea`，代码复现用 `linxsci-reproduce`，论文写作用 `linxsci-paper`，演示文稿用 `linxsci-ppt`，小红书内容用 `linxsci-xiaohongshu`。该 Skill 负责主流程，可按子步骤查阅本 Skill 的基础接口说明。直接检索、资源读取、PDF 或诊断请求继续使用基础能力。

仅给研究线索、但交付物依赖某篇论文时，论文发现是前置阶段。确定论文后继续原任务；PPT 和图文请求仍由制作 Skill 主导。Survey 和 Idea 可从主题或研究目标开始，不默认要求种子论文或 Paper QA。已有核实身份和充分证据时直接复用，不重复发现。

只使用当前环境中实际可用的 Skill。缺少所需扩展时，说明实际可用能力，沿用该扩展已有安装说明及[扩展发现约定](references/cli.zh-CN.md#自动发现与调用扩展-skill)。会话中已有安装授权则复用，否则安装前取得授权。保留已核实来源供续接，不声称调用了未安装的 Skill。仅安装本 Skill 仍可执行基础操作，不要求同时安装全部扩展。

## 独立安装 Skill

本 Skill 不依赖终端的 `linxsci` 命令、PyPI 安装包或已安装的 SDK，直接运行随 Skill 提供的 Python 脚本。需要 Python 3.9+、支持本地 Skill 发现及脚本执行的 AI 助手；调用远程服务时还需要已有的 LinxSci API Key。

登录 [LinxSci API Key 管理页](https://linxsci.com/open-api?tab=keys) 获取 API Key。随后按下方安装与配置说明，在本机输入 Key；已有有效 Key 和配置可直接复用。

### 方式一：GitHub Skill 安装器

本机有 Node.js / npx 时运行：

```bash
npx skills add https://github.com/LinxSci/linxsci-skills --skill linxsci-base
```

按安装器提示选择助手及安装范围。此方式安装完整 Skill，不需要 `pip install linxsci` 或 `uv tool install linxsci`。后续使用同一个外部安装器更新该副本。

### 方式二：独立 ZIP 或下载源码

解压 `linxsci-base-<version>.zip`，在解压后的目录运行 `python3 install.py`（Windows 使用 `py -3 install.py`），也可双击 `Install.command` / `Install.bat`。安装器复制完整 Skill 并启动隐藏输入 Key 的配置向导。此方式不需要 pip、SDK 或 Node.js。只安装、不配置时运行 `python3 install.py --no-config`。

ZIP 内的 `install.py` 支持以下参数，均放在 `install.py` 之后：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--skills-dir PATH` | `~/.agents/skills` | 助手扫描父目录，安装器追加 `/linxsci-base` |
| `--update` | 关闭 | 更新本工具管理的已有副本并保留备份 |
| `--no-config` | 关闭 | 仅复制 Skill，不启动 Key 配置向导 |
| `--online` | 关闭 | 向导建议使用正式服务根地址 |
| `--base-url URL` | 保存/发行地址 | 明确指定向导建议的服务根地址，优先于 `--online` |

`python3 install.py --help` 可查看帮助。设置 `--no-config` 后，`--online` 和 `--base-url` 不再生效。这些是 ZIP 安装器参数；独立脚本使用 `install-skill` 完成复制，再单独使用 `setup` 配置。

如果下载的是仓库源码或完整 Skill 目录，可直接运行包内脚本：

```bash
python3 /absolute/path/to/source/skills/linxsci-base/scripts/cli.py install-skill
```

默认安装位置是 `~/.agents/skills/linxsci-base`。助手使用其他扫描目录时，加上 `--skills-dir /absolute/path/to/assistant/skills`，参数为安装父目录，不包含末尾的 `linxsci-base`。安装后未发现 Skill 时，刷新或重启助手。

### 仅使用 Skill 完成配置与验证

macOS / Linux 默认安装后：

```bash
python3 "$HOME/.agents/skills/linxsci-base/scripts/cli.py" routes
python3 "$HOME/.agents/skills/linxsci-base/scripts/cli.py" setup
```

Windows 使用 `py -3 "C:\absolute\path\to\linxsci-base\scripts\cli.py" setup`。自定义安装目录时使用对应的脚本绝对路径。`routes` 不需要 Key、不联网，可验证本地脚本能否运行；`setup` 在交互终端中隐藏输入 Key、保存配置，并检查一次连接。随后在助手中使用 `$linxsci-base`。不要让用户将 Key 发到对话中。

更新本工具管理的副本时，下载或解压新版，使用**新版本源码中的** `scripts/cli.py install-skill --update`，或在新 ZIP 内执行 `python3 install.py --update --no-config`。旧副本备份到助手扫描目录之外。手动复制或外部安装器管理的副本应按原安装方式更新。必须完整保留 `SKILL.md`、`scripts/`、`references/`、`agents/`、`service.json` 及其他配套文件；仅复制 `SKILL.md` 无法执行接口。

后续所有操作均使用 Skill 内 `scripts/cli.py` 的绝对路径。[命令参考](references/cli.zh-CN.md) 逐项说明独立调用方式、全部命令、参数类型、默认值、必填条件和示例。

### 从旧版 linxsci-skills 迁移

使用**新版源码或安装器**执行 `--update`。安装器核验自己管理的 `linxsci-skills` 后，将旧目录备份到助手扫描目录之外，再安装 `linxsci-base`；安装失败时恢复旧目录。配置继续使用 `~/.config/linxsci-skills/config.json`（Windows：`%LOCALAPPDATA%\linxsci-skills\config.json`）。

不带 `--update` 时发现旧版，会提示迁移并停止，不创建第二份副本。新旧目录并存、目录或安装标记是符号链接、缺少有效标记或标记不匹配时，安装器保留已有文件并停止。外部安装器管理的副本用原工具迁移；手动安装的副本先备份并移出扫描目录，再安装新版。迁移后刷新助手。

## 接口调用入口

本 Skill 可调用 [接口文档](references/api.zh-CN.md) 中的全部 34 个接口，覆盖服务信息与健康、各来源搜索和标识解析、论文详情与引用、推荐、作者/机构/期刊及 PDF 解析。全部接口都提供便捷命令，按 [命令速查](references/cli.zh-CN.md) 选择；`request` 保留作通用调试入口。

用户指定接口或操作时，按目标路由、参数和响应直接执行；例如查询用量不需要先检索论文，调用推荐接口不需要先走章节阅读流程。按任务需要读取接口文档，使用 `routes` 查看支持的方法与路径（不联网）。

```bash
python3 <skill-dir>/scripts/cli.py health ready
python3 <skill-dir>/scripts/cli.py usage
python3 <skill-dir>/scripts/cli.py search-openalex "large language models"
python3 <skill-dir>/scripts/cli.py recommend --body @recommendations.json
python3 <skill-dir>/scripts/cli.py resolve-entities --body @entities.json
```

四个搜索命令都直接接收检索词，可选 `--body` 提供附加 JSON 对象，检索词以位置参数为准。示例中的 JSON 文件须先按部署环境的 Agent API 契约或用户提供的参数准备。便捷命令自动选择方法和路径；JSON 请求使用 `--body @file.json`，PDF 上传接口 `/pdf/parse/upload` 使用 `upload /absolute/path/paper.pdf`，由脚本构造 multipart 的 `file` 字段。接口调用不要求助手额外完成综述或研究分析。

## 配置与发现

脚本优先读取环境变量 `LINXSCI_BASE_URL` 和 `LINXSCI_OPENAPI_KEY`，其次读取 `setup` 保存的用户本地配置。地址默认值是正式服务 `https://linxsci.com`，可显式配置其他部署地址；服务根地址不含 `/openapi/v2`。已有配置优先于发行默认值，升级不会自动切换用户保存的地址。不要读取、展示或让用户把 Key 发到对话。缺少配置时请用户在本机运行向导，Key 通过隐藏输入保存：

```bash
python3 <skill-dir>/scripts/cli.py setup
# 线上地址作为默认提示：
python3 <skill-dir>/scripts/cli.py setup --online
```

`config` 仅显示配置状态，`config --clear` 清除保存的配置；执行清除需来自用户请求。

```bash
python3 <skill-dir>/scripts/cli.py doctor
# 需要元信息正文时再调用：
python3 <skill-dir>/scripts/cli.py meta
python3 <skill-dir>/scripts/cli.py routes
```

首次接入可用 `doctor`（调用 `/meta`）验证连接；它也经过用量检查和计费流程，已有有效连接结果时不重复探测。根据 [接口文档](references/api.zh-CN.md) 核对目标路由；对于未定义的业务请求模型，读取部署环境的上游契约或用户提供的请求 JSON。`meta` 不保证返回完整 schema；缺少目标接口必需的业务参数时，说明需要补充的契约或请求 JSON，不猜测字段和分页，也不擅自改为其他接口任务。

## 文献工作流

```bash
python3 <skill-dir>/scripts/cli.py search 'graph neural networks'
python3 <skill-dir>/scripts/cli.py paper 'arxiv:2301.07041'
python3 <skill-dir>/scripts/cli.py paper 'arxiv:2301.07041' --resource toc
python3 <skill-dir>/scripts/cli.py paper 'arxiv:2301.07041' --resource sections --item-id '<returned-section-id>'
```

从搜索结果中取实际论文 ID；先看详情、目录，再读取相关章节，需要完整文本时才读 `--resource content`。论文 ID 需要 `local:`、`arxiv:`、`openalex:`、`s2:` 或 `doi:` 前缀。便捷命令接收未经编码的 ID（例如 `doi:10.1000/example`），随附脚本负责编码。章节和资源 ID 必须取自返回结果。

整理检索与阅读结果时依据实际读取的内容，附上实际返回的论文标识、链接和章节依据。区分摘要和全文证据，说明缺失内容；不要声称存在服务端 `ask`、趋势榜或自动综述接口。

### 从研究线索定位论文

用户描述了具体研究但没有题名或标识时，使用下面的流程。已有论文 ID、DOI/arXiv 标识、标题、本地材料或充分证据时，按对应身份核验或阅读路径处理，不强制重新走线索发现。

1. 用当前可用的网页搜索，根据独特的实验或方法线索发现候选。通过期刊官网、PubMed/PMC 或论文仓库等主要书目信息源核实准确题名、作者/版本及 DOI 等可用标识。搜索片段和模型记忆只作线索，不支撑研究结果。仍有多个合理候选时，只澄清确定目标所必需的区别；检索型基准不得索要隐藏题名或 DOI。
2. 需要 LinxSci ID 时，用已核实题名或标识调用文档化搜索路由，检查真实响应，并读取论文详情核对匹配。标题搜索无匹配或返回不相关记录时，尝试其他受支持路由，例如用已核实题名或 DOI 调用 `search-openalex`。使用实际返回并核实的 ID，不编造 ID；接口契约未说明时，不假定搜索覆盖全文。
3. 网页搜索不可用或无进展时，使用文档化 LinxSci 发现路由。仍无进展时，可仅针对该阶段用其他可用且获准的方法提出候选，按相同标准核验后回到原任务。继续遵守预算、范围、认证、限额及错误停止规则；服务失败不等于零结果，不能据此反复请求。候选或 ID 仍无法核实时，明确未完成阶段及限制。
4. 单篇事实问题将已核实题名、标识、来源链接、LinxSci `paper_id`、原问题及已读证据交给可用的 `linxsci-paper-qa`。它须实际检查支持答案的原文段落、表格或图注后回答；搜索命中、加载 Skill 或命令成功都不证明已阅读。证据充分时直接复用，不重复请求。QA 不可用时按上方缺扩展约定处理；基础资源仍可直接读取，但不能声称完成了 QA，也不能用发现阶段的搜索片段回答实验事实。

用户要求筛选相关论文时：

- 按主题和用户条件初筛已返回的候选，再比较少量候选的摘要后选择。除非用户明确要求接口排名前 N 篇，否则不要直接取前 N 条。初筛优先读取标题和一种简短概述字段，仅对合适候选读取完整摘要，避免对每条记录同时读取摘要与概述。
- 返回的 `score` 在没有定义说明时只作为接口排序信号，不解释为相关性百分比或论文质量。分数相同时，根据主题和证据比较；引用数本身不能证明相关性。
- 单独保留实际来源和分页元信息。说明实际检查的范围（例如本地索引首批 20 条）、是否还有后续结果，以及筛选依据是摘要还是全文。仅当候选不足或用户要求的覆盖范围需要时，按已知分页契约继续检索。每篇解释与用户条件对应的入选理由，并附实际返回的来源链接，不暗示已完成穷尽性文献检索。

## 其他接口与 PDF

全部接口优先使用 [便捷命令速查](references/cli.zh-CN.md)，无需填写 HTTP 方法和路径。各来源检索、推荐、实体和 PDF 创建任务也都有独立命令。

```bash
python3 <skill-dir>/scripts/cli.py resolve --body @resolve.json
python3 <skill-dir>/scripts/cli.py author '<returned-author-id>' --papers --param '<upstream-key>=<value>'
python3 <skill-dir>/scripts/cli.py upload /absolute/path/paper.pdf
python3 <skill-dir>/scripts/cli.py task '<returned-task-id>'
python3 <skill-dir>/scripts/cli.py task '<returned-task-id>' --result
python3 <skill-dir>/scripts/cli.py --output /absolute/path/asset.bin paper 'arxiv:2301.07041' --resource assets --item-id '<returned-asset-id>'
```

全局可选参数 `--framework-request-id <id>`（放在 `scripts/cli.py` 之后、具体动作之前）发送 `X-ANYTHINGRIGHT-REQ-ID`，对应 LinxSci 自身错误的 `extra.request-id`；各接口命令的 `--request-id <id>` 发送独立的 `X-Request-ID`。两者用途不同。通用 `request` 的路径相对于 `/openapi/v2`，每个动态 ID 独立 URL 编码（包括 DOI 中的斜杠）；查询参数用重复的 `--param key=value`。JSON 通过 `--body @file.json` 原样传入。`upload` 可传 `--field key=value`；上游契约需要 `X-MinerU-API-Key` 时，在本机设置 `LINXSCI_MINERU_API_KEY`，`parse-pdf`、`upload`、`task`（含 `--result`）及通用 PDF `request` 都会读取它。

上传会发送本地文件到配置服务，仅在用户请求解析该文件时执行。任务状态结构未定义，使用实际返回的标识和状态；不自动无限轮询或重复创建任务，确认完成后获取结果。

## 控制工具输出量

默认使用紧凑 JSON 和结构化错误，`--pretty` / `--human-errors` 仅用于人工终端阅读。确认真实响应模型后，可将全局 `--select <JSON-Pointer>`、`--fields <字面字段,列表>`、`--limit <N>` 放在动作之前，仅保留筛选所需的真实论文 ID、标题、来源链接等字段。这些选项只调整本地响应，不改变请求或服务端分页；不能猜测 `data.items` 路径或字段别名，应按实际契约或保存的响应选择。选择数组时如需分页等外层元信息，应另外保留。`null` 和 `false` 有语义，不会自动丢弃。

面对陌生的已保存响应，先在本地检查根字段、结果数组位置和记录字段，再投影筛选。可以用简短的 Python 标准库脚本只输出字段名和数量，不输出记录值；单条样本的字段不一定存在于所有记录。字段错误的 `details` 提供所选路径、适用时从 0 开始的 `item_index`，以及首条出错记录的缺失字段和可用字段。修正本地筛选并复用 `read-output`。筛选结果再次转存时，减少字段或候选数量，不原样重复读取，也不默认关闭限制。只读取所需元信息，不必把不透明分页游标输出到回答或候选列表中。

大量字段一致的记录可用 `--table`，仅声明一次 `columns` 并返回 `rows`。全文或具体章节按需获取。接口输出超过 12000 字符时自动将完整原始字节保存到私有临时文件，应通过 `scripts/cli.py --select <真实路径> --fields <真实,字段> read-output <文件绝对路径>` 按需读取，不再次调用 API。`truncated:true` 和 `preview` 不代表完整证据；二进制资源同样返回文件元信息。临时文件保留到读取后自行删除。指定路径时使用 `--output /absolute/path/response.json --output-summary`；确需完整 JSON/文本时可用 `--max-output-chars 0` 关闭自动转存。详见 [全部输出选项](references/cli.zh-CN.md#紧凑输出与显式响应筛选)。

`response_output_error` 配合 `request_completed:true`、`do_not_repeat:true` 表示接口已成功执行，仅本地格式化/保存失败，应读取保留的原始响应文件并在本地修正，不能为格式问题重复上传或创建任务。保留业务错误码、两种请求 ID、Retry-After 和 `execution_uncertain`，尤其不能丢失 `-3905` 的含义。

## 输出与故障

接口 stdout 默认输出紧凑 JSON 或文件元信息；`--output`（放在 `scripts/cli.py` 之后、具体动作之前）保留响应原始字节，适用于二进制资源。上游响应原样透传，LinxSci 自身错误则使用 `code/data/error/extra` 框架结构；读取 `error.code` 和 `extra.request-id`，不把它当作上游业务模型。`extra.cost` 是请求耗时（秒），不是扣费金额。不要假定列表字段或 PDF 终态。

退出码：0 成功，1 HTTP/网络错误，2 参数/本地文件错误。随附脚本的结构化 HTTP/网络诊断提供 `error_code`、`request_id`、`framework_request_id`、`execution_uncertain`。随附脚本默认输出紧凑的结构化 JSON 诊断，保留可用的两种请求 ID；`--json-errors` 是兼容选项，`--human-errors` 切换文本诊断，不展示服务端错误消息全文。

按 HTTP 状态和实际 `error.code` 区分故障：

| error.code | 处理 |
| --- | --- |
| `-401` / `-404` | 检查 LinxSci Key / 路径和方法 |
| `-3900` | action 已登记但未启用，联系管理员配置并启用；不要反复重试 |
| `-3901` | 每日调用限额已满，额度恢复后或管理员处理后再调用 |
| `-3902` | 服务端 Agent API 地址或 Key 缺失，联系管理员 |
| `-3903` | 上游连接/传输失败，检查连接；不要将失败等同于业务操作一定未执行 |
| `-3904` | 请求准备失败，未转发上游，联系管理员排查 |
| `-3905` | 上游已返回但计量完成尚未确认，先查询执行与计费结果，再决定是否重试，尤其不要直接重复上传或创建解析任务 |

上游业务错误（例如 `validation_error`、`asset_unavailable`）保留其原有格式；不要把全部 502/503 当作相同原因。脚本不自动重试；保留 `Retry-After`，但它不能替代 `-3905` 的执行/计费核查。

每次请求预计调用量为 1，Agent API 2xx 对应实际调用量 1，其他状态或连接失败对应 0，预占释放由 服务确认计量完成后确定。不要根据 HTTP 失败自行保证扣费已经释放，尤其遇到 `-3905`。避免无目的的重复检索、诊断与轮询；查询动作也走调用限额。详细规则见 [references/api.md](references/api.zh-CN.md)。
