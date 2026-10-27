# Skill 使用指南

[English](USER_GUIDE.md)

LinxSci Skill 让你在 AI 助手中用自然语言检索、阅读和比较论文，也可以提交 PDF 解析任务。安装后，通过 `$linxsci-skills` 指定使用这个 Skill。

## 使用前准备

- Python 3.9 或更新版本。
- 支持本地 Skill 和工具执行的 AI 助手。
- 已有的 LinxSci API Key。

## 安装 Skill

### 方式一：下载安装包

下载 [完整 Skill 安装包](https://github.com/LinxSci/linxsci-skills/releases/download/v0.3.2/linxsci-skills-0.3.2.zip)，完整解压后再操作。

**macOS**：在解压目录双击 `Install.command`。如果无法双击运行，打开终端，进入解压目录后执行：

```bash
python3 install.py
```

**Windows**：在解压目录双击 `Install.bat`，或在该目录打开终端执行：

```bat
py -3 install.py
```

**Linux**：在解压目录运行 `python3 install.py`。

安装器会复制 Skill，再引导你在本机隐藏输入 API Key，并检查一次连接。默认安装到 `~/.agents/skills/linxsci-skills`。完成后刷新或重启助手，新建对话使用。

如果助手扫描其他位置，在安装时指定其 Skill 父目录：

```bash
python3 install.py --skills-dir /path/to/assistant/skills
```

`--skills-dir` 不包含末尾的 `linxsci-skills`；安装器会自动追加目录名。只下载单个 `SKILL.md` 无法完成安装，请保留完整安装包内容。

### 方式二：使用 Skill 安装器

本机已有 Node.js / npx 时，也可运行：

```bash
npx skills add https://github.com/LinxSci/linxsci-skills --skill linxsci-skills
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

ZIP 安装器会引导配置。通过其他安装器安装，或安装时跳过配置的用户，可以在助手中输入：

> 使用 $linxsci-skills 检查是否已配置。若缺少配置，请指导我在本机安全输入 API Key，不要让我将 Key 发到聊天中。

默认服务根地址为 `https://linxsci.com`，不包含 `/openapi/v2`。API Key 只在本机配置过程中输入，不粘贴到对话里。

配置完成后，可输入：

> 使用 $linxsci-skills 检查一次服务连接，并告诉我是否可以开始检索论文。

连接检查会实际调用服务。安装时已经检查成功，就可以直接提问，无需重复检查。

设置默认保存在 macOS/Linux 的 `~/.config/linxsci-skills/config.json`，或 Windows 的 `%LOCALAPPDATA%\linxsci-skills\config.json`。如果助手运行环境已经设置 `LINXSCI_BASE_URL` 或 `LINXSCI_OPENAPI_KEY`，它们会优先于保存的设置；`LINXSCI_CONFIG_FILE` 可指定另一份配置。切换环境后仍连接到旧地址时，可让助手检查这些覆盖关系，但不要展示 Key。

## 在助手中使用

### 检索论文

> 使用 $linxsci-skills 搜索 graph neural networks 相关论文，选择最相关的三篇，说明筛选理由并附上来源链接。

可以补充研究主题、筛选条件和期望的返回数量。助手会根据实际接口支持情况执行。

### 阅读论文

> 使用 $linxsci-skills 阅读刚才找到的第一篇论文，先查看目录，再解释方法和实验章节，标明引用来源。

使用搜索结果中的实际论文 ID 或已有论文标识；不要把章节名称当成章节 ID。

### 比较论文

> 使用 $linxsci-skills 比较刚才两篇论文的方法、实验设置和局限，用表格列出差异，并注明依据。

### 解析 PDF

> 使用 $linxsci-skills 解析 /absolute/path/paper.pdf，记录任务 ID，确认完成后获取结果并总结主要结论。

将路径换成助手能够访问的实际 PDF 文件。解析会将文件上传到配置的服务。任务尚未完成时，让助手查看已有任务的状态，避免重复上传。

### 查看用量

> 使用 $linxsci-skills 查看我的接口用量，简要说明结果。

### 控制返回内容

> 只返回三篇论文的标题、简短摘要和来源链接。详细内容需要时再读取。

> 将完整结果保存为文件，告诉我文件位置；在对话中只给出结论和引用。

可以直接说明语言、篇数、篇幅和呈现格式。助手负责检索和整理；较大的响应可能保存为本地文件，后续可以让助手读取相关部分。

## 更新 Skill

**通过 ZIP 随附安装器安装**：下载并解压新版本，在**新版本解压目录**运行：

```bash
python3 install.py --update --no-config
```

Windows 使用 `py -3 install.py --update --no-config`。自定义安装目录时，加上安装时使用的 `--skills-dir PATH`。更新保留已有配置，并把旧托管副本备份到助手扫描目录之外。完成后刷新或重启助手。

**通过其他 Skill 安装器安装**：使用原安装器的更新功能。不要用另一种安装方式覆盖其管理的副本，也不要重复安装到会被同一助手同时扫描的多个位置。

需要修改设置时，可在助手中请求：

> 使用 $linxsci-skills 指导我在本机更换服务地址或 API Key，不要在聊天中显示密钥。

## 卸载 Skill

通过外部安装器安装的副本，使用其移除功能。通过随附安装器安装的副本，删除安装时输出的 `linxsci-skills` 目录，然后刷新或重启助手。

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
