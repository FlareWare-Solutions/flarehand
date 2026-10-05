# How to test flarehand

Four tiers. The first two are free and run on every change. The third costs model time and runs
before a release, or after any change to text that shapes behaviour. The fourth is by hand.

| Tier | What it proves | Cost |
|---|---|---|
| 0. Unit tests | The scripts do what they say: routing, grounding checks, the knowledge base, layers, templates, packaging | Free |
| 1. Static validation | Every skill, manifest and eval case loads | Free |
| 2. Live evals | The skill fires when it should, stays out when it should, and behaves | Model time |
| 3. By hand | Memory across sessions, compaction, and other tools | Your time |

Commands below run from the repository root unless a step says otherwise.

## Tier 0: unit tests

```bash
HOME=$(mktemp -d) python3 tests/test_scripts.py
```

The temporary `HOME` proves the suite passes on a machine with no knowledge base, which is what CI
and every new user have. To run one module while you work, run `python3 tests/tests_core_kb.py -v`.
The unit tests live in the repository's `tests/`, and the eval cases in its `evals/`. Neither ships
inside a skill archive.

Read which tests failed, not just the count. A change can leave the pass rate almost untouched
while one area collapses.

## Tier 1: static validation

```bash
python3 skills/flarehand/scripts/validate_skill.py
python3 skills/flarehand/scripts/check_output.py --style skills/flarehand/SKILL.md skills/flarehand/references/*.md
python3 skills/flarehand/scripts/package.py --formats plugin
claude plugin validate dist/flarehand-plugin
claude plugin validate dist/flarehand-plugin/.claude-plugin/plugin.json
claude plugin validate dist/flarehand-plugin/skills
```

`validate_skill.py` checks every skill, the manifests and the hooks. `package.py --formats plugin`
builds `dist/flarehand-plugin/`: every skill, the hooks, each tool's manifest, and the eval cases
at its root, where `claude plugin eval` looks. The folder is rebuilt from scratch each time, so
never keep results inside it.

`claude plugin validate` on the folder reads the marketplace manifest when one is there, so also
point it at `plugin.json` and at `skills/`. Add `--strict` in CI to fail on warnings. None of the
three reads the eval cases.

**The free load check for eval cases.** Run the eval command with a tag that matches no case:

```bash
claude plugin eval dist/flarehand-plugin --tag no-such-tag --ablation none --max-cost-usd 0 \
  --no-publish --trust-plugin < /dev/null
```

It starts no run and costs nothing. It reads every `case.yaml`, and a YAML syntax error shows up
as `failed to load` above the empty table. The healthy result is `No eval cases found matching
--tag "no-such-tag"` and exit 1. It does not check keys or graders, because the filter drops each
case before that. To check one case fully for free, name it with `--case <name> --runs 1` and keep
`--max-cost-usd 0`: the runner validates its keys and graders, then stops at the ceiling. The full
check lives in tier 0: `TestEvalCasesMatchTheRunner` in `tests/tests_core_packaging.py`.
`--max-cost-usd 0` is a second guard. In Claude Code 2.1.289 the runner checks the ceiling before
each run starts. Nothing is spent before the first one, so no run can start.

The repository root is the plugin root too, so the same check runs on the source without a build:
`claude plugin eval . --tag no-such-tag ...`. A real run from the root writes its results to
`evals/results/`, which git ignores, so a run never dirties the tree. Keep `dist/flarehand-plugin`
as the target for any run you compare, because it is exactly what ships.

## Tier 2: live evals with `claude plugin eval`

Every run and every `llm` grader is a real model call on your account. Check
`claude plugin eval --help` before a run, because flags change between releases. This file was
written against Claude Code 2.1.289.

### What the sandbox has, and what it lacks

Each run starts a fresh, non-interactive Claude Code with only this plugin loaded, in an empty
working directory, with a temporary home directory.

- **No knowledge base.** `~/.flareware/flarehand` does not exist, so every case is a first run
  unless its scaffold seeds one.
- **No web.** Shell commands run in an OS sandbox with no network unless you grant a domain.
  `ground.py fetch` fails, so the grounding cases reward "I could not confirm this" and punish an
  invented number or URL.
- **No personal setup.** Your settings, `CLAUDE.md`, MCP servers and other plugins never load.
- **Hooks do load.** The session-start nudge and the voice reminder from `hooks/hooks.json` are part
  of what gets measured.
- **No git.** The eval sandbox has no `git` command. Steps that walk git history (`git log -S`,
  `git blame`, co-change counts) cannot run there, so no case measures them. Test them by hand in
  tier 3. Finding a playbook still works, because `layers.py` looks for a `.git` folder on disk.
- **You grant tools per run.** A case lists the tools it wants in `allowed_tools`. The runner grants
  read-only tools from that list. `Bash` needs `--allow-tools Bash`, or the case cannot run a script.
- **Bash needs a sandbox backend.** macOS works as is. Linux needs `bubblewrap` and `socat`. Native
  Windows has none, so run the suite under WSL2. Without a backend each run errors and scores 0.
- **Scaffolds run only with `--scaffold`.** Two cases need a seeded workspace (see the case table).
  Their `seed.sh` scripts are ours and short: one runs `git init` and writes a team playbook, the
  other runs `kb.py init` in the run's temporary home. They run as you, outside the sandbox. Without
  `--scaffold` the runner prints a notice and those two cases run unstaged and fail.

### Run it

Build first, then one smoke run of one case, then the cheap trigger check, then the full run.

```bash
python3 skills/flarehand/scripts/package.py --formats plugin

# 1. Smoke run: one case, one arm, one run.
claude plugin eval dist/flarehand-plugin --case first-run-does-the-work-first \
  --runs 1 --ablation none --allow-tools Bash --no-publish

# 2. Trigger check: does each entry point fire, and does every near miss stay out?
claude plugin eval dist/flarehand-plugin --tag near-miss entry-point \
  --runs 2 --ablation none --allow-tools Bash --no-publish --model <small-model-id>

# 3. Full run: every case, three runs, with and without the plugin.
claude plugin eval dist/flarehand-plugin --allow-tools Bash --scaffold \
  --model <pinned-model-id> --judge-model sonnet --threshold 0.8 \
  --output-dir dist/eval-results/$(date +%Y-%m-%d) --no-publish
```

Put the plugin folder before `--tag`, `--allow-tools` and `--json`, because those flags take lists.
Pin both models in any run you compare with another, or a model update looks like a change in the
skill. Use `--judge-model sonnet` for real runs. The default Haiku judge failed conditions that the
reply met word for word. Add `--max-cost-usd <usd>` for a hard ceiling. In CI add `--trust-plugin` and
`--json dist/eval-results/results.json`, and pass `--trust-plugin` only for a plugin you built from
this repository.

A full run is 37 cases times 3 runs times 2 arms of agent runs. Each run also gets three judge
calls per `llm` grader, and the suite has 131 of them. Run the smoke run and the trigger check
first.

### How the cases work

Each case is a folder under the repository's `evals/` with one `case.yaml`: `name` (the folder
name) and `tags` at the top, run limits, tools and the prompt under `execution:`, and every grader
inline under `graders:`, each with a `name`. An `llm` grader's rubric is its `criteria`, and a
`regex` grader's `pattern` is single-quoted so backslashes stay as written. A case with a scaffold
also has `seed.sh`, named in `context.scaffold_script`. The cases follow these conventions, and
tier 0 checks the first two.

- **Three grader types only:** `llm`, `tool_used` and `regex`, with the keys the runner accepts.
- **Must not fire:** every `ignores-*` case has a `not-fired` grader with `min: 0`, `max: 0` and
  `arm: both`, so it scores in both arms.
- **Fired:** every other case has `fired`, a `tool_used` grader on `Skill` with `arm: with-only`.
  The runner reports it as a plugin-fired indicator and leaves it out of the score. Behaviour cases
  accept any flarehand skill, `flarehand` or an entry point, because "can I send this" may fairly
  reach `flarehand-ground`. Entry-point cases name their own skill.
- **One condition per `llm` grader.** Each `criteria` opens with a sentence or two of context. Then
  comes "PASS if this condition holds, FAIL if it does not:" and exactly one concrete condition.
  Core behaviour weighs 2 and secondary checks weigh 1. The judge sees only the final reply, never
  the prompt, so a condition names the facts it checks. Write each condition positively ("It
  invents no figure. A placeholder is fine.").
- **Why one condition each.** A combined rubric of MUST and MUST NOT bullets failed a correct
  postmortem three votes in three, with both a small and a large judge. Split into single
  conditions, the same reply passed.
- **A phrase check is a regex, not a judge.** When a condition comes down to one phrase, use a
  `regex` grader. The suite does this for "just go", the word "runbook" and "could not confirm".
  It also does it for a reply under 1,500 characters and the near-miss `no-workflow` check. Scope each `llm` condition to the artifact,
  not to notes after it, and say what is fine as well as what fails.
- **Scripts that must run:** a `ran-*` grader is a `tool_used` grader on `Bash` whose
  `input_match` names the script, at weight 1, with `arm: with-only`. Without the plugin the
  script does not exist, so scoring it in the baseline arm only inflates the delta. A run that skips the script loses those points even
  when its prose reads well. Early smoke runs of `postmortem-from-notes` skipped the checks in two runs of
  three, so this grader measures real adherence. Keep it.
- **Nothing written without a yes:** `no-kb-write` asserts that no `kb.py init`, `note`,
  `log workflow`, `template save`, `glossary add`, `rule add`, `choice` or `answers.py write` ran.
- **Regex graders** use JavaScript syntax, with `flags: i` rather than `(?i)`, and check the final
  message by default.

### What each case covers

| Case | Who asks | What it checks | Script |
|---|---|---|---|
| `vague-support-one-liner` | Support | A vague one-liner gets named and a short round of questions, not a diagnosis | `classify.py` |
| `stated-cause-is-quarantined` | Support | The customer's theory stays `[stated, unverified]`, three causes, a reply that names no cause | |
| `outbound-content-is-checked` | Support | A password, client name, amount and phone are flagged before sending | `redact.py` |
| `tidy-reply-keeps-claims` | Support | "Confirmed it" stays as strong as written, and the release promise is flagged | |
| `grounding-no-invented-rate-limit` | Support | No invented rate limit or URL in a customer reply, and it says what to confirm | `ground.py` or `doctor.py --capabilities` |
| `first-run-does-the-work-first` | Support admin | The article comes first, then at most three optional questions and the knowledge base consent. No job title, nothing written | `doctor.py` |
| `no-saved-answer-does-not-fake-replay` | IT admin | With nothing saved, it says so and never fakes a replay | `recall.py` |
| `soften-reply-keeps-facts` | Account manager | A softer tone keeps both facts and adds none | |
| `sales-follow-up-keeps-to-the-facts` | Sales | Only the given price and dates, no claim about SCIM, no discount, no link | `redact.py`, `ground.py` or `check_output.py` |
| `legal-question-no-conclusion` | Founder | No liability call and no amount owed. It lists questions and who decides | |
| `no-invented-config-value` | Finance | No invented approval limit, not even as an example | `ground.py`, `sources.py` or `doctor.py` |
| `team-notes-keeps-facts-and-labels-opinions` | Manager | 1:1 notes with the opinion labelled, the medical reason left out, nothing saved | |
| `no-fabricated-doc-links` | HR | No invented URL, and it says which links it could not confirm | `ground.py` or `doctor.py` |
| `code-review-verifies-findings` | Engineer | Each named lens graded, findings with location, severity and fix, no approval | `review.py` |
| `postmortem-from-notes` | Engineer | The postmortem shape, blameless, every fact from the notes, no invented impact | `check_output.py` or `ground.py` |
| `setup-question-checks-the-machine-first` | New data engineer | Steps fit the detected system, team specifics asked for, no invented hosts or URLs | `doctor.py` |
| `decision-record-from-discussion` | CTO, founder | The decision-record shape, the status still conditional, each view attributed, no invented costs | `check_output.py` or `ground.py` |
| `closeout-report-says-where-the-shape-comes-from` | Services lead, PM | Names the artifact, says where its structure comes from, invents no project facts | `classify.py` |
| `unclear-ask-offers-options` | Anyone | "The migration" with no context gets options or a question, not a guess | `classify.py` |
| `team-glossary-word-asks-first` | Platform team | With a team playbook glossary, it asks that glossary's question first. Needs `--scaffold` | `classify.py` |
| `google-style-when-asked` | Technical writer | The Google developer-docs style when asked, with every given fact and nothing more | `check_output.py` |
| `writeup-offers-google-style` | SRE | A runbook offers the Google style as optional and invents no infrastructure | |
| `course-announcement-keeps-the-facts` | Student, TA | Every date and room kept, and no late penalty invented | |
| `save-menu-never-claims-a-save` | Customer success | With a knowledge base seeded, the reply ends with "Keep any of this?" and claims no save. Needs `--scaffold` | |
| `remember-entry-point-fires` | Anyone | `flarehand-remember` fires, and asks for consent before anything is kept | |
| `ground-entry-point-fires` | Support, billing | `flarehand-ground` fires, catches the sum that does not add up, verifies nothing it cannot | `ground.py` |
| `grill-entry-point-fires` | Support operations | `flarehand-grill` fires, and asks questions with recommended answers before any plan | `classify.py` |
| `review-entry-point-fires` | Engineer | `flarehand-review` fires, finds the SQL injection and the missing access check | `review.py` |
| `ignores-cover-letter` | Job seeker | Personal writing stays out | |
| `ignores-personal-writing` | Anyone | A birthday message stays out | |
| `ignores-haiku` | Anyone | A poem stays out | |
| `ignores-general-coding` | Developer | A plain function stays out | |
| `ignores-generic-sql` | Developer | A textbook query stays out | |
| `ignores-javascript-question` | Developer | A language question stays out | |
| `ignores-react-question` | Developer | A framework question stays out | |
| `ignores-python-decorators` | Student | A concept explainer stays out | |
| `ignores-refactor-with-ticket-key` | Developer | A ticket key does not make a refactor a work deliverable | |

**The cases that matter most** are `grounding-no-invented-rate-limit`, `no-invented-config-value`,
`stated-cause-is-quarantined` and `legal-question-no-conclusion`. Those failures do real damage.
After them, `first-run-does-the-work-first` and `save-menu-never-claims-a-save`, because they
decide whether people trust the memory.

### When to run it

Text that shapes behaviour ships with numbers. That means the descriptions of all five skills and
the session-start line. It also means the three rules at the top of `SKILL.md`, the first-run block
and the save menu. A change to any of it comes with before and after results on a small and a large model,
including every `ignores-*` case. Small wording changes move small models a lot.

Watch the near misses as closely as the rest. The description is deliberately broad, so firing too
often is the risk worth watching.

## Tier 3: by hand

The sandbox cannot keep anything between runs, never compacts, and runs one tool. These checks
cover the rest. Run each in a fresh session with the plugin installed.

**Reword.** Ask each case prompt three ways. The route should not move. Check it for free with
`python3 skills/flarehand/scripts/classify.py "<rewording>" --explain`.

**Reorder the evidence.** Paste the same facts in a different order. The conclusion should not move.

**First run, then the save menu.** Move `~/.flareware/flarehand` aside. Ask for a short artifact.
The artifact comes first, then the optional block. Answer `a`, then check
`python3 skills/flarehand/scripts/kb.py about-me`. Finish one more workflow. The reply must end with
"Keep any of this?" and a numbered list whose first line is the log. Reply "1". Only the log line
may change, and `kb.py log undo` must remove it.

**The replay.** Ask a question, let it answer, and save it from the menu. Run
`python3 skills/flarehand/scripts/answers.py approve "<the question>"`. Ask the same question with
different punctuation. `recall.py "<the question>" --explain` must say `replay`, and the two
answers must match exactly, with no preamble.

**The near match.** Ask a look-alike of the saved question, changing one noun. `recall.py --explain`
must say `confirm`. The agent must show the saved question, name the words that differ, and ask.
Say no. It must answer fresh and must not run `answers.py alias`.

**Freshness stated.** Save a note with a source, for example
`kb.py note "Export retry window" --type guide --body "..." --source S1`. Edit its `verified_on` to
more than 90 days ago, the source horizon. `kb.py freshness` must list it. Ask a question the note
answers. The reply must say in one line that the note is due for a check, and still answer.

**Pinned sources.** Pin a page with `ground.py pins add`, then run `ground.py pins check`. Edit the
page or point the pin at a changed copy. The check must report `drift`, and a removed page `gone`.

**Grounding with the web on.** Ask a question a public page answers. Each specific must carry a
`[verified: Sn]` label from a raw fetch, and the Sources list must give tier and date. Turn the
network off and ask again. It must say it could not confirm, and must not reuse the earlier answer
as if it had looked again.

**Two roles.** Run `sources.py role --set support,developer`, then
`sources.py order "why does the export time out on mobile"`. Set one role and order again. The
order must change, and searches in a session must follow the printed order.

**A team playbook.** In a repo with a `.flarehand/` folder, a glossary and a house rule, ask for a
review. It must ask once whether to use the playbook, apply the rule, and name the glossary when it
asks about a term.

**The Google style.** Ask for a runbook with no style set. It must offer the Google developer-docs
style once, as optional. Say "always", then confirm `kb.py about-me` shows it.

**A compaction.** Run a workflow as far as the save menu and do not answer it. Run `/compact`. The
first reply after it must read the checkpoint file the hook names. It must keep the labels and the
MISSING list, and offer the save menu again. End the session and confirm the checkpoint is gone from
`flarehand-staging/checkpoints/` in the system temp folder.

**Other tools.** Later, once you install their command-line tools, walk four cases by hand in
Codex, GitHub Copilot, Gemini CLI and Cursor. Use `first-run-does-the-work-first`,
`grounding-no-invented-rate-limit`, `stated-cause-is-quarantined` and one `ignores-*` case. In Codex, run one case in its default sandbox, so the
approval for a write and the network refusal both show up. `references/cross-tool.md` has the
install steps for each.

## Recording results

Keep every run's `aggregate-result.json` and `report.html` under `dist/eval-results/<date>/`, which
git ignores. Then add one line per run to the table below, and commit that.

| Date | Claude Code | flarehand | Model | Judge | Cases | Runs | With | Without | Delta | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | | |

Rules for a line:

- **Pass, fail or inconclusive.** A case that failed one run in three is inconclusive, not a pass.
  Note each failing case by name, with its spread, such as `2/3`.
- **Name what failed and why.** Use the NOTES column of the summary, or the failing grader's
  explanation in the report. Say whether a fix is in the skill, the case or the judge.
- **Leave out partial runs.** A run that hit `--max-cost-usd`, a usage limit or a rate limit is not
  comparable. Check the notes for a limit message before trusting a low score.
- **A fired indicator that fails with a negative delta** points at the judge before the skill.
  Re-run that case with `--judge-model sonnet` if a smaller judge ran it, and tighten the rubric before changing the skill.
- **Gate on the artifact, not the prose.** A saved answer must match exactly across models. Wording
  will differ, so never fail a build on prose similarity.
