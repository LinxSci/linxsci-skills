# 发布指南

## 产物

- `linxsci-scholar-0.3.0.zip`：普通用户解压后运行安装器；包含完整 Skill 和用户指南，无需 pip。
- `linxsci_scholar_sdk-0.3.0-py3-none-any.whl`：CLI/SDK 及完整 Skill。安装后用 `linxsci scholar install-skill` 注册到助手。
- `linxsci_scholar_sdk-0.3.0.tar.gz`：源码发行包。
- `SHA256SUMS`：以上文件的 SHA-256。

本工具需要用户电脑提供 Python 3.9+，没有打包 Python 或生成签名原生安装程序。macOS/Windows 启动器尚需实际平台的人工双击验收。

0.3.0 的统一 CLI 入口为 `linxsci`，Scholar 命令为 `linxsci scholar <动作>`；Python 发行包仍为 `linxsci-scholar-sdk`，导入名仍为 `linxsci_scholar`，Skill 名称仍为 `linxsci-scholar`。发布说明和安装示例需分别使用对应名称。ZIP 安装通过包内脚本运行，不注册终端命令。

## 构建与验证

使用独立虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install build twine
python3 -m unittest discover -s tests -v
python3 tools/build_release.py
python3 -m twine check dist/*.whl dist/*.tar.gz
python3 tools/check_release.py dist
python3 tools/smoke_release.py dist
```

只生成 ZIP 可以运行 `python3 tools/build_release.py --bundle-only`。打包使用文件白名单，不包含用户配置、.env、缓存或已有安装标记。`service.json` 定义默认测试地址 `http://101.126.93.213:28888` 和线上地址选项。已有用户配置及环境变量优先于发行默认值。

在新虚拟环境中从 wheel 安装，避免仅验证 editable 安装：

```bash
python3 -m venv /tmp/scholar-install-check
/tmp/scholar-install-check/bin/python -m pip install --no-deps dist/linxsci_scholar_sdk-0.3.0-py3-none-any.whl
/tmp/scholar-install-check/bin/linxsci --version
/tmp/scholar-install-check/bin/linxsci --help
/tmp/scholar-install-check/bin/linxsci scholar --help
/tmp/scholar-install-check/bin/linxsci scholar install-skill --skills-dir /tmp/scholar-install-check/skills
```

再解压 ZIP 到临时目录，进入解压后的 `linxsci-scholar-0.3.0` 目录，执行：

```bash
python3 install.py --no-config --skills-dir /tmp/scholar-zip-check/skills
python3 /tmp/scholar-zip-check/skills/linxsci-scholar/scripts/cli.py scholar routes
```

帮助与路由检查不访问远程服务。`tools/smoke_release.py` 会进一步使用本机模拟服务验证安装、配置、搜索、SDK、更新和清除配置。真实配置与联调使用用户本机秘密管理或隐藏输入，不能将真实 Key 打包。

发布给已有用户时，说明两种更新方式：ZIP 用户解压新版后运行 `python3 install.py --update`；CLI/SDK 用户在原 Python 环境安装新版 wheel，再执行 `linxsci scholar install-skill --update` 更新助手副本。源码开发者拉取后重新执行 `python -m pip install -e .`。已有 Key 配置继续复用。

## 上线验收

源码和模拟测试通过后，发布方还需针对实际部署执行：连接检查、搜索、用真实返回 ID 阅读目录和章节，以及按需 PDF 上传/任务/结果。其余业务接口依照完整上游请求模型测试。没有通过真实验收的接口不要对外宣称已验证可用。

明确发布许可并在仓库添加适用的许可证及维护者信息；工程没有擅自选择许可证。当前构建可通过元数据检查，但这不代表许可已确定。

## 分发

普通用户优先提供 ZIP 和校验和，放在你们的下载页面或版本 Release，链接到普通用户指南。当前工程不自动上传、创建公共 Release 或发布到商店。

可另外发布 CLI/SDK 到 PyPI。先在 [TestPyPI](https://packaging.python.org/en/latest/guides/using-testpypi/) 验证上传流程，确认包名和发布权限，再正式发布。使用独立发行版本目录，避免上传旧产物：

```bash
python3 -m twine upload --repository testpypi dist/linxsci_scholar_sdk-0.3.0-py3-none-any.whl dist/linxsci_scholar_sdk-0.3.0.tar.gz
# 完成验收、账号准备并决定正式发布后：
python3 -m twine upload dist/linxsci_scholar_sdk-0.3.0-py3-none-any.whl dist/linxsci_scholar_sdk-0.3.0.tar.gz
```

凭据通过 Twine 支持的交互或安全凭据机制提供，不写入仓库。PyPI 发布完成后，用户才可以通过包名安装；当前不将该步骤当成已完成。参考 [官方 Python 打包教程](https://packaging.python.org/en/latest/tutorials/packaging-projects/) 和 [setuptools 包数据文档](https://setuptools.pypa.io/en/latest/userguide/datafiles.html)。
