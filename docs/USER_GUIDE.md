# 普通用户指南

## 首次准备

准备你的 Scholar API Key，安装 Python 3.9 或更新版本，并使用一个支持本地 Skill 和脚本执行的 AI 助手。普通网页聊天并不一定支持读取你电脑上的 Skill。

本包默认使用测试服务 `http://101.126.93.213:28888`，无需在你的电脑部署 Scholar。使用其他环境时在向导中修改地址；线上服务填写 `https://linxsci.com`。

## 安装与首次配置

官方分发路线为 GitHub 维护完整 Skill，ZIP 提供直接下载。官方 GitHub Skill 仓库的完整地址尚待确定，目前不要把账号首页或数据集仓库作为安装源。

官方仓库上线后，可通过支持 GitHub Skill 的安装器安装。以下为命令模板，先把仓库地址替换为实际地址，再选择目标助手和安装范围：

```text
npx skills add "<官方 Skill 仓库完整地址>" --skill linxsci-scholar
```

该方式需要 Node.js / npx；具体参数见 [skills 安装器官方命令说明](https://github.com/vercel-labs/skills/blob/main/docs/commands.md)。安装来源应包含 `skills/linxsci-scholar/` 的完整脚本、参考资料和配置资源。只下载单个 `SKILL.md` 无法执行接口调用。

如果已安装本项目 CLI，也可使用现有命令安装同一版本随包携带的 Skill：

```bash
linxsci scholar install-skill
linxsci scholar setup
```

两种安装渠道按目标目录选择一种管理方式。`linxsci scholar install-skill --update` 只更新本工具托管的副本，外部安装器管理的 Skill 使用其对应更新方式。直接下载 ZIP 的完整流程如下。

下载发布方提供的 ZIP，完整解压，不要直接在压缩包中执行。macOS 双击 `Install.command`，Windows 双击 `Install.bat`。向导会安装 Skill，然后提示输入服务地址和 Key，并检查连接。

如果双击不运行，打开终端进入解压目录，执行：

```bash
# macOS / Linux
python3 install.py

# Windows
py -3 install.py
```

地址不包含 `/openapi/v2`。Key 输入时不会显示，这是正常现象；粘贴后按回车。不要把 Key 发到聊天中。

看到“连接成功”后即可提问。如果服务暂时不可用，Skill 和配置仍已保存，修复服务后重新检查即可。安装器不要求安装 Python SDK，也不修改助手的其他设置。

在助手中使用的名称仍是 `$linxsci-scholar`。终端的统一 CLI 命令为 `linxsci scholar …`，需要单独安装 CLI/SDK Python 包后才可使用；ZIP 安装不会注册该命令。下面的 ZIP 操作直接运行包内脚本，无需安装 CLI。

## 在助手中提问

新建对话，输入以下任意请求：

> 使用 $linxsci-scholar 搜索 graph neural networks 的相关论文，筛选最相关的论文并说明筛选依据。

> 使用 $linxsci-scholar 阅读 arxiv:2301.07041，先查看目录，再解释与我的问题相关的章节。

> 使用 $linxsci-scholar 比较你刚才检索到的两篇论文的方法和实验结果，给出论文和章节来源。

> 使用 $linxsci-scholar 上传 /absolute/path/paper.pdf，查询解析任务，完成后读取结果。

PDF 路径替换成你的实际文件路径。上传会将该文件发送到你配置的 Scholar 服务。助手使用你提供的 Key 执行接口请求；用量以服务返回的信息为准。

也可以直接调用 OpenAPI 中的指定接口，例如：

> 使用 $linxsci-scholar 调用 GET /usage，查询我的接口用量。

> 使用 $linxsci-scholar 调用 GET /recommendations/mobile-cards，返回接口结果。

> 使用 $linxsci-scholar 调用 POST /entities:resolve，请求 JSON 读取我指定的 /实际路径/entities-request.json，返回结果即可。

本 Skill 接入文档中的全部 34 个接口，调用某个接口无需先完成论文检索或分析。POST 请求文件需按实际服务的业务参数要求准备；不要在请求文件中写入 API Key，认证自动读取本机配置。

需要在终端逐个调用接口时，查看 [全接口 CLI 使用指南](CLI_GUIDE.md)，其中也说明了 ZIP 用户如何运行包内脚本。

没有找到 Skill 时，重启助手并确认安装输出的路径。当前默认位置为 `~/.agents/skills`；可为需要其他位置的客户端指定 `python3 install.py --skills-dir /path/to/skills`。见 [官方 Skill 安装位置说明](https://learn.chatgpt.com/docs/build-skills)。不要把同一个 Skill 安装到多个会被同时扫描的位置。

## 修改设置、检查连接和清除 Key

在解压目录运行：

```bash
python3 skills/linxsci-scholar/scripts/cli.py scholar setup --base-url http://101.126.93.213:28888
python3 skills/linxsci-scholar/scripts/cli.py scholar setup --online
python3 skills/linxsci-scholar/scripts/cli.py scholar doctor
python3 skills/linxsci-scholar/scripts/cli.py scholar config
python3 skills/linxsci-scholar/scripts/cli.py scholar config --clear
```

以上操作按需选择一条执行。Windows 将命令开头的 `python3` 替换为 `py -3`。如果已通过 wheel 或源码安装 CLI，可把 `python3 skills/linxsci-scholar/scripts/cli.py scholar` 替换为 `linxsci scholar`，例如 `linxsci scholar config`。两种方式共用同一份配置。

也可让助手运行 `doctor`，它通过 `/meta` 检查连接，不上传论文，但同样受接口用量与计费策略约束，避免反复运行。修改配置时留空 Key 可保留原 Key；清除本地配置不会撤销服务端 Key。

macOS/Linux 的配置保存在 `~/.config/linxsci-scholar/config.json`，Windows 保存在 `%LOCALAPPDATA%\linxsci-scholar\config.json`。Key 保存在该文件中，macOS/Linux 文件权限限制为当前用户读写；本文件不是加密保险库，不要分享或提交它。Windows 使用用户配置目录，未自动配置额外文件 ACL。

如果以前设置过 `SCHOLAR_BASE_URL` 或 `SCHOLAR_OPENAPI_KEY` 环境变量，它们会优先于保存的配置。运行 `config` 可检查是否有环境变量覆盖，但不会显示 Key。

## 更新和卸载

下载新版本并解压，运行：

```bash
python3 install.py --update
```

更新保留配置，并将旧 Skill 备份到安装父目录相邻的 `linxsci-skill-backups`。如果旧目录是手动安装的，本工具会拒绝覆盖；先备份并移走旧目录，再安装。

卸载时删除安装输出的 `linxsci-scholar` 目录；需要移除保存的 Key 时运行 `config --clear`。SDK 是单独安装的，可用相同 Python 环境的 `python -m pip uninstall linxsci-scholar-sdk` 卸载。更新备份可按需自行删除。

## 遇到问题

| 提示 | 处理方法 |
| --- | --- |
| 找不到 Python | 安装 Python 3.9+；Windows 可使用 `py -3` |
| 找不到 `linxsci` 命令 | ZIP 用户使用上文的包内脚本；CLI 用户激活安装该包的虚拟环境，更新源码后重新执行 `python -m pip install -e .` |
| API Key 无效或过期 | 运行 `setup` 重新输入 Key |
| 账号无权调用 | 检查账号权限 |
| 连接失败 | 检查服务地址、端口、网络；本地模式需要启动服务 |
| 服务返回非 JSON 内容 | 确认填的是 API 服务根地址，排除登录页或网页代理 |
| `-3900` 接口未启用 | 联系管理员配置并启用 action 后再调用 |
| `-3901` 每日调用限额 | 等待额度恢复或联系管理员 |
| `-3902` 服务端上游未配置 | 联系服务端管理员 |
| `-3903` 上游连接失败 | 联系服务维护者检查连接 |
| `-3904` 调用开始失败 | 尚未转发上游，联系管理员检查 member 服务 |
| `-3905` 执行和计费结果未确认 | 先核查执行与计费结果，不要直接重复上传或创建任务 |
| Skill 已存在 | 工具安装的版本使用 `--update`；手动安装先备份 |

反馈问题时提供操作步骤、错误码、上游/代理请求 ID 和 Scholar 框架请求 ID（如果显示），不要提供 Key 或配置文件全文。两种 ID 用途不同。错误响应中的 `extra.cost` 是耗时（秒），不是扣费金额。
