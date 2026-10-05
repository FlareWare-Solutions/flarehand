"""Checks on the shipped templates, their tables and the template catalog.

Loaded by tests/test_scripts.py, and runnable on its own:
    python3 -m unittest tests.tests_core_templates -v
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "flarehand"
REPO = ROOT
sys.path.insert(0, str(SKILL / "scripts"))

import kb  # noqa: E402
import check_output  # noqa: E402

TEMPLATES = SKILL / "assets" / "templates"
CATALOG = REPO / "docs" / "template-catalog.tsv"

GROUPS = {"decide", "plan", "build-run", "ship", "respond-support", "communicate", "learn",
          "people", "money", "sell"}
FREQUENCIES = {"daily", "weekly", "per-event", "quarterly"}
AUDIENCES = {"self", "team", "exec", "external"}
STATUSES = {"sourced", "mixed", "general-practice"}

# Terms that would tie a shipped file to the project this one grew from. They live in the
# gitignored .release-guard at the repository root, because publishing the list would publish the
# words. Without that file (a fresh clone, a packaged skill) the pattern matches nothing.
_GUARD = ROOT / ".release-guard"
_TERMS = [ln.strip() for ln in (_GUARD.read_text(encoding="utf-8").splitlines() if _GUARD.is_file() else [])
          if ln.strip() and not ln.lstrip().startswith("#")]
COMPANY_TERMS = re.compile("|".join(f"(?:{t})" for t in _TERMS) if _TERMS else r"(?!)", re.IGNORECASE)

NEW_TEMPLATES = {
    "decision-record", "postmortem", "weekly-update", "design-doc", "product-brief", "business-case",
    "project-charter", "retrospective", "okrs", "onboarding-plan", "performance-review",
    "incident-comms", "sop", "policy", "vendor-evaluation", "experiment-brief", "launch-plan",
    "pr-faq", "user-interview", "interview-scorecard", "case-study", "press-release",
    "investor-update", "research-proposal", "docs-page",
}
RENAMED = {
    "kcs-article": "knowledge-article", "known-error": "knowledge-article",
    "itil-incident": "incident-report", "qbr": "business-review", "bid-response": "client-proposal",
    "deal-artifact": "deal-summary", "ps-delivery": "statement-of-work",
    "marketing-brief": "creative-brief", "team-notes": "one-on-one-notes",
    "curriculum": "course-design", "setup-guide": "docs-page", "conversion": "data-migration",
}
# Text that is published or sent, so its body holds only what the reader sees.
OUTWARD = ["docs-page", "knowledge-article", "customer-reply", "release-notes", "press-release",
           "case-study", "policy", "sop", "job-description", "incident-comms", "investor-update",
           "research-proposal", "weekly-update", "project-closeout", "performance-review",
           "client-proposal", "statement-of-work", "hr-document"]
ENGINEERING_PACK = {"sql-build", "db-diagnostic", "ci-triage", "cutover", "data-migration", "code-review"}


def run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SKILL / "scripts" / script), *args],
        capture_output=True, text=True, timeout=60,
    )


def templates() -> list[Path]:
    return sorted(TEMPLATES.glob("*.md"))


def is_workflow_default(path: Path) -> bool:
    return bool(re.match(r"wf-\d\d-", path.stem))


def artifact_templates() -> list[Path]:
    return [p for p in templates() if not is_workflow_default(p)]


def meta_of(path: Path) -> dict:
    return kb.parse_frontmatter(path.read_text(encoding="utf-8"))[0]


def tags_of(path: Path) -> dict:
    """The one-level `tags:` map. kb.parse_frontmatter keeps a nested map as raw lines and
    does not parse it, so the tests read it here."""
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^tags:\n((?:  \S.*\n)+)", text, re.M)
    out: dict = {}
    if not m:
        return out
    for line in m.group(1).splitlines():
        key, _, value = line.strip().partition(":")
        value = value.strip()
        out[key] = [v.strip() for v in value[1:-1].split(",") if v.strip()] \
            if value.startswith("[") and value.endswith("]") else value
    return out


def catalog_rows() -> list[dict]:
    lines = CATALOG.read_text(encoding="utf-8").splitlines()
    head = lines[0].split("\t")
    return [dict(zip(head, l.split("\t"))) for l in lines[1:] if l.strip()]


class TestTemplates(unittest.TestCase):
    def test_every_template_has_frontmatter_learn_questions_and_passes_its_contract(self):
        contracts = check_output.load_contracts(SKILL / "assets" / "contracts.tsv")
        for path in templates():
            with self.subTest(template=path.name):
                text = path.read_text(encoding="utf-8")
                meta = meta_of(path)
                self.assertEqual(meta.get("template"), path.stem)
                self.assertTrue(meta.get("title"))
                self.assertIn(meta.get("source_status"), STATUSES)
                self.assertGreaterEqual(len(meta.get("learn") or []), 3)
                self.assertTrue(meta.get("basis"))
                self.assertIn(meta.get("workflow"), contracts)
                # A template is the shape the artifact takes, so it demonstrates its own
                # contract: every required section, and every required element shown in the
                # skeleton rather than described in a comment a reader has to obey.
                masked = "\n".join(check_output.mask(text))
                self.assertEqual(
                    check_output.check_contract(masked, meta["workflow"], contracts), [])

    def test_every_basis_cites_a_public_framework_by_url(self):
        for path in templates():
            with self.subTest(template=path.name):
                basis = meta_of(path).get("basis") or []
                urls = [u for b in basis for u in re.findall(r"https?://\S+", b)]
                self.assertTrue(urls, "basis names no URL")
                for u in urls:
                    self.assertRegex(u, r"^https://[a-z0-9.-]+\.[a-z]{2,}(/\S*)?$")
                for b in basis:
                    # A line without a URL is only allowed as a jurisdiction note.
                    if "http" not in b:
                        self.assertTrue(b.startswith("Examples by jurisdiction"), b)

    def test_shipped_templates_carry_no_company_sources_or_terms(self):
        for path in templates():
            with self.subTest(template=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertEqual(meta_of(path).get("team_sources"), [], "shipped templates cite no team sources")
                hit = COMPANY_TERMS.search(text)
                self.assertIsNone(hit, hit and hit.group(0))
        for rel in ("assets/contracts.tsv", "assets/workflows.tsv", "assets/workflow-graph.tsv",
                    "assets/style-profiles.tsv", "references/wf-05-draft.md"):
            with self.subTest(file=rel):
                hit = COMPANY_TERMS.search((SKILL / rel).read_text(encoding="utf-8"))
                self.assertIsNone(hit, hit and hit.group(0))
        hit = COMPANY_TERMS.search(CATALOG.read_text(encoding="utf-8"))
        self.assertIsNone(hit, hit and hit.group(0))

    def test_shipped_templates_cite_no_customer_named_documents(self):
        for path in templates():
            with self.subTest(template=path.name):
                self.assertNotRegex(path.read_text(encoding="utf-8"), r"Case \d+ - \([A-Z][a-z]+\)")

    def test_templates_have_no_em_dashes(self):
        for path in templates():
            with self.subTest(template=path.name):
                self.assertNotIn("—", path.read_text(encoding="utf-8"))

    def test_every_artifact_template_is_tagged(self):
        for path in artifact_templates():
            with self.subTest(template=path.name):
                tags = tags_of(path)
                self.assertIn(tags.get("group"), GROUPS)
                self.assertIn(tags.get("frequency"), FREQUENCIES)
                self.assertIn(tags.get("audience"), AUDIENCES)
                self.assertIsInstance(tags.get("roles"), list)
                self.assertTrue(tags.get("roles"))

    def test_tags_do_not_break_the_frontmatter_reader(self):
        """A nested map is kept as raw lines, so the keys after it still parse, and a save
        through kb.py writes it back unchanged."""
        path = TEMPLATES / "decision-record.md"
        meta = meta_of(path)
        self.assertNotIn("tags", meta)
        self.assertEqual(meta["next"], ["project-charter", "design-doc"])
        self.assertEqual(len(meta["learn"]), 3)
        self.assertIn("  group: decide", kb.dump_frontmatter(meta))

    def test_next_names_real_templates(self):
        names = {p.stem for p in templates()}
        for path in artifact_templates():
            with self.subTest(template=path.name):
                nxt = meta_of(path).get("next")
                self.assertIsInstance(nxt, list)
                for name in nxt:
                    self.assertIn(name, names)
                    self.assertNotEqual(name, path.stem)

    def test_new_templates_exist_with_four_to_nine_reader_sections(self):
        """Five to nine sections counting the status block. Outward templates moved that block
        to author-only notes, so four reader sections is the floor. docs-page is the exception:
        its sections depend on the mode, so all are optional."""
        contracts = check_output.load_contracts(SKILL / "assets" / "contracts.tsv")
        for name in sorted(NEW_TEMPLATES - {"docs-page"}):
            with self.subTest(template=name):
                path = TEMPLATES / f"{name}.md"
                self.assertTrue(path.is_file())
                _, spec = check_output.template_contract(path, contracts)
                own = [s for s in spec["sections"] if "missing" not in s.lower()]
                self.assertGreaterEqual(len(own), 4, own)
                self.assertLessEqual(len(own), 9, own)
                self.assertEqual(len(meta_of(path).get("learn")), 3)
        self.assertEqual(len(meta_of(TEMPLATES / "docs-page.md").get("learn")), 3)

    def test_outward_templates_keep_author_material_out_of_the_published_text(self):
        """Text that is published or sent holds only what its reader sees. Status, approvals,
        bias checks and reviewer notes sit in author-only sections after the artifact, which
        the template check does not require."""
        contracts = check_output.load_contracts(SKILL / "assets" / "contracts.tsv")
        for name in OUTWARD:
            with self.subTest(template=name):
                path = TEMPLATES / f"{name}.md"
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("## Draft status", text)
                self.assertNotRegex(text, r"(?m)^\*\*(Draft only|Session only)")
                if "## Draft notes" in text:
                    self.assertIn("## Draft notes\n<!-- author-only -->", text)
                    self.assertLess(text.index("## Draft notes"), text.index("## MISSING - you must supply"))
                _, spec = check_output.template_contract(path, contracts)
                for author in ("Draft notes", "Notes for the reviewer", "Fact check", "Bid plan",
                               "Bias check", "Bias and posting check", "Route to HR"):
                    self.assertNotIn(author, spec["sections"])
        for path in templates():
            text = path.read_text(encoding="utf-8")
            if "## Notes for the reviewer" in text:
                with self.subTest(template=path.name):
                    self.assertIn("## Notes for the reviewer\n<!-- author-only -->", text)

    def test_postmortem_marks_added_actions_as_proposed(self):
        text = (TEMPLATES / "postmortem.md").read_text(encoding="utf-8")
        self.assertIn("proposed", text.split("## Action items")[1].split("## ")[0])

    def test_wf05_states_the_drafting_rules(self):
        text = " ".join((SKILL / "references" / "wf-05-draft.md").read_text(encoding="utf-8").split())
        self.assertIn("It never suggests an answer", text)
        self.assertIn("Never interpret inside outbound text", text)
        self.assertIn("never `[inference]`", text)
        self.assertIn("`<!-- author-only -->`", text)

    def test_renamed_templates_are_gone_and_their_successors_exist(self):
        for old, new in RENAMED.items():
            with self.subTest(old=old):
                self.assertFalse((TEMPLATES / f"{old}.md").exists())
                self.assertTrue((TEMPLATES / f"{new}.md").is_file())
        self.assertTrue((TEMPLATES / "project-closeout.md").is_file())
        self.assertTrue((TEMPLATES / "job-description.md").is_file())
        self.assertTrue((TEMPLATES / "hr-document.md").is_file())

    def test_engineering_pack_is_flagged_and_found_by_template_get(self):
        """Templates stay flat because kb.py, classify.py and check_output find them by
        assets/templates/<name>.md. The pack is a frontmatter field until a subfolder works."""
        flagged = {p.stem for p in templates() if meta_of(p).get("pack") == "engineering"}
        self.assertEqual(flagged, ENGINEERING_PACK)
        self.assertEqual(list(TEMPLATES.glob("*/*.md")), [], "no template hides in a subfolder")
        tmp = Path(tempfile.mkdtemp(prefix="fh-tpl-"))
        try:
            root = tmp / "kb"
            run("kb.py", "init", "--root", str(root))
            for name in sorted(ENGINEERING_PACK):
                with self.subTest(template=name):
                    got = run("kb.py", "--root", str(root), "template", "get", name, "--json")
                    self.assertEqual(got.returncode, 0, got.stderr)
                    self.assertEqual(json.loads(got.stdout)["source"], "shipped")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_engineering_pack_is_vendor_neutral(self):
        diag = (TEMPLATES / "db-diagnostic.md").read_text(encoding="utf-8")
        for engine in ("PostgreSQL", "MySQL", "SQL Server", "Oracle"):
            self.assertIn(engine, diag)
        ci = (TEMPLATES / "ci-triage.md").read_text(encoding="utf-8")
        for system in ("GitHub Actions", "GitLab CI", "Jenkins"):
            self.assertIn(system, ci)

    def test_modes_promised_by_the_catalog_are_present(self):
        text = {p.stem: p.read_text(encoding="utf-8") for p in templates()}
        for group in ("Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"):
            self.assertIn(f"### {group}", text["release-notes"])
        self.assertIn("## Known error details", text["knowledge-article"])
        for section in ("## Before you begin", "## Steps", "## Undo the change", "## <Item name>",
                        "## Install", "## Usage"):
            self.assertIn(section, text["docs-page"])
        for mode in ("tutorial", "how-to", "reference", "explanation", "README"):
            self.assertIn(mode, text["docs-page"])
        for stage in ("## Desired results", "## Evidence", "## Steps", "## Lesson plan"):
            self.assertIn(stage, text["course-design"])
        self.assertIn("## Literature search record", text["research-proposal"])
        self.assertIn("## Budget request summary", text["business-case"])
        for phase in ("## Investigating", "## Identified", "## Monitoring", "## Resolved"):
            self.assertIn(phase, text["incident-comms"])
        self.assertIn("## Results", text["experiment-brief"])

    def test_people_and_legal_templates_keep_their_guards(self):
        text = {p.stem: p.read_text(encoding="utf-8") for p in templates()}
        self.assertIn("not legal advice", text["policy"])
        self.assertIn("Session only", text["performance-review"])
        self.assertIn("Rating: <left blank", text["performance-review"])
        self.assertIn("(session only, not saved)", text["hr-document"])
        self.assertIn("Blameless", text["postmortem"])
        for name in ("one-on-one-notes", "job-description", "performance-review", "policy", "hr-document"):
            with self.subTest(template=name):
                learn = " ".join(meta_of(TEMPLATES / f"{name}.md")["learn"]).lower()
                self.assertIn("province or state", learn)
        # RAPID is a trademark, so the decision record names only RAPID-style roles.
        self.assertNotRegex(text["decision-record"], r"RAPID(?!-style|\.| is a Bain| decision roles)")

    def test_postmortem_action_items_carry_owner_and_due(self):
        text = (TEMPLATES / "postmortem.md").read_text(encoding="utf-8")
        self.assertIn("| Action | Type | Owner | Due |", text)

    def test_vendor_weights_sum_to_one_hundred(self):
        text = (TEMPLATES / "vendor-evaluation.md").read_text(encoding="utf-8")
        self.assertIn("| Total | 100 |", text)
        self.assertIn("Total cost of ownership", text)

    def test_style_profiles_name_real_templates(self):
        names = {p.stem for p in templates()}
        for line in (SKILL / "assets" / "style-profiles.tsv").read_text(encoding="utf-8").splitlines()[1:]:
            if not line.strip():
                continue
            for name in line.split("\t")[1].split(","):
                with self.subTest(template=name):
                    self.assertIn(name.strip(), names)

    def test_personal_template_replaces_the_shipped_one_and_sets_the_contract(self):
        tmp = Path(tempfile.mkdtemp(prefix="fh-tpl-"))
        try:
            root = tmp / "memory"
            run("kb.py", "init", "--root", str(root))
            ours = tmp / "ours.md"
            ours.write_text("# Ours\n\n## Scope\n\n## Sign off\n", encoding="utf-8")
            self.assertEqual(run("kb.py", "--root", str(root), "template", "save", "test-plan",
                                 "--from", str(ours)).returncode, 0)
            got = json.loads(run("kb.py", "--root", str(root), "template", "get", "test-plan", "--json").stdout)
            self.assertEqual(got["source"], "yours")
            artifact = tmp / "a.md"
            artifact.write_text("# x\n\n## Scope\n\nok\n", encoding="utf-8")
            r = run("check_output.py", "--template", got["path"], str(artifact))
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("Sign off", r.stdout)
            self.assertIn("Gaps you must fill", r.stdout)  # test-plan is wf-11, whose gap section has this name
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_a_filled_new_template_passes_its_own_template_check(self):
        """The shape a model fills in, headings kept and placeholders replaced, passes
        check_output --template, so the required sections are reachable in practice."""
        tmp = Path(tempfile.mkdtemp(prefix="fh-tpl-"))
        try:
            contracts = check_output.load_contracts(SKILL / "assets" / "contracts.tsv")
            for name in sorted(NEW_TEMPLATES):
                with self.subTest(template=name):
                    path = TEMPLATES / f"{name}.md"
                    _, spec = check_output.template_contract(path, contracts)
                    body = "# Filled\n\n" + "".join(f"## {s}\n\nText [your input]\n\n" for s in spec["sections"])
                    body += "Owner: someone\n"
                    out = tmp / f"{name}.md"
                    out.write_text(body, encoding="utf-8")
                    r = run("check_output.py", "--template", str(path), str(out))
                    self.assertEqual(r.returncode, 0, r.stdout)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestCatalog(unittest.TestCase):
    """docs/template-catalog.tsv feeds the router rows. It must list every artifact template
    once, and agree with each template's own frontmatter."""

    def test_catalog_columns(self):
        head = CATALOG.read_text(encoding="utf-8").splitlines()[0].split("\t")
        self.assertEqual(head, ["template", "old_name", "group", "workflow", "roles", "trigger_words",
                                "audience", "frequency"])

    def test_catalog_lists_every_artifact_template_once(self):
        rows = catalog_rows()
        listed = [r["template"] for r in rows]
        self.assertEqual(len(listed), len(set(listed)))
        self.assertEqual(set(listed), {p.stem for p in artifact_templates()})

    def test_catalog_agrees_with_the_templates(self):
        for row in catalog_rows():
            with self.subTest(template=row["template"]):
                path = TEMPLATES / f"{row['template']}.md"
                tags = tags_of(path)
                self.assertEqual(row["workflow"], meta_of(path)["workflow"])
                self.assertEqual(row["group"], tags["group"])
                self.assertEqual(row["audience"], tags["audience"])
                self.assertEqual(row["frequency"], tags["frequency"])
                self.assertEqual(row["roles"].split(","), tags["roles"])
                words = [w.strip() for w in row["trigger_words"].split(",")]
                self.assertGreaterEqual(len(words), 3)
                self.assertTrue(all(words))

    def test_old_names_point_at_renamed_templates(self):
        for row in catalog_rows():
            for old in filter(None, row["old_name"].split(",")):
                with self.subTest(old=old):
                    self.assertIn(old, RENAMED.keys() | {"hr-document"})
                    self.assertFalse((TEMPLATES / f"{old}.md").exists() and old != "hr-document")


class TestWf05Reference(unittest.TestCase):
    def test_wf05_describes_the_catalog_by_group_and_team_specifics(self):
        text = (SKILL / "references" / "wf-05-draft.md").read_text(encoding="utf-8")
        self.assertIn("## Your team's specifics", text)
        self.assertNotIn("specifics\n\nA KB article", text)
        for label in ("Decide", "Plan", "Build and run", "Ship", "Respond and support", "Communicate",
                      "Learn", "People", "Money", "Sell"):
            self.assertIn(f"| {label} |", text)
        for path in artifact_templates():
            with self.subTest(template=path.stem):
                self.assertIn(path.stem, text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
