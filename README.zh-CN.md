# linxsci-skills

[English](README.md)

通过 LinxSci OpenAPI v2 检索学术论文、阅读章节与引用、查询学术实体并解析 PDF。本项目提供可独立运行的 AI Skill、CLI 和 Python SDK，覆盖文档中的全部 34 条接口。

需要 **Python 3.9+** 和 LinxSci API Key。使用 Skill 时，助手还需支持本地脚本执行。Python 运行时无需第三方依赖。

| 组件 | 名称 |
| --- | --- |
| 项目与 AI Skill | `linxsci-skills`，通过 `$linxsci-skills` 使用 |
| CLI / SDK Python 安装包 | `linxsci` |
| 终端命令 | `linxsci` |
| Python 导入 | `from linxsci import LinxSciClient, LinxSciError` |

## 安装 Skill

Skill 直接运行随附脚本，选择一种安装方式即可。

本机有 Node.js / npx 且使用兼容的 Skill 安装器时：

```bash
npx skills add https://github.com/LinxSci/linxsci-skills --skill linxsci-skills
```

也可以下载并解压 [仓库源码](https://github.com/LinxSci/linxsci-skills)，或独立的 `linxsci-skills-0.3.0.zip` 安装包，在解压目录执行：

```bash
python3 install.py
```

Windows 使用 `py -3 install.py`。独立安装包还包含 `Install.command` 和 `Install.bat`。安装器默认复制到 `~/.agents/skills/linxsci-skills`，随后通过隐藏输入配置 Key。其他助手位置可使用 `--skills-dir <安装父目录>`。详见 [独立安装与安装器参数](skills/linxsci-skills/SKILL.zh-CN.md#独立安装-skill)。

> 使用 $linxsci-skills 搜索图神经网络相关论文，阅读方法章节，比较主要方法并附上来源。

## 安装 CLI 或 SDK

下载或克隆源码，在自己的 Python 环境中安装：

```bash
git clone https://github.com/LinxSci/linxsci-skills.git
cd linxsci-skills
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
linxsci setup
linxsci search "graph neural networks"
```

Windows 激活命令为 `.venv\Scripts\activate`。也可通过 `python -m pip install /path/to/linxsci-0.3.0-py3-none-any.whl` 安装本地 wheel。需要隔离的 CLI 环境时，可使用 `uv tool install /path/to/linxsci-0.3.0-py3-none-any.whl`；SDK 则需安装到应用实际使用的 Python 环境。

## 配置

默认服务根地址为 `https://linxsci.com`，不添加 `/openapi/v2`。在本机运行向导并隐藏输入 Key。环境变量优先于保存的配置，升级保留已保存的服务地址。

| 环境变量 | 用途 |
| --- | --- |
| `LINXSCI_BASE_URL` | 覆盖服务根地址 |
| `LINXSCI_OPENAPI_KEY` | 覆盖客户端 API Key |
| `LINXSCI_CONFIG_FILE` | 指定配置文件路径 |
| `LINXSCI_MINERU_API_KEY` | 可选的 PDF 解析 Key |

macOS/Linux 配置路径为 `~/.config/linxsci-skills/config.json`，Windows 为 `%LOCALAPPDATA%\linxsci-skills\config.json`。`linxsci config` 查看状态而不展示 Key；`linxsci doctor --json` 调用 `/meta` 检查连接，计入正常接口调用；`linxsci config --clear` 清除保存的配置。

仅安装 Skill 时，将命令示例中的 `linxsci` 替换为 `python3 "/absolute/path/to/linxsci-skills/scripts/cli.py"`，Windows 使用 `py -3` 和实际路径。

## 检索、阅读与解析

```bash
linxsci search "graph neural networks"
linxsci paper "<returned-paper-id>"
linxsci paper "<returned-paper-id>" --resource toc
linxsci paper "<returned-paper-id>" --resource sections --item-id "<returned-section-id>"
linxsci upload /absolute/path/paper.pdf
linxsci task "<returned-task-id>"
linxsci task "<returned-task-id>" --result
```

论文 ID 来自真实检索结果，章节 ID 来自目录。全部 34 条接口均有便捷命令，`request` 提供通用入口。POST 字段、分页及 PDF 任务状态应按对应接口的契约使用。

```python
from linxsci import LinxSciClient

client = LinxSciClient()
print(client.search("graph neural networks").json())
```

## 输出与更新

接口及错误默认输出紧凑 JSON，人工阅读可使用 `--pretty` 或 `--human-errors`。全局 `--select`、`--fields`、`--limit` 按真实模型精简本地响应，`--table` 合并重复字段。超过 12000 输出字符的大响应和二进制内容保存到私有临时文件并返回 JSON 引用；`read-output` 可在本地筛选这些文件。`--output PATH --output-summary` 将原始字节保存到指定位置并输出文件元信息。详见 [全部输出选项](docs/CLI_GUIDE.zh-CN.md#紧凑输出与显式响应筛选)。

使用新版源码或 wheel 更新 Python 包。本工具管理的 Skill 副本可在更新后的包中执行 `linxsci install-skill --update`，或在新源码/安装包目录运行 `python3 install.py --update --no-config`。旧副本备份到助手扫描目录之外；外部工具安装的副本应使用原工具更新。

## 文档

- [Skill 用户指南](docs/USER_GUIDE.zh-CN.md)
- [CLI 命令与参数](docs/CLI_GUIDE.zh-CN.md)
- [Python SDK 指南](docs/DEVELOPMENT.zh-CN.md)
- [API 参考与错误处理](docs/API.zh-CN.md)
- [Skill 指令](skills/linxsci-skills/SKILL.zh-CN.md)

各指南均可切换至英文版。
