"""Shared local configuration for CLI, SDK and installed Skill."""
import json
import os
import tempfile
from pathlib import Path
from urllib.parse import urlsplit


class ConfigError(ValueError):
    pass


def config_path():
    override = os.environ.get("SCHOLAR_CONFIG_FILE")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local")))
    else:
        root = Path.home() / ".config"
    return root / "linxsci-scholar" / "config.json"


def validate_url(value):
    if not isinstance(value, str):
        raise ConfigError("服务地址必须是文本。")
    value = value.strip().rstrip("/")
    try:
        url = urlsplit(value)
        port = url.port
    except ValueError:
        raise ConfigError("服务地址格式错误，请填写 http(s) 服务根地址。") from None
    if (url.scheme not in ("http", "https") or not url.hostname or url.username is not None
            or url.password is not None or url.query or url.fragment
            or any(c.isspace() or ord(c) < 32 for c in value)):
        raise ConfigError("服务地址必须是 http(s) 根地址，不能包含账号、查询参数或空白。")
    if url.path.endswith(("/openapi/v2", "/openapi/v1")):
        raise ConfigError("服务地址不应包含 /openapi/v2 或 /openapi/v1。")
    return value


def validate_key(value):
    if not isinstance(value, str) or not value.strip() or any(c in value for c in "\r\n"):
        raise ConfigError("API Key 不能为空或包含换行。请重新配置。")
    return value.strip()


def service_defaults():
    try:
        values = json.loads((Path(__file__).resolve().parents[1] / "service.json").read_text(encoding="utf-8"))
        return {key: validate_url(values[key]) for key in ("base_url", "online_base_url")}
    except (OSError, KeyError, TypeError, ValueError):
        raise ConfigError("安装包的服务配置损坏，请重新安装。") from None


def load_config():
    path = config_path()
    if not path.exists():
        return {}
    try:
        values = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ConfigError("无法读取本地配置，请运行 setup 重新配置。") from None
    if not isinstance(values, dict):
        raise ConfigError("本地配置格式错误，请运行 setup 重新配置。")
    result = {}
    if "base_url" in values:
        result["base_url"] = validate_url(values["base_url"])
    if "api_key" in values:
        result["api_key"] = validate_key(values["api_key"])
    return result


def resolve_settings(base_url=None, api_key=None):
    # Explicit arguments > environment > saved configuration > release defaults.
    base_url = base_url or os.environ.get("SCHOLAR_BASE_URL")
    api_key = api_key or os.environ.get("SCHOLAR_OPENAPI_KEY")
    saved = load_config() if not (base_url and api_key) else {}
    base_url = base_url or saved.get("base_url") or service_defaults()["base_url"]
    api_key = api_key or saved.get("api_key")
    if not api_key:
        raise ConfigError("尚未配置 API Key。请运行 linxsci-scholar setup，或安装包内的 install.py。")
    return validate_url(base_url), validate_key(api_key)


def save_config(base_url, api_key):
    values = {"base_url": validate_url(base_url), "api_key": validate_key(api_key)}
    path = config_path()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.is_symlink():
        raise ConfigError("配置文件不能是符号链接，请选择普通配置文件。")
    fd, temporary = tempfile.mkstemp(prefix=".config-", dir=path.parent)
    try:
        if os.name != "nt":
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(values, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return path


def clear_config():
    path = config_path()
    if path.is_symlink():
        raise ConfigError("配置文件不能是符号链接。")
    path.unlink(missing_ok=True)
    return path
