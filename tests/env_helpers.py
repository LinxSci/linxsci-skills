"""Isolate application settings without breaking Windows system services."""
import os


def isolated_environment(overrides=None):
    # OpenSSL's Windows initialization needs the system directory. Clearing
    # these alongside application credentials can fail before a mocked request.
    environment = {name: os.environ[name] for name in ("SYSTEMROOT", "WINDIR")
                   if name in os.environ}
    environment.update(overrides or {})
    return environment
