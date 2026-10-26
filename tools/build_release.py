#!/usr/bin/env python3
"""Build a wheel, sdist and dependency-free user bundle; never upload."""
import argparse
import hashlib
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def bundle(output):
    metadata = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    version = re.search(r'^version = "([^"]+)"', metadata, re.MULTILINE).group(1)
    output.mkdir(parents=True, exist_ok=True)
    target = output / ("linxsci-skills-" + version + ".zip")
    # Explicit allowlist prevents accidentally shipping local settings or credentials.
    files = [ROOT / name for name in ("install.py", "Install.command", "Install.bat")]
    skill = ROOT / "skills/linxsci-skills"
    files += [skill / "SKILL.md", skill / "SKILL.zh-CN.md", skill / "service.json", skill / "__init__.py"]
    for directory, pattern in (("scripts", "*.py"), ("references", "*.md"), ("agents", "*.yaml")):
        files += list((skill / directory).glob(pattern))
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        # The standalone bundle opens with the Skill guide, not the multi-interface
        # repository README. Agent instructions and references remain complete.
        for language in ("", ".zh-CN"):
            guide = (ROOT / ("docs/USER_GUIDE" + language + ".md")).read_text(encoding="utf-8")
            guide = guide.replace("(USER_GUIDE.md)", "(README.md)").replace(
                "(USER_GUIDE.zh-CN.md)", "(README.zh-CN.md)")
            archive.writestr("linxsci-skills-" + version + "/README" + language + ".md", guide)
        for source in sorted(files):
            name = "linxsci-skills-" + version + "/" + source.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo.from_file(source, name)
            # Windows builders must also produce a usable macOS launcher.
            if source.name == "Install.command":
                info.create_system = 3
                info.external_attr = 0o100755 << 16
            archive.writestr(info, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
    artifacts = [p for p in output.iterdir() if p.name.endswith((".whl", ".tar.gz", ".zip"))]
    sums = output / "SHA256SUMS"
    sums.write_text("".join(hashlib.sha256(p.read_bytes()).hexdigest() + "  " + p.name + "\n"
                            for p in sorted(artifacts)), encoding="utf-8")
    print(target)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-only", action="store_true", help="Build ZIP without Python build dependencies")
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    if not args.bundle_only:
        subprocess.run([sys.executable, "-m", "build", "--outdir", str(args.output.resolve()), str(ROOT)], check=True)
    bundle(args.output.resolve())


if __name__ == "__main__":
    main()
