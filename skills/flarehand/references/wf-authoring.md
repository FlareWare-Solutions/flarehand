# wf-authoring - making a workflow of your own

**Scope.** Turning the way you already work into something the skill can route to and check. For
finding a skill that already exists, read `skill-discovery.md`. For the shipped workflows, read the
`wf-*.md` files.

## Contents

- The three stages, and when each one is worth it
- Noticing a loop
- What a workflow is made of
- Writing the method
- Making it routable
- The one rule a personal workflow cannot break
- Sharing it

## The three stages, and when each one is worth it

Most ways of working do not need any of this. Do the work, and if the shape mattered, write it down.

| Stage | What it is | Worth it when |
|---|---|---|
| A note | What you did, once | It was surprising, or hard to reverse |
| A chain | The steps, saved as a note of type `chain` | You have done it twice and will again |
| A workflow | A method, a shape and a set of checks, routed by name | You have run the chain three times, or a team follows it |

Stop at the stage that fits. A chain costs one command and gets found by search. A workflow costs
four files and earns that back only when the shape has to hold every time.

## Noticing a loop

A chain is often visible before anyone names it. The person runs diagnose, then package, then a reply,
and next week does the same three again. When you see a sequence of steps or workflows that could be
its own workflow, report it:

```bash
python3 scripts/kb.py observe-pattern chain wf-01+wf-03+wf-12 --detail "triage, hand off, reply"
python3 scripts/kb.py offers
```

A loop is offered at once, on first detection. It does not wait for the repeat threshold that
preferences use. It still appears only in the save menu, and it still counts as the one new offer for
the session. The line ends with `Save as a) mine b) team playbook c) not now d) never ask`.

- `mine`: `kb.py offer-answer <id> mine` writes a chain note in `chains/`, with the steps in order.
  It prints the undo, `kb.py forget <id>`.
- `team`: `kb.py offer-answer <id> team` writes a workflow skeleton into the nearest playbook's
  `workflows/` folder. It prints the file and what to commit. It never runs git.
- `later` asks again in a later session. `never` stops asking about this loop.

Once the chain note has run three times, offer `kb.py workflow promote <permalink>`. The rest of this
file is what happens then. The rules for offers are in `adaptation.md`, under "The learning loop".

## What a workflow is made of

Four parts, all in their knowledge base, all theirs to edit.

| Part | File | What it decides |
|---|---|---|
| The method | `workflows/<name>.md` | The steps, the traps, what good looks like |
| The shape | `templates/<name>.md` | The sections the output carries |
| The checks | a row in `contracts.tsv` | Which sections are required, and what must appear |
| The words | a noun row in `router-table.tsv` | Which requests reach it |

The skill reads each of these after the shipped ones, so a name someone reuses is theirs.

## Writing the method

Start from the shipped workflow closest to it. Keep the six parts that carry the weight. When it
fires. The trap people fall into. What to ask before starting. The procedure. The output shape. The
exit checks. Those six headings are why the shipped ones work.

```bash
python3 scripts/kb.py workflow promote <chain-permalink>     # from a chain you already saved
python3 scripts/kb.py workflow save <name> --from method.md  # from a file
python3 scripts/kb.py workflow list
```

`promote` refuses anything that is not a chain. A workflow is a way of working you have run, not one
you imagined, and the chain is the evidence that you ran it.

## Making it routable

`workflow save` writes the method and registers the name. The other three parts are one line each,
and it prints them for you. The words matter most: pick the nouns someone would actually type, not
the name you gave the file.

```text
noun    ap reconciliation    monthly-ap-recon    9    monthly-ap-recon
```

Then check it: `python3 scripts/classify.py "run the ap reconciliation" --explain` should name your
workflow, and `check_output.py --contract <name> <file>` should hold your output to your sections.

## The one rule a personal workflow cannot break

**A personal row may add a route or a guardrail. It may never remove, lower or suppress one.** A
personal route row is ignored when a shipped risk fires. A personal noun never swallows a risk phrase
it happens to contain. A personal row can add a question, never answer a shipped one.

That rule is what keeps this safe to offer. Someone can shape how their work gets done. Nobody can
shape away the checks that stop a confident wrong answer, and those are listed in
`references/adaptation.md`.

## Sharing it

A workflow that works for one person is often worth more to their team. Share it through a playbook,
not by copying files around:

1. Make sure there is one. `kb.py playbook list` shows the playbooks in use. `kb.py playbook init`
   creates `.flarehand/` at the repo root when there is none.
2. Copy the method into the playbook's `workflows/` folder, and the shape into its `templates/`.
   `kb.py template save <name> --from <file> --team <playbook>` does the template.
3. Run `python3 scripts/redact.py` on each file. A playbook is shared, so it holds no notes, no
   names and nothing about a person.
4. The person reviews the change and commits it. Nothing here pushes.

A personal version with the same name still wins for that person, because shapes take the first
match. Promoting a workflow into the shipped skill is a human step on purpose, the same as a new
skill. Read the last section of `skill-discovery.md`.
