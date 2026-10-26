# 发布指南

[English](RELEASING.md)

官网的下载入口、Skill / CLI / SDK 文档页面和文件交付方式见 [官网接入说明](WEBSITE_PUBLISHING.zh-CN.md)。

对外主渠道为 **PyPI 发布 CLI / SDK，官方 GitHub 分发 Skill，官网展示安装命令和三类文档**。源码已上传至 [LinxSci/linxsci-skills](https://github.com/LinxSci/linxsci-skills)，PyPI 首次发布仍在准备中。以下上传命令由具有发布权限的维护者在构建和验证完成后执行。

## 已具备的包配置

| 项目 | 当前配置 |
| --- | --- |
| PyPI 包名 | `linxsci` |
| Python 导入名 | `linxsci` |
| 主终端命令 | `linxsci <动作>`，例如 `linxsci setup`、`linxsci search` |
| 构建后端 | setuptools，`setuptools>=64` |
| Python 要求 | 3.9+ |
| 运行依赖 | 无，使用标准库 |
| Skill 资源 | `SKILL.md`、脚本、参考资料、`service.json`、助手元数据均进入 wheel |

现有 `pyproject.toml` 已提供标准包入口，无需为 uv 改名或新增另一套 CLI。版本号当前还需同步 `pyproject.toml`、SDK `__version__`、CLI `VERSION` 和安装标记中的版本；`tools/check_release.py` 会检查一致性。

## 产物

- `linxsci-skills-0.3.0.zip`：普通用户解压后运行安装器；包含完整 Skill 和用户指南，无需 pip。
- `linxsci-0.3.0-py3-none-any.whl`：CLI/SDK 及完整 Skill。安装后用 `linxsci install-skill` 注册到助手。
- `linxsci-0.3.0.tar.gz`：源码发行包。
- `SHA256SUMS`：以上文件的 SHA-256。

本工具需要用户电脑提供 Python 3.9+，没有打包 Python 或生成签名原生安装程序。macOS/Windows 启动器尚需实际平台的人工双击验收。

0.3.0 的 CLI 入口为 `linxsci <动作>`；Python 发行包为 `linxsci`，导入名为 `linxsci`，Skill 名称为 `linxsci-skills`。发布说明和安装示例需分别使用对应名称。ZIP 安装通过包内脚本运行，不注册终端命令。

## 构建与验证

使用独立虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install twine
python3 -m unittest discover -s tests -v
uv build --no-sources --out-dir dist/website/linxsci-skills/0.3.0 --no-create-gitignore
python3 tools/build_release.py --bundle-only --output dist/website/linxsci-skills/0.3.0
python3 tools/check_release.py dist/website/linxsci-skills/0.3.0
python3 tools/smoke_release.py dist/website/linxsci-skills/0.3.0 --uv uv
```

构建前按 [uv 官方安装说明](https://docs.astral.sh/uv/getting-started/installation/) 安装 uv。`--no-sources` 验证发布时不依赖本地来源覆盖，继续使用现有 setuptools 后端；本工程的实现资源来自包内文件配置。构建与上传参数见 [uv 包发布指南](https://docs.astral.sh/uv/guides/package/)。每个版本使用单独输出目录，避免将历史包一起上传。

需要沿用 Python 构建流程时，安装 `build twine` 后使用 `python3 tools/build_release.py --output dist/website/linxsci-skills/0.3.0`，其后执行相同检查。两种方式选择其一，不必反复构建覆盖已验收的产物。

ZIP 打包使用文件白名单，不包含用户配置、.env、缓存或已有安装标记。`service.json` 的默认地址和线上地址选项均为正式服务 `https://linxsci.com`。已有用户配置及环境变量优先于发行默认值，测试服务通过 `--base-url` 显式指定，见 [测试指南](TESTING.zh-CN.md)。

在新虚拟环境中从 wheel 安装，避免仅验证 editable 安装：

```bash
python3 -m venv /tmp/linxsci-install-check
/tmp/linxsci-install-check/bin/python -m pip install --no-deps dist/website/linxsci-skills/0.3.0/linxsci-0.3.0-py3-none-any.whl
/tmp/linxsci-install-check/bin/linxsci --version
/tmp/linxsci-install-check/bin/linxsci --help
/tmp/linxsci-install-check/bin/linxsci install-skill --skills-dir /tmp/linxsci-install-check/skills
```

再解压 ZIP 到临时目录，进入解压后的 `linxsci-skills-0.3.0` 目录，执行：

```bash
python3 install.py --no-config --skills-dir /tmp/linxsci-zip-check/skills
python3 /tmp/linxsci-zip-check/skills/linxsci-skills/scripts/cli.py routes
```

帮助与路由检查不访问远程服务。`tools/smoke_release.py` 会进一步使用本机模拟服务验证安装、配置、搜索、SDK、更新和清除配置。添加 `--uv uv` 时，也在临时工具和缓存目录中从本地 wheel 离线安装，测试全部 34 个接口、随包 Skill 安装与更新、工具卸载；不触碰用户原有的 uv 工具目录。真实配置与联调使用用户本机秘密管理或隐藏输入，不能将真实 Key 打包。

发布给已有用户时，安装过旧包名的用户先按 [名称迁移说明](DEVELOPMENT.zh-CN.md#14-从旧名称迁移) 卸载旧包再安装新包。后续同名版本更新：ZIP 用户解压新版后运行 `python3 install.py --update`；CLI/SDK 用户在原 Python 环境安装新版 wheel，再执行 `linxsci install-skill --update` 更新助手副本。源码开发者拉取后重新执行 `python -m pip install -e .`。同名版本更新保留配置；旧版本改名后需重新配置。

## 上线验收

源码和模拟测试通过后，发布方还需针对实际部署执行：连接检查、搜索、用真实返回 ID 阅读目录和章节，以及按需 PDF 上传/任务/结果。其余业务接口依照完整上游请求模型测试。没有通过真实验收的接口不要对外宣称已验证可用。

明确发布许可并在仓库添加适用的许可证及维护者信息；工程没有擅自选择许可证。当前构建可通过元数据检查，但这不代表许可已确定。

## 分发

### 1. 发布 Python 包到 PyPI

先确认包名及账号发布权限，本机发布通过 `UV_PUBLISH_TOKEN` 提供认证，GitHub CI 优先使用后文的 Trusted Publishing。PyPI token 与用户调用服务的 LinxSci API Key 不同，不写入仓库，也不在对话中提供。先用 [TestPyPI](https://packaging.python.org/en/latest/guides/using-testpypi/) 独立账号/凭据验收上传，再使用正式 PyPI 配置发布。

#### 本机配置：首次发布流程

1. 注册并登录 [PyPI](https://pypi.org/account/register/)，验证邮箱，在账号设置中启用 PyPI 要求的双因素认证（2FA）。GitHub 登录账号与 PyPI 发布账号分别管理。
2. 打开 [PyPI 账号设置](https://pypi.org/manage/account/)，在 API tokens 区域添加发布 Token，例如命名为 `linxsci-local-publish`。首次创建尚不存在的项目时使用账号范围 Token；如果项目已经存在，优先选择该项目范围，并确认自己具有发布权限。相关规则见 [PyPI Token 帮助](https://pypi.org/help/#apitoken)。
3. 在自己的终端进入本工程，按上文完成构建和验证，确认当前待发布文件及服务默认地址。
4. 在 macOS / Linux 的 Bash 或 Zsh 终端单独执行下面一行，然后粘贴完整 PyPI Token 并按回车，输入不会显示：

```bash
read -r -s UV_PUBLISH_TOKEN
```

Token 输入完成后，再单独执行：

```bash
export UV_PUBLISH_TOKEN
```

这会将 Token 仅配置到当前终端会话及其子进程。不要执行 `echo $UV_PUBLISH_TOKEN`，也不要将真实值写进 README、`.env`、Git、聊天或可复用的发布命令。

接下来选择下面的 TestPyPI 或正式 PyPI 上传命令；两个站点账号和 Token 独立，发布到不同站点前重新输入相应 Token。

```bash
uv publish --publish-url https://test.pypi.org/legacy/ dist/website/linxsci-skills/0.3.0/linxsci-0.3.0-py3-none-any.whl dist/website/linxsci-skills/0.3.0/linxsci-0.3.0.tar.gz
```

使用正式 PyPI 凭据并确定对外发布后，上传同一份已验收产物：

```bash
uv publish dist/website/linxsci-skills/0.3.0/linxsci-0.3.0-py3-none-any.whl dist/website/linxsci-skills/0.3.0/linxsci-0.3.0.tar.gz
```

上传结束后清除当前终端中的变量：

```bash
unset UV_PUBLISH_TOKEN
```

首发成功后，改用仅限 `linxsci` 项目的 Token，撤销首发时使用的临时账号范围 Token。已有项目的名称被其他账号使用时，不能仅靠配置 Token 获得该项目权限，需要项目维护者授权或选择可用包名。

命令只列出当前版本的 wheel 和 sdist，ZIP 不上传 PyPI。发布成功后，在新的工具环境验证 `uv tool install linxsci`，并在独立项目环境通过 `python -m pip install linxsci` 验证 SDK 导入和真实业务调用。只有通过注册表安装验证后，官网才将主安装流程标为已上线。

### 2. 官方 GitHub Skill 分发

在官方仓库 [LinxSci/linxsci-skills](https://github.com/LinxSci/linxsci-skills) 中维护完整 `skills/linxsci-skills/`，与构建 wheel 使用的 Skill 源文件保持一致。官网链接到该仓库及对应版本。

通用安装器命令：

```bash
npx skills add https://github.com/LinxSci/linxsci-skills --skill linxsci-skills
```

参考 [skills 安装器命令](https://github.com/vercel-labs/skills/blob/main/docs/commands.zh-CN.md)。直接 ZIP 下载和现有 `linxsci install-skill` 继续可用。两种安装器的管理标记不同，更新时使用最初安装该副本的工具；不要覆盖外部工具管理的安装。

### 3. 官网同步

同步同一版本的安装命令、三份使用文档、GitHub 链接及备用下载文件。官网的接入任务和已确认页面组件见 [官网接入说明](WEBSITE_PUBLISHING.zh-CN.md)。当前工程不会自动上传官网、创建公共 Release 或发布到 PyPI。

### 4. 后续接入 GitHub Actions

现有 `.github/workflows/ci.yml` 负责构建和验证，已包含 uv 工具安装验收，不执行发布。PyPI 首发完成后，可按 [uv 的 GitHub Actions 发布示例](https://docs.astral.sh/uv/guides/integration/github/#publishing-to-pypi) 配置 Trusted Publishing，将构建和发布任务分开，并在 PyPI 中登记精确的仓库、工作流和发布环境。

本机首发完成后，在 PyPI 的项目管理页面选择 **Publishing → Add a new publisher → GitHub**。按实际仓库和工作流填写：

| 字段 | 本项目应填写的内容 |
| --- | --- |
| PyPI 项目 | `linxsci` |
| GitHub owner | `LinxSci` |
| Repository name | `linxsci-skills` |
| Workflow filename | 实际发布工作流的文件名，例如计划创建的 `publish-pypi.yml`；不包含目录，且不能填写当前仅做测试的工作流代替发布流程 |
| Environment name | 可选；若发布任务使用 `pypi` 环境，这里与 GitHub 的环境名称保持一致 |

GitHub 发布任务应声明 `id-token: write`，在构建和验收通过后对同一份构建文件执行 `uv publish --trusted-publishing always ...`。其短期认证由 GitHub 与 PyPI 协作完成，无需在 GitHub Secrets 中保存长期 PyPI Token。字段匹配规则见 [PyPI Trusted Publisher 配置说明](https://docs.pypi.org/trusted-publishers/adding-a-publisher/)。

当前本地远端 `origin` 指向 Codeup，`github` 指向 `git@github.com:LinxSci/linxsci-skills.git`。完整工程已推送 GitHub；后续可在该仓库接入发布工作流。现阶段尚未新增自动上传工作流，也未创建版本 tag。
