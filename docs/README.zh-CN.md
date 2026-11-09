# LinxSci 文档目录

[English](README.md) · [项目介绍](../README.zh-CN.md)

按使用方式选择文档。本项目 `linxsci-openapi-skills` 中，独立 Skill 名为 `linxsci-base`，源码位于 `skills/linxsci-base/`。CLI 与 SDK 共用 Python 发行包 `linxsci`，终端命令为 `linxsci`，SDK 导入示例为 `from linxsci import LinxSciClient`。

| 需求 | 文档 |
| --- | --- |
| 安装、配置、更新和卸载独立 Skill | [Skill 用户指南](USER_GUIDE.zh-CN.md) |
| 安装命令行工具，查询命令和参数 | [CLI 指南](CLI_GUIDE.zh-CN.md) |
| 安装 SDK、配置 Python 客户端、调用方法和处理错误 | [Python SDK 指南](DEVELOPMENT.zh-CN.md) |
| 查询各入口共用的 HTTP 路由、认证与错误 | [API 参考](API.zh-CN.md) |
| 构建安装包、发布 GitHub/PyPI、验证安装 | [维护者发布指南](RELEASING.zh-CN.md) |
| 执行回归与集成检查 | [测试指南](TESTING.zh-CN.md) |

Skill 指南使用独立安装器和助手交互；CLI 指南使用终端命令；SDK 指南使用 Python 安装与代码。各使用指南均包含对应的更新步骤。发布凭据只用于维护者上传，用户安装不需要这些凭据。

发布指南说明公开文件排除规则、安装包内容、构建校验、GitHub 发布和 PyPI 上传。安装示例使用 `0.3.3`，其中附带改名后的 `linxsci-base` Skill。CLI 与 SDK 用户升级 `linxsci` 包；已经复制安装的 Skill 需使用原安装器单独更新。
