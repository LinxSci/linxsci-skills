# 官网下载与文档接入说明

[English](WEBSITE_PUBLISHING.md)

本文用于将当前项目交付给官网前端和发布维护人员。当前项目提供安装包与 Markdown 文档；官网负责下载入口、文档网页和版本展示。本文依据 2026-10-20 提供的测试页更新接入位置，新增路径仍为开发建议，尚未部署。

测试入口：[OpenAPI 使用情况页面](http://101.126.93.213:3000/open-api?tab=usage)。通过测试站公开返回的入口和路由模块确认，前端使用 React、TypeScript、Vite 和 React Router，OpenAPI 页面为 `pages/OpenApiPage.tsx`，路由注册在 `AppRouter.tsx`。

现有页面支持 `guide`、`docs`、`billing`、`keys`、`usage`，通过 `tab` 查询参数切换；另有 `/open-api/docs` 完整 API 文档路由。Skill、CLI、SDK 应接入这一现有页面体系。

## 1. 官网提供三个使用入口

| 入口 | 面向用户 | 主分发与安装方式 | 使用文档来源 |
| --- | --- | --- | --- |
| Skill | 在支持本地 Skill 的 AI 助手中提问的用户 | 官方 GitHub 仓库完整 Skill；ZIP 作为直接下载 | [普通用户指南](USER_GUIDE.zh-CN.md) |
| CLI | 在终端调用接口的用户 | PyPI：`uv tool install linxsci` | [全接口 CLI 使用指南](CLI_GUIDE.zh-CN.md) |
| Python SDK | 在 Python 程序中集成接口的开发者 | PyPI：在项目环境执行 `python -m pip install linxsci` | [SDK 开发者指南](DEVELOPMENT.zh-CN.md) |

CLI 和 SDK 来自同一个 Python 包，包名是 `linxsci`，命令名为 `linxsci`，导入名为 `linxsci`。官网分别展示安装命令和对应文档；手动下载时共用同一份 wheel。`uv tool install` 为 CLI 创建独立环境，SDK 则安装到使用它的 Python 项目环境。Skill ZIP 包含自包含脚本及安装器，不注册终端命令。以上使用方式均需要 Python 3.9+。

官方 Skill 源码已上传至 [LinxSci/linxsci-skills](https://github.com/LinxSci/linxsci-skills)，官网可以展示该仓库链接。PyPI 首次发布仍在准备中，包名安装命令在发布及安装验收完成后启用；此前使用本地 wheel / ZIP 或源码安装。源码发行包 `.tar.gz` 可作为开发者的可选下载项。

## 2. 页面与文件路径建议

| 页面 | 建议路径 | 展示内容 |
| --- | --- | --- |
| 使用引导与下载入口 | `/open-api?tab=guide` | 三种使用方式、当前版本、uv / SDK 安装命令、GitHub Skill 入口及备用下载 |
| Skill 文档（新增） | `/open-api?tab=skill` | 下载解压、安装、Key 配置、助手提问、更新和排错 |
| CLI 文档（新增） | `/open-api?tab=cli` | 安装、配置、全部 34 个接口的命令与参数 |
| Python SDK 文档（新增） | `/open-api?tab=sdk` | 安装、配置、Python 示例、方法签名、全部 34 个接口的 SDK 调用 |
| API 文档（现有） | `/open-api?tab=docs`、`/open-api/docs` | 保留现有 API 文档，按 [原始接口文档](API.zh-CN.md) 核对内容 |
| 当前版本下载文件目录 | `/downloads/linxsci-skills/0.3.0/` | ZIP、wheel、源码包和该版本的校验和 |

官网页面应将 Markdown 渲染为可阅读的网页，保留目录、代码块、表格和可点击锚点。下载按钮指向实际安装文件，文档按钮打开对应文档页面。页面的实际实现使用官网已有技术栈，当前 Skill 工程不需要运行新的业务 API 服务来提供这些文件。

当前项目没有提供文档中提到的 Postman 集合文件。接入原始 API 文档时，补齐该集合后再展示下载链接，或在官网页面去掉未交付的集合链接。

## 3. 将文档调整为官网用户的安装流程

仓库文档保留源码开发方式。官网 CLI 首屏使用 uv，SDK 首屏使用项目依赖安装；“源码安装”和 wheel 手动下载放在后面。不要让普通用户先执行私有 Codeup 的 `git clone`。

PyPI 发布成功后，CLI 用户的主流程为：

```bash
uv tool install linxsci
linxsci --version
linxsci setup
linxsci search "graph neural networks"
```

CLI 升级使用 `uv tool upgrade linxsci`；PATH 未配置时使用 `uv tool update-shell` 后重新打开终端。已有 pipx 的用户可使用 `pipx install linxsci` 作为备选。相关行为以 [uv 官方工具指南](https://docs.astral.sh/uv/guides/tools/) 为准。

SDK 用户在自己的项目中创建并激活虚拟环境，然后执行 `python -m pip install linxsci`；已有 uv 项目可使用 `uv add linxsci`。不要将 `uv tool install` 当成 SDK 项目依赖安装。

`setup` 在本机隐藏输入用户已有的 LinxSci API Key，无需在官网文档页输入 Key。CLI / SDK 的安装命令使用包名 `linxsci`，例如 `pip install linxsci`。

CLI 页接着展示：

```bash
linxsci search "graph neural networks"
```

SDK 页接着展示可直接保存运行的 Python 示例：

```python
from linxsci import LinxSciClient

client = LinxSciClient()
response = client.search("graph neural networks")
print(response.json())
```

SDK 页可将源码专属的 `examples/research.py` 运行方式和维护者扩展章节移至“源码开发”栏目；从 PyPI 或 wheel 安装的用户不拥有源码示例目录。保留第 3.2 节中可自行保存的 Python 示例和第 6 节的全接口对照表。

Skill 页展示 [官方 GitHub 仓库](https://github.com/LinxSci/linxsci-skills) 和安装器命令 `npx skills add https://github.com/LinxSci/linxsci-skills --skill linxsci-skills`，保留 ZIP 安装流程作为备选。已安装本 CLI 的用户可执行现有的 `linxsci install-skill` 安装随包 Skill。使用说明以 [普通用户指南](USER_GUIDE.zh-CN.md) 为准；`SKILL.md` 是助手执行指令，不作为官网普通用户的安装指南。

官方仓库维护完整 `skills/linxsci-skills/`，GitHub 与 wheel 使用同一份 Skill 源文件，随发行版本记录兼容关系。官网应链接到 `https://github.com/LinxSci/linxsci-skills`，不使用账号首页代替安装源。

将仓库相对 Markdown 链接映射到官网页面，例如 `CLI_GUIDE.md` → `/open-api?tab=cli`、`DEVELOPMENT.md` → `/open-api?tab=sdk`、`USER_GUIDE.md` → `/open-api?tab=skill`。保留使用中的章节锚点；不对外展示不存在的本地文件或私有仓库链接。

## 4. 生成干净的发布文件

旧的 `dist/` 同时包含历史版本。每次面向官网下载时，为当前版本使用独立目录，重新构建，确保安装包中的文档与网站文档一致。

当前版本的构建与验证命令：

```bash
python -m pip install twine
uv build --no-sources --out-dir dist/website/linxsci-skills/0.3.0 --no-create-gitignore
python tools/build_release.py --bundle-only --output dist/website/linxsci-skills/0.3.0
python tools/check_release.py dist/website/linxsci-skills/0.3.0
python tools/smoke_release.py dist/website/linxsci-skills/0.3.0 --uv uv
```

执行后交付以下四个文件：

```text
dist/website/linxsci-skills/0.3.0/
  linxsci-skills-0.3.0.zip
  linxsci-0.3.0-py3-none-any.whl
  linxsci-0.3.0.tar.gz
  SHA256SUMS
```

构建前需要安装 uv。按 [发布指南](RELEASING.zh-CN.md) 将 wheel / sdist 发布到 PyPI；在官方 GitHub Skill 仓库同步对应版本。官网可另外托管这四个文件作为备用下载，或链接到同版本的 GitHub Release 附件。不要把整个开发目录、虚拟环境或用户配置文件上传到下载区。`dist/` 不受 Git 跟踪，推送源码不会自动上传 PyPI 或官网。

版本下载链接示例：`/downloads/linxsci-skills/0.3.0/linxsci-skills-0.3.0.zip`。实际部署后才会可访问。官网三个入口的版本、文件名、文档和校验和必须对应同一版本；已经对外发布的版本文件保持不变，有更新时发布新版本。

## 5. 发布前确认服务环境

正式 API 根地址已确认为 `https://linxsci.com`。`skills/linxsci-skills/service.json` 的默认地址和线上地址选项均使用该地址，客户端会自动补齐 `/openapi/v2`。官网的 Skill、CLI、SDK 使用示例统一指向正式服务。

默认地址变更后需重新构建安装包，旧的本地产物不能直接用于正式发布。已有用户保存的配置和环境变量优先于发行默认值，原先使用测试环境的用户通过 `setup --online` 切换，并检查 `LINXSCI_BASE_URL` 覆盖情况。测试环境保留在 [测试指南](TESTING.zh-CN.md) 中，通过 `--base-url` 显式选择。

现有自动化验证使用本机模拟服务，覆盖全部 34 个接口的调用链。真实服务还需用实际 Key 和业务参数完成对应接口联调。不要将模拟测试通过写成全部真实接口已验收。

## 6. 官网前端的具体接入任务

1. 在现有 `pages/OpenApiPage.tsx` 的使用引导中增加 Skill、CLI、Python SDK 三个入口，CLI 首屏为 uv 安装，SDK 首屏为项目依赖安装，Skill 首屏为官方 GitHub 与 ZIP。
2. 将 `skill`、`cli`、`sdk` 加入该页面的 `tab` 参数有效值、`TAB_ITEMS` 和内容渲染分支。当前未知 tab 会回到 `guide`，只加链接不会显示新文档。保留原有五个标签页及 `/open-api/docs` 路由的行为。
3. 复用官网的语言配置、页面样式和文档呈现方式，加载三份对应 Markdown，调整安装首屏和站内链接。可使用一个共享组件渲染这三类文档，组件具体位置以仓库结构为准。
4. 在 PyPI、官方 GitHub 与备用下载文件准备完成后，接入实际可访问的渠道；各渠道尚未上线时展示实际状态。
5. 从官网实际下载安装，分别验证 Skill 提问、CLI 检索、SDK 检索和文档导航；直接打开三个新 tab 链接并刷新，确认不会回到默认使用引导。

第一轮可人工上传文件并更新文档；流程稳定后，再将构建、验证、文件上传和官网文档同步接入现有发布流程。后续官网接入需要提供前端项目路径或仓库地址，以及网站当前的文档和静态文件托管方式。

## 7. 当前源码位置与待补充信息

测试站公开模块中的调试信息包含 `/root/suwei/AgentXiv/agentxiv/pages/OpenApiPage.tsx`。这是定位测试机项目目录的线索，不代表当前工作区已取得该目录的访问权限，也不能替代前端仓库地址。

已确定的 [LinxSci/linxsci-skills](https://github.com/LinxSci/linxsci-skills) 是 Skill、CLI 和 SDK 的源码仓库。官网前端的完整 Git 地址或可访问源码目录仍需提供，才能实现三个文档页面。

本文采用 PyPI + uv 主安装、官方 GitHub Skill 分发的路线，沿用现有包名、命令名及已实现的安装入口。下一步完成 PyPI 上传及安装验收，并取得官网前端源码接入三份使用文档和下载入口。
