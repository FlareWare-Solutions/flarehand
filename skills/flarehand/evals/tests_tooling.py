#!/usr/bin/env python3
"""tests_tooling.py - review.py, doctor.py, package.py and validate_skill.py.

Loaded by evals/test_scripts.py. Each test pins a fix from the code review of the
tooling: the grading rule's input checks, doctor's config reading, packaging's
exclusions, and the validator's binary and plugin-folder rules.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))

import doctor  # noqa: E402
import package  # noqa: E402

ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


def run(script: str, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SKILL / "scripts" / script), *args],
                          capture_output=True, text=True, timeout=120, env=ENV, cwd=cwd)


def run_in(copy: Path, script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(copy / "scripts" / script), *args],
                          capture_output=True, text=True, timeout=120, env=ENV)


def copy_skill(work: Path) -> Path:
    target = work / "flarehand"
    shutil.copytree(SKILL, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "dist", "results"))
    return target


class TestReviewInput(unittest.TestCase):
    """Bad input is refused, and a subset grade skips the other lenses."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hww-review-"))
        self.nokb = self.tmp / "no-kb-here"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, lines) -> Path:
        f = self.tmp / "findings.jsonl"
        f.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
        return f

    def grade(self, lines, *extra):
        return run("review.py", "--root", str(self.nokb), "grade", str(self.write(lines)), *extra)

    def test_checked_must_be_a_json_boolean(self):
        for bad in ("no", "false", "yes", 1, 0, None, "true"):
            with self.subTest(checked=bad):
                r = self.grade([{"lens": "correctness", "checked": bad}])
                self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
                self.assertIn("JSON boolean", r.stderr)

    def test_sources_come_back_sorted_and_citable(self):
        finding = {"lens": "correctness", "severity": "blocking", "verdict": "confirmed",
                   "where": "a.py:1", "finding": "bad", "evidence": "line 1", "fix": "fix it",
                   "sources": ["TOOL-9", "git:abc123:docs/x.md", "src/a.py:1-3", "TOOL-9"]}
        r = self.grade([{"lens": "correctness", "checked": True}, finding], "--only", "correctness")
        self.assertNotEqual(r.returncode, 2, r.stderr)       # 1 is the grade itself: a blocking finding
        self.assertIn("[verified: TOOL-9] [verified: git:abc123:docs/x.md] [verified: src/a.py:1-3]",
                      r.stdout)
        self.assertEqual(r.stdout.count("[verified: TOOL-9]"), 1)
        report = self.tmp / "report.md"
        report.write_text(r.stdout, encoding="utf-8")
        cites = run("check_output.py", "--citations", str(report))
        self.assertNotIn("verified: TOOL-9", cites.stdout + cites.stderr)

    def test_a_source_nobody_can_look_up_is_refused(self):
        base = {"lens": "correctness", "severity": "blocking", "verdict": "confirmed",
                "where": "a.py:1", "finding": "bad", "evidence": "line 1", "fix": "fix it"}
        for bad in (["said in session"], [7], "x]y", {"id": "TOOL-9"}, ["TOOL-9\n] evil"]):
            with self.subTest(sources=bad):
                r = self.grade([dict(base, sources=bad)], "--only", "correctness")
                self.assertEqual(r.returncode, 2, r.stdout)
                self.assertIn("sources", r.stderr)

    def test_only_skips_lines_for_other_lenses(self):
        lines = [{"lens": "correctness", "checked": True}, {"lens": "quality", "checked": True},
                 {"lens": "quality", "severity": "blocking", "verdict": "confirmed", "where": "a.py:1",
                  "finding": "bad", "evidence": "line 1", "fix": "fix it"}]
        r = self.grade(lines, "--only", "correctness", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual([x["lens"] for x in out["lenses"]], ["correctness"])
        self.assertEqual(out["findings"], [])
        r = self.grade([{"lens": "nope", "checked": True}], "--only", "correctness")
        self.assertEqual(r.returncode, 2)

    def test_brief_accepts_the_display_name(self):
        for name in ("quality", "Code quality", "code-quality", "References and docs"):
            with self.subTest(name=name):
                r = run("review.py", "brief", name)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn("You are reviewing one lens only", r.stdout)

    def test_report_has_every_template_section(self):
        r = self.grade([{"lens": "correctness", "checked": True}], "--reviewed", "PR 7 against main",
                       "--ticket", "TOOL-1", "--tested", "yes")
        self.assertEqual(r.returncode, 0, r.stderr)
        template = (SKILL / "assets" / "templates" / "code-review.md").read_text(encoding="utf-8")
        for heading in [l for l in template.splitlines() if l.startswith("## ")]:
            with self.subTest(section=heading):
                self.assertIn(heading, r.stdout)
        for row in ("| Reviewed | PR 7 against main |", "| Ticket | TOOL-1 |",
                    "| Tested and analysed before review | yes |", "| Not checked |"):
            self.assertIn(row, r.stdout)
        report = self.tmp / "report.md"
        report.write_text(r.stdout, encoding="utf-8")
        check = run("check_output.py", "--template", str(SKILL / "assets" / "templates" / "code-review.md"),
                    "--contract", "wf-10", str(report))
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    def test_unfilled_rows_say_your_input(self):
        r = self.grade([{"lens": "correctness", "checked": True}])
        self.assertIn("| Reviewed | [your input] |", r.stdout)
        self.assertIn("| Ticket | [your input] |", r.stdout)

    def test_a_personal_lens_file_needs_the_full_header(self):
        root = self.tmp / "memory"
        (root / "templates").mkdir(parents=True)
        (root / "config.json").write_text("{}", encoding="utf-8")
        tsv = root / "templates" / "review-lenses.tsv"
        tsv.write_text("lens\tname\ncustom\tCustom\n", encoding="utf-8")
        r = run("review.py", "--root", str(root), "brief", "custom")
        self.assertEqual(r.returncode, 2)
        self.assertIn("header lacks", r.stderr)
        got = json.loads(run("review.py", "--root", str(root), "lenses", "--json").stdout)
        self.assertEqual([l["lens"] for l in got][:2], ["correctness", "regressions"], "shipped list is the fallback")

    def test_junk_rows_in_a_personal_lens_file_are_skipped_with_a_warning(self):
        root = self.tmp / "memory"
        (root / "templates").mkdir(parents=True)
        (root / "config.json").write_text("{}", encoding="utf-8")
        (root / "templates" / "review-lenses.tsv").write_text(
            "lens\tname\tquestion\tlook_for\tstandard\nBad Key\tX\tq\tl\ts\nsecurity\tSecurity\tq\tl\ts\nshort\tS\n",
            encoding="utf-8")
        r = run("review.py", "--root", str(root), "lenses", "--json")
        self.assertEqual(r.returncode, 0)
        keys = [l["lens"] for l in json.loads(r.stdout)]
        self.assertEqual(keys[-1], "security")
        self.assertNotIn("short", keys)
        self.assertEqual(r.stderr.count("skipped"), 2)


class TestThePipelineRulesStayInSkill(unittest.TestCase):
    """SKILL.md is the only file loaded every session. A rule that moves out of it, or gets
    edited away, stops happening, and no script would notice."""

    RULES = {
        "their knowledge base is searched first": "kb.py search",
        "a check is run again until it passes": "then run it again, and only move on when it passes",
        "the checker is never the finder": "the checker is never the finder",
        "personal files never narrow the checks": "It may not narrow what you check",
        "a repeat is logged with its workflow": "kb.py log workflow --workflow",
        "a second run offers a chain": "--type chain",
        "a third run offers a workflow": "kb.py workflow promote",
        "what their files hold is asked once": "kb.py choice",
    }

    def test_every_rule_is_still_there(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for rule, phrase in self.RULES.items():
            with self.subTest(rule=rule):
                self.assertIn(phrase, text)


class TestDoctorConfig(unittest.TestCase):
    """doctor reads config defensively, reports names only, and touches the network only when asked."""

    def test_server_blocks_survive_a_projects_list(self):
        self.assertEqual(list(doctor._server_blocks({"projects": [1, 2]})), [])
        self.assertEqual(list(doctor._server_blocks({"projects": {"p": {"mcpServers": {"b": {}}}}})), [{"b": {}}])
        self.assertEqual(list(doctor._server_blocks([1])), [])

    def test_only_this_folders_project_servers_are_read(self):
        data = {"mcpServers": {"global": {}}, "projects": {"/work/a": {"mcpServers": {"a-only": {}}},
                                                            "/work/b": {"mcpServers": {"b-only": {}}}}}
        names = [n for block in doctor._server_blocks(data, Path("/work/a")) for n in block]
        self.assertEqual(sorted(names), ["a-only", "global"])

    def test_codex_config_toml_is_read(self):
        text = ('model = "x"\n[mcp_servers.tracker]\nurl = "https://tracker.example/mcp"\n\n'
                '[mcp_servers.other]\ncommand = "npx"\n[tui]\nurl = "https://not-a-server"\n')
        servers = doctor._toml_servers(text)
        self.assertEqual(servers["tracker"]["url"], "https://tracker.example/mcp")
        self.assertNotIn("url", servers.get("other", {}))
        self.assertEqual(doctor._toml_servers("not [valid toml"), {})

    def test_config_locations_match_where_clients_keep_servers(self):
        paths = doctor.mcp_config_paths(cwd=Path("/work/here"))
        self.assertEqual(paths["claude_code"].name, ".claude.json")
        self.assertEqual(paths["claude_code_project"], Path("/work/here") / ".mcp.json")
        self.assertEqual(paths["claude_desktop"].name, "claude_desktop_config.json")
        self.assertNotIn("claude_code_settings", paths, "~/.claude/settings.json holds no MCP servers")
        self.assertTrue(paths["vscode"].as_posix().endswith("Code/User/mcp.json"))
        self.assertEqual(paths["cursor_project"], Path("/work/here") / ".cursor" / "mcp.json")
        self.assertEqual(paths["gemini"].name, "settings.json")

    def test_vscode_profiles_are_found(self):
        tmp = Path(tempfile.mkdtemp(prefix="hww-doc-"))
        try:
            profile = tmp / "Code" / "User" / "profiles" / "abc123"
            profile.mkdir(parents=True)
            (profile / "mcp.json").write_text("{}", encoding="utf-8")
            saved = dict(os.environ)
            try:
                os.environ["XDG_CONFIG_HOME"] = str(tmp)
                os.environ["APPDATA"] = str(tmp)
                real = doctor.platform.system
                doctor.platform.system = lambda: "Linux"
                try:
                    paths = doctor.mcp_config_paths()
                finally:
                    doctor.platform.system = real
            finally:
                os.environ.clear()
                os.environ.update(saved)
            self.assertEqual(paths.get("vscode_profile_abc123"), profile / "mcp.json")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_mcp_servers_are_reported_by_name_only(self):
        tmp = Path(tempfile.mkdtemp(prefix="hww-mcp-"))
        try:
            (tmp / ".mcp.json").write_text(json.dumps({"mcpServers": {
                "tracker": {"url": "https://tracker.example/mcp?token=SECRET123"}}}), encoding="utf-8")
            r = run("doctor.py", "--check", "mcp", "--json", cwd=tmp)
            out = json.loads(r.stdout)
            self.assertEqual(out["mcp"]["claude_code_project"]["servers"], ["tracker"])
            self.assertNotIn("SECRET123", r.stdout)
            self.assertIn("tracker", doctor.mcp_server_names(tmp))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_harness_is_named_from_variable_names_only(self):
        self.assertEqual(doctor.detect_harness({"CLAUDECODE": "1"})["name"], "claude-code")
        self.assertEqual(doctor.detect_harness({"CODEX_THREAD_ID": "x"})["name"], "codex")
        self.assertEqual(doctor.detect_harness({"COPILOT_AGENT_ID": "x"})["name"], "copilot")
        self.assertEqual(doctor.detect_harness({"CURSOR_TRACE_ID": "x"})["name"], "cursor")
        self.assertEqual(doctor.detect_harness({"GEMINI_CLI": "1"})["name"], "gemini")
        self.assertEqual(doctor.detect_harness({"CLAUDECODE": "1", "GEMINI_CLI": "1"})["name"],
                         "several: claude-code, gemini")

    def test_a_key_or_a_home_setting_is_not_a_running_harness(self):
        for env in ({}, {"GEMINI_API_KEY": "k"}, {"CODEX_HOME": "/x"}, {"COPILOT_GITHUB_TOKEN": "t"},
                    {"PATH": "/bin", "HOME": "/h"}):
            with self.subTest(env=sorted(env)):
                got = doctor.detect_harness(env)
                self.assertEqual(got["name"], "unknown")
                self.assertEqual(got["usually"]["subagents"], "unknown")

    def test_capabilities_never_touch_the_network_unless_asked(self):
        r = run("doctor.py", "--capabilities", "--json")
        self.assertIn(r.returncode, (0, 1), r.stderr)
        out = json.loads(r.stdout)
        self.assertNotIn("web", out)
        for key in ("os", "python", "shell", "harness", "git", "mcp", "knowledge_base", "playbooks", "capabilities"):
            with self.subTest(key=key):
                self.assertIn(key, out)
        self.assertEqual(out["capabilities"]["raw_fetch"], "not checked, run with --check web")
        self.assertIn("read only", run("doctor.py", "--capabilities").stdout.lower())

    def test_the_web_probe_is_one_head_to_the_url_it_is_given(self):
        import http.server
        import threading
        seen = []

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_HEAD(self):
                seen.append(self.command)
                self.send_response(200)
                self.end_headers()

            def log_message(self, *a):
                pass

        server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            got = doctor.probe_web(f"http://127.0.0.1:{server.server_port}/")
        finally:
            server.shutdown()
            server.server_close()
        self.assertTrue(got["reachable"])
        self.assertEqual(seen, ["HEAD"])

    def test_a_codex_sandbox_with_no_network_is_named_as_the_cause(self):
        old = dict(os.environ)
        try:
            os.environ["CODEX_SANDBOX"] = "seatbelt"
            os.environ["CODEX_SANDBOX_NETWORK_DISABLED"] = "1"
            got = doctor.probe_web("http://127.0.0.1:9/")
            self.assertEqual(got["cause"], "sandbox")
        finally:
            os.environ.clear()
            os.environ.update(old)

    def test_no_company_host_is_probed_or_named(self):
        src = (SKILL / "scripts" / "doctor.py").read_text(encoding="utf-8").lower()
        for word in ("c" + "mic", "bea" + "con", "v" + "pn"):    # in pieces, so the trace grep stays clean
            self.assertNotIn(word, src)

    def test_python_report_names_the_minimum(self):
        r = run("doctor.py", "--check", "python")
        self.assertIn("minimum 3.9", r.stdout)
        py = doctor.probe_python()
        self.assertEqual(py["minimum"], "3.9")
        self.assertIn("gets_security_fixes", py)

    def test_no_network_is_still_accepted(self):
        r = run("doctor.py", "--no-network", "--check", "mcp", "--json")
        self.assertIn(r.returncode, (0, 1), r.stderr)
        self.assertIn("mcp", json.loads(r.stdout))


class TestPackagingExclusions(unittest.TestCase):
    """The output folder never packages itself, and only top-level dist/ and results/ are dropped."""

    def setUp(self):
        self.work = Path(tempfile.mkdtemp(prefix="hww-pkgx-"))
        self.copy = copy_skill(self.work)

    def tearDown(self):
        shutil.rmtree(self.work, ignore_errors=True)

    def test_out_inside_the_skill_is_refused_except_dist(self):
        r = run_in(self.copy, "package.py", "--out", str(self.copy / "build"), "--skip-validate")
        self.assertEqual(r.returncode, 2)
        self.assertIn("inside the skill folder", r.stderr)
        for _ in range(2):  # a second build must not package the first
            r = run_in(self.copy, "package.py", "--out", str(self.copy / "dist"), "--skip-validate", "--json")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["problems"], [])
        import zipfile
        with zipfile.ZipFile(self.copy / "dist" / "flarehand.zip") as z:
            self.assertFalse([n for n in z.namelist() if "/dist/" in n or "-plugin/" in n])

    def test_nested_results_folder_still_ships(self):
        (self.copy / "assets" / "results").mkdir()
        (self.copy / "assets" / "results" / "x.md").write_text("x\n", encoding="utf-8")
        (self.copy / "results").mkdir(exist_ok=True)
        (self.copy / "results" / "run.md").write_text("x\n", encoding="utf-8")
        r = run_in(self.copy, "package.py", "--out", str(self.work / "out"), "--skip-validate",
                   "--formats", "zip", "--json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        import zipfile
        with zipfile.ZipFile(self.work / "out" / "flarehand.zip") as z:
            names = z.namelist()
        self.assertIn("flarehand/assets/results/x.md", names)
        self.assertNotIn("flarehand/results/run.md", names)

    def test_collect_drops_the_output_folder(self):
        self.assertEqual(package.EXCLUDE_TOP, {"dist", "results"})
        self.assertNotIn("dist", package.EXCLUDE_DIRS)


class TestValidatorPackagingRules(unittest.TestCase):
    """Binaries are caught by content, not just by name, and messages say the true cause."""

    def setUp(self):
        self.work = Path(tempfile.mkdtemp(prefix="hww-val-"))
        self.copy = copy_skill(self.work)

    def tearDown(self):
        shutil.rmtree(self.work, ignore_errors=True)

    def validate(self) -> dict:
        r = run_in(self.copy, "validate_skill.py", "--json")
        return json.loads(r.stdout)

    def test_binaries_are_caught_by_suffix_and_by_content(self):
        (self.copy / "assets" / "tool.jar").write_text("x\n", encoding="utf-8")
        (self.copy / "assets" / "blob.dat").write_bytes(b"MZ\x00\x00\x01\x02" * 10)
        (self.copy / "assets" / "note.txt").write_text("plain\n", encoding="utf-8")
        errors = "\n".join(self.validate()["errors"])
        self.assertIn("tool.jar cannot ship", errors)
        self.assertIn("blob.dat is a binary file", errors)
        self.assertNotIn("note.txt", errors)
        for suffix in (".bin", ".jar", ".class", ".wasm"):
            self.assertIn(suffix, __import__("validate_skill").BAD_SUFFIXES)

    def test_a_big_file_gets_a_warning(self):
        (self.copy / "assets" / "big.md").write_text("a" * (4 * 1024 * 1024), encoding="utf-8")
        warnings = "\n".join(self.validate()["warnings"])
        self.assertIn("big.md is 4.0 MB", warnings)

    def test_plugin_folder_messages_name_the_right_cause(self):
        (self.copy / "hooks").mkdir()
        (self.copy / "themes").mkdir()
        errors = "\n".join(self.validate()["errors"])
        self.assertIn("`hooks/` makes Claude Code load this folder as a plugin", errors)
        self.assertIn("`themes/` is a plugin component name. House rule", errors)
        self.assertNotIn("skips", errors)

    def test_limit_messages_cite_the_right_source(self):
        src = (SKILL / "scripts" / "validate_skill.py").read_text(encoding="utf-8")
        self.assertIn("1024-character limit in the Agent Skills spec", src)
        self.assertIn("likely to hit context limits", src)
        self.assertNotIn("Copilot's 1024", src)
        self.assertNotIn("refuses to load", src)


if __name__ == "__main__":
    unittest.main()
