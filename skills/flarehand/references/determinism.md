# determinism - asking again and getting the same answer

**Scope.** What stays the same between answers, what cannot, and how saved answers work. For
citing sources, read `evidence.md`. For the knowledge base itself, read `memory.md`.

## Contents

- What is impossible, stated plainly
- What stays the same, and for whom
- The saved answers, which do most of the work
- Reading a verdict
- Why a near match never replays on its own
- The other mechanisms
- What breaks it

## What is impossible, stated plainly

A hosted language model cannot be made to produce identical text twice. This is measured, not
theoretical. Thinking Machines Lab measured it in "Defeating Nondeterminism in LLM Inference",
September 2025: one model at temperature zero, a thousand runs, eighty different completions. The
serving batch size changes with how many other people use the system, and the maths is not batch
invariant. Other users are not an input you control.

Add to that: models change under the same name, and every tool injects its own context. So promising
identical wording from a fresh generation is a promise nobody can keep. Do not make it.

## What stays the same, and for whom

**The same person asking again gets the same answer.** Their saved answers live in their own knowledge
base. A confirmed repeat is a file read, not a new generation, so the words match exactly in any
session or AI tool on that machine.

**Two different people get the same method, not always the same sources.** Nobody shares saved answers.
Each person's knowledge base is private. What two people share is the skill itself, and their team's
playbook if they have one. That covers the router, the templates, the output contracts, the house
rules and the pinned sources. The source order still follows each person's role and usage. So two people can look in
different places and cite different sources. Cite the source with every fact, so the other person can
check it. Their role, their team's templates and their preferences then decide the shape.

That is intended. A controller and a developer asking about the same posting rule need the same rule,
explained two different ways.

**The same request runs the same workflow when the route is clear.** The routing table decides when
one route wins by a clear margin. When two routes score close, the skill names both and the person
picks. When nothing fits, it says so and offers the jobs that do.

Say this plainly when someone asks. Overselling it is how people stop trusting it.

## The saved answers, which do most of the work

```bash
python3 scripts/recall.py "<their words>" --explain
```

An answer replays word for word only when the question matches **a wording the person already
confirmed** asks the same thing. The match ignores only case, punctuation and spelling variants, so
"How do I set up the CLI?" and "how do i setup the cli." are the same wording. Nothing else collapses.

Saving, confirming and approving are three separate steps, and each waits for a yes:

```bash
python3 scripts/answers.py write "<question>" --source "<ids>" --body-file draft.md
python3 scripts/answers.py alias "<another wording>" --to "<the saved question>"
python3 scripts/answers.py approve "<question>"
```

An answer with no sources is refused. Without sources nobody can tell whether it is still true. An
answer that cites the skill's own reference files is refused too, because those are guidance, not
evidence. An answer that holds a password, key, token or connection string is refused, and so is a
snapshot it cites that holds one. Clean the text with `redact.py --apply` first.

**Replacing an answer.** Run `answers.py write` again on the same question. It overwrites the old
file, keeps its confirmed wordings, and makes it a draft again, so approve it once it is checked. A
wording that is only an alias of a different saved question is a collision, and write refuses it.
Pass `--replace` when overwriting that answer is what you mean.

## Reading a verdict

**replay.** Print the saved answer word for word. Do not reword it, do not add a preamble, do not
improve it. If it is wrong, run `answers.py invalidate` with a reason and write a new one.

**recheck.** Saved, but unapproved, not checked for thirty days, or edited by hand. Re-read each source
it cites, save what it says now, and compare:

```bash
python3 scripts/evidence.py compare <snapshot> --file what-it-says-now.txt
```

Identical for every source means nothing moved. Run `answers.py verified "<question>"`, which resets the
thirty days without touching the answer, then replay it. A changed source prints the difference. Show
it, and write a new answer with `answers.py write` on the same question, which replaces the old one.
The comparison is exact, so it is the same call whoever runs it.

**stale.** Someone marked it out of date and left a reason. Answer again, and save the replacement with
`answers.py write` on the same question.

**confirm.** A saved question looks similar but is not the same wording. Show the saved question and
the words that differ, then ask. On a yes, record the new wording with `answers.py alias` and replay. On
a no, answer it fresh.

**new.** Nothing saved. Run the workflow.

## Why a near match never replays on its own

The first version of this cache stripped filler words and hashed what was left. Similar questions then
shared a key. "Set up the CLI in Claude Code" and "set up the CLI in Claude Desktop" collapsed together.
The skill then replayed the wrong answer for the desktop app, with full confidence.

No word list fixes that. Strip too little and real repeats miss. Strip too much and different questions
merge. So the rule is structural: an exact confirmed wording replays, and anything merely similar is
shown to a person. The differing words are listed, because they usually decide the answer: *desktop*
against *code*, *uninstall* against *set up*, *staging* against *production*.

A missed repeat costs one extra answer. A false replay costs a wrong answer delivered with confidence.
The design always picks the first.

## The other mechanisms

**Tables instead of recall.** Routing, source tiers, style rules and redaction patterns all live in
`assets/*.tsv`. A lookup returns the same row forever. `sources.py order` gives the same order for the
same question, folder, roles, pins and usage.

**Pinned sources, with drift checks.** A recurring question names its source and the quote that source
must still hold. `ground.py pins check` re-fetches each one and reports `ok`, `drift` or `gone`. The
check date lives in the knowledge base, never in the skill.

**Citations.** Once the evidence is fixed, the only freedom left is wording.

**Checks a machine can run.** "The answer is good" is a judgment. `ground.py verify`, `ground.py lint`
and `check_output.py` passing are not. The quote is in the snapshot or it is not. Its numbers match
the claim or they do not.

**Content hashes.** Every saved answer and every kept snapshot records a hash of itself. `verify` on
either script reports anything edited by hand. Only `write` and `approve` record an answer's hash.
`alias`, `invalidate` and `verified` refuse a hand-edited answer until you approve it again, so an
unreviewed edit never replays.

## What breaks it

- Rewriting a replayed answer because you think you can phrase it better. This is the main one.
- Replaying on a near match without asking.
- Saving an answer with sources you did not actually read.
- Looking for a source from scratch when a pinned one exists.
- Approving an answer nobody has checked.
- Letting a saved answer live past a patch that changed the behaviour it describes.
