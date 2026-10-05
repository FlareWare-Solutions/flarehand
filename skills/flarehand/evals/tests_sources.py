"""tests_sources.py - source priority by role: the order, roles, pins, learning, project detection.

Runs as part of evals/test_scripts.py, which loads every tests_*.py beside it, and on its own:
    python3 -m unittest evals.tests_sources -v
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))

import sources  # noqa: E402


def run(script: str, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([sys.executable, str(SKILL / "scripts" / script), *args],
                          capture_output=True, text=True, timeout=60, env=env, cwd=cwd)


class Base(unittest.TestCase):
    role_words = "backend developer"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fh-src-"))
        self.root = self.tmp / "memory"
        run("kb.py", "init", "--root", str(self.root), "--role", self.role_words)
        self.set_config(created="2020-01-01")
        self.app = self.tmp / "app"
        (self.app / "src").mkdir(parents=True)
        (self.app / "pyproject.toml").write_text("[project]\nname='app'\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(self.app)], check=True)
        self.plain = self.tmp / "plain"
        self.plain.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def set_config(self, **values):
        path = self.root / "config.json"
        cfg = json.loads(path.read_text(encoding="utf-8"))
        cfg.update(values)
        path.write_text(json.dumps(cfg), encoding="utf-8")

    def src(self, *args):
        return run("sources.py", "--root", str(self.root), *args)

    def order(self, question, path=None):
        r = self.src("--json", "order", question, "--path", str(path or self.app))
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def rows(self, question, path=None):
        return {r["kind"]: r for r in self.order(question, path)["order"]}

    def kinds(self, question, path=None):
        return [r["kind"] for r in self.order(question, path)["order"]]


class TestTheOrder(Base):
    def test_user_and_kb_lead_every_order(self):
        for q in ("hello", "why did the cache change", "how do we deploy"):
            with self.subTest(q=q):
                self.assertEqual(self.kinds(q)[:2], ["user", "kb"])

    def test_a_question_about_change_puts_git_first_after_the_person(self):
        got = self.rows("why did the retry logic change last week")
        self.assertEqual(got["git"]["tier"], "signal")
        self.assertEqual(self.kinds("why did the retry logic change last week")[2], "git")

    def test_how_do_we_puts_the_playbook_first(self):
        self.assertEqual(self.rows("how do we cut a release", path=self.plain)["playbook"]["tier"], "signal")

    def test_a_version_question_puts_official_docs_first(self):
        self.assertEqual(self.rows("which version deprecated this flag")["official"]["tier"], "signal")

    def test_the_project_lifts_repo_and_official(self):
        rows = self.rows("hello")
        self.assertEqual(rows["repo"]["tier"], "project")
        self.assertEqual(rows["official"]["tier"], "project")
        got = self.order("hello")
        self.assertIn("python", got["project"]["technologies"])
        self.assertIn("docs.python.org", [d["domain"] for d in got["domains"]])

    def test_outside_a_repository_there_is_no_project_row(self):
        rows = self.rows("hello", path=self.plain)
        self.assertNotEqual(rows.get("repo", {}).get("tier"), "project")
        self.assertIn("not a git repository", rows["repo"]["how"])

    def test_every_row_has_a_concrete_hint(self):
        for r in self.order("hello")["order"]:
            with self.subTest(kind=r["kind"]):
                self.assertTrue(r["how"].strip())
        rows = self.rows("hello")
        self.assertIn("git -C", rows["git"]["how"])
        self.assertIn("kb.py search", rows["kb"]["how"])
        self.assertIn("ground.py fetch", rows["official"]["how"])
        self.assertIn("docs.python.org", rows["official"]["how"])

    def test_same_inputs_same_order(self):
        self.assertEqual(self.kinds("which table holds invoices"), self.kinds("which table holds invoices"))

    def test_text_output_prints_rows_and_hints(self):
        r = self.src("order", "why was this written this way", "--path", str(self.app))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Hint: ", r.stdout)
        self.assertIn("git log -S", r.stdout)

    def test_root_and_json_work_after_the_subcommand(self):
        r = run("sources.py", "order", "test plan", "--root", str(self.root), "--json", "--path", str(self.plain))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["roles"], ["developer"])


class TestRoles(Base):
    def test_role_is_guessed_from_their_own_words(self):
        self.assertEqual(self.order("anything")["roles"], ["developer"])

    def test_merged_roles_take_the_strongest_tier(self):
        self.src("role", "--set", "developer,support")
        rows = self.rows("a question with no signal words", path=self.plain)
        self.assertEqual(rows["mcp"]["tier"], "primary")       # secondary for developer, primary for support
        self.assertFalse(rows["mcp"]["only_if_weak"])

    def test_add_and_remove_replace_the_old_single_field(self):
        self.src("role", "--set", "support")
        self.src("role", "--add", "qa")
        self.src("role", "--remove", "support")
        prefs = json.loads((self.root / "config.json").read_text(encoding="utf-8"))["prefs"]
        self.assertEqual(prefs["roles"], ["qa"])
        self.assertNotIn("role", prefs)

    def test_an_unknown_role_is_refused_with_the_list(self):
        r = self.src("role", "--set", "astronaut")
        self.assertEqual(r.returncode, 2)
        self.assertIn("Pick from", r.stderr)
        self.assertIn("--new astronaut", r.stderr)

    def test_a_new_role_copies_another_and_can_be_set(self):
        r = self.src("role", "--new", "Platform Lead", "--like", "devops-sre")
        self.assertEqual(r.returncode, 0, r.stderr)
        tsv = (self.root / "source-tiers.tsv").read_text(encoding="utf-8")
        self.assertIn("role\tplatform-lead\tplaybook\tprimary", tsv)
        self.assertEqual(self.src("role", "--set", "platform-lead").returncode, 0)
        self.assertEqual(self.order("hello")["roles"], ["platform-lead"])

    def test_a_chosen_role_hears_about_other_words_once(self):
        self.src("role", "--set", "qa")
        out = self.src("role").stdout
        self.assertEqual(out.count("developer"), 2, out)   # the line, and the command in it
        self.assertNotIn("Your words point at", out)


class TestNewStarter(Base):
    def test_created_alone_does_not_make_a_new_starter(self):
        self.set_config(created=date.today().isoformat())
        self.src("role", "--set", "developer")
        self.assertNotIn("you are new", "; ".join(self.rows("hello", path=self.plain)["playbook"]["reasons"]))

    def test_started_on_within_thirty_days_boosts_the_playbook(self):
        self.src("role", "--set", "developer")
        self.set_config(started_on=(date.today() - timedelta(days=10)).isoformat())
        got = self.order("hello", path=self.plain)
        row = {r["kind"]: r for r in got["order"]}["playbook"]
        self.assertEqual(row["tier"], "primary")
        self.assertIn("you are new", "; ".join(row["reasons"]))
        self.assertIn("Onboarding pages first", row["how"])
        self.assertTrue(any("onboarding" in h for h in got["hints"]))

    def test_the_end_of_the_first_month_is_explained_not_reported_as_a_change(self):
        self.src("role", "--set", "it-helpdesk")
        self.set_config(started_on=(date.today() - timedelta(days=5)).isoformat())
        self.order("hello", path=self.plain)
        self.set_config(started_on=(date.today() - timedelta(days=33)).isoformat())
        got = self.order("hello", path=self.plain)
        self.assertNotIn("changed_since_last_time", got)


class TestPins(Base):
    def test_a_never_pin_removes_a_kind_even_when_the_question_asks_for_it(self):
        self.src("pin", "forum", "never")
        self.src("pin", "git", "never")
        kinds = self.kinds("why did the retry logic change")
        self.assertNotIn("forum", kinds)
        self.assertNotIn("git", kinds)

    def test_a_pin_can_lower_a_kind(self):
        self.src("pin", "official", "secondary")
        row = self.rows("hello")["official"]
        self.assertEqual(row["tier"], "secondary")
        self.assertTrue(row["only_if_weak"])

    def test_a_domain_pin_is_preferred_and_a_never_domain_is_dropped(self):
        self.src("pin", "https://www.example.org/docs/page", "primary")
        self.src("pin", "docs.python.org", "never")
        got = self.order("hello")
        domains = [d["domain"] for d in got["domains"]]
        self.assertIn("example.org", domains)
        self.assertNotIn("docs.python.org", domains)

    def test_pin_rejects_nonsense_and_clear_always_works(self):
        self.assertEqual(self.src("pin", "", "secondary").returncode, 2)
        r = self.src("pin", "forums", "primary")
        self.assertEqual(r.returncode, 2)
        self.assertIn("Did you mean forum", r.stderr)
        self.assertEqual(self.src("pin", "official", "maybe").returncode, 2)
        self.assertEqual(self.src("pin", "gone", "--clear").returncode, 0)

    def test_a_real_baseline_change_is_reported_and_question_signals_are_not(self):
        self.order("hello")
        self.assertNotIn("changed_since_last_time", self.order("why did it change"))
        self.src("pin", "forum", "primary")
        self.assertEqual(self.order("hello")["changed_since_last_time"]["added"], ["forum:primary"])

    def test_a_team_preference_applies_and_your_pin_beats_it(self):
        (self.root / "sources.tsv").write_text("type\tkey\tvalue\texpect\tnote\n"
                                               "prefer\tforum\tnever\t\tteam rule\n"
                                               "prefer\tsecondary\tprimary\t\t\n", encoding="utf-8")
        kinds = self.kinds("hello")
        self.assertNotIn("forum", kinds)
        self.assertEqual(self.rows("hello")["secondary"]["tier"], "primary")
        self.src("pin", "secondary", "secondary")
        self.assertEqual(self.rows("hello")["secondary"]["tier"], "secondary")


class TestLearning(Base):
    def test_used_writes_nothing_until_the_person_agrees(self):
        self.src("used", "https://docs.python.org/3/library/re.html")
        self.assertFalse((self.root / ".index" / "usage.jsonl").exists())
        self.src("learning", "--off")
        self.src("used", "https://docs.python.org/3/library/re.html")
        self.assertFalse((self.root / ".index" / "usage.jsonl").exists())

    def test_used_records_kind_domain_and_day_only(self):
        self.src("learning", "--on")
        self.src("used", "https://docs.python.org/3/library/re.html?secret=1", "git:abc123:src/a.py",
                 "mcp:tracker:ABC-1", "src/secret_module.py")
        text = (self.root / ".index" / "usage.jsonl").read_text(encoding="utf-8")
        rows = [json.loads(l) for l in text.splitlines()]
        self.assertEqual({k for r in rows for k in r}, {"kind", "domain", "day"})
        self.assertEqual(sorted(r["kind"] for r in rows), ["git", "mcp", "official", "repo"])
        self.assertIn("docs.python.org", [r["domain"] for r in rows])
        for secret in ("secret", "ABC-1", "abc123", "re.html"):
            self.assertNotIn(secret, text)

    def test_ledger_ids_are_resolved_to_their_kind(self):
        sys.path.insert(0, str(SKILL / "scripts"))
        import evidence
        folder = evidence.staging_dir(self.root)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "sources.jsonl").write_text(json.dumps(
            {"id": "S1", "kind": "web", "canonical": "https://stackoverflow.com/q/1", "tier": "T4"}) + "\n",
            encoding="utf-8")
        try:
            got = sources.classify_used(["S1", "S9"], self.root, sources.load_tiers())
            self.assertEqual(got, [("forum", "stackoverflow.com")])
        finally:
            shutil.rmtree(folder, ignore_errors=True)

    def test_one_day_of_use_moves_nothing_and_three_days_do(self):
        self.src("role", "--set", "developer")
        self.src("learning", "--on")
        log = self.root / ".index" / "usage.jsonl"
        today = date.today().isoformat()
        log.write_text("".join(json.dumps({"kind": "forum", "domain": "", "day": today}) + "\n" for _ in range(5)),
                       encoding="utf-8")
        self.assertEqual(self.rows("hello")["forum"]["tier"], "secondary")
        days = [(date.today() - timedelta(days=d)).isoformat() for d in (1, 2, 3)]
        log.write_text("".join(json.dumps({"kind": "forum", "domain": "dev.example.com", "day": d}) + "\n"
                               for d in days), encoding="utf-8")
        got = self.order("hello")
        row = {r["kind"]: r for r in got["order"]}["forum"]
        self.assertEqual(row["tier"], "primary")
        self.assertIn("3 days", "; ".join(row["reasons"]))
        self.assertIn("dev.example.com", [d["domain"] for d in got["domains"]])

    def test_learning_never_overrides_a_pin_and_suggests_instead(self):
        self.src("pin", "forum", "secondary")
        self.src("learning", "--on")
        days = [(date.today() - timedelta(days=d)).isoformat() for d in (1, 2, 3)]
        (self.root / ".index" / "usage.jsonl").write_text(
            "".join(json.dumps({"kind": "forum", "domain": "", "day": d}) + "\n" for d in days), encoding="utf-8")
        got = self.order("hello")
        self.assertEqual({r["kind"]: r for r in got["order"]}["forum"]["tier"], "secondary")
        self.assertIn(("raise the pin on", "forum"), [(s["action"], s["source"]) for s in got["pin_suggestions"]])

    def test_an_old_pin_that_never_helps_is_suggested_for_review(self):
        self.src("pin", "secondary", "primary")
        cfg = json.loads((self.root / "config.json").read_text(encoding="utf-8"))
        cfg["prefs"]["source_pin_dates"]["secondary"] = "2020-01-01"
        (self.root / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
        got = self.order("hello")
        self.assertIn("review the pin on", [s["action"] for s in got["pin_suggestions"] if s["source"] == "secondary"])

    def test_usage_list_can_be_cleared(self):
        self.src("learning", "--on")
        self.src("used", "git:HEAD:a.py")
        self.assertTrue((self.root / ".index" / "usage.jsonl").exists())
        self.src("learning", "--clear")
        self.assertFalse((self.root / ".index" / "usage.jsonl").exists())

    def test_citations_suggest_a_role_but_never_apply_it(self):
        tiers = sources.load_tiers()
        days = {(date.today() - timedelta(days=d)).isoformat() for d in (1, 2, 3)}
        usage = {"mcp": {"cites": 4, "days": days, "last": ""}, "repo": {"cites": 4, "days": days, "last": ""}}
        got = sources.role_suggestions(["trainer"], usage, tiers)
        self.assertIn("qa", [s["role"] for s in got if s["action"] == "add"])
        self.assertEqual(sources.role_suggestions(["trainer"], {k: dict(v, days={sources.today()})
                                                                 for k, v in usage.items()}, tiers), [])

    def test_a_url_scheme_or_junk_never_counts(self):
        seen = defaultdict(lambda: {"cites": 0, "days": set(), "last": ""})
        for key in ("https", "C:", "note", "", "not a domain"):
            sources._count(seen, key, sources.today())
        self.assertEqual(dict(seen), {})
        sources._count(seen, "official", sources.today())
        sources._count(seen, "docs.python.org", sources.today())
        self.assertEqual(sorted(seen), ["docs.python.org", "official"])


class TestTables(unittest.TestCase):
    def setUp(self):
        self.tiers = sources.load_tiers()

    def test_every_role_row_names_a_known_kind(self):
        for role, rows in self.tiers["role"].items():
            for r in rows:
                with self.subTest(role=role, kind=r["kind"]):
                    self.assertIn(r["kind"], sources.KINDS)
                    self.assertIn(r["tier"], ("primary", "secondary"))

    def test_every_kind_is_described(self):
        self.assertEqual(sorted(self.tiers["source"]), sorted(sources.KINDS))

    def test_a_borrowed_order_resolves(self):
        for name, like in self.tiers["alias"].items():
            with self.subTest(role=name):
                self.assertTrue(self.tiers["role"][name], f"{name} borrows {like} and got nothing")

    def test_business_family_roles_are_detected(self):
        for words, want in (("finance controller, I run month end close", "finance"),
                            ("HR business partner", "hr"), ("legal counsel", "legal"),
                            ("customer success manager", "customer-success"),
                            ("site reliability engineer on call", "devops-sre"),
                            ("I do appsec and threat models", "security")):
            with self.subTest(words=words):
                self.assertIn(want, sources.detect_roles(words, self.tiers))

    def test_nothing_known_is_general(self):
        self.assertEqual(sources.detect_roles("I juggle", self.tiers), ["general"])

    def serves_names(self):
        import kb
        out = set()
        for path in sorted((SKILL / "assets" / "templates").rglob("*.md")):
            meta, _ = kb.parse_frontmatter(path.read_text(encoding="utf-8"))
            for name in meta.get("serves") or []:
                out.add(str(name).strip())
        return out

    def test_every_job_title_a_template_serves_resolves_to_a_role(self):
        roles, serves = set(self.tiers["role"]), self.tiers["serves"]
        missing = sorted(n for n in self.serves_names() if n not in roles and n not in serves)
        self.assertEqual(missing, [], "add a serves row to assets/source-tiers.tsv for each")

    def test_every_mapping_points_at_a_role_that_exists(self):
        for title, role in sorted(self.tiers["serves"].items()):
            with self.subTest(title=title):
                self.assertIn(role, self.tiers["role"])

    def test_the_table_holds_no_company_trace(self):
        import re
        text = (SKILL / "assets" / "source-tiers.tsv").read_text(encoding="utf-8")
        # Spelled in pieces, so the build's own trace grep does not trip over this guard.
        words = ["c" + "mic", "bea" + "con", "v" + "pn", "dev" + "docs", "ai-" + "market", "vau" + "lt"]
        self.assertIsNone(re.search("(?i)" + "|".join(words), text))


class TestPersonalTiers(unittest.TestCase):
    def test_a_personal_role_is_loaded_and_replaces_the_shipped_rows(self):
        tmp = Path(tempfile.mkdtemp(prefix="fh-tiers-"))
        try:
            (tmp / "source-tiers.tsv").write_text(
                "kind\tkey\tselector\ttier\tnote\n"
                "role\tap-clerk\tplaybook\tprimary\tmonth end\n"
                "role\tdeveloper\tforum\tprimary\tmine\n"
                "role\tdeveloper\tnot-a-kind\tprimary\ttypo\n", encoding="utf-8")
            tiers = sources.load_tiers(tmp)
            self.assertEqual([r["kind"] for r in tiers["role"]["ap-clerk"]], ["playbook"])
            self.assertEqual([r["kind"] for r in tiers["role"]["developer"]], ["forum"])
            self.assertIn("ap-clerk", tiers["personal_roles"])
            self.assertNotIn("ap-clerk", sources.load_tiers()["role"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestProjectDetection(unittest.TestCase):
    MARKERS = {"package.json": "javascript", "pyproject.toml": "python", "go.mod": "go", "Cargo.toml": "rust",
               "pom.xml": "java", "build.gradle": "jvm", "pubspec.yaml": "dart", "App.csproj": "dotnet",
               "Gemfile": "ruby"}

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fh-proj-"))
        self.tiers = sources.load_tiers()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_each_marker_names_its_technology_and_docs(self):
        for marker, tech in self.MARKERS.items():
            with self.subTest(marker=marker):
                d = self.tmp / marker.replace(".", "_")
                d.mkdir()
                (d / marker).write_text("x\n", encoding="utf-8")
                got = sources.detect_project(d, self.tiers)
                self.assertIn(tech, [t["technology"] for t in got["technologies"]])
                self.assertTrue(got["docs"])

    def test_a_subfolder_finds_its_project(self):
        app = self.tmp / "app"
        (app / "src" / "deep").mkdir(parents=True)
        (app / "go.mod").write_text("module x\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(app)], check=True)
        got = sources.detect_project(app / "src" / "deep", self.tiers)
        self.assertEqual([t["technology"] for t in got["technologies"]], ["go"])
        self.assertEqual(Path(got["repository"]).resolve(), app.resolve())

    def test_nothing_recognised_is_said_plainly(self):
        r = run("sources.py", "project", "--path", str(self.tmp))
        self.assertEqual(r.returncode, 1)
        self.assertIn("nothing this table recognises", r.stdout)


class TestClassifyingSources(unittest.TestCase):
    def setUp(self):
        self.tiers = sources.load_tiers()

    def test_tiers_for_urls(self):
        cases = {"https://stackoverflow.com/questions/1": ("forum", "T4"),
                 "https://www.reddit.com/r/x": ("forum", "T4"),
                 "https://docs.python.org/3/library/re.html": ("official", "T2"),
                 "https://www.rfc-editor.org/rfc/rfc9110": ("official", "T1"),
                 "https://learn.microsoft.com/dotnet/core": ("official", "T2"),
                 "https://learn.microsoft.com/en-us/azure": ("secondary", "T3"),
                 "https://someblog.example/post": ("secondary", "T3")}
        for url, want in cases.items():
            with self.subTest(url=url):
                self.assertEqual(sources.tier_for_url(url, self.tiers), want)

    def test_locators_map_to_kinds(self):
        self.assertEqual(sources.kind_of("git:abc:src/a.py", self.tiers), ("git", ""))
        self.assertEqual(sources.kind_of("mcp:tracker:ABC-1", self.tiers), ("mcp", ""))
        self.assertEqual(sources.kind_of("src/a.py", self.tiers), ("repo", ""))
        self.assertEqual(sources.kind_of("repo/.flarehand/house-rules.md", self.tiers), ("playbook", ""))
        self.assertEqual(sources.kind_of("https://docs.python.org/3/", self.tiers), ("official", "docs.python.org"))


class TestWalkTheHistory(unittest.TestCase):
    def test_a_question_about_a_link_or_a_change_says_walk(self):
        cases = {
            "who calls the post_batch function": "git grep",
            "why is the lock check written this way": "git log -S",
            "what changed in the payroll calc since march": "git log -L",
            "which files change together with the posting module": "--name-only",
            "list every endpoint in the billing service": "git ls-files",
            "what did the config look like in march": "git show <rev>:<path>",
            "this file was renamed, where did it come from": "--follow",
        }
        for question, move in cases.items():
            with self.subTest(question=question):
                self.assertIn(move, sources.traversal_hint(question))

    def test_a_plain_fact_stays_one_search(self):
        for question in ("what columns does the invoice table have", "how do I install the CLI"):
            with self.subTest(question=question):
                self.assertEqual(sources.traversal_hint(question), "")

    def test_the_reference_names_every_move(self):
        text = (SKILL / "references" / "sources.md").read_text(encoding="utf-8")
        for move in ("git log -S", "git log -G", "git log -L", "git blame", "git log --follow", "--name-only",
                     "git show <rev>:<path>", "--since", 'sources.py order "<their words>" --path'):
            with self.subTest(move=move):
                self.assertIn(move, text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
