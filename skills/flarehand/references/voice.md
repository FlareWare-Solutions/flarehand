# voice - how this skill writes

**Scope.** The writing rules for every word the skill produces. That means answers, the questions it
asks, notes, log entries, templates, the README, and these reference files. It does not cover what to
say or which workflow to run. For that, read `router.md` and the `wf-*.md` files.

The goal is simple. Anyone on the team should be able to read the output once and know what to do. A
support analyst, a controller, a trainer and a developer should all get the same clarity from the same
page.

## Contents

- Profiles: plain is the default
- The nine rules
- Before and after
- Formatting habits that help
- Habits that stop a misreading
- Words to avoid
- How to check
- A stricter style for documents
- What the checker cannot see

---

## Profiles: plain is the default

This file is the **plain** profile. **It is the default.** Every rule below applies in full unless the
person picked another profile. They pick one at first run and can change it any time with
`kb.py config --style plain|google|none`.

| Profile | What it means |
|---|---|
| `plain` | The default. Everything in this file: the nine rules, the habits and the word list. |
| `google` | Everything in `plain`, plus the Google developer-docs rules for documents. Read `voice-google.md`. It adds rules and never removes one. |
| `none` | No house voice. The checker's style rules are off, so write the way the person or their team writes. The rules about facts still hold: never drop one, never invent one, label every claim. |

Picking a profile changes how the words sound. It never changes what gets checked for truth.

A team can add writing rules in its `house-rules.md`, under `## Writing`. Those add to the profile.
A personal setting can add a rule but never remove a team one.

**The em-dash gate is opt-in.** In `plain`, no em dashes is a rule, and the checker fails a file that
has one. The extra gate that holds a chat reply with an em dash is off until the person turns it on
with `kb.py config --voice-gate on`. See "How to check" below.

---

## The nine rules

1. **One idea per sentence.** Aim for 15 to 20 words. Stop at 25.
2. **Plain words.** Say `use` not `utilize`. Say `start` not `commence`. Say `before` not `prior to`.
3. **No em dashes.** Use a period, a comma, a colon or brackets instead. Keep numbers, warnings and
   required steps out of brackets, because many readers skip them.
4. **Active voice.** Say who does the thing.
5. **Talk to the reader as "you".**
6. **Explain jargon the first time it appears.** Every team has a lot of it.
7. **No filler openers.** The first sentence carries real content.
8. **Use headings, short lists and tables.** Break up any paragraph over five lines.
9. **Keep every fact, number, name and step.** Simplify the sentence, never drop the detail.

Rule 9 is the one that matters most. Shorter is not the goal. Easy to follow is the goal. If a rule
would cost the reader a fact, keep the fact and rewrite the sentence around it.

**These rules and the word lists are written for English.** `assets/style-words.tsv` and the checker's
passive-voice and filler patterns only know English words. When someone asks for output in another
language, keep rules 6 to 9 as they are. Apply rule 1 loosely, because sentence length works
differently in French, German or Spanish. Do not run the checker on that text and report its hits as
errors.

---

## Before and after

Wordy, passive, and hiding the point:

```text
It is important to note that in order to facilitate the escalation process, the debug log
should be obtained by the analyst prior to the ticket being submitted, as this is considered
best practice and will minimize subsequent back-and-forth with the engineering team.
```

Same facts, readable:

```text
Capture the debug log before you file the ticket. Engineering asks for it first, so sending it
up front saves a round trip.
```

Nothing was lost. The log, the timing, the reason and the audience are all still there.

Another one. Vague and corporate:

```text
We will leverage a comprehensive, robust methodology to holistically address the various
issues that have been identified going forward.
```

Say what actually happens:

```text
Here is the plan. We will fix the three issues in the list below, starting with the posting
error, because it blocks month end.
```

---

## Formatting habits that help

- Lead with the answer, then explain it. Busy readers stop after two lines.
- Put numbers, dates, paths and names in the sentence, not in a footnote.
- Use a table when you are comparing more than two things.
- Use a numbered list for steps someone will follow in order.
- Use a bulleted list for things with no order.
- Bold the one phrase a skimmer must not miss. One per section, no more.
- Keep code, paths and commands in backticks so they stand out and survive copying.
- Bold an on-screen label exactly as the product shows it, such as **Post**. A label is a name, not
  emphasis, so it does not count against the one bold phrase.

---

## Habits that stop a misreading

These came from a review of the Google developer documentation style guide. Each one prevents a real
mistake, not a matter of taste, so they apply to everything, chat replies included.

- **Dates.** Write the month as a word, or use YYYY-MM-DD. `04/05/26` is April in the US and May in
  much of the world. The checker fails a numeric date.
- **Money.** When a symbol is shared, write the currency out. When $ could be US or Canadian dollars,
  write US$ or CA$.
- **Times.** A cutover, a maintenance window or a go-live names its time zone in full.
- **Instructions.** Put the goal or the condition first: "To reopen the period, run..." One action per
  step, and name the screen before the action.
- **Pronouns.** Every "it" points at one thing. Follow "this" with a noun: "this batch". Use "they" for
  a person whose pronouns you do not know.
- **Claims.** No best, fastest, always, never or guaranteed unless a source says so. Never promise a
  release, a fix or a date that no source confirms.
- **Names.** One name for one thing, all the way through.
- **Negatives.** No double negatives such as "not uncommon". Say what is true.
- **Commands.** A command someone will paste runs as pasted. Use a placeholder in capitals, such as
  `ENV_NAME`, never angle brackets, and explain it after the block.
- **Examples.** Invented data only: example.com addresses, 555-0100 phone numbers and an invented
  company name. `privacy.md` has the full list.

---

## Words to avoid

The full list lives in `assets/style-words.tsv`, with a plain replacement for each entry. It has two
levels. An `error` is filler or a pompous word with an obvious plain twin. A `warn` is a softer
suggestion that is sometimes fine in technical writing.

You do not need to memorise the list. Run the checker.

---

## How to check

```bash
python3 scripts/check_output.py --style path/to/file.md
python3 scripts/check_output.py --style --strict path/to/file.md   # warnings count as errors too
python3 scripts/check_output.py --style --json path/to/file.md     # machine readable
python3 scripts/check_output.py --style - < reply.txt              # a reply that is not a file
```

It reports a file, line and column for every hit. It exits 0 when clean and 1 when it finds an error.

The checker skips YAML frontmatter, fenced code blocks, indented code, inline code, link targets, URLs
and HTML tags. So sample output, commands and quoted bad writing never trip it. That is why the two
examples above sit inside code fences.

**Run it on anything you write into a file, and on any reply longer than a few lines.** Pipe the reply
in with `-`. Taste drifts between models and between people. A word list and a sentence counter do not.
A 2026-09 review found every Sonnet reply still had em dashes when nothing checked them. In Claude Code,
`scripts/voice_gate.py` adds a one-line house-voice reminder before each turn, once this skill ran. A
stricter gate holds a reply with an em dash and asks for a rewrite. **It is opt-in and off by default,**
because the person sees the reply twice. `kb.py config --voice-gate on` turns it on, and
`kb.py config --voice-gate off` turns it off again. To see what it would do, pipe
the hook input in: `python3 scripts/voice_gate.py < stop-event.json`.

---

## A stricter style for documents

For a knowledge article, a runbook, release notes or another document people will reuse, a person can
opt in to the Google developer-docs profile. It adds rules on top of these nine and never removes one. Read
`voice-google.md`, and check with `--profile google`.

---

## What the checker cannot see

It counts words and matches strings. It has no idea whether the writing is any good. These stay your
job:

- Did you lead with the answer?
- Would a new hire understand it without asking a follow-up question?
- Is every claim labelled and sourced? See `evidence.md`.
- Did simplifying quietly drop a number, a name or a step? That is rule 9, and it is the failure that
  costs the reader most.
