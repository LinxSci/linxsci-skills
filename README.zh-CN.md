# linxsci-skills

[English](README.md)

让 AI 助手帮你搜索学术论文、阅读相关章节、查询引用，并解析你指定的 PDF。

你需要一个已有的 LinxSci API Key，以及能够执行本地 Python 脚本的 AI 助手。运行环境需要 **Python 3.9+**；本工具不需要额外 Python 运行依赖。

## 命令和 Skill 如何命名

| 层级 | 当前名称或用法 |
| --- | --- |
| PyPI 安装包名 | `linxsci` |
| 终端命令名 | `linxsci`，例如 `linxsci search "graph neural networks"` |
| Python 导入名 | `linxsci`，例如 `from linxsci import LinxSciClient` |
| AI Skill 名称 | `linxsci-skills`，在助手中使用 `$linxsci-skills` |

当前论文相关动作直接使用 `linxsci <动作>`，例如 `linxsci setup`、`linxsci search`、`linxsci paper`。单独执行 `linxsci` 显示帮助。未来新增能力可注册独立命令组，例如 `linxsci patents search`；这是命名示例，当前只提供 LinxSci API 能力。

本文统一使用表中的新名称。配置变量使用 `LINXSCI_*`；旧版本升级后请重新运行 `linxsci setup`；安装过旧名称包的开发者先按 [名称迁移说明](docs/DEVELOPMENT.zh-CN.md#14-从旧名称迁移) 更新，避免两个包共用同一终端入口。新增能力的开发步骤见 [开发者指南](docs/DEVELOPMENT.zh-CN.md#91-新增其他-skill-的命名与入口)。

## 对外发布路线

通过 **PyPI 发布 CLI / SDK，通过官方 GitHub 仓库维护和分发 Skill**。源码已上传至 [LinxSci/linxsci-skills](https://github.com/LinxSci/linxsci-skills)，PyPI 首次发布仍在准备中。以下包名安装命令仅在 PyPI 发布成功后适用；发布前可使用本地 wheel、ZIP 或源码安装。

CLI 的推荐安装与使用方式：

```bash
uv tool install linxsci
linxsci setup
linxsci search "graph neural networks"
```

升级使用 `uv tool upgrade linxsci`；找不到命令时按 [uv 官方工具指南](https://docs.astral.sh/uv/guides/tools/) 使用 `uv tool update-shell`，然后重新打开终端。SDK 用户应在自己的 Python 项目环境中执行 `python -m pip install linxsci`；`uv tool install` 的隔离环境不会把 SDK 安装到当前 Python 项目。

Skill 官方仓库为 [LinxSci/linxsci-skills](https://github.com/LinxSci/linxsci-skills)，可使用支持 GitHub Skill 的安装器：

```bash
npx skills add https://github.com/LinxSci/linxsci-skills --skill linxsci-skills
```

该方式需要 Node.js / npx，按提示选择目标助手和安装范围。已安装本 CLI 的用户也可以运行 `linxsci install-skill` 安装随包携带的完整 Skill。安装后按 [普通用户指南](docs/USER_GUIDE.zh-CN.md) 配置 Key。官网接入步骤见 [官网接入说明](docs/WEBSITE_PUBLISHING.zh-CN.md) 与 [发布指南](docs/RELEASING.zh-CN.md)。

## 普通用户：安装、配置、提问

1. 下载发布方提供的 `linxsci-skills-0.3.0.zip`，解压。
2. macOS 双击 `Install.command`；Windows 双击 `Install.bat`。也可以在解压目录运行 `python3 install.py`（Windows 用 `py -3 install.py`）。
3. 在向导中确认服务地址，输入你的 API Key。输入时 Key 不会显示。向导保存配置并检查连接。
4. 在助手中输入：

> 使用 $linxsci-skills 搜索图神经网络相关论文，阅读方法章节，比较主要方法并附上来源。

默认使用正式服务 **https://linxsci.com**，无需在用户电脑部署 LinxSci。已有本地配置或环境变量优先于默认值，升级不会自动替换用户保存的测试地址。切换正式服务可运行 `linxsci setup --online`；ZIP 用户在解压目录运行 `python3 skills/linxsci-skills/scripts/cli.py setup --online`。测试环境配置见 [测试指南](docs/TESTING.zh-CN.md)。

安装器默认将 Skill 放到 `~/.agents/skills/linxsci-skills`，见 [官方本地 Skill 说明](https://learn.chatgpt.com/docs/build-skills)。客户端未发现 Skill 时重启助手；其他加载位置可通过 `--skills-dir` 指定。旧版客户端使用 `~/.codex/skills` 时，也可显式指定该目录。

ZIP 安装后即可在助手中使用 Skill；安装器不注册终端的 `linxsci` 命令。需要该命令时，按下面的 wheel 或源码安装流程操作。完整操作步骤、更新和故障处理见 [普通用户指南](docs/USER_GUIDE.zh-CN.md)。本项目不包含 AI 助手或 LinxSci 服务器，也不负责注册账号或发放 Key。

## 已安装 CLI 的用户

当前发布文件可本地安装；尚未上传到 PyPI。安装 wheel 后执行：

```bash
linxsci install-skill
linxsci setup --base-url https://linxsci.com
linxsci search 'graph neural networks'
```

`linxsci setup` 一次保存配置，后续 CLI、SDK 和本地 Skill 共用。不需要每次 export 环境变量。`linxsci config` 查看配置状态，不显示 Key；`linxsci config --clear` 清除保存的地址和 Key。更新包后运行 `linxsci install-skill --update` 更新助手使用的脚本，旧 Skill 保留备份。

逐个接口的完整命令、请求文件、ID 编码及 PDF 上传方式见 [全部 34 个接口的 CLI 使用指南](docs/CLI_GUIDE.zh-CN.md)。

## 从本地源码开始测试

在项目根目录执行。首次创建环境并安装开发版；已有 `.venv` 时可跳过创建：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -e .

linxsci --version
linxsci setup --base-url http://101.126.93.213:28888
```

Windows 激活命令为 `.venv\Scripts\activate`。统一使用同一个虚拟环境，不要混用 `.venv` 和 `.venv-1`。旧 pip 可能提示找不到 setup.py/setup.cfg，先执行上述升级命令；指定解释器安装时使用 `.venv/bin/python -m pip install -e .`，不要写成 `python -m python3 -m pip ...`。

从旧名称的开发版本更新时，先按 [名称迁移说明](docs/DEVELOPMENT.zh-CN.md#14-从旧名称迁移) 卸载旧包，再安装当前源码。用 `linxsci --version` 和 `linxsci --help` 确认入口。旧版本改名后需运行 `linxsci setup` 保存配置；`linxsci install-skill --update` 更新本工具管理的同名 Skill 并备份。

按向导输入已有 API Key，输入时不会显示。`setup` 会检查一次连接，成功后即可检索；之后需要单独检查连接时运行 `linxsci doctor --json`，确认 `ok` 为 true 且 `base_url` 是测试服务地址。检查连接也会实际调用接口，无需反复执行。

## 论文检索和阅读示例

以下命令在已经激活虚拟环境、完成 Key 配置后执行。CLI 会输出服务返回的数据，整理和比较论文可以交给安装了 Skill 的助手。

### 1. 按英文或中文主题检索

```bash
linxsci search "graph neural networks"
linxsci search "大语言模型智能体"
```

将引号中的文字替换为自己的研究主题。检查返回论文的标题、摘要和主题是否相关，记录实际返回的论文 ID；未检索到结果时不应编造论文。

### 2. 保存搜索结果

```bash
linxsci --output search.json search "graph neural networks"
```

响应原始内容保存到当前目录的 `search.json`，可用编辑器打开核查。`--output` 是全局选项，放在 `linxsci` 之后、`search` 或 `paper` 等具体动作之前。

### 3. 查看论文详情、目录和相关章节

先从搜索响应选择一篇论文，再从其目录选择章节。下列中文占位参数必须替换为真实返回值后执行：

```bash
linxsci paper "实际论文ID"
linxsci paper "实际论文ID" --resource toc
linxsci paper "实际论文ID" --resource sections --item-id "实际章节ID"
```

论文 ID 保留 `local:`、`arxiv:`、`openalex:`、`s2:` 或 `doi:` 来源前缀，不要用论文标题代替 ID。便捷命令接收未编码的 ID，并负责 URL 编码；章节 ID 必须来自接口响应，不能根据章节名称猜测。

测试通过的标准是：详情对应所选论文，目录能定位真实章节，读取的章节内容与所选 ID 一致。不要仅凭接口未报错就判断内容正确。

## 在助手中测试 Skill

源码安装只提供 CLI/SDK。需要通过 `$linxsci-skills` 使用时，再安装 Skill；首次执行：

```bash
linxsci install-skill
```

已由本工具安装过，或修改源码后要同步到安装副本，执行：

```bash
linxsci install-skill --update
```

在支持本地 Skill 和脚本执行的助手中新建对话，分别尝试：

**检索与筛选**

> 使用 $linxsci-skills 检索图神经网络相关论文，选择最多三篇最相关的，说明相关性，并附实际返回的论文 ID 和来源。结果不足三篇时请如实说明。

**按章节阅读**

> 使用 $linxsci-skills 阅读论文“实际论文ID”，先查看目录，再读取方法相关章节，解释主要方法，并标明章节依据。

**比较两篇论文**

> 使用 $linxsci-skills 比较论文“实际论文ID一”和“实际论文ID二”的方法和实验结论，逐项列出来源。未找到证据的数据请明确说明，不要补写。

将提示中的论文 ID 替换为实际检索结果。检查助手是否真正调用服务、引用是否能对应响应、数值是否有章节证据，以及是否存在重复检索或无目的读取全文。

开发时也可在新对话中直接指定当前仓库 `skills/linxsci-skills/SKILL.md` 的绝对路径，要求助手读取该文件并执行同目录下的脚本，从而直接测试当前源码。复制安装的 Skill 不会随源码自动更新，修改后要先同步，避免误测旧版本。

## 测试样例与验收重点

| 测试样例 | 验收重点 |
| --- | --- |
| 英文、中文关键词检索 | 执行真实搜索，返回相关论文；空结果如实说明 |
| 保存搜索结果 | `search.json` 存在，保留服务原始响应 |
| 论文详情与目录 | 使用真实且带来源前缀的 ID，内容与论文对应 |
| 读取指定章节 | 使用目录返回的实际章节 ID，证据能定位到正文 |
| 助手筛选和比较 | 有真实调用记录，论文来源和结论可核查，不编造数值 |

本地修改可直接连接测试环境验证，无需每次先 push Git 或重新打包。调优前后固定提示词和模型设置，记录结果准确性、调用次数、耗时以及需要人工纠正的地方。完整的 8 个验收场景、故障处理及记录模板见 [测试环境验收与 Skill 调优](docs/TESTING.zh-CN.md)。

## 能力与范围

已适配新版数字框架错误码、请求追踪和计费异常诊断。覆盖接口文档中的 34 条路由：服务信息和健康、论文搜索和标识解析、详情/内容/目录/章节/图表资源/引用、推荐、作者/机构/期刊、PDF 解析任务。全部 34 个接口均提供便捷命令，无需填写 HTTP 方法或接口路径；`request` 保留作通用调试入口。

| 接口分类 | 数量 | 调用入口 |
| --- | --- | --- |
| 服务信息与健康检查 | 4 | `meta`、`usage`、`health live/ready` |
| 论文搜索与解析 | 6 | `search`、`search-openalex`、`search-semantic-scholar`、`search-google-scholar`、`resolve`、`batch-get` |
| 论文详情与引用 | 11 | `paper`，搭配 `--resource` 和 `--item-id` |
| 论文推荐 | 2 | `recommend`、`mobile-cards` |
| 作者、机构与期刊 | 7 | `author`、`institution`、`venue`（可加 `--papers`）、`resolve-entities` |
| PDF 解析 | 4 | `parse-pdf`、`upload`、`task`（结果加 `--result`） |

只需调用指定接口时，可以直接使用便捷命令。例如：

```bash
linxsci mobile-cards
linxsci search-openalex "large language models"
```

四个搜索命令都直接接收检索词，可通过 `--body @文件.json` 添加契约中定义的其他参数。其他 JSON 请求文件需先按实际 Agent API 契约准备。便捷命令自动选择接口方法和路径；JSON 请求可通过 `--body @文件路径` 传入请求。PDF 上传为 multipart，使用 `linxsci upload /实际路径/paper.pdf`。在助手中也可直接提出“使用 $linxsci-skills 调用指定接口”，并提供接口路径及必要参数。

研究比较和总结由助手根据实际读取的内容完成。目前接口文档未定义多数 POST 的业务字段、分页和 PDF 状态模型；这些高级接口应按部署版本的上游契约使用，不能假定空 JSON 有效。所有路由可调用不代表每条接口都已有专用表单或经过真实生产验证。

## 开发与发布

- [SDK 开发者指南：安装、配置、方法签名与全部 34 个接口](docs/DEVELOPMENT.zh-CN.md)
- [CLI 使用指南：全部 34 个接口逐一调用](docs/CLI_GUIDE.zh-CN.md)
- [测试环境验收与 Skill 调优](docs/TESTING.zh-CN.md)
- [发布指南：构建、验证与分发](docs/RELEASING.zh-CN.md)
- [官网接入说明：下载入口、三类文档与发布文件](docs/WEBSITE_PUBLISHING.zh-CN.md)
- [Skill 指令](skills/linxsci-skills/SKILL.zh-CN.md)
- [原始接口文档](docs/API.zh-CN.md)

```bash
python3 -m unittest discover -s tests -v
python3 tools/build_release.py --bundle-only
```
