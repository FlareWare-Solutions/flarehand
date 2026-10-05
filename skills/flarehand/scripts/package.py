#!/usr/bin/env python3
"""package.py - build the files you hand to someone else.

For each skill, three archives with the same contents in different wrappers:

  <skill>.skill    Claude Desktop. Double-click, or drop it in a chat, and a "Save skill" button
                   appears. It is a zip with a different extension.
  <skill>.zip      Everything else: Windows, macOS, Linux, the claude.ai upload, and any agent that
                   reads a skills folder.
  <skill>.tar.gz   Linux. tar is on every machine. unzip often is not.

And one plugin folder:

  flarehand-plugin/   The whole plugin: every skill, the hooks, and the manifest for each tool
                      (Claude, Codex, Cursor, Gemini), plus the eval cases at its root, where
                      `claude plugin eval` looks.

Every archive holds one folder named after the skill, with SKILL.md inside it. That is the shape
Claude Desktop, claude.ai and the skills folders all expect. The entry-point skills
(flarehand-remember and the rest) hand over to the flarehand skill, so install them beside it.

Run inside the repository (skills/<name>/scripts/package.py, with .claude-plugin/plugin.json two
levels up), it builds every skill under skills/ and takes the version from that plugin.json. Run in
a skill folder on its own, it builds that skill, and a plugin folder with a generated manifest and
no hooks, taking the version from the `flarehand.version` metadata in SKILL.md.

The build is reproducible. File order is sorted and timestamps are fixed, so the same source
always produces the same bytes and the same checksum. If a checksum changes, the contents changed.

Usage
  python3 scripts/package.py
  python3 scripts/package.py --out ~/Desktop
  python3 scripts/package.py --formats skill zip
  python3 scripts/package.py --check          # verify only, build nothing

Exit codes: 0 built and verified, 1 a check failed, 2 usage or file error.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
NAME = SKILL_DIR.name

# A fixed timestamp keeps the build reproducible. Zip cannot store a year before 1980.
FIXED_TIME = (1980, 1, 1, 0, 0, 0)

# Tool and editor folders never ship, wherever they sit. Build output and eval results are
# excluded only at the top level, so a future assets/results/ still ships.
EXCLUDE_DIRS = {".git", "__pycache__", ".pytest_cache", ".idea", ".vscode"}
EXCLUDE_TOP = {"dist", "results"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".zip", ".skill", ".tar", ".gz", ".log", ".redacted", ".swp", ".orig", ".rej"}

# What the plugin folder carries from the repository root, besides skills/. docs/, tools/ and the
# contributor files stay in the repository.
PLUGIN_ROOT_FILES = (".claude-plugin", ".codex-plugin", ".cursor-plugin", ".agents/plugins", "hooks",
                     "gemini-extension.json", "GEMINI.md", "AGENTS.md", "README.md", "LICENSE", "CHANGELOG.md")

# Operating systems leave litter in every folder you open. None of it belongs in
# something you email to a colleague, and a stray file inside a skill archive
# looks careless at best. Matching on an exact filename is not enough: an
# AppleDouble fork is named after the file it shadows, so it needs a prefix rule.
STRAY = [
    re.compile(r"(^|/)\.DS_Store$"),          # Finder folder state
    re.compile(r"(^|/)\._[^/]*$"),            # AppleDouble resource forks
    re.compile(r"^__MACOSX/"),                # what Finder's Compress adds
    re.compile(r"(^|/)Icon\r?$"),             # Finder custom folder icon
    re.compile(r"(^|/)\.AppleDouble(/|$)"),
    re.compile(r"(^|/)\.AppleDB(/|$)"),
    re.compile(r"(^|/)\.AppleDesktop(/|$)"),
    re.compile(r"(^|/)\.Spotlight-V100(/|$)"),
    re.compile(r"(^|/)\.fseventsd(/|$)"),
    re.compile(r"(^|/)\.TemporaryItems(/|$)"),
    re.compile(r"(^|/)\.Trashes(/|$)"),
    re.compile(r"(^|/)\.VolumeIcon\.icns$"),
    re.compile(r"(^|/)\.com\.apple\.timemachine"),
    re.compile(r"(^|/)\.apdisk$"),
    re.compile(r"(^|/)\.localized$"),
    re.compile(r"(?i)(^|/)Thumbs\.db$"),       # Windows
    re.compile(r"(?i)(^|/)ehthumbs\.db$"),
    re.compile(r"(?i)(^|/)desktop\.ini$"),
    re.compile(r"(^|/)\.directory$"),          # Linux, KDE
    re.compile(r"(^|/)\.Trash-\d+(/|$)"),
    re.compile(r"(^|/)\.nfs[0-9a-f]{8,}$"),
    re.compile(r"(^|/)\.gitignore$"),
    re.compile(r"(^|/)\.gitkeep$"),
    re.compile(r"(^|/)__pycache__(/|$)"),
    re.compile(r"(^|/)\.tmp$"),                # scratch files left by tools
    re.compile(r"\.tmp$"),
    re.compile(r"(^|/)\.[^/]*\.tmp-\d+$"),     # an interrupted atomic write
    re.compile(r"~$"),                         # editor backups
    re.compile(r"(^|/)\.#"),                   # emacs lock files
    re.compile(r"(^|/)\.~lock\."),              # LibreOffice lock files
]


def is_stray(rel_posix: str) -> bool:
    return any(p.search(rel_posix) for p in STRAY)


def find_repo_root(skill_dir: Path = SKILL_DIR) -> Path | None:
    """The repository root when this skill sits at <root>/skills/<name>/, else None."""
    root = skill_dir.parent.parent
    if skill_dir.parent.name == "skills" and (root / ".claude-plugin" / "plugin.json").is_file():
        return root
    return None


REPO_ROOT = find_repo_root()


def skill_dirs() -> list[Path]:
    """Every skill this build covers: all of skills/ in the repository, or this one on its own."""
    if REPO_ROOT is None:
        return [SKILL_DIR]
    return sorted(p for p in (REPO_ROOT / "skills").iterdir() if (p / "SKILL.md").is_file())


def collect(out_dir: Path | None = None, base: Path = SKILL_DIR) -> list[Path]:
    """Every file that ships from one folder, sorted so the archive is byte-stable.

    Nothing under out_dir ships, so a previous build in the output folder never
    gets packaged into the next one."""
    out = []
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(base)
        if rel.parts[0] in EXCLUDE_TOP or any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if out_dir is not None and _inside(path, out_dir):
            continue
        if path.suffix.lower() in EXCLUDE_SUFFIXES:
            continue
        if is_stray(rel.as_posix()):
            continue
        out.append(rel)
    return sorted(out, key=lambda p: p.as_posix())


def entries_for(skill: Path, out_dir: Path | None) -> list[tuple[str, Path]]:
    """(path inside the skill folder, source file). A skill shipped alone carries the licence."""
    entries = [(rel.as_posix(), skill / rel) for rel in collect(out_dir, skill)]
    names = {name for name, _ in entries}
    if REPO_ROOT is not None and (REPO_ROOT / "LICENSE").is_file() and "LICENSE" not in names:
        entries.append(("LICENSE", REPO_ROOT / "LICENSE"))
    return sorted(entries)


def _inside(path: Path, folder: Path) -> bool:
    try:
        path.resolve().relative_to(folder.resolve())
        return True
    except ValueError:
        return False


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# Files a runner may execute directly: the scripts, the hook launcher (hooks/run-hook.cmd, which
# Cursor runs by path), and eval scaffold scripts (seed.sh, which `claude plugin eval --scaffold` runs).
EXECUTABLE_SUFFIXES = (".py", ".cmd", ".sh")


def _mode(name: str) -> int:
    # keep the executable bit on scripts, drop every other mode difference
    return 0o755 if name.endswith(EXECUTABLE_SUFFIXES) else 0o644


def build_zip(target: Path, entries: list[tuple[str, Path]], name: str = NAME) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel, src in entries:
            info = zipfile.ZipInfo(f"{name}/{rel}", date_time=FIXED_TIME)
            # regular-file type plus permissions, both in the high word where unzip reads them
            info.external_attr = (stat.S_IFREG | _mode(rel)) << 16
            # record Unix as the creator on every platform, or a Windows build differs by one byte
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, src.read_bytes())
    return target


def build_tar(target: Path, entries: list[tuple[str, Path]], name: str = NAME) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as tar:
        for rel, src in entries:
            data = src.read_bytes()
            info = tarfile.TarInfo(f"{name}/{rel}")
            info.size = len(data)
            info.mtime = 0
            info.mode = _mode(rel)
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            tar.addfile(info, io.BytesIO(data))
    # mtime=0 in the gzip header too, or the checksum moves every build
    with open(target, "wb") as fh:
        fh.write(gzip.compress(raw.getvalue(), compresslevel=9, mtime=0))
    return target


def _copy(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
    dest.chmod(_mode(dest.name))


def skill_metadata(skill: Path = SKILL_DIR) -> dict:
    """`flarehand.version` and `flarehand.owner` from a SKILL.md's metadata block."""
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    out = {}
    m = re.search(r"flarehand\.version:\s*[\"']?([0-9][^\"'\n]*)[\"']?", text)
    if m:
        out["version"] = m.group(1).strip()
    m = re.search(r"flarehand\.owner:\s*[\"']?([^\"'\n]+)[\"']?", text)
    if m:
        out["owner"] = m.group(1).strip()
    return out


def plugin_manifest() -> dict:
    if REPO_ROOT is not None:
        return json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    meta = skill_metadata()
    return {
        "name": NAME,
        "version": meta.get("version", "0.0.0"),
        "description": "Turns a vague ask into the right deliverable, grounded in real sources, "
                       "and remembers only what you approve.",
        "author": {"name": meta.get("owner", "Flareware")},
        "license": "MIT",
    }


def build_plugin(target: Path, out_dir: Path | None) -> Path:
    """The plugin folder. Built fresh each time, so nothing stale survives."""
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    if REPO_ROOT is not None:
        for item in PLUGIN_ROOT_FILES:
            src = REPO_ROOT / item
            if src.is_file():
                _copy(src, target / item)
            elif src.is_dir():
                for rel in collect(out_dir, src):
                    _copy(src / rel, target / item / rel)
    else:
        (target / ".claude-plugin").mkdir(parents=True)
        (target / ".claude-plugin" / "plugin.json").write_text(
            json.dumps(plugin_manifest(), indent=2) + "\n", encoding="utf-8")
    repo_evals = REPO_ROOT is not None and (REPO_ROOT / "evals").is_dir()
    if repo_evals:
        for rel in collect(out_dir, REPO_ROOT / "evals"):
            _copy(REPO_ROOT / "evals" / rel, target / "evals" / rel)
    for skill in skill_dirs():
        for rel in collect(out_dir, skill):
            if rel.parts[0] == "evals":
                if not repo_evals and skill.name == NAME:
                    _copy(skill / rel, target / rel)  # eval cases sit at the plugin root, where the runner looks
                continue
            _copy(skill / rel, target / "skills" / skill.name / rel)
    return target


def verify_archive(path: Path, name: str = NAME) -> list[str]:
    """Check the shape a client actually requires."""
    problems = []
    if path.suffix in (".zip", ".skill"):
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            bad = z.testzip()
            if bad:
                problems.append(f"{path.name}: corrupt entry {bad}")
    else:
        with tarfile.open(path, "r:gz") as tar:
            names = tar.getnames()

    # Claude Desktop refuses anything larger, with "Skill file is too large.
    # Maximum size is 30 MB." The check is a stat before the read, so a big
    # archive fails at the door rather than part way in.
    max_bytes = 30 * 1024 * 1024
    if path.stat().st_size > max_bytes:
        problems.append(f"{path.name}: {path.stat().st_size / 1024 / 1024:.1f} MB is over the 30 MB "
                        f"limit Claude Desktop enforces.")

    # Exclusion happens on the way in. This checks on the way out, because a
    # build that silently ships litter is worse than one that fails loudly.
    litter = sorted({n for n in names if is_stray(n)})
    if litter:
        problems.append(f"{path.name}: operating system litter got packaged: {litter[:6]}")

    if f"{name}/SKILL.md" not in names:
        problems.append(f"{path.name}: no {name}/SKILL.md at the archive root. "
                        f"Claude Desktop and claude.ai both need that exact shape.")
    roots = {n.split("/")[0] for n in names if n}
    if roots != {name}:
        problems.append(f"{path.name}: archive root should hold only `{name}/`, found {sorted(roots)}")
    return problems


def verify_plugin(plugin_dir: Path) -> list[str]:
    problems = []
    for skill in skill_dirs():
        if not (plugin_dir / "skills" / skill.name / "SKILL.md").is_file():
            problems.append(f"{plugin_dir.name}: skills/{skill.name}/SKILL.md is missing")
    if not (plugin_dir / ".claude-plugin" / "plugin.json").is_file():
        problems.append(f"{plugin_dir.name}: .claude-plugin/plugin.json is missing")
    if (plugin_dir / "bin").exists():
        problems.append(f"{plugin_dir.name}: a top-level bin/ blocks the claude.ai and Cowork install")
    litter = [p for p in plugin_dir.rglob("*") if is_stray(p.relative_to(plugin_dir).as_posix())]
    if litter:
        problems.append(f"{plugin_dir.name}: operating system litter got copied: {litter[:3]}")
    return problems


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass
    ap = argparse.ArgumentParser(prog="package.py", description="Build the shareable archives and the plugin folder.")
    ap.add_argument("--out", help="where to write them (default: dist/ at the repository root, or beside the skill folder)")
    ap.add_argument("--formats", nargs="+", choices=["skill", "zip", "tar.gz", "plugin"],
                    default=["skill", "zip", "tar.gz", "plugin"], help="which outputs to build")
    ap.add_argument("--check", action="store_true", help="verify the skills and stop, build nothing")
    ap.add_argument("--skip-validate", action="store_true", help="package even if validation fails")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if not (SKILL_DIR / "SKILL.md").is_file():
        print("error: no SKILL.md to package", file=sys.stderr)
        return 2

    # never ship something that will not load
    if not args.skip_validate:
        r = subprocess.run([sys.executable, str(SKILL_DIR / "scripts" / "validate_skill.py")],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print("Not packaging. The skill does not pass its own validation:\n", file=sys.stderr)
            print(r.stdout, file=sys.stderr)
            print("Fix it, or pass --skip-validate if you know what you are doing.", file=sys.stderr)
            return 1

    default_out = (REPO_ROOT / "dist") if REPO_ROOT is not None else SKILL_DIR.parent / "dist"
    out_dir = Path(args.out).expanduser() if args.out else default_out
    # An output folder inside a skill would be packaged into itself. Only that skill's dist/ is safe,
    # because it never ships.
    for skill in skill_dirs():
        if _inside(out_dir, skill) and out_dir.resolve() != (skill / "dist").resolve():
            print(f"error: --out {out_dir} is inside the skill folder. Use a folder outside it, "
                  f"or {skill / 'dist'}, which never ships.", file=sys.stderr)
            return 2

    skills = skill_dirs()
    entries = {skill.name: entries_for(skill, out_dir) for skill in skills}
    total_files = sum(len(e) for e in entries.values())

    if args.check:
        total = sum(src.stat().st_size for e in entries.values() for _, src in e)
        print(f"{len(skills)} skill(s), {total_files} files, {total / 1024:.0f} KB uncompressed. Validation passed.")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)

    built: list[tuple[Path, str]] = []
    for skill in skills:
        name = skill.name
        if "zip" in args.formats or "skill" in args.formats:
            with tempfile.TemporaryDirectory() as tmp:
                staged = build_zip(Path(tmp) / f"{name}.zip", entries[name], name)
                for fmt in ("skill", "zip"):
                    if fmt in args.formats:
                        # identical bytes, different extension, exactly as the Desktop app describes it
                        dest = out_dir / f"{name}.{fmt}"
                        shutil.copyfile(staged, dest)
                        built.append((dest, name))
        if "tar.gz" in args.formats:
            built.append((build_tar(out_dir / f"{name}.tar.gz", entries[name], name), name))

    plugin_dir = None
    if "plugin" in args.formats:
        plugin_dir = build_plugin(out_dir / f"{plugin_manifest().get('name', NAME)}-plugin", out_dir)

    problems = []
    for path, name in built:
        problems += verify_archive(path, name)
    if plugin_dir is not None:
        problems += verify_plugin(plugin_dir)

    results = [{"file": str(p), "skill": n, "bytes": p.stat().st_size, "sha256": sha256(p)} for p, n in built]

    if args.json:
        print(json.dumps({"skills": [s.name for s in skills], "files_packaged": total_files,
                          "version": plugin_manifest().get("version"), "archives": results,
                          "plugin": str(plugin_dir) if plugin_dir else None, "problems": problems}, indent=2))
    else:
        print(f"Packaged {len(skills)} skill(s), {total_files} files, into {out_dir}\n")
        for r in results:
            print(f"  {Path(r['file']).name:30} {r['bytes'] / 1024:7.0f} KB   sha256 {r['sha256'][:16]}...")
        if plugin_dir:
            print(f"  {plugin_dir.name + '/':30}   folder   for claude plugin eval and a local marketplace")
        print()
        if problems:
            for p in problems:
                print(f"  PROBLEM  {p}")
        else:
            print("  Every archive holds one folder with SKILL.md inside it, which is the shape")
            print("  Claude Desktop, claude.ai and the skills folders all expect.")
        print("\nInstall instructions for each tool are in references/cross-tool.md.")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
