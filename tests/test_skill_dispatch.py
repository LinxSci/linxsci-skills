import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from env_helpers import isolated_environment

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/linxsci-base/scripts"
sys.path.insert(0, str(SCRIPTS))
import cli
import skill_dispatch


class SkillDispatchTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="linxsci-dispatch-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.skills = self.root / "installed skills 论文"
        self.work = self.root / "other working directory"
        self.skills.mkdir()
        self.work.mkdir()
        self.env = isolated_environment({
            "LINXSCI_SKILLS_DIR": str(self.skills),
            "LINXSCI_CONFIG_FILE": str(self.root / "config.json"),
            "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1",
        })
        environment = patch.dict(os.environ, self.env, clear=True)
        environment.start()
        self.addCleanup(environment.stop)

    def skill(self, name, code="raise SystemExit(0)\n", *, marker=True):
        directory = self.skills / ("linxsci-" + name)
        (directory / "scripts").mkdir(parents=True)
        if marker:
            (directory / "SKILL.md").write_text("# Fixture Skill\n", encoding="utf-8")
        script = directory / "scripts" / (name.replace("-", "_") + ".py")
        script.write_text(code, encoding="utf-8")
        return script

    def invoke(self, *args, **kwargs):
        return subprocess.run([sys.executable, str(SCRIPTS / "cli.py"), *args],
                              cwd=self.work, env=self.env, capture_output=True, timeout=20, **kwargs)

    def test_default_directory_and_explicit_override(self):
        with patch.object(Path, "home", return_value=self.root):
            with patch.dict(os.environ, {"LINXSCI_SKILLS_DIR": ""}):
                self.assertEqual(skill_dispatch.skills_directory(), self.root / ".agents/skills")
            self.assertEqual(skill_dispatch.skills_directory(), self.skills)
            with patch.dict(os.environ, {"LINXSCI_SKILLS_DIR": "~/custom skills"}):
                with patch.object(Path, "expanduser", return_value=self.root / "custom skills"):
                    self.assertEqual(skill_dispatch.skills_directory(), self.root / "custom skills")

    def test_relative_root_is_rejected_and_builtin_version_still_works(self):
        with patch.dict(os.environ, {"LINXSCI_SKILLS_DIR": "relative/skills"}):
            with self.assertRaises(skill_dispatch.SkillDispatchError):
                skill_dispatch.discover_skills()
            with contextlib.redirect_stdout(io.StringIO()) as output, self.assertRaises(SystemExit) as error:
                cli.main(["--version"])
            self.assertEqual(error.exception.code, 0)
            self.assertEqual(output.getvalue().strip(), cli.VERSION)

    def test_help_lists_complete_skills_without_executing_them(self):
        self.skill("paper-qa", "raise RuntimeError('must not run during discovery')\n")
        self.skill("survey")
        self.skill("missing-marker", marker=False)
        self.skill("missing-script").unlink()
        self.skill("search", "raise RuntimeError('must not override a built-in')\n")
        result = self.invoke("--help", encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("paper-qa", result.stdout)
        self.assertIn("survey", result.stdout)
        self.assertNotIn("missing-marker", result.stdout)
        self.assertNotIn("missing-script", result.stdout)
        self.assertEqual(skill_dispatch.discover_skills({"search"}), ["paper-qa", "survey"])
        self.assertEqual(result.stderr, "")

    def test_command_added_after_cli_installation_runs_without_registration(self):
        self.assertEqual(skill_dispatch.discover_skills(), [])
        self.skill("fresh-command", "print('new command')\n")
        result = self.invoke("fresh-command", encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "new command\n")

    def test_forwarded_arguments_interpreter_environment_and_cwd(self):
        script = self.skill("paper-qa", """import json, os, sys
from pathlib import Path
Path('relative-output.txt').write_text('fixture', encoding='utf-8')
print(json.dumps({'argv': sys.argv[1:], 'python': sys.executable, 'cwd': os.getcwd(),
                  'config': os.environ.get('LINXSCI_CONFIG_FILE')}, ensure_ascii=False))
""")
        arguments = ["doi:10.1000/a", "--question", '方法 "quoted" $(false) `false` $VALUE ; &',
                     "--section-id", "sec:方法/1", "--section-id", "sec:2", "--timeout", "-1", "--", "-query"]
        result = self.invoke("paper-qa", *arguments, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["argv"], arguments)
        self.assertEqual(Path(data["python"]), Path(sys.executable))
        self.assertEqual(Path(data["cwd"]).resolve(), self.work.resolve())
        self.assertEqual(data["config"], self.env["LINXSCI_CONFIG_FILE"])
        self.assertTrue((self.work / "relative-output.txt").is_file())
        self.assertFalse((script.parent / "relative-output.txt").exists())

    def test_standard_streams_and_nonzero_exit_status_are_preserved(self):
        self.skill("stream", "import sys\nsys.stdout.buffer.write(sys.stdin.buffer.read())\n"
                   "sys.stderr.buffer.write(b'fixture-stderr\\n')\nraise SystemExit(7)\n")
        content = b"\x00\xffinput\n"
        result = self.invoke("stream", input=content)
        self.assertEqual(result.returncode, 7)
        self.assertEqual(result.stdout, content)
        self.assertEqual(result.stderr, b"fixture-stderr\n")

    def test_script_help_is_forwarded(self):
        self.skill("sample", "import argparse\np=argparse.ArgumentParser(description='Fixture help')\n"
                   "p.add_argument('--question', required=True)\np.parse_args()\n")
        result = self.invoke("sample", "--help", encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Fixture help", result.stdout)
        self.assertIn("--question", result.stdout)

    def test_missing_skill_and_entrypoint_have_installation_hints(self):
        missing = self.invoke("paper-qa", "--help", encoding="utf-8")
        self.assertEqual(missing.returncode, 2)
        error = json.loads(missing.stderr)
        self.assertEqual(error["error_code"], "invalid_arguments")
        self.assertIn("LINXSCI_SKILLS_DIR", error["message"])
        self.skill("paper-qa").unlink()
        incomplete = self.invoke("paper-qa", "--help", encoding="utf-8")
        self.assertEqual(incomplete.returncode, 2)
        self.assertIn("paper_qa.py", json.loads(incomplete.stderr)["message"])
        self.assertNotIn("Traceback", incomplete.stderr)

    def test_cwd_and_nested_skills_are_not_discovered(self):
        local = self.work / "linxsci-paper-qa"
        (local / "scripts").mkdir(parents=True)
        (local / "SKILL.md").write_text("# Local fixture\n")
        (local / "scripts/paper_qa.py").write_text("print('must not run')\n")
        nested = self.skills / "nested/linxsci-survey"
        (nested / "scripts").mkdir(parents=True)
        (nested / "SKILL.md").write_text("# Nested fixture\n")
        (nested / "scripts/survey.py").write_text("print('must not run')\n")
        self.assertEqual(skill_dispatch.discover_skills(), [])
        for name in ("paper-qa", "survey"):
            result = self.invoke(name, encoding="utf-8")
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, "")

    def test_invalid_command_names_never_start_a_process(self):
        with patch.object(skill_dispatch.subprocess, "run") as run:
            for name in ("../paper-qa", "../outside", "/tmp/script", "paper_qa", "Paper-QA", "a--b", "x\\y"):
                with self.subTest(name=name), self.assertRaises(skill_dispatch.SkillDispatchError):
                    skill_dispatch.run_skill(name, [])
            run.assert_not_called()

    def test_builtins_take_precedence_over_skill_folders(self):
        self.skill("setup", "raise RuntimeError('must not run')\n")
        with patch.object(cli, "run_skill") as run, contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                cli.main(["setup", "--help"])
            self.assertEqual(error.exception.code, 0)
            run.assert_not_called()

    def test_explicit_skill_route_handles_builtin_name_collisions(self):
        self.skill("paper", "import json,sys\nprint(json.dumps(sys.argv[1:]))\n")
        result = self.invoke("skill", "paper", "--help", "--output", "a file.json", encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), ["--help", "--output", "a file.json"])
        builtin = self.invoke("paper", "--help", encoding="utf-8")
        self.assertEqual(builtin.returncode, 0, builtin.stderr)
        self.assertIn("--resource", builtin.stdout)
        route_help = self.invoke("skill", "--help", encoding="utf-8")
        self.assertEqual(route_help.returncode, 0, route_help.stderr)
        self.assertIn("skill_name", route_help.stdout)

    def test_linked_skill_directory_is_supported(self):
        script = self.skill("sample", "print('linked skill')\n")
        external = self.root / "external sample"
        script.parent.parent.rename(external)
        try:
            (self.skills / "linxsci-sample").symlink_to(external, target_is_directory=True)
        except OSError as error:
            self.skipTest("Directory symlinks unavailable: " + str(error))
        result = self.invoke("sample", encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "linked skill\n")

    def test_missing_directory_and_invalid_directory_type(self):
        with patch.dict(os.environ, {"LINXSCI_SKILLS_DIR": str(self.root / "absent")}):
            self.assertEqual(skill_dispatch.discover_skills(), [])
        file = self.root / "not-a-directory"
        file.write_text("fixture")
        with patch.dict(os.environ, {"LINXSCI_SKILLS_DIR": str(file)}):
            with self.assertRaises(skill_dispatch.SkillDispatchError):
                skill_dispatch.discover_skills()
        self.skill("unreadable")
        with patch.object(Path, "is_file", side_effect=PermissionError):
            self.assertEqual(skill_dispatch.discover_skills(), [])

    def test_launch_error_and_interrupt_are_handled(self):
        self.skill("sample")
        with patch.object(skill_dispatch.subprocess, "run", side_effect=OSError):
            with self.assertRaises(skill_dispatch.SkillDispatchError):
                skill_dispatch.run_skill("sample", [])
        with patch.object(skill_dispatch.subprocess, "run", side_effect=KeyboardInterrupt):
            self.assertEqual(skill_dispatch.run_skill("sample", []), 130)
        with patch.object(skill_dispatch.subprocess, "run", return_value=subprocess.CompletedProcess([], -15)):
            self.assertEqual(skill_dispatch.run_skill("sample", []), 143)


if __name__ == "__main__":
    unittest.main()
