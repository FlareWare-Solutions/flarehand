"""tests_core_packaging.py - packaging, validation, the manifests, the hooks and the version tool.

Loaded by tests/test_scripts.py, and runnable on its own. The tests that need the plugin repository
around the skill (manifests, hooks, the version tool) skip when the skill sits on its own.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "flarehand"
REPO = ROOT if (ROOT / ".claude-plugin" / "plugin.json").is_file() else None
SKILLS = sorted(p for p in (REPO / "skills").iterdir() if (p / "SKILL.md").is_file()) if REPO else [SKILL]
ENTRY_POINTS = ("flarehand-remember", "flarehand-ground", "flarehand-grill", "flarehand-review")
ACTIONS = ("session-start", "prompt-submit", "stop", "pre-compact", "session-end")
HOST_VARS = ("CURSOR_PLUGIN_ROOT", "COPILOT_CLI", "CODEX_HOME", "CODEX_PLUGIN_ROOT", "CODEX_SANDBOX",
             "CLAUDE_PLUGIN_ROOT", "PLUGIN_ROOT")
sys.path.insert(0, str(SKILL / "scripts"))

import kb  # noqa: E402
import voice_gate  # noqa: E402

needs_repo = unittest.skipIf(REPO is None, "the skill is not inside the plugin repository")


def run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SKILL / "scripts" / script), *args],
        capture_output=True, text=True, timeout=120,
    )


def frontmatter(path: Path) -> dict:
    meta, _ = kb.parse_frontmatter(path.read_text(encoding="utf-8"))
    return meta


# ---------------------------------------------------------------- the skill folders


class TestPackaging(unittest.TestCase):
    def test_validator_passes(self):
        r = run("validate_skill.py")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_no_file_type_that_blocks_an_install(self):
        root = REPO or SKILL
        bad = [p for p in root.rglob("*") if ".git" not in p.parts and p.suffix.lower() in
               {".ps1", ".psm1", ".app", ".pkg", ".command", ".exe", ".dll"}]
        self.assertEqual(bad, [], f"these break a download install: {bad}")

    def test_no_folder_that_turns_a_skill_into_a_plugin(self):
        for skill in SKILLS:
            for name in ("agents", "hooks", "workflows", "monitors", "themes", ".claude-plugin"):
                with self.subTest(skill=skill.name, folder=name):
                    self.assertFalse((skill / name).is_dir(), f"{name}/ makes Claude Code adopt this as a plugin")

    def test_scripts_never_block_on_input(self):
        for path in (SKILL / "scripts").glob("*.py"):
            with self.subTest(script=path.name):
                r = run(path.name, "--help")
                self.assertEqual(r.returncode, 0, f"{path.name} --help failed: {r.stderr}")

    def test_every_sibling_suite_actually_runs(self):
        """_load_extra_tests hoists unittest classes, so a suite written any other way is
        silently skipped."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_suite_probe", Path(__file__).resolve().parent / "test_scripts.py")
        suite = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(suite)
        loaded = [k for k in vars(suite) if k.startswith("tests_")]
        for path in sorted(Path(__file__).resolve().parent.glob("tests_*.py")):
            with self.subTest(suite=path.name):
                self.assertTrue(any(k.startswith(path.stem + "_") for k in loaded),
                                f"{path.name} contributes no test to this suite")

    @needs_repo
    def test_executable_in_git_exactly_when_there_is_a_shebang(self):
        """A file runs by path only with a shebang, so git marks it executable exactly then. The hook
        launcher is the one exception: it is a cmd and sh polyglot that Cursor runs directly."""
        if shutil.which("git") is None or not (REPO / ".git").exists():
            self.skipTest("not a git checkout")
        r = subprocess.run(["git", "-C", str(REPO), "ls-files", "-s", "--", "skills", "hooks", "tests", "evals"],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        for line in r.stdout.splitlines():
            meta, rel = line.split("\t", 1)
            path = REPO / rel
            if not path.is_file():
                continue
            with path.open("rb") as fh:
                shebang = fh.read(2) == b"#!"
            want = "100755" if shebang or rel == "hooks/run-hook.cmd" else "100644"
            with self.subTest(file=rel):
                self.assertEqual(meta.split()[0], want,
                                 f"fix with: git update-index --chmod={'+' if want == '100755' else '-'}x {rel}")

    def test_every_sibling_suite_runs_on_its_own(self):
        for path in sorted(Path(__file__).resolve().parent.glob("tests_*.py")):
            with self.subTest(suite=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertIn("__main__", text, f"{path.name} cannot be run on its own")
                self.assertIn("unittest.TestCase", text, f"{path.name} defines no unittest class")

    def test_every_data_file_the_scripts_need_exists(self):
        for name in ("router-table.tsv", "style-words.tsv", "redact-patterns.tsv", "contracts.tsv",
                     "review-lenses.tsv", "workflows.tsv", "workflow-graph.tsv"):
            self.assertTrue((SKILL / "assets" / name).is_file(), f"missing assets/{name}")

    def test_the_hooks_copy_inside_the_skill_is_gone(self):
        """Hooks live once, at the repository root. A second copy drifts."""
        self.assertFalse((SKILL / "assets" / "plugin-hooks.json").exists())

    def test_the_pipeline_writes_to_the_answer_cache(self):
        """recall.py reads answers/. If nothing in the pipeline calls answers.py write, no
        question ever replays. A table mention is not enough: it has to be in the pipeline."""
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        start = text.index("## The pipeline")
        pipeline = text[start:text.index("\n## ", start)]
        self.assertIn("answers.py", pipeline, "the pipeline never saves an answer, so the cache can never fill")
        self.assertIn("recall.py", pipeline, "the pipeline never checks the cache, so nothing ever replays")

    def test_every_script_is_invoked_somewhere(self):
        prose = "\n".join((s / "SKILL.md").read_text(encoding="utf-8") for s in SKILLS)
        for path in sorted((SKILL / "references").glob("*.md")):
            prose += "\n" + path.read_text(encoding="utf-8")
        prose += "\n" + (SKILL / "README.md").read_text(encoding="utf-8")
        for path in sorted((SKILL / "scripts").glob("*.py")):
            if path.name.startswith("_"):
                continue  # library modules are imported by scripts, not run by people
            with self.subTest(script=path.name):
                self.assertIn(f"scripts/{path.name}", prose,
                              f"{path.name} is never invoked anywhere, so it is dead weight")

    def test_every_contract_has_a_template(self):
        for line in (SKILL / "assets" / "contracts.tsv").read_text(encoding="utf-8").splitlines()[1:]:
            if not line.strip():
                continue
            wf = line.split("\t")[0]
            matches = list((SKILL / "assets" / "templates").glob(f"{wf}-*.md"))
            self.assertTrue(matches, f"no template for {wf}")


@needs_repo
class TestEntryPoints(unittest.TestCase):
    """Four thin skills, each handing over to the router with a fixed route."""

    FIRST_COMMANDS = {
        "flarehand-remember": "python3 ../flarehand/scripts/recall.py",
        "flarehand-ground": "python3 ../flarehand/scripts/ground.py lint -",
        "flarehand-grill": "python3 ../flarehand/scripts/classify.py",
        "flarehand-review": "python3 ../flarehand/scripts/review.py lenses",
    }

    def test_each_exists_with_portable_frontmatter_only(self):
        for name in ENTRY_POINTS:
            with self.subTest(skill=name):
                path = REPO / "skills" / name / "SKILL.md"
                self.assertTrue(path.is_file())
                meta = frontmatter(path)
                self.assertEqual(meta.get("name"), name)
                self.assertLessEqual(set(meta), {"name", "description", "license", "compatibility",
                                                 "metadata", "allowed-tools"})
                self.assertLessEqual(len(meta["description"]), 1024)
                self.assertNotIn("\u2014", path.read_text(encoding="utf-8"))

    def test_each_hands_over_to_the_router_with_its_first_command(self):
        for name, command in self.FIRST_COMMANDS.items():
            with self.subTest(skill=name):
                text = (REPO / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("../flarehand/SKILL.md", text)
                self.assertIn(command, text)

    def test_grill_credits_grill_me(self):
        text = (REPO / "skills" / "flarehand-grill" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("https://github.com/mattpocock/skills", text)
        self.assertIn("Matt Pocock", text)

    def test_descriptions_put_the_trigger_words_first(self):
        """Codex shortens descriptions before it drops them, so the first sentence carries the job."""
        for name in ENTRY_POINTS:
            with self.subTest(skill=name):
                desc = frontmatter(REPO / "skills" / name / "SKILL.md")["description"]
                self.assertIn("Use when", desc[:400])


# ---------------------------------------------------------------- the archives


class TestPackaging_Archives(unittest.TestCase):
    """The archives are what people actually receive. Wrong shape means a failed install."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="fh-pkg-"))
        r = run("package.py", "--out", str(cls.tmp), "--json", "--skip-validate")
        assert r.returncode == 0, r.stdout + r.stderr
        cls.result = json.loads(r.stdout)
        cls.files = {Path(a["file"]).name: a for a in cls.result["archives"]}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_all_three_formats_are_built_for_every_skill(self):
        for skill in SKILLS:
            for ext in ("skill", "zip", "tar.gz"):
                with self.subTest(skill=skill.name, ext=ext):
                    self.assertIn(f"{skill.name}.{ext}", self.files)

    def test_skill_and_zip_are_the_same_bytes(self):
        """A .skill file is a zip with a different extension. Not a different format."""
        self.assertEqual(self.files["flarehand.skill"]["sha256"], self.files["flarehand.zip"]["sha256"])

    def test_skill_file_is_really_a_zip(self):
        import zipfile
        self.assertTrue(zipfile.is_zipfile(self.tmp / "flarehand.skill"))

    def test_archive_root_matches_what_clients_expect(self):
        """Anthropic's own bundled skills are <name>/SKILL.md. Ours must match, for every skill."""
        import zipfile
        for skill in SKILLS:
            with self.subTest(skill=skill.name):
                with zipfile.ZipFile(self.tmp / f"{skill.name}.zip") as z:
                    names = z.namelist()
                self.assertIn(f"{skill.name}/SKILL.md", names)
                self.assertEqual({n.split("/")[0] for n in names}, {skill.name})

    def test_no_skill_archive_carries_tests_or_evals(self):
        """Tests and eval cases live at the repository root, never inside what a user installs."""
        import tarfile
        import zipfile
        for skill in SKILLS:
            for ext in ("skill", "zip", "tar.gz"):
                with self.subTest(skill=skill.name, ext=ext):
                    path = self.tmp / f"{skill.name}.{ext}"
                    if ext == "tar.gz":
                        with tarfile.open(path, "r:gz") as tar:
                            names = tar.getnames()
                    else:
                        with zipfile.ZipFile(path) as z:
                            names = z.namelist()
                    inside = {n.split("/")[1] for n in names if n.count("/") >= 1}
                    self.assertFalse(inside & {"evals", "tests"}, f"{path.name} ships {inside & {'evals', 'tests'}}")
                    self.assertFalse([n for n in names if re.search(r"(^|/)tests?_[^/]*\.py$", n)],
                                     f"{path.name} ships a test module")

    def test_tarball_has_the_same_shape(self):
        import tarfile
        with tarfile.open(self.tmp / "flarehand.tar.gz", "r:gz") as tar:
            names = tar.getnames()
        self.assertIn("flarehand/SKILL.md", names)
        self.assertEqual({n.split("/")[0] for n in names}, {"flarehand"})

    @needs_repo
    def test_a_skill_shipped_alone_carries_the_licence(self):
        import zipfile
        with zipfile.ZipFile(self.tmp / "flarehand-review.zip") as z:
            self.assertIn("MIT License", z.read("flarehand-review/LICENSE").decode("utf-8"))

    def test_build_is_reproducible(self):
        """Same source, same checksum. A changed hash means changed contents."""
        second = Path(tempfile.mkdtemp(prefix="fh-pkg2-"))
        try:
            r = run("package.py", "--out", str(second), "--json", "--skip-validate")
            again = {Path(a["file"]).name: a["sha256"] for a in json.loads(r.stdout)["archives"]}
            for name, meta in self.files.items():
                with self.subTest(archive=name):
                    self.assertEqual(meta["sha256"], again[name])
        finally:
            shutil.rmtree(second, ignore_errors=True)

    def test_no_junk_ships(self):
        import zipfile
        with zipfile.ZipFile(self.tmp / "flarehand.zip") as z:
            names = z.namelist()
        for junk in (".DS_Store", "__pycache__", ".pyc", "/dist/", "/results/"):
            with self.subTest(junk=junk):
                self.assertFalse([n for n in names if junk in n], f"{junk} got packaged")

    def test_scripts_keep_their_executable_bit(self):
        import zipfile
        with zipfile.ZipFile(self.tmp / "flarehand.zip") as z:
            info = z.getinfo("flarehand/scripts/kb.py")
        self.assertTrue((info.external_attr >> 16) & 0o100, "scripts lost the executable bit")

    def test_library_modules_ship_without_the_executable_bit(self):
        """A module with no shebang cannot run by path, so it ships 0644, as it is in git."""
        import tarfile
        import zipfile
        with zipfile.ZipFile(self.tmp / "flarehand.zip") as z:
            for name in ("_text.py", "_kb_learning.py"):
                with self.subTest(archive="zip", module=name):
                    self.assertEqual((z.getinfo(f"flarehand/scripts/{name}").external_attr >> 16) & 0o777, 0o644)
        with tarfile.open(self.tmp / "flarehand.tar.gz", "r:gz") as tar:
            self.assertEqual(tar.getmember("flarehand/scripts/_text.py").mode, 0o644)
            self.assertEqual(tar.getmember("flarehand/scripts/kb.py").mode, 0o755)

    def test_archives_are_well_under_the_desktop_limit(self):
        limit = 30 * 1024 * 1024
        for name, meta in self.files.items():
            with self.subTest(archive=name):
                self.assertLess(meta["bytes"], limit)

    def test_operating_system_litter_never_ships(self):
        """Plant every kind of OS droppings in a lone copy of the skill, then prove none of it
        reaches an archive. AppleDouble forks are named after the file they shadow, so an
        exact-filename exclusion list is not enough."""
        import tarfile
        import zipfile
        work = Path(tempfile.mkdtemp(prefix="fh-litter-"))
        try:
            target = work / "flarehand"
            shutil.copytree(SKILL, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "dist"))
            for rel in (".DS_Store", "references/.DS_Store", "assets/templates/.DS_Store",
                        "._SKILL.md", "references/._router.md", "scripts/._kb.py",
                        ".localized", ".apdisk") + (() if os.name == "nt" else ("Icon\r",)):
                (target / rel).write_bytes(b"x")
            for d in ("__MACOSX", ".Spotlight-V100", ".fseventsd", ".TemporaryItems", ".AppleDouble"):
                (target / d).mkdir(exist_ok=True)
                (target / d / "planted").write_bytes(b"x")
            (target / "Thumbs.db").write_bytes(b"x")
            (target / "references" / "desktop.ini").write_bytes(b"x")
            (target / ".directory").write_bytes(b"x")

            out = work / "dist"
            r = subprocess.run([sys.executable, str(target / "scripts" / "package.py"),
                                "--out", str(out), "--json", "--skip-validate"],
                               capture_output=True, text=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

            patterns = [r"\.DS_Store", r"(^|/)\._", r"__MACOSX", r"Icon\r", r"Thumbs\.db",
                        r"desktop\.ini", r"\.Spotlight", r"\.fseventsd", r"\.TemporaryItems",
                        r"\.AppleDouble", r"\.localized", r"\.apdisk", r"\.directory",
                        r"__pycache__", r"\.pyc$"]

            def litter(names):
                return sorted({n for n in names for p in patterns if re.search(p, n)})

            with zipfile.ZipFile(out / "flarehand.zip") as z:
                self.assertEqual(litter(z.namelist()), [], "litter reached the zip")
            with zipfile.ZipFile(out / "flarehand.skill") as z:
                self.assertEqual(litter(z.namelist()), [], "litter reached the .skill")
            with tarfile.open(out / "flarehand.tar.gz", "r:gz") as tar:
                self.assertEqual(litter(tar.getnames()), [], "litter reached the tarball")
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def test_validator_is_not_confused_by_litter(self):
        """A .DS_Store in a lone skill must not change what the validator reports."""
        work = Path(tempfile.mkdtemp(prefix="fh-lint-litter-"))
        try:
            target = work / "flarehand"
            shutil.copytree(SKILL, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "dist"))

            def errors():
                r = subprocess.run([sys.executable, str(target / "scripts" / "validate_skill.py"), "--json"],
                                   capture_output=True, text=True, timeout=60)
                return json.loads(r.stdout)["errors"]

            before = errors()
            (target / "references" / "._router.md").write_bytes(b"x")
            (target / "scripts" / "._kb.py").write_bytes(b"x")
            (target / ".DS_Store").write_bytes(b"x")
            self.assertEqual(errors(), before, "litter confused the validator")
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def test_packaging_refuses_when_validation_fails(self):
        """Never ship something that will not load."""
        broken = Path(tempfile.mkdtemp(prefix="fh-broken-"))
        try:
            target = broken / "flarehand"
            shutil.copytree(SKILL, target, ignore=shutil.ignore_patterns("__pycache__", "dist"))
            skill_md = target / "SKILL.md"
            skill_md.write_text(skill_md.read_text(encoding="utf-8").replace(
                "name: flarehand", "name: Wrong_Name"), encoding="utf-8")
            r = subprocess.run([sys.executable, str(target / "scripts" / "package.py")],
                               capture_output=True, text=True, timeout=60)
            self.assertEqual(r.returncode, 1)
            self.assertIn("does not pass its own validation", r.stderr)
        finally:
            shutil.rmtree(broken, ignore_errors=True)


class TestPluginWrapper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="fh-plug-"))
        r = run("package.py", "--out", str(cls.tmp), "--formats", "plugin", "--skip-validate")
        assert r.returncode == 0, r.stdout + r.stderr
        cls.plugin = cls.tmp / "flarehand-plugin"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_plugin_folder_has_a_manifest_the_skills_and_the_eval_cases(self):
        manifest = json.loads((self.plugin / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "flarehand")
        for skill in SKILLS:
            self.assertTrue((self.plugin / "skills" / skill.name / "SKILL.md").is_file(), skill.name)
        self.assertTrue(list((self.plugin / "evals").glob("*/case.yaml")))
        self.assertFalse((self.plugin / "skills" / "flarehand" / "evals").exists())
        self.assertFalse((self.plugin / "bin").exists())

    def test_the_plugin_evals_hold_no_python(self):
        """The eval cases ship at the plugin root for `claude plugin eval`; the unit tests do not."""
        self.assertEqual(sorted(p.relative_to(self.plugin).as_posix() for p in (self.plugin / "evals").rglob("*.py")),
                         [])
        self.assertFalse((self.plugin / "tests").exists())
        for skill in SKILLS:
            with self.subTest(skill=skill.name):
                for name in ("evals", "tests"):
                    self.assertFalse((self.plugin / "skills" / skill.name / name).exists())

    @needs_repo
    def test_plugin_folder_carries_every_tool_and_no_repository_extras(self):
        for rel in (".codex-plugin/plugin.json", ".cursor-plugin/plugin.json", ".agents/plugins/marketplace.json",
                    ".claude-plugin/marketplace.json", "gemini-extension.json", "GEMINI.md", "AGENTS.md",
                    "LICENSE", "README.md", "hooks/hooks.json", "hooks/hooks-cursor.json",
                    "hooks/run-hook.cmd", "hooks/hook.py"):
            with self.subTest(file=rel):
                self.assertTrue((self.plugin / rel).is_file())
        for rel in ("docs", "tools", "CONTRIBUTING.md", ".git", ".version-bump.json"):
            with self.subTest(absent=rel):
                self.assertFalse((self.plugin / rel).exists())
        if os.name == "posix":
            self.assertTrue(os.access(self.plugin / "hooks" / "run-hook.cmd", os.X_OK))

    def test_scaffold_scripts_are_executable_in_the_build(self):
        """`claude plugin eval --scaffold` may run seed.sh by path, so it keeps 0755 like the launcher."""
        if os.name != "posix":
            self.skipTest("file modes are POSIX only")
        scripts = list((self.plugin / "evals").glob("*/*.sh"))
        for path in scripts:
            with self.subTest(script=path.parent.name):
                self.assertTrue(os.access(path, os.X_OK), f"{path.name} lost its executable bit")
        if REPO is not None:
            self.assertTrue(os.access(self.plugin / "hooks" / "run-hook.cmd", os.X_OK))


# ---------------------------------------------------------------- the live eval cases

# The documented keys for `claude plugin eval`, from https://code.claude.com/docs/en/plugin-evals.md
# ("Eval suite reference"), checked 2026-10-04. The CLI's free load check (`--tag no-such-tag`) drops
# every case before it parses one, and the runner fails a whole case on an unknown key or grader
# type, so this catches it before a paid run.
#
# Each case is one evals/<case>/case.yaml holding the prompt, the run settings and every grader
# inline, plus the scaffold script it names. One file per case keeps the repository well under the
# plugin directory's file limit.
CASE_TOP_KEYS = {"schema_version", "name", "description", "tags", "plugins", "runs", "expected_outcome",
                 "context", "execution", "graders"}
CASE_CONTEXT_KEYS = {"scaffold_script", "history_file", "add_dirs"}
CASE_EXECUTION_KEYS = {"prompt", "model", "max_turns", "timeout_seconds", "allowed_tools", "append_system_prompt",
                       "env"}
GRADER_COMMON = {"name", "type", "weight", "arm"}
GRADER_OPTIONS = {"regex": {"pattern", "flags", "match", "target"},
                  "tool_used": {"tool", "input_match", "min", "max"},
                  "tool_order": {"before", "after"},
                  "file_exists": {"path", "exists"},
                  "llm": {"criteria", "focus"},
                  "baseline": {"baseline_file", "criteria"}}
VIEW_TARGETS = {"last_message", "trace", "files", "mock_calls"}


def load_yaml(text: str):
    """The YAML subset the case files use, without a YAML library: block mappings, block lists,
    flow lists of plain scalars, plain, 'single-quoted' and "double-quoted" one-line scalars, and
    `|` / `|-` block scalars. Scalars stay strings. Anything else raises ValueError, so a case file
    that drifts past the subset fails loudly instead of being read wrong."""
    lines = [l for l in text.split("\n")]
    if any("\t" in l[:len(l) - len(l.lstrip())] for l in lines):
        raise ValueError("tab indentation")
    value, i = _yaml_block(lines, 0, 0)
    i = _yaml_skip(lines, i)
    if i < len(lines):
        raise ValueError(f"line {i + 1}: unexpected {lines[i]!r}")
    return value


def _yaml_skip(lines: list, i: int) -> int:
    while i < len(lines) and (not lines[i].strip() or lines[i].lstrip().startswith("#")):
        i += 1
    return i


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _yaml_block(lines: list, i: int, min_indent: int):
    i = _yaml_skip(lines, i)
    if i >= len(lines) or _indent(lines[i]) < min_indent:
        return None, i
    ind = _indent(lines[i])
    if lines[i].lstrip().startswith("- ") or lines[i].strip() == "-":
        out = []
        while i < len(lines) and _indent(lines[i]) == ind and lines[i].lstrip().startswith("-"):
            rest = lines[i].lstrip()[1:].lstrip()
            if not rest:
                item, i = _yaml_block(lines, i + 1, ind + 1)
            elif re.match(r"^[\w-]+:(\s|$)", rest):
                # `- key: v` opens a mapping whose keys sit two columns in.
                lines = lines[:i] + [" " * (ind + 2) + rest] + lines[i + 1:]
                item, i = _yaml_block(lines, i, ind + 2)
            else:
                item, i = _yaml_scalar(rest), i + 1
                if _yaml_skip(lines, i) < len(lines) and _indent(lines[_yaml_skip(lines, i)]) > ind:
                    raise ValueError(f"line {i + 1}: multi-line scalar")
            out.append(item)
            i = _yaml_skip(lines, i)
        return out, i
    out = {}
    while i < len(lines) and _indent(lines[i]) == ind and not lines[i].lstrip().startswith("- "):
        m = re.match(r"^([\w-]+):(?:\s+(.*))?$", lines[i].strip())
        if not m:
            raise ValueError(f"line {i + 1}: not a key: {lines[i]!r}")
        key, rest = m.group(1), (m.group(2) or "").strip()
        if key in out:
            raise ValueError(f"line {i + 1}: duplicate key {key}")
        if rest in ("|", "|-"):
            j, body = i + 1, []
            while j < len(lines) and (not lines[j].strip() or _indent(lines[j]) > ind):
                body.append(lines[j])
                j += 1
            pad = min((_indent(l) for l in body if l.strip()), default=0)
            text = "\n".join(l[pad:] for l in body).rstrip("\n")
            out[key] = text if rest == "|-" else text + "\n"
            i = j
        elif rest:
            out[key] = _yaml_scalar(rest)
            i += 1
            nxt = _yaml_skip(lines, i)
            if nxt < len(lines) and _indent(lines[nxt]) > ind:
                raise ValueError(f"line {i + 1}: multi-line scalar under {key}")
        else:
            out[key], i = _yaml_block(lines, i + 1, ind + 1)
        i = _yaml_skip(lines, i)
    return out, i


def _yaml_scalar(text: str) -> str | list:
    text = text.strip()
    if text.startswith("'"):
        if not re.fullmatch(r"'(?:[^']|'')*'", text):
            raise ValueError(f"bad single-quoted scalar {text!r}")
        return text[1:-1].replace("''", "'")
    if text.startswith('"'):
        if not re.fullmatch(r'"(?:[^"\\]|\\.)*"', text):
            raise ValueError(f"bad double-quoted scalar {text!r}")
        return json.loads(text)
    if text.startswith("["):
        if not text.endswith("]") or any(c in text[1:-1] for c in "[]{}'\""):
            raise ValueError(f"unsupported flow list {text!r}")
        return [part.strip() for part in text[1:-1].split(",") if part.strip()]
    if text[0] in "{&*!|>%@`":
        raise ValueError(f"unsupported scalar {text!r}")
    return re.split(r"\s+#", text, maxsplit=1)[0].strip()


def load_case(case: Path) -> dict:
    return load_yaml((case / "case.yaml").read_text(encoding="utf-8"))


CASES = sorted(p for p in (REPO / "evals").iterdir()
               if p.is_dir() and ((p / "prompt.md").is_file() or (p / "case.yaml").is_file())) if REPO else []


class TestYamlSubsetReader(unittest.TestCase):
    """The reader the eval-case tests rely on, pinned on the shapes the case files use."""

    def test_the_shapes_the_case_files_use(self):
        text = ("schema_version: \"1.1\"\nname: demo\ntags: [a, b-c]\nexecution:\n  max_turns: 25\n"
                "  prompt: |-\n    line one\n\n      indented: not a key\n    last\ngraders:\n"
                "  - name: g\n    type: regex\n    pattern: '\\bI(?:''ve)? \\\\ #x'\n"
                "  - name: h\n    type: llm\n    criteria: |\n      PASS if:\n      it holds.\n")
        self.assertEqual(load_yaml(text), {
            "schema_version": "1.1", "name": "demo", "tags": ["a", "b-c"],
            "execution": {"max_turns": "25", "prompt": "line one\n\n  indented: not a key\nlast"},
            "graders": [{"name": "g", "type": "regex", "pattern": "\\bI(?:'ve)? \\\\ #x"},
                        {"name": "h", "type": "llm", "criteria": "PASS if:\nit holds.\n"}]})

    def test_anything_past_the_subset_fails_loudly(self):
        for text in ("a: {b: c}\n", "a: b\n  c\n", "a: 'unterminated\n", "a: >\n  folded\n", "a: 1\na: 2\n"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    load_yaml(text)


@needs_repo
class TestEvalCasesMatchTheRunner(unittest.TestCase):
    """Every live eval case is one case.yaml using only keys and values `claude plugin eval` documents."""

    def test_there_are_cases(self):
        self.assertTrue(CASES)

    def test_each_case_is_one_case_yaml(self):
        """A prompt.md or graders/ beside case.yaml would be merged into it by the runner (prompt.md
        frontmatter wins, graders/*.md are appended), so keep each case in its one file."""
        for case in CASES:
            with self.subTest(case=case.name):
                self.assertTrue((case / "case.yaml").is_file())
                self.assertFalse((case / "prompt.md").exists(), "move the prompt into execution.prompt")
                self.assertFalse((case / "graders").exists(), "move each grader into the graders: list")

    def test_case_yaml_keys_and_the_files_they_name(self):
        for case in CASES:
            with self.subTest(case=case.name):
                raw = (case / "case.yaml").read_bytes()
                self.assertNotIn(b"\r", raw, "keep LF line endings")
                data = load_case(case)
                self.assertEqual(set(data) - CASE_TOP_KEYS, set(), "unknown case.yaml key")
                self.assertEqual(data.get("schema_version"), "1.1")
                self.assertEqual(data.get("name"), case.name, "the report keys on the name, so keep it the folder")
                if "runs" in data:
                    self.assertTrue(1 <= int(data["runs"]) <= 50)
                self.assertIsInstance(data.get("tags", []), list)
                context = data.get("context") or {}
                self.assertEqual(set(context) - CASE_CONTEXT_KEYS, set(), "unknown context key")
                execution = data.get("execution") or {}
                self.assertEqual(set(execution) - CASE_EXECUTION_KEYS, set(), "unknown execution key")
                self.assertTrue(str(execution.get("prompt", "")).strip(), "a case needs execution.prompt")
                if "max_turns" in execution:
                    self.assertTrue(1 <= int(execution["max_turns"]) <= 200)
                if "timeout_seconds" in execution:
                    self.assertTrue(1 <= int(execution["timeout_seconds"]) <= 3600)
                if "allowed_tools" in execution:
                    self.assertIsInstance(execution["allowed_tools"], list)
                for env_key in execution.get("env") or {}:
                    self.assertRegex(env_key, r"^EVAL_[A-Z0-9_]*$")
                for key in ("scaffold_script", "history_file"):
                    if key in context:
                        self.assertTrue((case / context[key]).is_file(), f"{key} names a missing file")
                if "scaffold_script" in context:
                    script = case / context["scaffold_script"]
                    self.assertTrue(script.read_bytes().startswith(b"#!"), "a scaffold script needs a shebang")
                    self.assertNotIn(b"\r", script.read_bytes(), "bash fails on CRLF")
                    if os.name == "posix":
                        self.assertTrue(os.access(script, os.X_OK), "a scaffold script needs its executable bit")

    def test_graders(self):
        for case in CASES:
            graders = load_case(case).get("graders")
            with self.subTest(case=case.name):
                self.assertIsInstance(graders, list, "a case without a grader fails to load")
                self.assertTrue(graders, "a case without a grader fails to load")
                names = [g.get("name") for g in graders]
                self.assertTrue(all(names), "every grader needs a name")
                self.assertEqual(len(names), len(set(names)), "the runner rejects a duplicate grader name")
            for grader in graders or []:
                with self.subTest(case=case.name, grader=grader.get("name")):
                    self.assertIsInstance(grader, dict)
                    self.check_grader(grader)

    def test_regexes_are_single_quoted(self):
        """A single-quoted YAML scalar keeps every backslash as written; a plain or double-quoted one
        can eat an escape or cut a pattern at ` #`, which changes what the grader matches."""
        for case in CASES:
            for line in (case / "case.yaml").read_text(encoding="utf-8").splitlines():
                m = re.match(r"^\s*(pattern|input_match):\s*(.*)$", line)
                if m:
                    with self.subTest(case=case.name, line=line.strip()[:60]):
                        self.assertTrue(m.group(2).startswith("'") and m.group(2).endswith("'"))

    def test_must_not_fire_graders_actually_score(self):
        for case in CASES:
            if not case.name.startswith("ignores-"):
                continue
            with self.subTest(case=case.name):
                graders = {g["name"]: g for g in load_case(case)["graders"]}
                g = graders.get("not-fired", {})
                self.assertEqual((g.get("type"), g.get("tool"), g.get("min"), g.get("max"), g.get("arm")),
                                 ("tool_used", "Skill", "0", "0", "both"))

    def check_grader(self, values: dict) -> None:
        kind = values.get("type")
        self.assertIn(kind, GRADER_OPTIONS, f"unknown grader type {kind}")
        self.assertEqual(set(values) - GRADER_COMMON - GRADER_OPTIONS[kind], set(), f"unknown {kind} grader key")
        for key, value in values.items():
            if key not in ("before", "after"):
                self.assertIsInstance(value, str, f"{key} should be a scalar")
        if values.get("arm"):
            self.assertIn(values["arm"], ("with-only", "both"))
        if values.get("weight"):
            self.assertGreater(float(values["weight"]), 0)
        if kind == "regex":
            self.assertTrue(values.get("pattern"), "a regex grader needs a pattern")
            self.assertNotIn("\n", values["pattern"])
            self.assertRegex(values.get("match", "contains"), r"^(contains|not_contains|count:\d+)$")
            if values.get("target"):
                self.assertIn(values["target"], VIEW_TARGETS)
            self.assertNotIn("(?i)", values["pattern"], "put case-insensitivity in flags: i")
        if kind in ("llm", "baseline"):
            self.assertTrue(values.get("criteria", "").strip(), f"an {kind} grader needs criteria")
        if kind == "llm" and values.get("focus"):
            self.assertIn(values["focus"], VIEW_TARGETS)
        if kind == "tool_used":
            self.assertTrue(values.get("tool"))
            for bound in ("min", "max"):
                if values.get(bound):
                    self.assertGreaterEqual(int(values[bound]), 0)
        if kind == "tool_order":
            self.assertTrue(values.get("before") is not None and values.get("after") is not None)
        if kind == "file_exists":
            self.assertTrue(values.get("path"))
        if kind == "baseline":
            self.assertTrue(values.get("baseline_file", "").endswith(".jsonl"))


# ---------------------------------------------------------------- the manifests


@needs_repo
class TestManifests(unittest.TestCase):
    def load(self, rel: str) -> dict:
        return json.loads((REPO / rel).read_text(encoding="utf-8"))

    def test_every_manifest_names_flarehand_at_one_version(self):
        versions = set()
        for rel in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json", ".cursor-plugin/plugin.json",
                    "gemini-extension.json"):
            with self.subTest(manifest=rel):
                data = self.load(rel)
                self.assertEqual(data["name"], "flarehand")
                self.assertTrue(data["description"])
                versions.add(data["version"])
        self.assertEqual(len(versions), 1, versions)

    def test_claude_manifests(self):
        plugin = self.load(".claude-plugin/plugin.json")
        self.assertEqual((plugin["license"], plugin["author"]["name"]), ("MIT", "FlareWare Solutions"))
        market = self.load(".claude-plugin/marketplace.json")
        self.assertEqual(market["name"], "flareware")
        self.assertEqual(market["owner"]["name"], "FlareWare Solutions")
        entry = market["plugins"][0]
        self.assertEqual((entry["name"], entry["source"]), ("flarehand", "./"))
        self.assertNotIn("version", entry, "keep the version only in plugin.json")

    def test_codex_manifests(self):
        plugin = self.load(".codex-plugin/plugin.json")
        self.assertEqual((plugin["skills"], plugin["hooks"]), ("./skills/", "./hooks/hooks.json"))
        for key in ("displayName", "shortDescription", "developerName", "category", "capabilities"):
            self.assertIn(key, plugin["interface"])
        market = self.load(".agents/plugins/marketplace.json")
        entry = market["plugins"][0]
        self.assertEqual(entry["name"], "flarehand")
        self.assertIn(entry["source"]["source"], ("local", "url"))
        self.assertEqual(entry["policy"], {"installation": "AVAILABLE", "authentication": "ON_INSTALL"})

    def test_cursor_and_gemini_point_at_files_that_exist(self):
        cursor = self.load(".cursor-plugin/plugin.json")
        self.assertTrue((REPO / cursor["skills"]).is_dir())
        self.assertTrue((REPO / cursor["hooks"]).is_file())
        gemini = self.load("gemini-extension.json")
        self.assertTrue((REPO / gemini["contextFileName"]).is_file())

    def test_the_repository_is_fit_for_the_plugin_directory(self):
        self.assertFalse((REPO / "bin").exists(), "a top-level bin/ blocks the claude.ai install")
        self.assertGreaterEqual(len((REPO / "README.md").read_text(encoding="utf-8").split()), 40)
        licence = (REPO / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("MIT License", licence)
        self.assertIn("Copyright (c) 2026 FlareWare Solutions", licence)

    def test_the_bootstrap_files_are_short_and_for_users(self):
        for rel in ("AGENTS.md", "GEMINI.md"):
            with self.subTest(file=rel):
                text = (REPO / rel).read_text(encoding="utf-8")
                self.assertLess(len(text.splitlines()), 40)
                self.assertIn("flarehand", text)
                self.assertNotIn("\u2014", text)
                self.assertNotIn("pull request", text.lower(), "contributor rules belong in CONTRIBUTING.md")
                for name in ENTRY_POINTS:
                    self.assertIn(f"`{name}`", text, "the bootstrap names the skill that fits, as the nudge does")


# ---------------------------------------------------------------- the hooks


def _actions(commands) -> set:
    return {m for c in commands for m in re.findall(r"run-hook\.cmd\"?\s+([a-z-]+)", c)}


@needs_repo
class TestHookParity(unittest.TestCase):
    CLAUDE = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8")) if REPO else {}
    CURSOR = json.loads((REPO / "hooks" / "hooks-cursor.json").read_text(encoding="utf-8")) if REPO else {}

    def claude_commands(self):
        return [h["command"] for groups in self.CLAUDE["hooks"].values() for g in groups for h in g["hooks"]]

    def test_both_formats_run_the_same_five_actions(self):
        cursor = [h["command"] for items in self.CURSOR["hooks"].values() for h in items]
        self.assertEqual(_actions(self.claude_commands()), set(ACTIONS))
        self.assertEqual(_actions(cursor), set(ACTIONS))
        self.assertEqual(self.CURSOR["version"], 1)

    def test_the_events_match_the_actions(self):
        pairs = {("SessionStart", "session-start"), ("UserPromptSubmit", "prompt-submit"), ("Stop", "stop"),
                 ("PreCompact", "pre-compact"), ("SessionEnd", "session-end")}
        for event, action in pairs:
            cmds = [h["command"] for g in self.CLAUDE["hooks"][event] for h in g["hooks"]]
            self.assertEqual(_actions(cmds), {action}, event)
        cursor_pairs = {("sessionStart", "session-start"), ("beforeSubmitPrompt", "prompt-submit"),
                        ("stop", "stop"), ("preCompact", "pre-compact"), ("sessionEnd", "session-end")}
        for event, action in cursor_pairs:
            self.assertEqual(_actions(h["command"] for h in self.CURSOR["hooks"][event]), {action}, event)

    def test_session_start_matches_every_source(self):
        self.assertEqual(self.CLAUDE["hooks"]["SessionStart"][0]["matcher"], "startup|resume|clear|compact")

    def test_every_claude_command_is_harmless_without_the_plugin_root(self):
        """Gemini reads hooks/hooks.json too, without CLAUDE_PLUGIN_ROOT. Run each command with it
        empty, as Gemini would, and nothing may happen."""
        env = {k: v for k, v in os.environ.items() if k not in HOST_VARS}
        env["CLAUDE_PLUGIN_ROOT"] = ""
        for cmd in self.claude_commands():
            with self.subTest(cmd=cmd[-30:]):
                self.assertIn('sh "${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd"', cmd,
                              "run the launcher through sh, never by its executable bit")
                if shutil.which("sh"):
                    r = subprocess.run(["sh", "-c", cmd], input=b"{}", capture_output=True, env=env, timeout=30)
                    self.assertEqual((r.returncode, r.stdout), (0, b""))

    def test_the_launcher_stays_executable_for_cursor(self):
        if os.name == "posix":
            self.assertTrue(os.access(REPO / "hooks" / "run-hook.cmd", os.X_OK))


@needs_repo
class TestDispatcher(unittest.TestCase):
    """hooks/hook.py prints exactly one output shape per host, and always exits 0."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="fh-hook-"))
        cls.temp = cls.tmp / "temp"
        cls.temp.mkdir()
        cls.home = cls.tmp / "home"
        cls.home.mkdir()
        cls.with_skill = cls.tmp / "with.jsonl"
        cls.with_skill.write_text(json.dumps({"type": "user", "message": {"role": "user", "content":
                                  "<command-name>/flarehand</command-name>\n<command-args>draft it</command-args>"}})
                                  + "\n", encoding="utf-8")
        cls.without = cls.tmp / "without.jsonl"
        cls.without.write_text(json.dumps({"type": "user", "message": {"role": "user", "content": "hi"}}) + "\n",
                               encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def env(self, host: str) -> dict:
        env = {k: v for k, v in os.environ.items() if k not in HOST_VARS}
        env.update(TMPDIR=str(self.temp), TEMP=str(self.temp), TMP=str(self.temp), HOME=str(self.home),
                   USERPROFILE=str(self.home), PYTHONIOENCODING="utf-8")
        root = str(REPO)
        if host == "claude":
            env["CLAUDE_PLUGIN_ROOT"] = root
        elif host == "cursor":
            env.update(CURSOR_PLUGIN_ROOT=root, CLAUDE_PLUGIN_ROOT=root)
        elif host == "copilot":
            env.update(COPILOT_CLI="1", CLAUDE_PLUGIN_ROOT=root)
        elif host == "codex":
            env.update(CODEX_HOME=str(self.home / ".codex"), PLUGIN_ROOT=root, CLAUDE_PLUGIN_ROOT=root)
        return env

    def hook(self, action: str, event, host: str = "claude", launcher: bool = False) -> subprocess.CompletedProcess:
        data = event if isinstance(event, (str, bytes)) else json.dumps(event)
        data = data if isinstance(data, bytes) else data.encode("utf-8")
        if launcher:
            cmd = ["sh", str(REPO / "hooks" / "run-hook.cmd"), action]
        else:
            cmd = [sys.executable, str(REPO / "hooks" / "hook.py"), action]
        return subprocess.run(cmd, input=data, capture_output=True, timeout=60, env=self.env(host))

    def out(self, *args, **kw) -> dict:
        r = self.hook(*args, **kw)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout.decode("utf-8")) if r.stdout.strip() else {}

    def test_session_start_shape_per_host(self):
        event = {"hook_event_name": "SessionStart", "session_id": "s1", "source": "startup"}
        claude = self.out("session-start", event, "claude")
        self.assertEqual(list(claude), ["hookSpecificOutput"])
        self.assertEqual(claude["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertIn("flarehand-ground to check a draft", claude["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.out("session-start", event, "codex"), claude)
        cursor = self.out("session-start", event, "cursor")
        self.assertEqual(list(cursor), ["additional_context"])
        copilot = self.out("session-start", event, "copilot")
        self.assertEqual(list(copilot), ["additionalContext"])
        self.assertEqual(cursor["additional_context"], copilot["additionalContext"])

    def test_the_nudge_names_the_skill_that_fits_and_stays_short(self):
        """A bare "use flarehand" sent a fact-check to the router instead of flarehand-ground. The
        nudge is paid in every session, so it also stays short."""
        text = self.out("session-start", {"session_id": "s0", "source": "startup"})[
            "hookSpecificOutput"]["additionalContext"]
        for name, job in (("flarehand-ground", "facts or numbers"), ("flarehand-review", "review code"),
                          ("flarehand-remember", "save, recall or forget"), ("flarehand-grill", "stress-test"),
                          ("otherwise flarehand", "deliverable")):
            with self.subTest(skill=name):
                self.assertIn(name, text)
                self.assertIn(job, text[text.index(name):text.index(name) + 90])
        self.assertLess(len(text), 600)
        self.assertIn("answer normally", text)
        self.assertNotIn("\u2014", text)

    def test_the_launcher_gives_the_same_result(self):
        if not shutil.which("sh"):
            self.skipTest("no POSIX shell")
        event = {"session_id": "s1", "source": "startup"}
        self.assertEqual(self.out("session-start", event, launcher=True), self.out("session-start", event))

    def test_the_reminder_waits_until_the_skill_ran(self):
        self.assertEqual(self.out("prompt-submit", {"session_id": "s2", "transcript_path": str(self.without)}), {})
        said = self.out("prompt-submit", {"session_id": "s2", "transcript_path": str(self.with_skill)})
        self.assertEqual(said["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        self.assertIn("no em dashes", said["hookSpecificOutput"]["additionalContext"])
        cursor = self.out("prompt-submit", {"conversation_id": "s2", "transcript_path": str(self.with_skill)}, "cursor")
        self.assertEqual(list(cursor), ["additional_context"])

    def test_the_gate_is_off_by_default_and_silent_on_cursor(self):
        event = {"session_id": "s3", "transcript_path": str(self.with_skill),
                 "last_assistant_message": "It failed \u2014 again."}
        for host in ("claude", "cursor", "copilot"):
            with self.subTest(host=host):
                self.assertEqual(self.out("stop", event, host), {})

    def test_save_then_restore_then_end(self):
        sid = "s4-compact"
        transcript = self.tmp / "compact.jsonl"
        transcript.write_text("".join(json.dumps(r) + "\n" for r in (
            {"type": "assistant", "message": {"role": "assistant", "content": [
                {"type": "tool_use", "id": "a", "name": "Skill", "input": {"skill": "flarehand"}}]}},
            {"type": "assistant", "message": {"role": "assistant", "content": [
                {"type": "text", "text": "Their version is 13.0 [your input]."}]}})), encoding="utf-8")
        self.assertEqual(self.out("pre-compact", {"session_id": sid, "transcript_path": str(transcript),
                                                  "trigger": "auto"}), {})
        saved = self.temp / "flarehand-staging" / "checkpoints" / f"{sid}.md"
        self.assertTrue(saved.is_file())
        text = self.out("session-start", {"session_id": sid, "source": "compact"})["hookSpecificOutput"]["additionalContext"]
        self.assertIn("invoke the matching skill", text)
        self.assertIn(str(saved), text)
        self.assertNotIn("13.0", text, "the checkpoint is pointed at, never injected")
        self.assertEqual(self.out("session-end", {"session_id": sid}), {})
        self.assertFalse(saved.exists())

    def test_always_exit_0_whatever_it_is_given(self):
        junk = (b"not json", b"[1, 2]", b"", b"\xff\xfe\x00garbage", b'{"session_id": 7, "transcript_path": []}',
                json.dumps({"session_id": "../../x", "transcript_path": "/no/such/file"}).encode())
        for host in ("claude", "cursor", "copilot", "codex"):
            for action in ACTIONS + ("bogus",):
                for data in junk:
                    with self.subTest(host=host, action=action, data=data[:12]):
                        r = self.hook(action, data, host)
                        self.assertEqual(r.returncode, 0, r.stderr)
                        if action != "session-start":
                            self.assertEqual(r.stdout, b"")
                        else:
                            self.assertEqual(len(json.loads(r.stdout)), 1, "exactly one output shape")

    def test_no_arguments_or_help_exits_0(self):
        for args in ([], ["--help"]):
            r = subprocess.run([sys.executable, str(REPO / "hooks" / "hook.py"), *args], capture_output=True,
                               timeout=30, env=self.env("claude"))
            self.assertEqual(r.returncode, 0)

    def test_the_launcher_exits_0_without_python_or_without_the_dispatcher(self):
        if not shutil.which("sh"):
            self.skipTest("no POSIX shell")
        bare = self.tmp / "bare-bin"
        bare.mkdir(exist_ok=True)
        for tool in ("dirname",):
            found = shutil.which(tool)
            if found and not (bare / tool).exists():
                os.symlink(found, bare / tool)
        env = dict(self.env("claude"), PATH=str(bare))
        r = subprocess.run([shutil.which("sh"), str(REPO / "hooks" / "run-hook.cmd"), "session-start"],
                           input=b"{}", capture_output=True, env=env, timeout=30)
        self.assertEqual((r.returncode, r.stdout), (0, b""), r.stderr)
        alone = self.tmp / "alone"
        alone.mkdir(exist_ok=True)
        shutil.copyfile(REPO / "hooks" / "run-hook.cmd", alone / "run-hook.cmd")
        r = subprocess.run(["sh", str(alone / "run-hook.cmd"), "session-start"], input=b"{}",
                           capture_output=True, env=self.env("claude"), timeout=30)
        self.assertEqual((r.returncode, r.stdout), (0, b""))


@needs_repo
class TestNoStateUnderThePluginRoot(unittest.TestCase):
    """Run every hook against a copy of the plugin, then prove the copy did not change."""

    def test_hooks_write_nothing_inside_the_plugin(self):
        work = Path(tempfile.mkdtemp(prefix="fh-state-"))
        try:
            plugin = work / "plugin"
            ignore = shutil.ignore_patterns("__pycache__", "*.pyc", "dist", ".git", "docs")
            shutil.copytree(REPO / "hooks", plugin / "hooks", ignore=ignore)
            shutil.copytree(SKILL, plugin / "skills" / "flarehand", ignore=ignore)
            before = sorted(p.relative_to(plugin).as_posix() for p in plugin.rglob("*"))
            transcript = work / "t.jsonl"
            transcript.write_text(json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [
                {"type": "tool_use", "id": "a", "name": "Skill", "input": {"skill": "flarehand"}}]}}) + "\n",
                                  encoding="utf-8")
            temp = work / "temp"
            temp.mkdir()
            env = {k: v for k, v in os.environ.items() if k not in HOST_VARS}
            env.update(CLAUDE_PLUGIN_ROOT=str(plugin), TMPDIR=str(temp), TEMP=str(temp), TMP=str(temp),
                       HOME=str(work / "home"))
            event = json.dumps({"session_id": "state", "transcript_path": str(transcript), "source": "compact",
                                "last_assistant_message": "a \u2014 b"}).encode()
            for action in ("session-start", "prompt-submit", "stop", "pre-compact", "session-start", "session-end"):
                r = subprocess.run([sys.executable, str(plugin / "hooks" / "hook.py"), action], input=event,
                                   capture_output=True, env=env, timeout=60)
                self.assertEqual(r.returncode, 0, r.stderr)
            after = sorted(p.relative_to(plugin).as_posix() for p in plugin.rglob("*"))
            self.assertEqual(after, before, "a hook wrote inside the plugin folder")
            self.assertTrue(any(temp.rglob("*")), "the hooks kept their state in the temp folder")
        finally:
            shutil.rmtree(work, ignore_errors=True)


class TestVoiceGateDetection(unittest.TestCase):
    """The skill is found however it was called, and a long transcript is read once."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fh-voice-"))
        self._state_dir = voice_gate.state_dir
        voice_gate.state_dir = lambda: self.tmp / "state"
        self.path = self.tmp / "t.jsonl"

    def tearDown(self):
        voice_gate.state_dir = self._state_dir
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, *lines: str, mode: str = "w") -> None:
        with open(self.path, mode, encoding="utf-8") as fh:
            fh.write("".join(line + "\n" for line in lines))

    def test_every_form_of_the_skill_counts(self):
        forms = ('{"type":"tool_use","name":"Skill","input":{"skill":"flarehand"}}',
                 '{"input": {"skill": "flarehand:flarehand"}}',
                 '{"input":{"skill":"flarehand-review"}}',
                 '{"content":"<command-name>/flarehand</command-name>"}',
                 '{"content":"<command-name>/flarehand:flarehand-grill</command-name>"}',
                 '{"input":{"file_path":"/home/a/.agents/skills/flarehand/SKILL.md"}}',
                 '{"input":{"path":"C:\\\\skills\\\\flarehand\\\\SKILL.md"}}')
        for i, line in enumerate(forms):
            with self.subTest(form=line):
                self.path = self.tmp / f"f{i}.jsonl"
                self.write('{"content":"hello"}', line)
                self.assertTrue(voice_gate.skill_ran(str(self.path)))

    def test_lookalikes_do_not_count(self):
        for i, line in enumerate(('{"input":{"skill":"flarehand-other"}}', '{"content":"use flarehand"}',
                                  '{"content":"<command-name>/flarehands</command-name>"}')):
            with self.subTest(line=line):
                self.path = self.tmp / f"n{i}.jsonl"
                self.write(line)
                self.assertFalse(voice_gate.skill_ran(str(self.path)))

    def test_a_transcript_is_read_once_and_only_new_lines_after(self):
        self.write(*['{"content":"%s"}' % ("x" * 200)] * 2000)
        self.assertFalse(voice_gate.skill_ran(str(self.path)))
        # Rewrite an early line in place, same length. A full re-read would now find the skill.
        data = self.path.read_bytes()
        planted = b'{"skill":"flarehand"}'
        self.path.write_bytes(planted + data[len(planted):])
        self.assertFalse(voice_gate.skill_ran(str(self.path)), "it re-read the whole transcript")
        self.write('{"content":"<command-name>/flarehand</command-name>"}', mode="a")
        self.assertTrue(voice_gate.skill_ran(str(self.path)))

    def test_a_half_written_line_is_read_again(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            fh.write('{"content":"hello"}\n{"input":{"skill":"flare')
        self.assertFalse(voice_gate.skill_ran(str(self.path)))
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write('hand"}}\n')
        self.assertTrue(voice_gate.skill_ran(str(self.path)))

    def test_the_reply_comes_from_the_end_of_a_long_transcript(self):
        old = json.dumps({"message": {"role": "assistant", "content": [{"type": "text", "text": "old"}]}})
        new = json.dumps({"message": {"role": "assistant", "content": [{"type": "text", "text": "newest"}]}})
        self.write(old, *['{"content":"%s"}' % ("y" * 500)] * 1000, new)
        self.assertEqual(voice_gate.last_reply({"transcript_path": str(self.path)}), "newest")

    def test_odd_paths_are_ignored(self):
        for value in (None, "", 7, ["x"], str(self.tmp / "missing.jsonl")):
            self.assertFalse(voice_gate.skill_ran(value))


# ---------------------------------------------------------------- the validator over the repository


@needs_repo
class TestValidatorOverTheRepository(unittest.TestCase):
    """validate_skill.py checks every skill and the plugin around them. Break one thing at a time in
    a copy of the repository, and the validator must name it."""

    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="fh-val-repo-"))
        cls.repo = cls.work / "flarehand"
        shutil.copytree(REPO, cls.repo, symlinks=True,
                        ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "dist", ".DS_Store"))
        cls.baseline = cls.errors(cls)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, ignore_errors=True)

    def errors(self) -> list:
        r = subprocess.run([sys.executable, str(self.repo / "skills" / "flarehand" / "scripts" / "validate_skill.py"),
                            "--json"], capture_output=True, text=True, timeout=120)
        return json.loads(r.stdout)["errors"]

    def new_errors(self) -> str:
        return "\n".join(e for e in self.errors() if e not in self.baseline)

    def test_it_reports_on_every_skill(self):
        r = subprocess.run([sys.executable, str(self.repo / "skills" / "flarehand" / "scripts" / "validate_skill.py"),
                            "--json"], capture_output=True, text=True, timeout=120)
        names = set(json.loads(r.stdout)["facts"]["skills"])
        self.assertEqual(names, {p.name for p in SKILLS})

    def test_a_non_portable_key_in_an_entry_point(self):
        path = self.repo / "skills" / "flarehand-review" / "SKILL.md"
        original = path.read_text(encoding="utf-8")
        try:
            path.write_text(original.replace("license: MIT", "license: MIT\nargument-hint: \"<x>\""), encoding="utf-8")
            self.assertIn("flarehand-review: frontmatter key `argument-hint`", self.new_errors())
        finally:
            path.write_text(original, encoding="utf-8")

    def test_a_path_into_the_router_that_does_not_exist(self):
        path = self.repo / "skills" / "flarehand-remember" / "SKILL.md"
        original = path.read_text(encoding="utf-8")
        try:
            path.write_text(original + "\nRead `../flarehand/references/no-such-file.md`.\n", encoding="utf-8")
            self.assertIn("../flarehand/references/no-such-file.md, which does not exist", self.new_errors())
        finally:
            path.write_text(original, encoding="utf-8")

    def test_hooks_that_drift_apart(self):
        path = self.repo / "hooks" / "hooks-cursor.json"
        original = path.read_text(encoding="utf-8")
        try:
            data = json.loads(original)
            del data["hooks"]["stop"]
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertIn("Keep them the same", self.new_errors())
        finally:
            path.write_text(original, encoding="utf-8")

    def test_a_manifest_missing_a_key_or_a_version_out_of_step(self):
        path = self.repo / ".cursor-plugin" / "plugin.json"
        original = path.read_text(encoding="utf-8")
        try:
            data = json.loads(original)
            del data["displayName"]
            data["version"] = "9.9.9"
            path.write_text(json.dumps(data), encoding="utf-8")
            found = self.new_errors()
            self.assertIn(".cursor-plugin/plugin.json has no `displayName`", found)
            self.assertIn("disagree on the version", found)
        finally:
            path.write_text(original, encoding="utf-8")

    def test_a_top_level_bin_and_a_powershell_file(self):
        (self.repo / "bin").mkdir()
        (self.repo / "hooks" / "setup.ps1").write_text("Write-Host hi\n", encoding="utf-8")
        try:
            found = self.new_errors()
            self.assertIn("top-level bin/", found)
            self.assertIn("hooks/setup.ps1 cannot ship", found)
        finally:
            shutil.rmtree(self.repo / "bin")
            (self.repo / "hooks" / "setup.ps1").unlink()


# ---------------------------------------------------------------- the version tool


@needs_repo
class TestVersionBump(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="fh-bump-"))
        for rel in (".version-bump.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json",
                    ".cursor-plugin/plugin.json", "gemini-extension.json"):
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / rel, self.root / rel)
        for skill in SKILLS:
            (self.root / "skills" / skill.name).mkdir(parents=True)
            shutil.copyfile(skill / "SKILL.md", self.root / "skills" / skill.name / "SKILL.md")
        self.bump("set", "0.1.0")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def bump(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(REPO / "tools" / "bump_version.py"), "--root", str(self.root),
                               *args], capture_output=True, text=True, timeout=60)

    def versions(self) -> dict:
        return json.loads(self.bump("check", "--json").stdout)["versions"]

    def test_set_moves_every_file_together(self):
        r = self.bump("set", "1.2.3")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(set(self.versions().values()), {"1.2.3"})
        self.assertEqual(self.bump("check").returncode, 0)
        meta = (self.root / "skills" / "flarehand-review" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn('flarehand.version: "1.2.3"', meta)

    def test_bump_raises_the_right_part(self):
        for part, expected in (("patch", "0.1.1"), ("minor", "0.2.0"), ("major", "1.0.0")):
            with self.subTest(part=part):
                self.assertEqual(self.bump("bump", part).returncode, 0)
                self.assertEqual(set(self.versions().values()), {expected})

    def test_check_fails_when_one_file_drifts(self):
        path = self.root / "gemini-extension.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["version"] = "7.7.7"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(self.bump("check").returncode, 1)

    def test_dry_run_changes_nothing_and_a_bad_version_is_refused(self):
        before = self.versions()
        self.assertEqual(self.bump("bump", "major", "--dry-run").returncode, 0)
        self.assertEqual(self.versions(), before)
        self.assertEqual(self.bump("set", "one.two").returncode, 2)
        self.assertEqual(self.versions(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
