"""Compact, explicit response views without assuming upstream business schemas."""
import json
import re
import tempfile
from pathlib import Path


def json_text(value, pretty=False):
    return json.dumps(value, ensure_ascii=False, indent=2 if pretty else None,
                      separators=None if pretty else (",", ":"), allow_nan=False)


def select_value(value, pointer):
    """Resolve an RFC 6901 JSON Pointer; the empty pointer selects the root."""
    if pointer == "":
        return value
    if not pointer.startswith("/"):
        raise ValueError("--select must be a JSON Pointer beginning with /, or empty for the root")
    for raw in pointer[1:].split("/"):
        if re.search(r"~(?:[^01]|$)", raw):
            raise ValueError("Invalid JSON Pointer escape; use ~0 for ~ and ~1 for /")
        key = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict) and key in value:
            value = value[key]
        elif isinstance(value, list) and re.fullmatch(r"0|[1-9][0-9]*", key) and int(key) < len(value):
            value = value[int(key)]
        else:
            raise ValueError("--select does not match the response; inspect the saved raw response")
    return value


def response_view(value, args):
    if args.select is not None:
        value = select_value(value, args.select)
    total = None
    if args.limit is not None:
        if not isinstance(value, list):
            raise ValueError("--limit requires an array; use --select to choose the actual result array")
        total = len(value)
        value = value[:args.limit]
    if args.fields:
        fields = args.fields.split(",")
        if any(not key for key in fields) or len(set(fields)) != len(fields):
            raise ValueError("--fields requires unique, nonempty comma-separated literal field names")
        def project(item):
            if not isinstance(item, dict) or any(key not in item for key in fields):
                raise ValueError("--fields requires objects containing every requested field")
            return {key: item[key] for key in fields}
        value = [project(item) for item in value] if isinstance(value, list) else project(value)
    if args.table:
        if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
            raise ValueError("--table requires an array of objects")
        columns = list(value[0]) if value else (args.fields.split(",") if args.fields else [])
        if any(set(item) != set(columns) for item in value):
            raise ValueError("--table requires identical fields in every row; use --fields to choose shared fields")
        value = {"columns": columns, "rows": [[item[key] for key in columns] for item in value]}
    if total is not None and total > args.limit:
        value = {"data": value, "total": total, "returned": args.limit, "truncated": True}
    return value


def file_report(path, response, reason=None):
    report = {"file": str(path.resolve()), "bytes": len(response.body)}
    content_type = next((v for k, v in response.headers.items() if k.lower() == "content-type"), None)
    if content_type:
        report["content_type"] = content_type
    if reason:
        report.update(reason=reason, raw_response=True)
    return report


def save_response(response, suffix):
    # TemporaryDirectory would remove the file before the assistant could read it.
    # mkdtemp creates a private directory; the caller may remove it after reading.
    directory = Path(tempfile.mkdtemp(prefix="linxsci-response-"))
    path = directory / ("response" + suffix)
    try:
        path.write_bytes(response.body)
    except OSError:
        path.unlink(missing_ok=True)
        directory.rmdir()
        raise
    return path


def _write_response(response, args, source_path=None):
    if args.output:
        path = Path(args.output)
        path.write_bytes(response.body)
        if args.output_summary:
            print(json_text(file_report(path, response), args.pretty))
        return
    content_type = next((v.split(";", 1)[0].strip().lower() for k, v in response.headers.items()
                         if k.lower() == "content-type"), "")
    binary_type = content_type in ("application/pdf", "application/octet-stream") or content_type.startswith(("image/", "audio/", "video/"))
    if binary_type and source_path is None:
        if args.select is not None or args.fields is not None or args.limit is not None or args.table:
            raise ValueError("Response selection requires JSON; use --output to save the binary response")
        path = save_response(response, ".bin")
        print(json_text(file_report(path, response, "binary_response"), args.pretty))
        return
    try:
        value = response.json()
        is_json = True
    except (ValueError, UnicodeDecodeError):
        is_json = False
        if args.select is not None or args.fields is not None or args.limit is not None or args.table:
            raise ValueError("Response selection requires JSON; use --output to save the raw response") from None
        try:
            text = None if binary_type else response.body.decode("utf-8")
        except UnicodeDecodeError:
            text = None
        if text is None:
            path = source_path or save_response(response, ".bin")
            print(json_text(file_report(path, response, "binary_response"), args.pretty))
            return
        value = {"text": text}
    value = response_view(value, args)
    text = json_text(value, args.pretty)
    if args.max_output_chars and len(text) > args.max_output_chars:
        path = source_path or save_response(response, ".json" if is_json else ".txt")
        report = file_report(path, response, "output_limit")
        report.update(truncated=True, output_chars=len(text))
        # A bounded preview is for orientation, not a complete result or valid JSON document.
        report["preview"] = text[:min(500, args.max_output_chars)]
        text = json_text(report, args.pretty)
    print(text)


class ResponseOutputError(ValueError):
    """The request completed; output formatting failed, so do not repeat the call."""
    def __init__(self, message, response, path=None):
        super().__init__(message)
        self.report = {"error_code": "response_output_error", "message": message,
                       "request_completed": True, "status": response.status, "do_not_repeat": True}
        if path is not None:
            self.report.update(file_report(path, response), raw_response=True)


def write_response(response, args, source_path=None):
    try:
        _write_response(response, args, source_path)
    except (ValueError, OSError) as error:
        if source_path is not None:
            raise  # The original local response file is already available.
        # Preserve successful writes/tasks even if the requested local view is invalid.
        try:
            path = source_path or save_response(response, ".bin")
        except OSError:
            path = None
        raise ResponseOutputError(str(error), response, path) from None
