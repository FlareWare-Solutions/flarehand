# Evals

This page explains how flarehand is tested, what the latest results show, and how to run the tests yourself.

## Four tiers

| Tier | What it proves | Cost |
|---|---|---|
| 0. Unit tests | The scripts do what they say: routing, grounding checks, the knowledge base, layers, templates, packaging | Free |
| 1. Static validation | Every skill, manifest and eval case loads | Free |
| 2. Live evals | The skill fires when it should, stays out when it should, and behaves | Model time |
| 3. By hand | Memory across sessions, compaction, and other tools | Your time |

The first two run on every change. Live evals run before a release, and after any change to text that shapes behaviour. That means the five skill descriptions, the session-start line, the rules at the top of `SKILL.md`, the first-run block and the save menu.

## Tier 0: unit tests

Over 800 tests, standard library only, no model. A full run took about four minutes on a recent laptop.

```bash
HOME=$(mktemp -d) python3 tests/test_scripts.py
```

The temporary `HOME` proves the suite passes on a machine with no knowledge base, which is what CI and every new user have. To run one module while you work, run `python3 tests/tests_core_kb.py -v` from the repository root.

The routing tests include a table of real prompts, including every prompt a review ever found misrouted. A new routing pattern can steal a request from another workflow, and those tests are how you find out.

## Tier 1: static validation

```bash
python3 skills/flarehand/scripts/validate_skill.py
python3 skills/flarehand/scripts/check_output.py --style skills/flarehand/SKILL.md skills/flarehand/references/*.md
python3 skills/flarehand/scripts/package.py --formats plugin
claude plugin validate dist/flarehand-plugin
```

`validate_skill.py` checks that every skill, the manifests and the hooks will load in every tool. It also enforces three packaging rules: no PowerShell script files, no binaries, and no plugin folders inside a skill. The style check holds the skill to its own writing rules.

## Tier 2: live evals

Live evals run the plugin against a real model with `claude plugin eval`. Each case runs in a fresh, non-interactive Claude Code with only this plugin loaded, an empty working folder and a temporary home folder. So there is no knowledge base, no web, no git, and none of your personal settings or MCP servers. Hooks do load, so the session-start line and the voice reminder are part of what is measured.

**Every case runs twice: with the plugin and without it.** The difference between the two arms is the lift the plugin gives.

### The cases

There are 37 cases. Each is a folder under the repository's `evals/`. They cover:

- **Behaviour** across roles: support, sales, finance, HR, legal, engineering, management, product, writers and students. For example, a postmortem from notes, a decision record from a discussion, a code review, a customer reply that keeps the facts.
- **Grounding**: no invented rate limit, config value, URL or legal conclusion.
- **Memory**: the first run does the work first, the save menu never claims a save, and nothing fakes a replay.
- **Entry points**: each of the four fires on its own trigger words.
- **Near misses**: nine `ignores-*` cases where flarehand must stay out. Examples are a cover letter, a haiku, a React question and a refactor with a ticket key.

The cases that matter most are the ones whose failure does real damage: `grounding-no-invented-rate-limit`, `no-invented-config-value`, `stated-cause-is-quarantined` and `legal-question-no-conclusion`.

### How grading works

Three grader types only:

| Type | Checks | Used for |
|---|---|---|
| `llm` | One condition, judged by a model that sees only the final reply | Behaviour, such as "it keeps these timeline facts" |
| `regex` | A phrase is present or absent | "Just go", "could not confirm", blame words in a postmortem |
| `tool_used` | A tool ran, optionally with a matching input | That a script such as `check.py` or `redact.py` really ran |

Rules the suite follows:

- **One condition per `llm` grader.** Each grader's `criteria` in `case.yaml` gives a sentence of context, then "PASS if this condition holds, FAIL if it does not:" and exactly one condition. A combined rubric of must and must-not bullets failed a correct postmortem three times in three, with both a small and a large judge. Split into single conditions, the same reply passed.
- **A Sonnet judge.** Real runs use `--judge-model sonnet`. The default Haiku judge failed conditions the reply met word for word.
- **Weights.** Core behaviour weighs 2, secondary checks weigh 1.
- **Scripts that must run are graded with the plugin only.** Without the plugin the script does not exist, so scoring it in the baseline arm would only inflate the lift. A run that skips the script loses those points even when its prose reads well.
- **"Fired" is reported, not scored.** Every behaviour case has a `fired` grader that records whether a flarehand skill ran, and leaves it out of the score. Every `ignores-*` case has a `not-fired` grader that scores in both arms.
- **Nothing written without a yes** is checked by asserting that no saving command ran.

The suite has 131 `llm` graders. Each gets three judge calls per run.

## Latest results

The 1.0.0 confirmation run was one full run of the whole suite on a single commit:

- **When:** 2026-10-04, flarehand 1.0.0 at commit `8802a56`, Claude Code 2.1.289.
- **Models:** agent `claude-opus-5-5`, judge Sonnet (`--judge-model sonnet`).
- **Shape:** 37 cases, 3 runs each with the plugin and 3 without, 222 agent runs in about 29 minutes.

| | With flarehand | Without |
|---|---|---|
| Mean score, all 37 cases | 0.97 | 0.83 |
| Mean score, the 28 work cases | 0.96 | 0.78 |
| Cases at 0.80 or above | 37 of 37 | |
| Cases at 1.00 | 25 of 37 | |
| Fired on a near-miss request | 0 of 27 runs | |

What stands out:

| Pattern | Cases |
|---|---|
| Biggest lift | `legal-question-no-conclusion` 1.00 against 0.44. `first-run-does-the-work-first` 0.98 against 0.48. `grill-entry-point-fires` 1.00 against 0.52. `writeup-offers-google-style` 0.92 against 0.46. `no-fabricated-doc-links` 1.00 against 0.56. `save-menu-never-claims-a-save` 1.00 against 0.58. `closeout-report-says-where-the-shape-comes-from` 0.90 against 0.52. `soften-reply-keeps-facts` 0.89 against 0.56. |
| No difference | The nine near-miss cases score 1.00 in both arms, which is the goal: the plugin stays out. Several grounding cases also score 1.00 without the plugin on this model. |
| Lower with the plugin | `decision-record-from-discussion`: 0.91 with, 0.94 without. |

**Known gaps, tracked for 1.0.1.**

- `outbound-content-is-checked`: in all three runs, the tidied customer reply turned "found the problem" into "found the cause", and "confirmed it" into "confirmed the issue". That strengthens a fact, which flarehand promises not to do.
- `decision-record-from-discussion`: the record names its gaps in MISSING, not in an "open items" section, and the judge failed it on shape in all three runs.
- `code-review-verifies-findings`: findings carry a severity by group, such as "must fix", not one per finding. It scores 0.92 in both arms.

**Read it honestly.** The cases are written by the authors, and a model does the judging. A strong model already avoids many inventions on its own. Much of the lift comes from what a model does not do unprompted. That means the first-run flow, the save menu and quarantining a stated cause. It also means keeping a legal question to the source text, and running the checks.

## Run the evals yourself

Commands run from the repository root. Every run and every `llm` grader is a real model call on your account. Check `claude plugin eval --help` first, because flags change between releases.

```bash
# Build the plugin folder the eval runner targets.
python3 skills/flarehand/scripts/package.py --formats plugin

# Free: check every case loads. It starts no run and costs nothing.
claude plugin eval dist/flarehand-plugin --tag no-such-tag --ablation none --max-cost-usd 0 \
  --no-publish --trust-plugin < /dev/null

# 1. Smoke run: one case, one arm, one run.
claude plugin eval dist/flarehand-plugin --case first-run-does-the-work-first \
  --runs 1 --ablation none --allow-tools Bash --no-publish

# 2. Trigger check: does each entry point fire, and does every near miss stay out?
claude plugin eval dist/flarehand-plugin --tag near-miss entry-point \
  --runs 2 --ablation none --allow-tools Bash --no-publish --model SMALL_MODEL_ID

# 3. Full run: every case, three runs, with and without the plugin.
claude plugin eval dist/flarehand-plugin --allow-tools Bash --scaffold \
  --model PINNED_MODEL_ID --judge-model sonnet --threshold 0.8 \
  --output-dir dist/eval-results/RUN_DATE --no-publish
```

Replace the following:

- `SMALL_MODEL_ID` and `PINNED_MODEL_ID`: the model ids to test. Pin both models in any run you compare with another, or a model update looks like a change in the skill.
- `RUN_DATE`: the date of the run, as YYYY-MM-DD.

Things to know:

- **Put the plugin folder first**, before `--tag`, `--allow-tools` and `--json`, because those flags take lists.
- **`Bash` must be granted** with `--allow-tools Bash`, or no case can run a script.
- **Bash needs a sandbox backend.** macOS works as it is. Linux needs `bubblewrap` and `socat`. On Windows, run the suite under WSL2.
- **Two cases need `--scaffold`**: `team-glossary-word-asks-first` and `save-menu-never-claims-a-save`. Their short `seed.sh` scripts run `git init` with a team playbook, or `kb.py init` in the run's temporary home. They run as you, outside the sandbox.
- **Set a ceiling** with `--max-cost-usd`. A full run is 37 cases, times 3 runs, times 2 arms. Run the smoke run and the trigger check first.
- **Pass `--trust-plugin` only** for a plugin you built from this repository.

### Recording results

Keep each run's `aggregate-result.json` and `report.html` under `dist/eval-results/<date>/`, which git ignores. Add one line per run to the table in `evals/consistency.md`. A case that failed one run in three is inconclusive, not a pass. Leave out a run that hit a cost, usage or rate limit, because it is not comparable.

## Tier 3: by hand

The eval sandbox cannot keep anything between runs, never compacts, and runs one tool. So some checks are done by hand, each in a fresh session with the plugin installed. The full list is in `evals/consistency.md`. Among them:

- **Reword** a case prompt three ways. The route should not move. `classify.py "<rewording>" --explain` checks this for free.
- **First run, then the save menu.** Move the knowledge base aside, ask for a short artifact, and answer `a`. Check that only the lines you pick are saved, and that `kb.py log undo` removes the log line.
- **The replay.** Save and approve an answer, then ask again with different punctuation. The two answers must match exactly.
- **The near match.** Change one noun. `recall.py` must say `confirm`, and the agent must ask, not replay.
- **A compaction.** Stop at the save menu, run `/compact`, and check the first reply after it reads the checkpoint and offers the menu again.
- **Other tools.** Walk four cases by hand in Codex, Copilot, Gemini CLI and Cursor.

Next: [Architecture](architecture.md)
