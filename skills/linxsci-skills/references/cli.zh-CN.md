# 全接口便捷命令

[English](cli.md)

全部 34 个接口都可直接调用，无需指定 HTTP 方法或接口路径。已安装 CLI 时使用下表的 `linxsci`；仅安装 Skill 时，替换为 `python3 <skill-dir>/scripts/cli.py`。

动态 ID 使用响应返回的原始值，由 CLI 自动编码。表中的尖括号是占位参数，须替换。JSON 文件需按实际 Agent API 契约准备；四个搜索命令把检索词发送为 `query`，可选 `--body` 只提供附加参数，不能覆盖位置参数中的检索词；不推断其他业务字段。`{}` 不是通用有效业务请求。

| 编号 | 接口 | 命令 |
| --- | --- | --- |
| 01 | 接口元信息 | `linxsci meta` |
| 02 | 用量信息 | `linxsci usage` |
| 03 | 存活检查 | `linxsci health live` |
| 04 | 就绪检查 | `linxsci health ready` |
| 05 | 综合论文搜索 | `linxsci search "large language models"` |
| 06 | OpenAlex 搜索 | `linxsci search-openalex "large language models"` |
| 07 | Semantic Scholar 搜索 | `linxsci search-semantic-scholar "large language models"` |
| 08 | Google Scholar 搜索 | `linxsci search-google-scholar "large language models"` |
| 09 | 论文标识解析 | `linxsci resolve --body @papers-resolve.json` |
| 10 | 批量获取论文 | `linxsci batch-get --body @papers-batch-get.json` |
| 11 | 论文详情 | `linxsci paper "<paper-id>"` |
| 12 | 论文内容 | `linxsci paper "<paper-id>" --resource content` |
| 13 | 论文目录 | `linxsci paper "<paper-id>" --resource toc` |
| 14 | 论文章节 | `linxsci paper "<paper-id>" --resource sections --item-id "<section-id>"` |
| 15 | 论文图表 | `linxsci paper "<paper-id>" --resource figures` |
| 16 | 论文资源 | `linxsci --output asset.bin paper "<paper-id>" --resource assets --item-id "<asset-id>"` |
| 17 | 参考文献 | `linxsci paper "<paper-id>" --resource references` |
| 18 | 被引论文 | `linxsci paper "<paper-id>" --resource citations` |
| 19 | 相关论文 | `linxsci paper "<paper-id>" --resource related` |
| 20 | 引用图谱 | `linxsci paper "<paper-id>" --resource graph` |
| 21 | 论文引用格式 | `linxsci paper "<paper-id>" --resource citation` |
| 22 | 论文推荐 | `linxsci recommend --body @recommendations.json` |
| 23 | 移动端推荐卡片 | `linxsci mobile-cards` |
| 24 | 作者详情 | `linxsci author "<author-id>"` |
| 25 | 作者论文 | `linxsci author "<author-id>" --papers` |
| 26 | 机构详情 | `linxsci institution "<institution-id>"` |
| 27 | 机构论文 | `linxsci institution "<institution-id>" --papers` |
| 28 | 期刊或会议详情 | `linxsci venue "<venue-id>"` |
| 29 | 期刊或会议论文 | `linxsci venue "<venue-id>" --papers` |
| 30 | 实体标识解析 | `linxsci resolve-entities --body @entities-resolve.json` |
| 31 | 创建 PDF 解析任务 | `linxsci parse-pdf --body @pdf-parse.json` |
| 32 | 上传 PDF 并创建解析任务 | `linxsci upload "/实际路径/paper.pdf"` |
| 33 | 查询 PDF 解析任务 | `linxsci task "<task-id>"` |
| 34 | 获取 PDF 解析结果 | `linxsci task "<task-id>" --result` |

所有接口命令支持重复的 `--param key=value` 和 `--request-id`；`--output`、`--timeout`、`--framework-request-id`、`--json-errors` 放在动作之前。PDF 命令按需读取 `LINXSCI_MINERU_API_KEY`。创建/上传任务后记录真实 ID，不自动重试或无限轮询。

`linxsci <动作> --help` 可查看参数。`request` 保留作通用调试入口；该入口的动态 ID 需自行编码。接口定义和错误码见 [api.md](api.zh-CN.md)。
