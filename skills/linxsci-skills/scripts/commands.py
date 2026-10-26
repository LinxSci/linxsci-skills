#!/usr/bin/env python3
"""LinxSci：搜索论文、按章节阅读和解析 PDF；首次使用请运行 linxsci setup。"""
import argparse
import getpass
from functools import partial
import json
import os
import sys
import warnings
from pathlib import Path
if __package__:
    from .client import ROUTES, Response, LinxSciClient, LinxSciError, paper_path, segment
    from .config import config_path, clear_config, load_config, save_config, service_defaults, validate_url
    from .installer import install_skill
    from .output import ResponseOutputError, json_text, write_response
else:
    from client import ROUTES, Response, LinxSciClient, LinxSciError, paper_path, segment
    from config import config_path, clear_config, load_config, save_config, service_defaults, validate_url
    from installer import install_skill
    from output import ResponseOutputError, json_text, write_response

VERSION = "0.3.1"

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
    if code is None:
        code = "network_error" if error.status is None else "http_error"
    hints = {
        401: "API Key 无效或已过期，请运行 linxsci setup 重新配置。",
        403: "账号无权调用此接口，请检查账号权限。",
        404: "服务未提供此接口，请核对服务根地址和部署版本。",
        429: "请求过于频繁或额度不足，请稍后重试或检查账号用量。",
        502: "LinxSci 无法连接上游服务，请联系服务维护者。",
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
        # Keep compatibility with older LinxSci deployments.
        "upstream_unconfigured": "LinxSci 服务端上游配置不完整，请联系服务维护者。",
    }
    message = code_hints.get(code, message)
    headers = {k.lower(): v for k, v in error.headers.items()}
    # Only selected response metadata is exposed; never print the upstream error body.
    report = {"message": message, "status": error.status, "error_code": code,
            "request_id": error.request_id, "framework_request_id": error.framework_request_id,
            "execution_uncertain": error.execution_uncertain, "retry_after": headers.get("retry-after")}
    return {key: value for key, value in report.items() if value is not None}


def print_error_details(report, stream):
    if report.get("error_code") is not None:
        print("错误码：" + str(report["error_code"]), file=stream)
    if report.get("request_id"):
        print("上游/代理请求 ID：" + report["request_id"], file=stream)
    if report.get("framework_request_id"):
        print("LinxSci 框架请求 ID：" + report["framework_request_id"], file=stream)
    if report.get("retry_after"):
        print("Retry-After：" + report["retry_after"], file=stream)


def doctor(client, as_json=True, pretty=False):
    report = {"ok": False, "base_url": client.base_url, "key_configured": True,
              "config_file": str(config_path())}
    try:
        response = client.request("GET", "/meta")
        response.json()  # A 200 HTML login page is not a working API connection.
        report.update(ok=True, status=response.status, message="连接成功，可以开始检索论文。")
    except LinxSciError as error:
        report.update(error_info(error))
    except (ValueError, UnicodeDecodeError):
        report["message"] = "服务返回了非 JSON 内容，请核对根地址，排除登录页或代理页面。"
    if as_json:
        print(json_text(report, pretty))
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
        print("LinxSci 配置向导（API Key 输入不会显示）")
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
    if os.environ.get("LINXSCI_BASE_URL") or os.environ.get("LINXSCI_OPENAPI_KEY"):
        print("提示：后续调用时，已有环境变量优先于本地配置。")
    if args.no_check:
        print("已跳过连接检查。稍后运行 linxsci doctor 检查连接。")
        return 0
    return doctor(LinxSciClient(base_url, key, timeout=args.timeout, framework_request_id=args.framework_request_id), pretty=args.pretty)


def pairs(values):
    result = {}
    for value in values or []:
        key, sep, val = value.partition("=")
        if not sep or not key:
            raise ValueError("Parameters must use key=value")
        result.setdefault(key, []).append(val)
    return result


class CLIArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, human_errors=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.human_errors = human_errors

    def error(self, message):
        if self.human_errors:
            super().error(message)
        self.exit(2, json_text({"error_code": "invalid_arguments", "message": message}) + "\n")


def nonnegative_int(value):
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("expected a nonnegative integer") from None
    if number < 0:
        raise argparse.ArgumentTypeError("expected a nonnegative integer")
    return number


def validate_output_options(args):
    transforms = args.select is not None or args.fields is not None or args.limit is not None or args.table
    if args.output_summary and not args.output:
        raise ValueError("--output-summary requires --output")
    if args.output and transforms:
        raise ValueError("--output saves raw bytes and cannot be combined with --select, --fields, --limit or --table")
    if args.command in ("setup", "config", "doctor", "routes", "install-skill"):
        if transforms or args.output or args.output_summary:
            raise ValueError("Response selection and file output apply only to endpoint commands")
    if args.select is not None and args.select != "" and not args.select.startswith("/"):
        raise ValueError("--select must start with /, or be empty for the root")
    if args.fields is not None:
        fields = args.fields.split(",")
        if any(not key for key in fields) or len(set(fields)) != len(fields):
            raise ValueError("--fields requires unique, nonempty comma-separated literal field names")


def build_parser(*, prog=None, human_errors=False):
    parser = CLIArgumentParser(prog=prog, description=__doc__, human_errors=human_errors)
    parser.add_argument("--version", action="version", version=VERSION)
    errors = parser.add_mutually_exclusive_group()
    errors.add_argument("--json-errors", dest="json_errors", action="store_true", default=True,
                        help="Output structured errors on stderr (default)")
    errors.add_argument("--human-errors", dest="json_errors", action="store_false", help="Human-readable errors")
    parser.add_argument("--pretty", action="store_true", help="Indent JSON for terminal reading")
    parser.add_argument("--select", metavar="POINTER", help="Select response data using a JSON Pointer, e.g. /data/items")
    parser.add_argument("--fields", metavar="KEYS", help="Keep literal comma-separated fields in the selected object(s)")
    parser.add_argument("--limit", type=nonnegative_int, help="Locally limit a selected array; not server pagination")
    parser.add_argument("--table", action="store_true", help="Encode uniform object arrays as columns and rows")
    parser.add_argument("--max-output-chars", type=nonnegative_int, default=12000,
                        help="Save larger endpoint output to a temporary file (default 12000; 0 disables)")
    parser.add_argument("--output-summary", action="store_true", help="With --output, print file metadata as JSON")
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--framework-request-id", help="设置 X-ANYTHINGRIGHT-REQ-ID，用于定位 LinxSci 框架请求")
    sub = parser.add_subparsers(dest="command", required=True,
                                parser_class=partial(CLIArgumentParser, human_errors=human_errors))
    sub.add_parser("routes", help="列出已知接口，无需配置 Key")
    reader = sub.add_parser("read-output", help="Read and filter a saved response locally; no API call")
    reader.add_argument("file", help="Path of a saved response file")
    configure = sub.add_parser("setup", help="首次配置服务地址和 API Key")
    configure.add_argument("--base-url", help="Service root URL")
    configure.add_argument("--online", action="store_true", help="Use linxsci.com as the suggested service")
    configure.add_argument("--api-key-stdin", action="store_true", help="Read the Key from stdin without echoing it")
    configure.add_argument("--no-check", action="store_true", help="Save settings without a network check")
    diagnose = sub.add_parser("doctor", help="检查配置和服务连接")
    doctor_format = diagnose.add_mutually_exclusive_group()
    doctor_format.add_argument("--json", action="store_true", help="JSON report (default)")
    doctor_format.add_argument("--text", action="store_true", help="Human-readable diagnostic report")
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
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser(prog=prog, human_errors="--human-errors" in argv)
    args = parser.parse_args(argv)
    try:
        validate_output_options(args)
        if args.command == "setup":
            return setup(args)
        if args.command == "config":
            if args.clear:
                clear_config()
                print(json_text({"cleared": True, "config_file": str(config_path())}, args.pretty))
            else:
                saved = load_config()
                print(json_text({"config_file": str(config_path()),
                                  "saved_base_url": saved.get("base_url"),
                                  "saved_key_configured": bool(saved.get("api_key")),
                                  "environment_url_override": bool(os.environ.get("LINXSCI_BASE_URL")),
                                  "environment_key_override": bool(os.environ.get("LINXSCI_OPENAPI_KEY"))},
                                 args.pretty))
            return 0
        if args.command == "install-skill":
            destination, backup = install_skill(args.skills_dir, args.update)
            report = {"installed": str(destination.resolve()), "skill": "linxsci-skills"}
            if backup:
                report["backup"] = str(backup.resolve())
            print(json_text(report, args.pretty))
            return 0
        if args.command == "routes":
            print(json_text(ROUTES, args.pretty))
            return 0
        if args.command == "read-output":
            source = Path(args.file).expanduser().resolve()
            headers = {"Content-Type": "application/octet-stream"} if source.suffix.lower() == ".bin" else {}
            response = Response(200, headers, source.read_bytes())
            write_response(response, args, source_path=source)
            return 0
        client = LinxSciClient(timeout=args.timeout, framework_request_id=args.framework_request_id)
        if args.command == "doctor":
            return doctor(client, as_json=not args.text, pretty=args.pretty)
        def body(value):
            return json.loads(Path(value[1:]).read_text(encoding="utf-8") if value.startswith("@") else value)
        def invoke(method, path, **options):
            return client.request(method, path, query=pairs(args.param), request_id=args.request_id,
                                  mineru_key=os.environ.get("LINXSCI_MINERU_API_KEY") if path.startswith("/pdf/parse") else None,
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
        write_response(response, args)
        return 0
    except LinxSciError as error:
        report = error_info(error)
        print(json_text(report) if args.json_errors else report["message"], file=sys.stderr)
        if not args.json_errors:
            print_error_details(report, sys.stderr)
        return 1
    except ResponseOutputError as error:
        if args.json_errors:
            print(json_text(error.report), file=sys.stderr)
        else:
            print("接口已成功执行，请勿重复请求。" + str(error), file=sys.stderr)
            if error.report.get("file"):
                print("原始响应：" + error.report["file"], file=sys.stderr)
        return 2
    except (ValueError, OSError) as error:
        message = "配置、输入或文件错误：" + str(error)
        if args.command == "doctor" and not args.text:
            print(json_text({"ok": False, "message": message}, args.pretty))
        else:
            print(json_text({"error_code": "local_error", "message": message}) if args.json_errors else message, file=sys.stderr)
        return 2
    except (EOFError, KeyboardInterrupt):
        print(json_text({"error_code": "cancelled", "message": "操作已取消。"}) if args.json_errors else "操作已取消。", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
