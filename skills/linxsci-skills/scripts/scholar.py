#!/usr/bin/env python3
"""LinxSci Scholar：搜索论文、按章节阅读和解析 PDF；首次使用请运行 linxsci setup。"""
import argparse
import getpass
import json
import os
import sys
import warnings
from pathlib import Path
if __package__:
    from .scholar_client import ROUTES, ScholarClient, ScholarError, paper_path, segment
    from .scholar_config import config_path, clear_config, load_config, save_config, service_defaults, validate_url
    from .scholar_install import install_skill
else:
    from scholar_client import ROUTES, ScholarClient, ScholarError, paper_path, segment
    from scholar_config import config_path, clear_config, load_config, save_config, service_defaults, validate_url
    from scholar_install import install_skill

VERSION = "0.3.0"

SEARCH_COMMANDS = {
    "search": ("/papers/search", "综合论文搜索"),
    "search-openalex": ("/search/openalex", "OpenAlex 搜索"),
    "search-semantic-scholar": ("/search/semantic-scholar", "Semantic Scholar 搜索"),
    "search-google-scholar": ("/search/google-scholar", "Google Scholar 搜索"),
}
JSON_COMMANDS = {
    "resolve": ("/papers/resolve", "解析论文标识"),
    "batch-get": ("/papers:batchGet", "批量获取论文"),
    "recommend": ("/recommendations", "推荐论文"),
    "resolve-entities": ("/entities:resolve", "解析作者、机构或期刊标识"),
    "parse-pdf": ("/pdf/parse", "按 JSON 请求创建 PDF 解析任务"),
}
ENTITY_COMMANDS = {"author": "authors", "institution": "institutions", "venue": "venues"}


def error_info(error):
    code = error.error_code
    hints = {
        401: "API Key 无效或已过期，请运行 linxsci setup 重新配置。",
        403: "账号无权调用此接口，请检查账号权限。",
        404: "服务未提供此接口，请核对服务根地址和部署版本。",
        429: "请求过于频繁或额度不足，请稍后重试或检查账号用量。",
        502: "Scholar 无法连接上游服务，请联系服务维护者。",
        503: "服务暂不可用，请稍后重试或联系服务维护者。",
    }
    message = hints.get(error.status, "服务调用失败，请检查服务地址、网络和服务状态。")
    code_hints = {
        -401: hints[401],
        -404: hints[404],
        -3900: "接口 action 已登记但未启用，请联系管理员配置并启用后再调用。",
        -3901: "已达到每日调用限额，请在额度恢复后重试或联系管理员。",
        -3902: "Agent API 地址或服务端 Key 未配置，请联系服务端管理员。",
        -3903: "Agent API 连接或传输失败，请联系服务维护者检查连接。",
        -3904: "member 的 begin 未成功，请求尚未转发上游；请联系管理员检查 member 服务和内部鉴权。",
        -3905: "Agent API 已返回，但 member 的 finish 未确认。请先查询执行与计费结果，再决定是否重试；不要直接重复上传或创建任务。",
        # Keep compatibility with older Scholar deployments.
        "upstream_unconfigured": "Scholar 服务端上游配置不完整，请联系服务维护者。",
    }
    message = code_hints.get(code, message)
    headers = {k.lower(): v for k, v in error.headers.items()}
    # Only selected response metadata is exposed; never print the upstream error body.
    return {"message": message, "status": error.status, "error_code": code,
            "request_id": error.request_id, "framework_request_id": error.framework_request_id,
            "execution_uncertain": error.execution_uncertain, "retry_after": headers.get("retry-after")}


def print_error_details(report, stream):
    if report.get("error_code") is not None:
        print("错误码：" + str(report["error_code"]), file=stream)
    if report.get("request_id"):
        print("上游/代理请求 ID：" + report["request_id"], file=stream)
    if report.get("framework_request_id"):
        print("Scholar 框架请求 ID：" + report["framework_request_id"], file=stream)
    if report.get("retry_after"):
        print("Retry-After：" + report["retry_after"], file=stream)


def doctor(client, as_json=False):
    report = {"ok": False, "base_url": client.base_url, "key_configured": True,
              "config_file": str(config_path())}
    try:
        response = client.request("GET", "/meta")
        response.json()  # A 200 HTML login page is not a working API connection.
        report.update(ok=True, status=response.status, message="连接成功，可以开始检索论文。")
    except ScholarError as error:
        report.update(error_info(error))
    except (ValueError, UnicodeDecodeError):
        report["message"] = "服务返回了非 JSON 内容，请核对根地址，排除登录页或代理页面。"
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("服务地址：" + report["base_url"])
        print(report["message"])
        print_error_details(report, sys.stdout)
    return 0 if report["ok"] else 1


def setup(args):
    defaults = service_defaults()
    try:
        saved = load_config()
    except ValueError:
        saved = {}  # setup can repair a corrupt configuration.
    base_url = args.base_url
    if not base_url:
        base_url = defaults["online_base_url"] if args.online else saved.get("base_url", defaults["base_url"])
    if not args.api_key_stdin:
        if not sys.stdin.isatty():
            raise ValueError("配置向导需要交互终端；自动配置请使用 --api-key-stdin。")
        print("LinxSci Scholar 配置向导（API Key 输入不会显示）")
        print("线上服务：" + defaults["online_base_url"])
        base_url = input("服务根地址 [" + base_url + "]：").strip() or base_url
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", getpass.GetPassWarning)
                key = getpass.getpass("请输入 API Key" + ("（留空保留已有 Key）" if saved.get("api_key") else "") + "：")
        except getpass.GetPassWarning:
            raise ValueError("当前终端无法隐藏 Key 输入，请在普通终端运行 setup。") from None
        key = key or saved.get("api_key", "")
    else:
        key = sys.stdin.readline().rstrip("\r\n")
    base_url = validate_url(base_url)
    path = save_config(base_url, key)
    print("配置已保存：" + str(path))
    if os.environ.get("SCHOLAR_BASE_URL") or os.environ.get("SCHOLAR_OPENAPI_KEY"):
        print("提示：后续调用时，已有环境变量优先于本地配置。")
    if args.no_check:
        print("已跳过连接检查。稍后运行 linxsci doctor 检查连接。")
        return 0
    return doctor(ScholarClient(base_url, key, timeout=args.timeout, framework_request_id=args.framework_request_id))


def pairs(values):
    result = {}
    for value in values or []:
        key, sep, val = value.partition("=")
        if not sep or not key:
            raise ValueError("Parameters must use key=value")
        result.setdefault(key, []).append(val)
    return result


def build_parser(*, prog=None):
    parser = argparse.ArgumentParser(prog=prog, description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    parser.add_argument("--json-errors", action="store_true", help="Output structured errors on stderr")
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--framework-request-id", help="设置 X-ANYTHINGRIGHT-REQ-ID，用于定位 Scholar 框架请求")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("routes", help="列出已知接口，无需配置 Key")
    configure = sub.add_parser("setup", help="首次配置服务地址和 API Key")
    configure.add_argument("--base-url", help="Service root URL")
    configure.add_argument("--online", action="store_true", help="Use linxsci.com as the suggested service")
    configure.add_argument("--api-key-stdin", action="store_true", help="Read the Key from stdin without echoing it")
    configure.add_argument("--no-check", action="store_true", help="Save settings without a network check")
    diagnose = sub.add_parser("doctor", help="检查配置和服务连接")
    diagnose.add_argument("--json", action="store_true")
    configuration = sub.add_parser("config", help="查看配置状态（不显示 Key）或清除配置")
    configuration.add_argument("--clear", action="store_true")
    installer = sub.add_parser("install-skill", help="安装自包含 Skill，无需联网")
    installer.add_argument("--skills-dir", help="Parent directory for the Skill (default: ~/.agents/skills)")
    installer.add_argument("--update", action="store_true", help="Update a managed installation and retain a backup")
    def api_command(name, help):
        command = sub.add_parser(name, help=help, description=help)
        command.add_argument("--param", action="append", help="查询参数 key=value，可重复；字段按上游契约")
        command.add_argument("--request-id", help="上游/代理 X-Request-ID")
        return command

    for name, help in (("meta", "接口元信息"), ("usage", "用量信息"),
                       ("mobile-cards", "移动端推荐卡片")):
        api_command(name, help)
    health = api_command("health", "存活或就绪检查")
    health.add_argument("check", choices=("live", "ready"))
    for name, (_, help) in JSON_COMMANDS.items():
        command = api_command(name, help)
        command.add_argument("--body", required=True, help="JSON 或 @文件.json，字段按上游契约")
    for name in ENTITY_COMMANDS:
        entity = api_command(name, {"author": "作者详情或论文", "institution": "机构详情或论文", "venue": "期刊/会议详情或论文"}[name])
        entity.add_argument("entity_id", help="响应中的原始 ID，无需 URL 编码")
        entity.add_argument("--papers", action="store_true", help="获取该实体的论文")
    for name, (_, help) in SEARCH_COMMANDS.items():
        search = api_command(name, help)
        search.add_argument("query", help="检索词")
        search.add_argument("--body", help="可选附加参数，JSON 对象或 @文件.json；字段按上游契约")
    paper = api_command("paper", "读取论文详情、内容、目录、章节或引用等资源")
    paper.add_argument("paper_id")
    paper.add_argument("--resource", choices=("content", "toc", "sections", "figures", "assets", "references", "citations", "related", "graph", "citation"))
    paper.add_argument("--item-id")
    upload = api_command("upload", "上传 PDF 并创建解析任务")
    upload.add_argument("file")
    upload.add_argument("--field", action="append")
    task = api_command("task", "查询 PDF 任务或结果")
    task.add_argument("task_id")
    task.add_argument("--result", action="store_true")
    request = api_command("request", "通用接口调试入口；日常调用使用便捷命令")
    request.add_argument("method", choices=("GET", "POST"))
    request.add_argument("path", help="Encoded path relative to /openapi/v2")
    request.add_argument("--body", help="JSON or @file; required for JSON POST")
    parser.add_argument("--output", help="Write response bytes to a file (also supports binary assets)")
    return parser


def main(argv=None, *, prog=None):
    parser = build_parser(prog=prog)
    args = parser.parse_args(argv)
    try:
        if args.command == "setup":
            return setup(args)
        if args.command == "config":
            if args.clear:
                clear_config()
                print("本地配置已清除；如设置了环境变量，请另行清除。")
            else:
                saved = load_config()
                print(json.dumps({"config_file": str(config_path()),
                                  "saved_base_url": saved.get("base_url"),
                                  "saved_key_configured": bool(saved.get("api_key")),
                                  "environment_url_override": bool(os.environ.get("SCHOLAR_BASE_URL")),
                                  "environment_key_override": bool(os.environ.get("SCHOLAR_OPENAPI_KEY"))},
                                 ensure_ascii=False, indent=2))
            return 0
        if args.command == "install-skill":
            destination, backup = install_skill(args.skills_dir, args.update)
            print("Skill 已安装：" + str(destination))
            if backup:
                print("旧版本备份：" + str(backup))
            print("现在可在助手中使用 $linxsci-skills；如果没有显示，请重启助手。")
            return 0
        if args.command == "routes":
            print(json.dumps(ROUTES, ensure_ascii=False, indent=2))
            return 0
        client = ScholarClient(timeout=args.timeout, framework_request_id=args.framework_request_id)
        if args.command == "doctor":
            return doctor(client, args.json)
        def body(value):
            return json.loads(Path(value[1:]).read_text(encoding="utf-8") if value.startswith("@") else value)
        def invoke(method, path, **options):
            return client.request(method, path, query=pairs(args.param), request_id=args.request_id,
                                  mineru_key=os.environ.get("SCHOLAR_MINERU_API_KEY") if path.startswith("/pdf/parse") else None,
                                  **options)
        if args.command in ("meta", "usage"):
            response = invoke("GET", "/" + args.command)
        elif args.command == "mobile-cards":
            response = invoke("GET", "/recommendations/mobile-cards")
        elif args.command in JSON_COMMANDS:
            response = invoke("POST", JSON_COMMANDS[args.command][0], payload=body(args.body))
        elif args.command in ENTITY_COMMANDS:
            path = "/" + ENTITY_COMMANDS[args.command] + "/" + segment(args.entity_id)
            response = invoke("GET", path + ("/papers" if args.papers else ""))
        elif args.command == "health":
            response = invoke("GET", "/health/" + args.check)
        elif args.command in SEARCH_COMMANDS:
            options = body(args.body) if args.body else {}
            if not isinstance(options, dict):
                raise ValueError("Search body must be a JSON object")
            options.pop("query", None)
            response = invoke("POST", SEARCH_COMMANDS[args.command][0], payload={**options, "query": args.query})
        elif args.command == "paper":
            response = invoke("GET", paper_path(args.paper_id, args.resource, args.item_id))
        elif args.command == "upload":
            values = pairs(args.field)
            if any(len(v) != 1 for v in values.values()):
                raise ValueError("Form field names must be unique")
            response = invoke("POST", "/pdf/parse/upload", file=args.file, fields={k: v[0] for k, v in values.items()})
        elif args.command == "task":
            if args.task_id == "upload":
                raise ValueError("task_id cannot be upload")
            response = invoke("GET", "/pdf/parse/" + segment(args.task_id) + ("/result" if args.result else ""))
        else:
            if args.method == "POST" and not args.body:
                raise ValueError("JSON POST requires --body with the upstream request schema; use upload for files")
            response = invoke(args.method, args.path, payload=body(args.body) if args.body else None)
        if args.output:
            Path(args.output).write_bytes(response.body)
        else:
            try:
                print(json.dumps(response.json(), ensure_ascii=False, indent=2))
            except (ValueError, UnicodeDecodeError):
                sys.stdout.buffer.write(response.body)
        return 0
    except ScholarError as error:
        report = error_info(error)
        print(json.dumps(report, ensure_ascii=False) if args.json_errors else report["message"], file=sys.stderr)
        if not args.json_errors:
            print_error_details(report, sys.stderr)
        return 1
    except (ValueError, OSError) as error:
        message = "配置、输入或文件错误：" + str(error)
        if args.command == "doctor" and args.json:
            print(json.dumps({"ok": False, "message": message}, ensure_ascii=False))
        else:
            print(json.dumps({"message": message}, ensure_ascii=False) if args.json_errors else message, file=sys.stderr)
        return 2
    except (EOFError, KeyboardInterrupt):
        print("操作已取消。", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
