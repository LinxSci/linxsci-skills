import contextlib
import io
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from env_helpers import isolated_environment

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/linxsci-base/scripts"
sys.path.insert(0, str(SCRIPTS))
from commands import main, doctor, error_info
from client import LinxSciClient, LinxSciError, Response
from config import config_path, load_config, resolve_settings, save_config
from installer import LEGACY_SKILL_NAME, MARKER, SKILL_NAME, install_skill


class OnboardingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = patch.dict(os.environ, isolated_environment({"LINXSCI_CONFIG_FILE": str(self.root / "settings/config.json")}), clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def invoke(self, args, stdin=""):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors), patch("sys.stdin", io.StringIO(stdin)):
            status = main(args)
        return status, output.getvalue(), errors.getvalue()

    def test_setup_and_desktop_configuration(self):
        status, out, err = self.invoke(["setup", "--api-key-stdin", "--no-check"], "test-secret\n")
        self.assertEqual(status, 0, err)
        self.assertNotIn("test-secret", out + err)
        client = LinxSciClient()  # A fresh process need not inherit terminal exports.
        self.assertEqual(client.base_url, "https://linxsci.com")
        self.assertEqual(client.api_key, "test-secret")
        if os.name != "nt":
            self.assertEqual(stat.S_IMODE(config_path().stat().st_mode), 0o600)

    def test_online_profile_and_hidden_interactive_key(self):
        with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", return_value=""), patch("getpass.getpass", return_value="hidden-secret"):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                status = main(["setup", "--online", "--no-check"])
        self.assertEqual(status, 0)
        self.assertEqual(load_config()["base_url"], "https://linxsci.com")
        self.assertNotIn("hidden-secret", out.getvalue())

    def test_priority_and_redaction(self):
        save_config("http://localhost:9090", "saved-secret")
        os.environ.update(LINXSCI_BASE_URL="https://linxsci.com", LINXSCI_OPENAPI_KEY="env-secret")
        self.assertEqual(resolve_settings(), ("https://linxsci.com", "env-secret"))
        self.assertEqual(resolve_settings("https://other.example", "explicit"), ("https://other.example", "explicit"))
        status, out, err = self.invoke(["config"])
        self.assertEqual(status, 0)
        self.assertNotIn("saved-secret", out + err)
        self.assertNotIn("env-secret", out + err)

    def test_bad_setup_preserves_valid_config_and_repair(self):
        save_config("http://localhost:9090", "old-key")
        original = config_path().read_bytes()
        status, out, err = self.invoke(["setup", "--api-key-stdin", "--no-check", "--base-url", "https://example.com/openapi/v2"], "new-key\n")
        self.assertEqual(status, 2)
        self.assertEqual(config_path().read_bytes(), original)
        config_path().write_text("{invalid", encoding="utf-8")
        status, out, err = self.invoke(["setup", "--api-key-stdin", "--no-check"], "repaired-key\n")
        self.assertEqual(status, 0, err)
        self.assertEqual(load_config()["api_key"], "repaired-key")

    def test_clear_and_missing_key(self):
        save_config("http://localhost:9090", "secret")
        self.assertEqual(self.invoke(["config", "--clear"])[0], 0)
        status, out, err = self.invoke(["doctor", "--json"])
        self.assertEqual(status, 2)
        self.assertFalse(json.loads(out)["ok"])
        self.assertNotIn("secret", out + err)

    def test_setup_refuses_echoing_key(self):
        import getpass
        with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", return_value=""), patch("getpass.getpass", side_effect=getpass.GetPassWarning("unsafe fallback")):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                status = main(["setup", "--no-check"])
        self.assertEqual(status, 2)
        self.assertFalse(config_path().exists())
        self.assertIn("隐藏", err.getvalue())

    def test_doctor_does_not_accept_html_or_expose_error_body(self):
        save_config("http://localhost:9090", "secret")
        with patch.object(LinxSciClient, "request", return_value=Response(200, {}, b"<html>login</html>")):
            status, out, err = self.invoke(["doctor", "--json"])
        self.assertEqual(status, 1)
        self.assertFalse(json.loads(out)["ok"])
        with patch.object(LinxSciClient, "request", side_effect=LinxSciError("unsafe", 401, {"error": {"message": "secret"}})):
            status, out, err = self.invoke(["search", "topic"])
        self.assertEqual(status, 1)
        self.assertNotIn("secret", out + err)
        self.assertIn("setup", err)

    def test_install_update_and_backup(self):
        parent = self.root / "agent/skills"
        destination, backup = install_skill(parent)
        self.assertEqual(destination.name, "linxsci-base")
        self.assertIsNone(backup)
        self.assertTrue((destination / "SKILL.md").is_file())
        self.assertTrue((destination / "scripts/config.py").is_file())
        self.assertTrue((destination / "references/api.md").is_file())
        with self.assertRaises(ValueError):
            install_skill(parent)
        (destination / "custom-note.txt").write_text("keep me", encoding="utf-8")
        new, backup = install_skill(parent, update=True)
        self.assertEqual(new, destination)
        self.assertEqual((backup / "custom-note.txt").read_text(), "keep me")
        self.assertNotEqual(backup.parent, parent)
        self.assertFalse((new / "custom-note.txt").exists())

    def legacy_install(self, parent):
        legacy = parent / LEGACY_SKILL_NAME
        legacy.mkdir(parents=True)
        (legacy / MARKER).write_text(json.dumps({"name": LEGACY_SKILL_NAME, "version": "0.3.2"}), encoding="utf-8")
        (legacy / "custom-note.txt").write_bytes(b"preserve old installation\x00")
        return legacy

    def test_migrate_legacy_installation_and_reuse_default_configuration(self):
        for platform in ("posix", "nt"):
            with self.subTest(platform=platform):
                home = self.root / platform
                appdata = home / "AppData/Local"
                expected_config = (appdata if platform == "nt" else home / ".config") / "linxsci-skills/config.json"
                expected_config.parent.mkdir(parents=True)
                original_config = b'{"base_url":"https://saved.example","api_key":"saved-migration-secret"}'
                expected_config.write_bytes(original_config)
                parent = home / ".agents/skills"
                legacy = self.legacy_install(parent)
                old_files = {p.name: p.read_bytes() for p in legacy.iterdir()}
                with patch.dict(os.environ, isolated_environment({"LOCALAPPDATA": str(appdata)}), clear=True), \
                        patch("config.os", SimpleNamespace(name=platform, environ=os.environ)), \
                        patch("pathlib.Path.home", return_value=home):
                    status, out, err = self.invoke(["install-skill", "--update"])
                    self.assertEqual(status, 0, err)
                    report = json.loads(out)
                    destination = Path(report["installed"])
                    backup = Path(report["backup"])
                    self.assertEqual(report["skill"], SKILL_NAME)
                    self.assertEqual(destination, (parent / SKILL_NAME).resolve())
                    self.assertEqual(config_path(), expected_config)
                    self.assertEqual(resolve_settings(), ("https://saved.example", "saved-migration-secret"))
                self.assertFalse(legacy.exists())
                self.assertEqual(json.loads((destination / MARKER).read_text())["name"], SKILL_NAME)
                self.assertEqual({p.name: p.read_bytes() for p in backup.iterdir()}, old_files)
                self.assertNotEqual(backup.parent, parent)
                self.assertEqual(expected_config.read_bytes(), original_config)
                self.assertNotIn("saved-migration-secret", out + err)

    def test_legacy_installation_requires_explicit_update(self):
        parent = self.root / "skills"
        legacy = self.legacy_install(parent)
        original = (legacy / MARKER).read_bytes()
        with self.assertRaisesRegex(ValueError, "--update"):
            install_skill(parent)
        self.assertEqual((legacy / MARKER).read_bytes(), original)
        self.assertFalse((parent / SKILL_NAME).exists())
        self.assertEqual(list(parent.iterdir()), [legacy])

    def test_legacy_unmanaged_or_invalid_marker_is_preserved(self):
        for index, marker in enumerate((None, "not json", "[]", '{"name":"another-skill"}')):
            with self.subTest(marker=marker):
                parent = self.root / str(index) / "skills"
                legacy = self.legacy_install(parent)
                marker_path = legacy / MARKER
                if marker is None:
                    marker_path.unlink()
                else:
                    marker_path.write_text(marker, encoding="utf-8")
                original = {p.name: p.read_bytes() for p in legacy.iterdir()}
                with self.assertRaises(ValueError):
                    install_skill(parent, update=True)
                self.assertEqual({p.name: p.read_bytes() for p in legacy.iterdir()}, original)
                self.assertEqual(list(parent.iterdir()), [legacy])

    def test_both_names_present_preserves_both_installations(self):
        parent = self.root / "skills"
        destination, _ = install_skill(parent)
        legacy = self.legacy_install(parent)
        for update in (False, True):
            with self.subTest(update=update):
                with self.assertRaisesRegex(ValueError, "同时存在"):
                    install_skill(parent, update=update)
                self.assertTrue((destination / "SKILL.md").is_file())
                self.assertEqual((legacy / "custom-note.txt").read_bytes(), b"preserve old installation\x00")
                self.assertEqual(set(parent.iterdir()), {destination, legacy})
                self.assertFalse((parent.parent / "linxsci-skill-backups").exists())

    def test_legacy_migration_failure_restores_original_path(self):
        parent = self.root / "skills"
        legacy = self.legacy_install(parent)
        original = {p.name: p.read_bytes() for p in legacy.iterdir()}
        real_replace = os.replace

        def replace(source, target):
            if Path(source).name.startswith(".linxsci-stage-"):
                raise OSError("simulated migration failure")
            return real_replace(source, target)

        with patch("installer.os.replace", side_effect=replace), self.assertRaises(OSError):
            install_skill(parent, update=True)
        self.assertEqual({p.name: p.read_bytes() for p in legacy.iterdir()}, original)
        self.assertEqual(list(parent.iterdir()), [legacy])

    def test_installer_refuses_current_and_legacy_symlinks(self):
        target = self.root / "external-copy"
        target.mkdir()
        (target / "user-note.txt").write_text("keep", encoding="utf-8")
        for name in (SKILL_NAME, LEGACY_SKILL_NAME):
            for dangling in (False, True):
                with self.subTest(name=name, dangling=dangling):
                    parent = self.root / (name + str(dangling)) / "skills"
                    parent.mkdir(parents=True)
                    link = parent / name
                    try:
                        link.symlink_to(target / "missing" if dangling else target, target_is_directory=True)
                    except (OSError, NotImplementedError):
                        self.skipTest("Directory symlinks unavailable on this platform")
                    with self.assertRaisesRegex(ValueError, "符号链接"):
                        install_skill(parent, update=True)
                    self.assertTrue(link.is_symlink())
                    self.assertEqual(list(parent.iterdir()), [link])
                    self.assertEqual((target / "user-note.txt").read_text(), "keep")

    def test_install_refuses_unmanaged_directory(self):
        parent = self.root / "skills"
        destination = parent / "linxsci-base"
        destination.mkdir(parents=True)
        user_file = destination / "SKILL.md"
        user_file.write_text("user content")
        with self.assertRaises(ValueError):
            install_skill(parent, update=True)
        self.assertEqual(user_file.read_text(), "user content")

    def test_installer_rollback(self):
        parent = self.root / "agent/skills"
        destination, _ = install_skill(parent)
        original = (destination / "SKILL.md").read_bytes()
        real_replace = os.replace
        def replace(source, target):
            if Path(source).name.startswith(".linxsci-stage-"):
                raise OSError("simulated failure")
            return real_replace(source, target)
        with patch("installer.os.replace", side_effect=replace), self.assertRaises(OSError):
            install_skill(parent, update=True)
        self.assertEqual((destination / "SKILL.md").read_bytes(), original)

    def test_raw_output_file(self):
        save_config("http://localhost:9090", "secret")
        binary = b"\x00\xffPDF asset"
        output = self.root / "asset.bin"
        with patch.object(LinxSciClient, "request", return_value=Response(200, {}, binary)):
            status, out, err = self.invoke(["--output", str(output), "paper", "arxiv:123", "--resource", "assets", "--item-id", "figure1"])
        self.assertEqual(status, 0, err)
        self.assertEqual(output.read_bytes(), binary)


if __name__ == "__main__":
    unittest.main()
