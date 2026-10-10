# Changelog

All notable changes to flarehand are listed here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- A website at https://flarehand.flareware.app: one page, `site/index.html`, published to GitHub
  Pages by `.github/workflows/pages.yml`.
  It explains flarehand for any role, gives every supported tool the same install card, and loads
  nothing from other sites.
- `tests/tests_site.py` checks the page's numbers, install commands and links against the
  repository. The Pages deploy runs it first.

### Changed

- The install guide gives the Copilot CLI marketplace commands, and a local-plugin install for Cursor
  until flarehand is in the Cursor Marketplace.
- `homepage` in every manifest points at the website instead of the repository, and the README
  links to it.

## [1.0.0] - 2026-10-05

The first public release.

### Added

#### Skills

- `flarehand`, the router skill. It turns a one-line work request into the deliverable it needs,
  through a nine-step pipeline: orient, classify, name, recall, ground, interview, run, check and
  record.
- Four entry points that hand into the same pipeline:
  - `flarehand-ground` checks a draft's facts and numbers before it goes out.
  - `flarehand-review` gives a graded review of code, a pull request, a document or a plan. Its
    perspectives lens reads the change as the people it will actually meet.
  - `flarehand-grill` stress-tests a plan or a vague ask in rounds of questions.
  - `flarehand-remember` saves, recalls and forgets.

#### Turning a weak prompt into a clear job

- A deterministic router of over 1,600 table rows. It picks the route, workflow, template, risk
  flags and how many questions to allow.
- It names the deliverable first, looks things up before asking, and asks a capped round of
  questions, each with a recommended answer. "Just go" accepts the recommended answers.
- A MISSING list that names who can supply each gap and never suggests an answer.

#### The method

- 12 workflows: diagnose, elicit, package (SBAR), compress, draft, translate, reconcile, themes,
  plan, critique, enumerate and re-tone.
- 60 templates in ten groups, each citing the framework it follows, plus an engineering pack.
- `check.py`, which runs every check on a draft in one command and prints `PASS` or a numbered fix
  list.

#### Grounding

- A grounding protocol with a claim ledger and nine labels.
- Source tiers and freshness classes.
- Quote checks against raw snapshots, number matching, and link checks.
- A checker that never saw the draft must record its verdict before a claim earns `verified`.

#### Memory

- A private knowledge base of plain Markdown at `~/.flareware/flarehand`, with a local git history.
- A save menu, so nothing is written without a yes.
- Provenance and status on every note line, review-by dates, and linked notes that pass doubt along.
- Saved answers that replay word for word, with their evidence kept beside them, and a re-check
  when a source drifts.
- Pinned sources with drift detection.

#### Learning and teams

- A learning loop that notices a repeated edit and asks before keeping it.
- Repeated chains of steps offered as your own workflows.
- A voice card, a context import and periodic check-ins.
- A first run that does the work before asking anything.
- Team and company playbooks in `.flarehand/`. Shapes take the nearest layer and rules add up
  across layers.

#### Safety

- Redaction before anything goes outbound.
- Sensitive data in notes is decided once and then said out loud each time it applies.
- Rules for notes about people.
- Guardrails for legal, finance, HR and production writes.
- Voice profiles: `plain` (the default), `google` and `none`.

#### Platforms and tooling

- One repository that installs in Claude Code, Codex, Cursor, Gemini CLI and Copilot, and as Agent
  Skills anywhere else.
- One hook dispatcher for every tool. Its hooks give a session nudge, a voice reminder and a
  compaction checkpoint.
- Over 800 unit tests.
- 37 live eval cases for `claude plugin eval`.
- Continuous integration on Linux, macOS and Windows.
- User documentation and the flarehand mark.

[Unreleased]: https://github.com/FlareWare-Solutions/flarehand/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/FlareWare-Solutions/flarehand/releases/tag/v1.0.0
