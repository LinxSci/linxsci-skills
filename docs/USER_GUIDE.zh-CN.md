# Skill 使用指南

[English](USER_GUIDE.md)

`linxsci-base` Skill 让你在 AI 助手中用自然语言检索、阅读和比较论文，也可以提交 PDF 解析任务。安装后，通过 `$linxsci-base` 指定使用这个 Skill。它直接运行随附的 Python 脚本，无需安装 `linxsci` CLI/SDK 包。

## 使用前准备

- Python 3.9 或更新版本。
- 支持本地 Skill 和工具执行的 AI 助手。
- LinxSci API Key：登录 [API Key 管理页](https://linxsci.com/open-api?tab=keys) 获取，在本机配置时输入；已有有效 Key 和配置可直接复用。

## 安装 Skill

### 包格式与扩展安装

下文 `install.py` 的步骤适用于旧基础安装器包。八个 Skill 的套件与 SDK/CLI `0.3.4` 分别管理版本。下表的 `<套件版本>` 以所选发行清单为准。

| 包 | 内容与用途 |
| --- | --- |
| 旧 `linxsci-base-0.3.4.zip` | 基础 Skill 及根目录的 `install.py`、`Install.command`、`Install.bat`，使用下方安装器步骤 |
| 平铺 `linxsci-base-skill-<套件版本>.zip` | 根目录为 `SKILL.md` 和 `scripts/` 等，没有根目录 `install.py` 或桌面启动器 |
| 七个 `linxsci-<扩展名>-<套件版本>.zip` | 解压后为完整单项扩展，分别放入以 Skill 名称命名的目录 |
| `linxsci-skills-<套件版本>-full.zip` | `skills/` 下八个真实目录、单项 ZIP 和 SDK wheel，按需安装所需 Skill |
| `linxsci-skills-<套件版本>-source.zip` | 包含测试与开发工具的固定源码快照；开发验证使用此快照或维护者完整源码 |

从 [LinxSci Releases](https://github.com/LinxSci/linxsci-skills/releases) 中实际存在的同一套件取得 `release-manifest.json`、`SHA256SUMS` 和所需资产。对照清单及校验和核对单项 ZIP 的身份、版本、大小与 SHA256；完整套件和源码快照的哈希在 `SHA256SUMS` 中。安全解压时拒绝越界路径或符号链接，再核对各 Skill 的 `release.json` 文件清单。这些元数据由构建生成，不是源码目录中必须存在的文件。不要把 SDK 的 `v0.3.4` 或仓库 latest 发行当成套件版本；也可使用同版本本地资产；清单或文件获取失败时，报告具体缺项。

在已核验的基础平铺包中，进入包含 `SKILL.md` 的目录，使用 Python 3.9+：

```bash
python3 scripts/cli.py install-skill --skills-dir "/absolute/path/to/assistant/skills"
```

将路径换成当前助手实际使用的 Skill 父目录；Windows 可将 `python3` 换成 `py -3`。该命令只复制基础 Skill，不配置 API Key，随后按下文配置。也可将完整内容复制到该父目录下的 `linxsci-base/` 中。替换前保留已有文件、本地修改与来源，完成后刷新助手发现。

七个扩展不在公开主仓库跟踪范围内，其 GitHub 自动 Source code ZIP 和主仓库 Skills CLI 命令都不能提供这些扩展。应获取单项 Release / 本地包，再按各自 README 准备 Python 依赖、发现路径与条件协作。单项包随附独立于 SDK 的共用安装器 `scripts/linxsci_release_install.py`，Idea 通过 `scripts/install_survey.py` 安装同套件 Survey。安装器只安装明确选择的目标，不升级 Python 环境或递归补装全部协作者。需要新取证时准备同一套件的 Survey，复用已有证据不强制安装它。完整套件不是第三方 Python 库、字体或外部工具的离线环境。单项包和完整套件目录均不包含 `tests/`。

### 方式一：下载安装包

下载 [完整 Skill 安装包](https://github.com/LinxSci/linxsci-skills/releases/download/v0.3.4/linxsci-base-0.3.4.zip)，完整解压后再操作。

**macOS**：在解压目录双击 `Install.command`。如果无法双击运行，打开终端，进入解压目录后执行：

```bash
python3 install.py
```

**Windows**：在解压目录双击 `Install.bat`，或在该目录打开终端执行：

```bat
py -3 install.py
```

**Linux**：在解压目录运行 `python3 install.py`。

安装器会复制 Skill，再引导你在本机隐藏输入 API Key，并检查一次连接。默认安装到 `~/.agents/skills/linxsci-base`。完成后刷新或重启助手，新建对话使用。

如果助手扫描其他位置，在安装时指定其 Skill 父目录：

```bash
python3 install.py --skills-dir /path/to/assistant/skills
```

`--skills-dir` 不包含末尾的 `linxsci-base`；安装器会自动追加目录名。只下载单个 `SKILL.md` 无法完成安装，请保留完整安装包内容。

### 方式二：使用 Skill 安装器

本机已有 Node.js / npx 时，也可运行：

```bash
npx skills add https://github.com/LinxSci/linxsci-skills --skill linxsci-base
```

按提示选择目标助手和安装范围。安装成功后刷新或重启助手，再按下方“配置与确认安装”完成设置。

如果停留在 `Cloning repository`，最终出现 `Clone timed out`，说明仓库下载超时；可以使用上面的 ZIP 安装方式。该方式无需克隆仓库。

### 安装选项

以下选项仅用于随安装包提供的 `install.py`，放在文件名之后：

| 选项 | 默认值 | 用途 |
| --- | --- | --- |
| `--skills-dir PATH` | `~/.agents/skills` | 指定助手扫描的 Skill 父目录 |
| `--update` | 关闭 | 更新此安装器管理的已有副本，并保留备份 |
| `--no-config` | 关闭 | 只安装，不启动 Key 配置向导 |
| `--online` | 关闭 | 配置时建议使用正式服务地址 |
| `--base-url URL` | 已保存或发行默认地址 | 配置时建议使用指定服务根地址，优先于 `--online` |

使用 `--no-config` 时，`--online` 和 `--base-url` 不生效。可用 `python3 install.py --help` 查看安装器帮助。Windows 将 `python3` 替换为 `py -3`。

## 配置与确认安装

旧基础 ZIP 安装器会引导配置。通过其他安装器安装，或安装时跳过配置的用户，可以在助手中输入：

> 使用 $linxsci-base 检查是否已配置。若缺少配置，请指导我在本机安全输入 API Key，不要让我将 Key 发到聊天中。

默认服务根地址为 `https://linxsci.com`，不包含 `/openapi/v2`。API Key 只在本机配置过程中输入，不粘贴到对话里。

配置完成后，可输入：

> 使用 $linxsci-base 检查一次服务连接，并告诉我是否可以开始检索论文。

连接检查会实际调用服务。安装时已经检查成功，就可以直接提问，无需重复检查。

设置默认保存在 macOS/Linux 的 `~/.config/linxsci-skills/config.json`，或 Windows 的 `%LOCALAPPDATA%\linxsci-skills\config.json`。如果助手运行环境已经设置 `LINXSCI_BASE_URL` 或 `LINXSCI_OPENAPI_KEY`，它们会优先于保存的设置；`LINXSCI_CONFIG_FILE` 可指定另一份配置。切换环境后仍连接到旧地址时，可让助手检查这些覆盖关系，但不要展示 Key。

## 在助手中使用

### 检索论文

> 使用 $linxsci-base 搜索 graph neural networks 相关论文，选择最相关的三篇，说明筛选理由并附上来源链接。

可以补充研究主题、筛选条件和期望的返回数量。助手会根据实际接口支持情况执行。

### 阅读论文

> 使用 $linxsci-base 阅读刚才找到的第一篇论文，先查看目录，再解释方法和实验章节，标明引用来源。

使用搜索结果中的实际论文 ID 或已有论文标识；不要把章节名称当成章节 ID。

### 比较论文

> 使用 $linxsci-base 比较刚才两篇论文的方法、实验设置和局限，用表格列出差异，并注明依据。

### 解析 PDF

> 使用 $linxsci-base 解析 /absolute/path/paper.pdf，记录任务 ID，确认完成后获取结果并总结主要结论。

将路径换成助手能够访问的实际 PDF 文件。解析会将文件上传到配置的服务。任务尚未完成时，让助手查看已有任务的状态，避免重复上传。

### 查看用量

> 使用 $linxsci-base 查看我的接口用量，简要说明结果。

### 控制返回内容

> 只返回三篇论文的标题、简短摘要和来源链接。详细内容需要时再读取。

> 将完整结果保存为文件，告诉我文件位置；在对话中只给出结论和引用。

可以直接说明语言、篇数、篇幅和呈现格式。助手负责检索和整理；较大的响应可能保存为本地文件，后续可以让助手读取相关部分。

## 更新 Skill

平铺基础包更新时，在已核验的新版解压目录使用 `python3 scripts/cli.py install-skill --update --skills-dir "/absolute/path/to/assistant/skills"`，Windows 可用 `py -3`；仅适用于该安装器管理的副本，不配置 API Key。手动副本先备份和保留修改，再替换完整目录；扩展按各自 README 更新。Release 副本不使用 `git pull`，本地目录 npx 安装不承诺远程自动更新。

**通过 ZIP 随附安装器安装**：下载并解压新版本，在**新版本解压目录**运行：

```bash
python3 install.py --update --no-config
```

Windows 使用 `py -3 install.py --update --no-config`。自定义安装目录时，加上安装时使用的 `--skills-dir PATH`。更新保留已有配置，并把旧托管副本备份到助手扫描目录之外。完成后刷新或重启助手。

**通过其他 Skill 安装器安装**：使用原安装器的更新功能。不要用另一种安装方式覆盖其管理的副本，也不要重复安装到会被同一助手同时扫描的多个位置。

需要修改设置时，可在助手中请求：

> 使用 $linxsci-base 指导我在本机更换服务地址或 API Key，不要在聊天中显示密钥。

### 从旧版 linxsci-skills 迁移

使用**新版源码或安装器**执行 `--update`。安装器核验自己管理的 `linxsci-skills` 后，将旧目录备份到助手扫描目录之外，再安装 `linxsci-base`；安装失败时恢复旧目录。配置继续使用 `~/.config/linxsci-skills/config.json`（Windows：`%LOCALAPPDATA%\linxsci-skills\config.json`）。

不带 `--update` 时发现旧版，会提示迁移并停止，不创建第二份副本。新旧目录并存、目录或安装标记是符号链接、缺少有效标记或标记不匹配时，安装器保留已有文件并停止。外部安装器管理的副本用原工具迁移；手动安装的副本先备份并移出扫描目录，再安装新版。迁移后刷新助手。

## 卸载 Skill

通过外部安装器安装的副本，使用其移除功能。通过随附安装器安装的副本，删除安装时输出的 `linxsci-base` 目录，然后刷新或重启助手。

如果还要删除本机保存的设置，请在卸载前让助手协助清除；清除本机设置不会撤销服务端 Key，也不会删除环境变量。

## 常见问题

| 情况 | 处理方式 |
| --- | --- |
| 下载仓库超时 | 使用本页的完整 Skill ZIP，解压后安装 |
| 找不到 Python | 安装 Python 3.9+；Windows 可使用 `py -3` |
| 助手找不到 Skill | 确认安装目录属于该助手的扫描范围，刷新或重启后新建对话 |
| 安装器提示已有副本 | 托管副本使用更新选项；其他安装器管理的副本用原工具更新 |
| API Key 无效 | 在本机重新配置 Key，并检查助手环境是否覆盖了保存的设置 |
| PDF 无法读取 | 确认文件存在，且助手有权访问该路径 |
| `-3900` | 当前接口未启用，联系服务管理员 |
| `-3905` | 执行与计费结果尚未确认，先核查已有任务及用量，不直接重复上传或创建任务 |
| 结果整理或保存失败 | 让助手检查已保存的响应，避免为了重新整理结果而再次提交原任务 |

反馈问题时提供操作步骤、错误码和请求追踪 ID，不提供 API Key 或配置文件全文。
