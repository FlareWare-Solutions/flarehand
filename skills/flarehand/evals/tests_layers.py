"""Tests for scripts/layers.py: playbook discovery, precedence, parents, cycles and the
two merge rules (shapes take the first match, rules add up).

Every test builds its own folders under a temporary directory and passes --root, so the
real knowledge base is never read.
"""

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

import layers  # noqa: E402


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class LayersCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fh-layers-")).resolve()
        self.root = self.tmp / "kb"
        self.root.mkdir()
        self.set_config([])
        self.repo = self.tmp / "repo"
        (self.repo / ".git").mkdir(parents=True)
        self.cwd = self.repo / "src" / "app"
        self.cwd.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def set_config(self, playbooks):
        write(self.root / "config.json", json.dumps({"prefs": {"playbooks": [str(p) for p in playbooks]}}))

    def make_playbook(self, folder: Path, name=None, parent=None) -> Path:
        folder.mkdir(parents=True, exist_ok=True)
        meta = {}
        if name:
            meta["name"] = name
        if parent:
            meta["parent"] = parent
        if meta:
            write(folder / "playbook.json", json.dumps(meta))
        return folder

    def names(self, **kw):
        return [pb.name for pb in layers.playbooks(kw.get("cwd", self.cwd), self.root)]


class TestDiscovery(LayersCase):
    def test_no_playbooks_is_an_empty_list(self):
        self.assertEqual(layers.playbooks(self.cwd, self.root), [])
        self.assertEqual(layers.layered("glossary.tsv", self.cwd, self.root), [])

    def test_repo_playbook_found_walking_up_to_the_git_root(self):
        self.make_playbook(self.repo / ".flarehand", name="payments-team")
        found = layers.playbooks(self.cwd, self.root)
        self.assertEqual([pb.name for pb in found], ["payments-team"])
        self.assertEqual(found[0].origin, "repo")
        self.assertEqual(found[0].path, (self.repo / ".flarehand").resolve())

    def test_nested_repo_playbooks_nearest_first(self):
        self.make_playbook(self.repo / ".flarehand", name="whole-repo")
        self.make_playbook(self.repo / "src" / ".flarehand", name="src-team")
        self.assertEqual(self.names(), ["src-team", "whole-repo"])

    def test_walk_stops_at_the_git_root(self):
        self.make_playbook(self.tmp / ".flarehand", name="above-the-repo")
        self.assertEqual(self.names(), [])

    def test_outside_a_repo_only_cwd_counts(self):
        plain = self.tmp / "plain" / "deep"
        plain.mkdir(parents=True)
        self.make_playbook(self.tmp / "plain" / ".flarehand", name="higher")
        self.assertEqual(self.names(cwd=plain), [])
        self.make_playbook(plain / ".flarehand", name="here")
        self.assertEqual(self.names(cwd=plain), ["here"])

    def test_name_falls_back_to_the_folder(self):
        self.make_playbook(self.repo / ".flarehand")
        self.assertEqual(self.names(), ["repo"])
        other = self.make_playbook(self.tmp / "company-book")
        self.set_config([other])
        self.assertEqual(self.names(), ["repo", "company-book"])

    def test_config_paths_come_after_the_repo(self):
        self.make_playbook(self.repo / ".flarehand", name="team")
        a = self.make_playbook(self.tmp / "a", name="dept")
        b = self.make_playbook(self.tmp / "b", name="company")
        self.set_config([a, b])
        found = layers.playbooks(self.cwd, self.root)
        self.assertEqual([pb.name for pb in found], ["team", "dept", "company"])
        self.assertEqual([pb.origin for pb in found], ["repo", "config", "config"])

    def test_config_path_may_hold_a_flarehand_folder(self):
        holder = self.tmp / "shared-repo"
        self.make_playbook(holder / ".flarehand", name="shared")
        self.set_config([holder])
        self.assertEqual(self.names(), ["shared"])

    def test_relative_config_path_is_read_from_the_knowledge_base(self):
        self.make_playbook(self.root / "books" / "mine-team", name="rel")
        write(self.root / "config.json", json.dumps({"prefs": {"playbooks": ["books/mine-team"]}}))
        self.assertEqual(self.names(), ["rel"])

    def test_no_duplicates_when_config_repeats_the_repo_playbook(self):
        pb = self.make_playbook(self.repo / ".flarehand", name="team")
        self.set_config([pb, self.repo, pb])
        self.assertEqual(self.names(), ["team"])
        self.assertEqual(layers.playbooks(self.cwd, self.root)[0].origin, "repo")

    def test_missing_config_path_is_a_problem_not_a_crash(self):
        self.set_config([self.tmp / "nowhere"])
        self.assertEqual(self.names(), [])
        self.assertTrue(any("not a folder" in p for p in layers.problems(self.cwd, self.root)))

    def test_broken_playbook_json_is_reported(self):
        pb = self.make_playbook(self.repo / ".flarehand")
        write(pb / "playbook.json", "{not json")
        self.assertEqual(self.names(), ["repo"])
        self.assertTrue(any("not a JSON object" in p for p in layers.problems(self.cwd, self.root)))


class TestParents(LayersCase):
    def test_parent_found_by_name_goes_after_its_child(self):
        company = self.make_playbook(self.tmp / "co", name="company")
        self.make_playbook(self.repo / ".flarehand", name="team", parent="company")
        self.set_config([company])
        self.assertEqual(self.names(), ["team", "company"])

    def test_parent_listed_first_in_config_still_comes_after_the_child(self):
        company = self.make_playbook(self.tmp / "co", name="company")
        team = self.make_playbook(self.tmp / "tm", name="team", parent="company")
        self.set_config([company, team])
        self.assertEqual(self.names(), ["team", "company"])

    def test_parent_given_as_a_path(self):
        self.make_playbook(self.tmp / "co", name="company")
        self.make_playbook(self.repo / ".flarehand", name="team", parent=str(self.tmp / "co"))
        found = layers.playbooks(self.cwd, self.root)
        self.assertEqual([pb.name for pb in found], ["team", "company"])

    def test_relative_parent_path_is_read_from_the_child(self):
        self.make_playbook(self.repo / "standards", name="org")
        self.make_playbook(self.repo / ".flarehand", name="team", parent="../standards")
        self.assertEqual(self.names(), ["team", "org"])

    def test_grandparent_chain(self):
        org = self.make_playbook(self.tmp / "org", name="org")
        dept = self.make_playbook(self.tmp / "dept", name="dept", parent="org")
        self.make_playbook(self.repo / ".flarehand", name="team", parent="dept")
        self.set_config([org, dept])
        self.assertEqual(self.names(), ["team", "dept", "org"])

    def test_two_teams_share_one_parent_which_comes_last(self):
        co = self.make_playbook(self.tmp / "co", name="company")
        a = self.make_playbook(self.tmp / "a", name="team-a", parent="company")
        b = self.make_playbook(self.tmp / "b", name="team-b", parent="company")
        self.set_config([a, co, b])
        self.assertEqual(self.names(), ["team-a", "team-b", "company"])

    def test_cycle_is_followed_once(self):
        a = self.make_playbook(self.tmp / "a", name="alpha", parent="beta")
        b = self.make_playbook(self.tmp / "b", name="beta", parent="alpha")
        self.set_config([a, b])
        found = self.names()
        self.assertEqual(sorted(found), ["alpha", "beta"])
        self.assertTrue(any("loop" in p for p in layers.problems(self.cwd, self.root)))

    def test_self_parent_is_a_loop(self):
        a = self.make_playbook(self.tmp / "a", name="alpha", parent="alpha")
        self.set_config([a])
        self.assertEqual(self.names(), ["alpha"])

    def test_unknown_parent_is_a_problem(self):
        self.make_playbook(self.repo / ".flarehand", name="team", parent="ghost")
        self.assertEqual(self.names(), ["team"])
        self.assertTrue(any("ghost" in p for p in layers.problems(self.cwd, self.root)))


class TestPrecedence(LayersCase):
    def setUp(self):
        super().setUp()
        co = self.make_playbook(self.tmp / "co", name="company")
        team = self.make_playbook(self.repo / ".flarehand", name="team", parent="company")
        self.set_config([co])
        self.shipped = write(self.tmp / "shipped" / "templates" / "test-plan.md", "shipped")
        write(team / "templates" / "test-plan.md", "team")
        write(co / "templates" / "test-plan.md", "company")
        self.co, self.team = co, team

    def test_layered_order_yours_team_company_shipped(self):
        write(self.root / "templates" / "test-plan.md", "yours")
        got = layers.layered("templates/test-plan.md", self.cwd, self.root, self.shipped)
        self.assertEqual([l for l, _ in got], ["yours", "team:team", "team:company", "shipped"])
        self.assertEqual([p.read_text() for _, p in got], ["yours", "team", "company", "shipped"])

    def test_layered_lists_existing_files_only(self):
        (self.team / "templates" / "test-plan.md").unlink()
        got = layers.layered("templates/test-plan.md", self.cwd, self.root, self.shipped)
        self.assertEqual([l for l, _ in got], ["team:company", "shipped"])
        got = layers.layered("templates/test-plan.md", self.cwd, self.root, self.tmp / "missing.md")
        self.assertEqual([l for l, _ in got], ["team:company"])

    def test_layered_refuses_a_path_that_leaves_the_layer(self):
        write(self.tmp / "secret.md", "x")
        self.assertEqual(layers.layered("../secret.md", self.cwd, self.root), [])
        self.assertEqual(layers.layered(str(self.tmp / "secret.md"), self.cwd, self.root), [])

    def test_read_tsv_tags_every_row_and_skips_comments(self):
        write(self.root / "glossary.tsv", "term\tmeanings\task\tadded\n# a comment\nrole\ta | b\tWhich?\t2026-01-01\n")
        write(self.team / "glossary.tsv", "# header comment\nterm\tmeanings\task\tadded\nrole\tc\t\t\nbatch\td\t\t\n")
        write(self.co / "glossary.tsv", "term\tmeanings\nbatch\te\n")
        rows = layers.read_tsv("glossary.tsv", self.cwd, self.root)
        self.assertEqual([(r["term"], r["layer"]) for r in rows],
                         [("role", "yours"), ("role", "team:team"), ("batch", "team:team"),
                          ("batch", "team:company")])
        self.assertEqual(rows[0]["ask"], "Which?")
        self.assertNotIn("ask", rows[3])

    def test_shapes_take_the_first_match(self):
        rows = [{"key": "x", "v": "1", "layer": "yours"}, {"key": "X", "v": "2", "layer": "team:t"},
                {"key": "y", "v": "3", "layer": "shipped"}]
        got = layers.first_by_key(rows, "key")
        self.assertEqual(got["x"]["layer"], "yours")
        self.assertEqual(got["y"]["v"], "3")

    def test_rules_add_up(self):
        rows = [{"rule": "a", "layer": "yours"}, {"rule": "a", "layer": "team:t"},
                {"rule": "b", "layer": "team:t"}]
        self.assertEqual(len(layers.union(rows)), 3)
        self.assertEqual([r["rule"] for r in layers.union(rows, "rule")], ["a", "b"])

    def test_house_rules_add_up_across_layers(self):
        write(self.root / "house-rules.md", "## Writing\n\n- Lead with the answer.\n")
        write(self.team / "house-rules.md", "# House rules\n\n## Pull requests\n\n- Link the ticket.\n"
                                            "- Keep it small.\n\n## Writing\n\n- Lead with the answer.\n")
        write(self.co / "house-rules.md", "## Security\n\n- No secrets in code.\n```\n- not a rule\n```\n")
        got = layers.house_rules(self.cwd, self.root)
        self.assertEqual([(r["area"], r["rule"], r["layer"]) for r in got],
                         [("Writing", "Lead with the answer.", "yours"),
                          ("Pull requests", "Link the ticket.", "team:team"),
                          ("Pull requests", "Keep it small.", "team:team"),
                          ("Security", "No secrets in code.", "team:company")])

    def test_a_personal_file_cannot_remove_a_team_rule(self):
        write(self.root / "house-rules.md", "## Pull requests\n")
        write(self.team / "house-rules.md", "## Pull requests\n\n- Link the ticket.\n")
        self.assertEqual([r["rule"] for r in layers.house_rules(self.cwd, self.root)], ["Link the ticket."])

    def test_glossary_merges_meanings(self):
        write(self.root / "glossary.tsv", "term\tmeanings\task\tadded\nrole\tjob title\t\t\n")
        write(self.team / "glossary.tsv", "term\tmeanings\task\tadded\nRole\tsecurity role | job title\tWhich role?\t\n")
        got = layers.glossary(self.cwd, self.root)
        self.assertEqual(got[0]["meanings"], ["job title", "security role"])
        self.assertEqual(got[0]["ask"], "Which role?")
        self.assertEqual(got[0]["layers"], ["yours", "team:team"])


class TestCommandLine(LayersCase):
    def test_list_json_and_read_only(self):
        self.make_playbook(self.repo / ".flarehand", name="team")
        before = sorted(str(p) for p in self.tmp.rglob("*"))
        r = subprocess.run([sys.executable, str(SKILL / "scripts" / "layers.py"), "--root", str(self.root),
                            "--cwd", str(self.cwd), "--json", "list"], capture_output=True, text=True,
                           env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["playbooks"][0]["name"], "team")
        self.assertEqual(before, sorted(str(p) for p in self.tmp.rglob("*")))

    def test_help(self):
        r = subprocess.run([sys.executable, str(SKILL / "scripts" / "layers.py"), "--help"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertIn("Read only", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
