"""LinxSci OpenAPI v2 client; Python standard library only."""
import json
import math
import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

if __package__:
    from .config import resolve_settings
else:
    from config import resolve_settings


class LinxSciError(Exception):
    def __init__(self, message, status=None, body=None, headers=None):
        super().__init__(message)
        self.status, self.body, self.headers = status, body, headers or {}

    @property
    def error_code(self):
        if isinstance(self.body, dict) and isinstance(self.body.get("error"), dict):
            code = self.body["error"].get("code")
            return code if type(code) in (str, int) else None
        return None

    @property
    def request_id(self):
        headers = {k.lower(): v for k, v in self.headers.items()}
        if headers.get("x-request-id"):
            return headers["x-request-id"]
        if isinstance(self.body, dict) and isinstance(self.body.get("error"), dict):
            value = self.body["error"].get("request_id")
            return value if isinstance(value, str) else None
        return None

    @property
    def framework_request_id(self):
        if isinstance(self.body, dict) and isinstance(self.body.get("extra"), dict):
            value = self.body["extra"].get("request-id")
            return value if isinstance(value, str) else None
        return None

    @property
    def execution_uncertain(self):
        """The upstream returned, but member did not confirm finish; do not blindly retry."""
        return self.error_code == -3905


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward credentials to another location.


@dataclass
class Response:
    status: int
    headers: dict
    body: bytes

    def json(self):
        return json.loads(self.body)


# The proxy document defines routes, but not upstream business schemas.
ROUTES = [
    ("GET", "/meta"), ("GET", "/usage"),
    ("GET", "/health/live"), ("GET", "/health/ready"),
    ("POST", "/papers/search"), ("POST", "/search/openalex"),
    ("POST", "/search/semantic-scholar"), ("POST", "/search/google-scholar"),
    ("POST", "/papers/resolve"), ("POST", "/papers:batchGet"),
    ("POST", "/recommendations"), ("GET", "/recommendations/mobile-cards"),
    ("POST", "/entities:resolve"), ("POST", "/pdf/parse"),
    ("POST", "/pdf/parse/upload"), ("GET", "/pdf/parse/{task_id}"),
    ("GET", "/pdf/parse/{task_id}/result"),
]
ROUTES += [("GET", "/papers/{paper_id}" + suffix) for suffix in
           ("", "/content", "/toc", "/sections/{section_id}", "/figures",
            "/assets/{asset_id}", "/references", "/citations", "/related",
            "/graph", "/citation")]
ROUTES += [("GET", "/" + kind + "/{" + ident + "}" + suffix)
           for kind, ident in (("authors", "author_id"),
                               ("institutions", "institution_id"), ("venues", "venue_id"))
           for suffix in ("", "/papers")]


def segment(value):
    if not str(value) or str(value) in (".", ".."):
        raise ValueError("Path identifiers must be nonempty and cannot be . or ..")
    return quote(str(value), safe=":")


def paper_segment(value):
    if not re.fullmatch(r"(?:local|arxiv|openalex|s2|doi):.+", value):
        raise ValueError("paper_id requires local:, arxiv:, openalex:, s2: or doi: prefix")
    return segment(value)


def paper_path(paper_id, resource=None, item_id=None):
    path = "/papers/" + paper_segment(paper_id)
    if resource:
        if resource not in ("content", "toc", "sections", "figures", "assets", "references", "citations", "related", "graph", "citation"):
            raise ValueError("Unknown paper resource")
        path += "/" + resource
        if resource in ("sections", "assets"):
            path += "/" + segment(item_id if item_id is not None else "")
        elif item_id is not None:
            raise ValueError("item_id is only supported for sections or assets")
    elif item_id is not None:
        raise ValueError("item_id requires sections or assets")
    return path


def request_header(value, name):
    if not isinstance(value, str) or not value or any(ord(c) < 32 or ord(c) > 126 for c in value):
        raise ValueError(name + " must be a nonempty printable ASCII value")
    return value


class LinxSciClient:
    def __init__(self, base_url=None, api_key=None, timeout=60, *, framework_request_id=None):
        base_url, api_key = resolve_settings(base_url, api_key)
        url = urlsplit(base_url)
        if url.scheme not in ("http", "https") or not url.netloc or url.username or url.password or url.query or url.fragment:
            raise ValueError("LINXSCI_BASE_URL must be an http(s) service root URL")
        if url.path.endswith(("/openapi/v2", "/openapi/v1")):
            raise ValueError("Base URL must not include /openapi/v2 or /openapi/v1")
        if not api_key or any(c in api_key for c in "\r\n"):
            raise ValueError("Set LINXSCI_OPENAPI_KEY to a valid LinxSci key")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be a positive finite number")
        self.base_url, self.api_key, self.timeout = base_url, api_key, timeout
        self.framework_request_id = (request_header(framework_request_id, "X-ANYTHINGRIGHT-REQ-ID")
                                     if framework_request_id is not None else None)
        self.opener = build_opener(NoRedirect())

    def request(self, method, path, *, query=None, payload=None, file=None,
                fields=None, mineru_key=None, request_id=None, framework_request_id=None):
        method = method.upper()
        if not any(method == m and re.fullmatch(re.sub(r"\{[^}]+\}", r"[^/]+", p), path)
                   for m, p in ROUTES):
            raise ValueError("Unsupported v2 route or HTTP method")
        if any(x in path for x in ("?", "#")) or any(x in (".", "..") for x in path.split("/")):
            raise ValueError("Invalid path; pass query separately and encode identifiers")
        if method == "GET" and (payload is not None or file is not None):
            raise ValueError("GET requests cannot carry a body")
        if path == "/pdf/parse/upload" and file is None:
            raise ValueError("PDF upload requires a file")
        if file is not None and (path != "/pdf/parse/upload" or payload is not None):
            raise ValueError("file is only supported for PDF upload without JSON")
        if fields and file is None:
            raise ValueError("Form fields require PDF upload")
        if mineru_key and not path.startswith("/pdf/parse"):
            raise ValueError("MinerU key is only supported on PDF routes")
        headers = {"Authorization": "Bearer " + self.api_key,
                   "X-Request-ID": request_header(request_id, "X-Request-ID") if request_id is not None else str(uuid.uuid4())}
        framework_id = framework_request_id if framework_request_id is not None else self.framework_request_id
        if framework_id is not None:
            headers["X-ANYTHINGRIGHT-REQ-ID"] = request_header(framework_id, "X-ANYTHINGRIGHT-REQ-ID")
        if mineru_key:
            headers["X-MinerU-API-Key"] = mineru_key
        body = None
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode()
            headers["Content-Type"] = "application/json"
        if file is not None:
            source = Path(file)
            boundary = "linxsci-" + uuid.uuid4().hex
            chunks = []
            for key, value in (fields or {}).items():
                if any(c in key for c in '\r\n"'):
                    raise ValueError("Invalid form field name")
                chunks.append((f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n').encode())
            filename = source.name.replace('"', '_').replace("\r", "_").replace("\n", "_")
            chunks.append((f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\nContent-Type: application/pdf\r\n\r\n').encode())
            chunks += [source.read_bytes(), f"\r\n--{boundary}--\r\n".encode()]
            body = b"".join(chunks)
            headers["Content-Type"] = "multipart/form-data; boundary=" + boundary
        url = self.base_url + "/openapi/v2" + path
        if query:
            url += "?" + urlencode(query, doseq=True)
        try:
            with self.opener.open(Request(url, data=body, headers=headers, method=method), timeout=self.timeout) as response:
                return Response(response.status, dict(response.headers), response.read())
        except HTTPError as error:
            raw = error.read()
            try:
                detail = json.loads(raw)
            except (ValueError, UnicodeDecodeError):
                detail = raw.decode("utf-8", errors="replace")
            raise LinxSciError(f"LinxSci HTTP {error.code}", error.code, detail, dict(error.headers)) from None
        except (URLError, TimeoutError, OSError):
            raise LinxSciError("LinxSci network request failed; check service URL and connectivity") from None

    def search(self, query, **options):
        return self.request("POST", "/papers/search", payload={**options, "query": query})

    def paper(self, paper_id, resource=None, *, item_id=None, query=None):
        return self.request("GET", paper_path(paper_id, resource, item_id), query=query)

    def upload_pdf(self, file, *, fields=None, mineru_key=None):
        return self.request("POST", "/pdf/parse/upload", file=file, fields=fields, mineru_key=mineru_key)

    def pdf_task(self, task_id, *, result=False):
        if task_id == "upload":
            raise ValueError("task_id cannot be upload")
        return self.request("GET", "/pdf/parse/" + segment(task_id) + ("/result" if result else ""))
