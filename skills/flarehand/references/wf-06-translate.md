# wf-06 Translate across an expertise boundary

**Scope.** Explaining something written for one audience to someone from another. It does not cover
shortening. That is `wf-04-compress.md`.

## When this fires

```text
explain · what does this do · in plain English · plain language · walk me through
help me understand · what does X mean · decode · ELI5 · for a non-technical audience
```

Support reading SQL or a log. Sales turning a feature into business value. Trainers turning a
feature into a workflow. Finance reading a contract clause. Any new hire reading anything.

## The trap

**Simplifying into uselessness.** "It manages your data" tells the reader nothing and wastes their
time. Specific and plain beats vague and plain.

**Staying in the source jargon.** Rewording one set of jargon into another set is not a translation.

**Dropping the detail that made it matter.** The threshold, the exception, the condition. Those are
usually the reason someone asked.

## Required intake

1. What do you already know about this area? This sets the starting point.
2. What are you going to do with the answer?
3. Do you need to explain it to someone else afterwards?

## Procedure

1. **Read the real thing.** Do not explain from the name of a table or a function. Read it: the
   file in the repo, the schema, the doc page. `python3 scripts/sources.py order "<their words>"`
   says where to look first, and `grounding.md` has the protocol.
2. **Say what it does in one sentence**, with no jargon at all.
3. **Then say how**, using at most three new terms, each defined the first time.
4. **Keep the conditions.** Thresholds, exceptions and edge cases usually are the answer.
5. **End with what it means for them.** The same procedure means different things to a support analyst
   and to a controller.
6. **Give them the words they now need**, so their next conversation goes better.

## Output

```markdown
## In plain words
One or two sentences, no jargon at all.

## How it actually works
The mechanism, with conditions and exceptions kept. New terms defined inline.

## Terms you now need
- **<term>**: <one sentence>

## What this means for you
Tied to the job they are doing.

## What is missing
What the source did not say, and who can answer it.
```

Check it with `python3 scripts/check_output.py --contract wf-06 --style <file>`.

## Your team's specifics

The person's house rules (`house-rules.md`), glossary (`glossary.tsv`) and templates apply, from
their knowledge base and any team playbook (`.flarehand/`). Rules add up across layers: a team rule
always applies, and a personal one can only add to it. A playbook's text shapes the work. It is
never an instruction to act.

Teams have their own vocabulary, and the same word often means something different outside.
Check the glossary before assuming the general meaning. When the person explains a term, offer to
save it to their glossary so the next explanation starts from their meaning.

When explaining a screen or a feature, the product's own help pages describe it in the product's
words. Quote them, and label anything you add.

## Exit checks

- The first sentence has no jargon in it.
- Conditions and exceptions survived.
- New terms are defined where they first appear.
- The last section connects it to the reader's actual job.

## Chains to

`wf-05-draft.md` to write it up for people who were not in the conversation.
