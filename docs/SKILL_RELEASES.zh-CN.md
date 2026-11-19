# 固定提交构建与发布 Skill 套件

[English](SKILL_RELEASES.md) · [本地开发](LOCAL_DEVELOPMENT.zh-CN.md)

构建器为维护者生成本地候选或正式发行文件，不提交或上传。独立发布入口默认只生成本地计划，显式参数才执行 GitHub 操作。七个扩展仍是主仓库忽略的独立仓库，不使用子模块。公开用户从 Release 资产获取实际文件，不需要私有仓库权限。

## 输入与版本

- 根目录 `extensions.lock.json`：七个扩展的完整提交 SHA。`branch` 仅作开发说明，构建不会跟随分支最新版本。
- `release/suite.json`：套件版本、各入口、Python/SDK 约束、功能依赖和协作条件。标签采用 `suite-v<套件版本>` 命名。本页以 `0.1.0-rc.1` 演示资产命名；实际构建使用配方指定的新版本和未使用的输出目录。
- `--base-commit`：主仓库完整 SHA；基础 Skill 从该提交的 `skills/linxsci-base/` 取得。工作区的暂存及未暂存修改不会进入包。
- `--sources`：私有 JSON 对象，八个键分别为 `linxsci-base`、`linxsci-idea`、`linxsci-survey`、`linxsci-paper-qa`、`linxsci-paper`、`linxsci-ppt`、`linxsci-reproduce`、`linxsci-xiaohongshu`，值为获授权的仓库 URL。基础项使用主仓库来源。保存在已忽略的 `.local/release-sources.json` 或外部私有配置中，不提交此文件，也不在 URL 内嵌密码或令牌。
- `--sdk-wheel`：已构建的 `linxsci-0.3.4-py3-none-any.whl`。工具核对配方中的 SHA256、包版本和其 `linxsci/` 文件与固定基础源码的一致性，不重打包 CLI/SDK。

套件版本与 CLI/SDK 版本分别管理。当前八个单项包使用同一个套件版本，并各自记录源提交；这不改动扩展源码里的版本定义。内部 Skill 依赖通过同一套件清单中的名称解析，目标版本就是该清单记录的版本。

## 构建与验证

使用 Python 3.10+ 进行整套验收；构建和静态校验工具本身只需要 Python 3.9+ 标准库及 Git。维护者须预先具有私有源的只读访问权限。

在主仓库根目录执行；先自行准备上述私有映射、既有 wheel，并确认锁定提交是所需版本。将 `BASE_COMMIT` 设置为本次选定、已核对与 wheel 一致的主工程完整 SHA：

```bash
python tools/build_skill_releases.py \
  --sources .local/release-sources.json \
  --base-commit "$BASE_COMMIT" \
  --sdk-wheel dist/0.3.4/linxsci-0.3.4-py3-none-any.whl \
  --output dist/suite-0.1.0-rc.1

python tools/check_skill_releases.py dist/suite-0.1.0-rc.1
python tools/smoke_skill_releases.py dist/suite-0.1.0-rc.1 \
  --report .local/release-checks/smoke.json
```

`--lock` 和 `--recipe` 可显式指定配置文件。已有输出目录会被拒绝，需选择新目录；不覆盖已有发行文件。测试命令为 `python -m unittest discover -s tests -p test_skill_releases.py -v`。

构建在空临时仓库中获取并检出完整 SHA，校验工作树干净状态，再直接读取 Git blob，避免本机换行符转换影响固定源码。若服务端不支持直接获取旧 SHA，则获取分支与标签的可达对象，仍只接受清单中的精确提交；无法获取即失败。私有映射也可使用本机绝对仓库路径或 `file://` 来源，但非裸仓库存在未提交或未跟踪文件时会被拒绝，检查不会改变源索引。

开发目录中若保留了本次暂不发行的修改，应在私有映射中使用选定提交的干净检出目录或远程来源。保留这些修改，固定提交不会包含它们。

每个包使用固定排序、时间戳、权限和压缩设置。在相同 Python/zlib 工具链下，同一输入应生成逐字节一致的文件；不同压缩库版本尚未验证。失败的中间文件由临时目录清理，只有整套静态校验成功后才生成目标目录。

## 13 个输出文件

| 文件 | 内容 |
| --- | --- |
| `linxsci-base-skill-0.1.0-rc.1.zip` | 基础 Skill 单项包，`SKILL.md` 在根目录 |
| `linxsci-<扩展名>-0.1.0-rc.1.zip`，共七个 | 对应扩展的指令、入口和必要资源，`SKILL.md` 在根目录 |
| `linxsci-skills-0.1.0-rc.1-full.zip` | `skills/` 下八个实际目录、`packages/` 下相同单项包、`wheels/` 下既有 SDK 和发行清单 |
| `linxsci-skills-0.1.0-rc.1-source.zip` | 单层根目录下展开的八个固定提交源码，包含允许分发的测试和维护工具，另附构建输入快照 |
| `linxsci-0.3.4-py3-none-any.whl` | 按原字节复用的 SDK/CLI |
| `release-manifest.json` | 公共版本、来源提交、依赖条件、资产大小、下载地址与单项校验值 |
| `SHA256SUMS` | 其余 12 个文件的完整 SHA256 清单 |

单项包显式选取根目录指令、README、requirements、许可证等文件，以及 `scripts/`、`references/`、`agents/`、`assets/`、`tools/`。测试只进入源码快照。源码快照以 Git 跟踪文件为集合，过滤 Git 元数据、本机配置、虚拟环境、缓存、构建结果和 `docs/local/`。禁止符号链接、嵌套仓库、危险或冲突的归档路径，并扫描实际私有源地址。`.env.example` 可保留，真实 `.env` 被排除。

源码快照中的 `release/build-inputs/` 保存本次使用的锁文件、配方、构建、校验、冒烟、包外安装验收、发布工具及共用 `tools/skill_install.py`，其文件哈希记录在清单的 `build_inputs`。这些配方文件与固定主仓库提交明确分开：即使新工具尚未提交，也能审计实际构建逻辑。复现时使用其中的构建器并显式传入 `--lock`、`--recipe` 和其余输入；重建私有源码仍需维护者权限。源码快照不包含 Git 历史或开发工作区未提交修改。

## 清单与完整性

`release-manifest.json` 和各单项的 `release.json` 使用 schema 1。清单固定记录八个源 SHA，单项元数据记录入口、Python 约束、SDK 约束、条件依赖及文件清单。Idea 对 Survey 的 `feature / fresh-evidence` 表示需要新证据时的功能依赖；`workflow` 表示相应协作场景，不将双向协作误判为无条件安装循环。

清单包含八个单项 ZIP 和 wheel 的大小、SHA256 及预定公开 URL；同时记录完整包与源码包名称。完整包及源码包内嵌清单，所以二者的最终哈希放在外层 `SHA256SUMS`，避免文件对自身产生循环哈希。校验器核对完整资产集合、单项文件清单、内嵌包、展开目录、源码、构建输入和 wheel 的一致性，并检查 Markdown 相对文件链接；不校验网页可达性或锚点名称。这些哈希用于完整性核验，不是发行者数字签名。

候选配方使用 `status: candidate`，产物为 `published: false`。正式配方使用 `status: release`、稳定套件版本，并且构建命令必须显式加 `--release`；产物统一生成 `status: release` / `published: true`。这是待上传正式资产的元数据，构建结果仍报告 `uploaded: false`，不代表远端已经可下载。校验器和安装器拒绝互相矛盾的状态，公开安装只接受正式元数据。包内身份、源码/完整包内嵌清单及校验和在同一次构建中生成，不手改外层 JSON。

## 验收范围与后续步骤

冒烟验证在源码树外解压三类 ZIP，创建临时 venv，仅从随包 wheel 离线安装 SDK，清除继承的 LinxSci/Python/Pip 配置，将 PATH 限定到环境目录并确认 Git 不可用。检查八个直接入口、七个 SDK 分发入口、扩展发现及基础路由，不调用业务 API。它不验证论文、图文、PPT 等实际业务产出，也不安装小红书第三方依赖或外部工具。

[共用包安装器与 Idea → Survey](SKILL_INSTALLATION.zh-CN.md)由构建器生成到八个包的 `scripts/linxsci_release_install.py`，并以 `generated_files` 记录构建输入路径和 SHA256；源码快照也包含该模块，校验器核对它与 `release/build-inputs/tools/skill_install.py` 逐字节一致。生成文件不伪称为固定源提交中的文件；其哈希进入包清单和构建输入清单，SDK wheel 按原字节复用。安装器只安装显式选择的包。文档或代码更新需形成可获取的新提交、更新版本与固定 SHA，并写入新的输出目录；已有资产保持不变。完整套件不是完全离线的 Python/字体/实验环境。匿名下载、SkillHub 和生产任务验收应在相应发行记录中单独记录。

回退本轮构建只需保留或移走候选目录及新增构建文件；工具不会修改源仓库。若之后有新工作，先备份再逐文件恢复，避免重置整个索引或覆盖无关修改。

## 正式封装与安装验收

先分别完成各仓库源码提交，确认锁文件中的提交可获取。选择一个未使用的稳定套件版本，并将 `SUITE_VERSION` 和 `BASE_COMMIT` 设置为该版本和真实主工程完整 SHA。`BASE_COMMIT` 的 SDK 包数据必须与原 wheel 一致；基础 SKILL 也属于包数据，不能把仅文字修改视为自动兼容。保留工作区修改不等于这些修改已进入发行来源。

将配方复制到 `.local/suite.release.json`，设置 `status` 为 `release`、`suite_version` 为选定版本；其余依赖、SDK 哈希及入口按实际验证结果维护。以下命令在主仓库执行，变量必须先设定；所有输出目录和报告路径都应未使用：

```bash
python tools/build_skill_releases.py --release \
  --recipe .local/suite.release.json --lock extensions.lock.json \
  --sources .local/release-sources.json --base-commit "$BASE_COMMIT" \
  --sdk-wheel dist/0.3.4/linxsci-0.3.4-py3-none-any.whl \
  --output "dist/suite-$SUITE_VERSION"
python tools/check_skill_releases.py "dist/suite-$SUITE_VERSION"
python tools/verify_skill_installation.py "dist/suite-$SUITE_VERSION" \
  --report ".local/release-checks/install-$SUITE_VERSION.json"
```

`verify_skill_installation.py` 同样接受新版候选资产。它先执行八个 Skill 在单项、完整包和源码快照中的帮助/发现冒烟，再从单项 Idea ZIP 创建源码树外环境，离线安装随包 SDK，通过明确的本机 HTTP 测试入口安装 Survey。检查拒绝、同套件约束、404/超时/中断、损坏与危险路径、回退、修改保护、无下载复用，以及模拟 API 下的原任务和续问；没有 Survey 的已有证据复用不得触发下载。关键场景缺失直接失败，不跳过。报告绑定清单及全部 13 个资产的哈希。

正式 HTTPS 选择路径使用本地传输替代验证；报告明确记录未验证真实匿名下载。测试请求只到本机回环服务，子进程不需要 Git、私有凭据或开发源码。报告写在资产目录外，已有报告不覆盖。运行需要 Python 3.10+、venv 和绑定本机回环端口的能力；单项包没有测试，工具自身在主工程或源码快照中运行。

## 套件发布入口

准备实际套件发行说明文件，并完成授权条款、支持平台和最终源码检查。`publish_skill_releases.py` 不使用 SDK 的 `v*` 发布工作流，不需要 Codeup 权限。它读取已经构建、校验的资产及与这些字节匹配的安装验收报告。

默认只输出本地计划，不访问网络：

```bash
python tools/publish_skill_releases.py "dist/suite-$SUITE_VERSION" \
  --installation-report ".local/release-checks/install-$SUITE_VERSION.json" \
  --notes-file "docs/releases/suite-v$SUITE_VERSION.md"
```

得到发布授权后，先将真实主工程提交与对应 `suite-v<版本>` 标签推送到公开主仓库。标签必须解析为清单的基础源提交。安装好 GitHub CLI 并使用维护者凭据，然后在上述命令末尾加 `--upload-draft`：创建新草稿、上传 13 个文件，再下载比较文件集合和全部字节。已有 Release 不覆盖；失败时检查远端草稿，工具不会删除或替换它。

草稿复核通过后，用相同命令加 `--publish`：重新核对标签和远端草稿字节，然后公开。已公开的 Release 拒绝修改；发布不移动 SDK 的 latest 标记。两个写入参数互斥，没有参数时始终只生成计划。

公开后另行从匿名环境下载固定 HTTPS 清单与 ZIP，实际安装并检查 SkillHub。认证下载草稿、模拟 API 以及本地 HTTPS 传输替代不能代替这一步。许可证和原生平台验收也不因生成了本地发布计划而自动完成。
