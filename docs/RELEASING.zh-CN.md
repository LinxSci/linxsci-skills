# 维护者构建与发布指南

[English](RELEASING.md)

本文说明源码构建、安装产物验证及包上传操作。用户安装与使用方法见 [README](../README.zh-CN.md)。

## 版本与安装产物

同步 `pyproject.toml`、SDK `__version__`、CLI `VERSION` 和安装标记中的版本号。每个版本使用独立输出目录，已发布的版本文件保持不变。

| 文件 | 内容 |
| --- | --- |
| `linxsci-skills-0.3.0.zip` | 独立安装器、完整 Skill 及中英文用户文档 |
| `linxsci-0.3.0-py3-none-any.whl` | CLI、Python SDK 与完整 Skill |
| `linxsci-0.3.0.tar.gz` | 源码、测试、构建工具与维护者文档 |
| `SHA256SUMS` | 安装产物的 SHA-256 校验和 |

构建后端为 setuptools，需要 Python 3.9+，运行时没有第三方依赖。Skill 脚本无需安装 SDK 即可执行。

## 构建与验证

在已配置构建工具的 Python 环境中执行：

```bash
python -m pip install build twine
python -m unittest discover -s tests -v
python tools/build_release.py --output dist/0.3.0
python tools/check_release.py dist/0.3.0
python tools/smoke_release.py dist/0.3.0
```

本机已安装 uv 时，可在冒烟命令后追加 `--uv uv`，验证隔离的 CLI 工具安装。检查使用本地模拟 API 和临时配置，无需正式 API Key。校验和、元数据和文件检查覆盖 wheel、源码包及 ZIP；冒烟测试从全新环境安装，调用全部 34 条便捷接口，并检查 Skill 安装/更新、SDK 调用和本地响应筛选。桌面启动器可在对应系统中验证。

`python tools/build_release.py --bundle-only --output dist/0.3.0` 仅构建独立 ZIP 和校验和。ZIP 只包含 README、用户/API/CLI/SDK 指南、安装器及完整 Skill；维护者和测试指南保留在源码仓库及源码包中。用户配置、凭据、缓存和已有安装标记不进入 ZIP。ZIP 中的 Markdown 链接应均能在包内访问。

回归测试与助手行为检查见 [测试指南](TESTING.zh-CN.md)。真实接口联调应显式选择服务根地址并准备合适的测试数据。

## 上传 Python 包

使用维护者的发布凭据，将验证后的 wheel 与源码包上传到指定注册表；ZIP 作为独立下载文件。例如，本机已安装 uv 并配置 `UV_PUBLISH_TOKEN` 时：

```bash
uv publish dist/0.3.0/linxsci-0.3.0-py3-none-any.whl dist/0.3.0/linxsci-0.3.0.tar.gz
```

Token 使用本机秘密管理或 CI 凭据机制保存。发布凭据与用户调用 LinxSci 的 API Key 分开管理。上传后从对应注册表验证安装。

## 源码与文档一致性

wheel 与独立安装包使用同一份 `skills/linxsci-skills/` 源码。两种语言文档、命令示例与包版本保持一致。`.github/workflows/ci.yml` 在支持的 Python/系统组合中运行测试、构建产物并验证安装。
