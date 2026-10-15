# LinxSci Scholar Skill

让 AI 助手帮你搜索学术论文、阅读相关章节、查询引用，并解析你指定的 PDF。

你需要一个已有的 Scholar API Key，以及能够执行本地 Python 脚本的 AI 助手。运行环境需要 **Python 3.9+**；本工具不需要额外 Python 运行依赖。

## 普通用户：安装、配置、提问

1. 下载发布方提供的 `linxsci-scholar-0.2.2.zip`，解压。
2. macOS 双击 `Install.command`；Windows 双击 `Install.bat`。也可以在解压目录运行 `python3 install.py`（Windows 用 `py -3 install.py`）。
3. 在向导中确认服务地址，输入你的 API Key。输入时 Key 不会显示。向导保存配置并检查连接。
4. 在助手中输入：

> 使用 $linxsci-scholar 搜索图神经网络相关论文，阅读方法章节，比较主要方法并附上来源。

默认使用测试服务 **http://101.126.93.213:28888**，地址可在向导中修改，无需在用户电脑部署 Scholar。线上地址仍为 **https://linxsci.com**，可运行 `python3 install.py --online` 切换。已有本地配置或环境变量优先于默认值；修改已有配置可运行 `linxsci-scholar setup --base-url http://101.126.93.213:28888`。

安装器默认将 Skill 放到 `~/.agents/skills/linxsci-scholar`，见 [官方本地 Skill 说明](https://learn.chatgpt.com/docs/build-skills)。客户端未发现 Skill 时重启助手；其他加载位置可通过 `--skills-dir` 指定。旧版客户端使用 `~/.codex/skills` 时，也可显式指定该目录。

完整图文无关的操作步骤、更新和故障处理见 [普通用户指南](docs/USER_GUIDE.md)。本项目不包含 AI 助手或 Scholar 服务器，也不负责注册账号或发放 Key。

## 已安装 CLI 的用户

当前发布文件可本地安装；尚未上传到 PyPI。安装 wheel 后执行：

```bash
linxsci-scholar install-skill
linxsci-scholar setup --online
linxsci-scholar doctor
linxsci-scholar search 'graph neural networks'
```

`setup` 一次保存配置，后续 CLI、SDK 和本地 Skill 共用。不需要每次 export 环境变量。`config` 查看配置状态，不显示 Key；`config --clear` 清除保存的地址和 Key。更新包后运行 `install-skill --update` 更新助手使用的脚本，旧 Skill 保留备份。

## 能力与范围

已适配新版数字框架错误码、请求追踪和计费异常诊断。覆盖接口文档中的 34 条路由：服务信息和健康、论文搜索和标识解析、详情/内容/目录/章节/图表资源/引用、推荐、作者/机构/期刊、PDF 解析任务。便捷命令包括 `search`、`paper`、`upload` 和 `task`，其他路由通过 `request` 原样调用。

研究比较和总结由助手根据实际读取的内容完成。目前接口文档未定义多数 POST 的业务字段、分页和 PDF 状态模型；这些高级接口应按部署版本的上游契约使用，不能假定空 JSON 有效。所有路由可调用不代表每条接口都已有专用表单或经过真实生产验证。

## 开发与发布

- [开发者指南：CLI、SDK、配置与测试](docs/DEVELOPMENT.md)
- [发布指南：构建、验证与分发](docs/RELEASING.md)
- [Skill 指令](skills/linxsci-scholar/SKILL.md)
- [原始接口文档](Scholar-OpenAPI-v2-使用文档.md)

```bash
python3 -m unittest discover -s tests -v
python3 tools/build_release.py --bundle-only
```
