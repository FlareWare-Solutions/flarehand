# interview - asking the user without wasting their time

**Scope.** Questions you put to the user. For building a question list they will send to someone else,
read `wf-02-elicit.md`.

## Contents

- Where this comes from
- The rule that does most of the work
- How much to ask, by stakes
- Build the decision tree
- Rounds, not a queue
- How to write a question
- When to stop
- The question you cannot ask

## Where this comes from

The way this file asks questions takes its inspiration from Matt Pocock's `grill-me` and grilling skills, MIT
licensed, at https://github.com/mattpocock/skills. Three ideas come from there. Treat the open
decisions as a tree. Ask every question that is ready in one round. Give your recommended answer with
each one. The wording and the rules below are this skill's own.

## The rule that does most of the work

**Finding facts is your job. Decisions are theirs.**

Before any question, ask yourself whether a tool could answer it. Look first, in this order:

1. their knowledge base, with `kb.py search`
2. the files in front of you, and the repository they work in
3. git history, with `git log`, `git blame` and `git show`
4. the sources `sources.py order` names, including any MCP server they connected
5. `doctor.py`, for anything about the machine

If any of them can answer it, go and look. Asking someone for something you could have found is the
fastest way to feel like a form.

What is genuinely theirs:

- what they are trying to achieve
- which trade-off they prefer
- what the constraints are
- what "good" looks like
- anything only they saw

## How much to ask, by stakes

`classify.py` returns a ceremony level. That is the one source of truth, so two sessions never disagree
about how much to ask. One setting moves it a little. At `adaptation: yours`, a `standard` request may
skip one optional question. A `full` request never skips one.

| Ceremony | Example | How much |
|---|---|---|
| `light` | A lookup, a definition, a setup step, saving a note | Ask nothing unless you are blocked |
| `standard` | A draft or plan for themselves or their team | At most three questions, each with a recommended answer |
| `full` | Anything a customer, an executive, engineering or an auditor acts on, or any risk flag | At most four questions a round, round after round, until the frontier is empty |

**A round has a cap, and the cap counts everything.** Template `learn` questions count toward it. The
Google style offer does not: it is one optional line after the questions. When there are more candidates than the cap, keep the ones whose answer
would change the artifact most. The rest take their recommended answer, which you state in one line
under the questions, or wait for the next round.

The ceremony sets how much to ask, not whether to check facts. A light task still gets grounded and cited.

**When they already gave you the facts, draft first.** Notes to write up, a draft to tidy, or steps to
turn into an article need no interview before the work. Write it, put anything missing on the MISSING
list, and ask after. A review found the skill asking three questions before writing 1:1 notes that
held every fact. That scored worse than no skill at all. Interview first only at `full` ceremony, or
when a missing fact would change the whole shape.

**A template's `learn` questions follow one rule, in `SKILL.md` step 6.** Get the template before you
ask anything. If its `source` is `shipped`, its `learn` questions go in the same round as your intake
questions, not a round of their own. If its `source` is `yours`, the person already saved their
version, so skip them. They find out how this person's team already does the work, and one round is
enough.

## Build the decision tree

Before you write a single question, list the decisions the work depends on. Then see which ones depend
on others.

- **A root** is a decision nothing else settles. Who reads it, what it is for, what is in scope.
- **A branch** only makes sense once its parent is settled. "Which rollback step?" waits on "is there a
  rollback at all?".
- **A leaf** changes a detail, not the shape. Leaves are the first questions to drop at `standard`.

The **frontier** is every open decision whose parents are all settled. That is what one round asks.

Do this in your head, not in the reply. The person sees numbered questions, not a diagram.

## Rounds, not a queue

Ask the whole frontier in one message, numbered. Then wait.

A question whose premise is still unsettled belongs in the next round. Asking it now means guessing at
the answer to the earlier one.

When the answers come back, work out what is now unblocked and ask that. Repeat until nothing is left.

This is much cheaper for the user than one question at a time. Numbered questions let them answer in
shorthand: "1 yes, 2 the cloud one, 3 skip".

## How to write a question

Every question carries three things.

1. **A real question**, not a topic label. "Which environment?" not "Environment".
2. **A recommended answer**, marked clearly. This turns an interview into a quick yes or no. Base it on
   what you found while looking, and say where it came from.
3. **One line on why it matters**, so they can tell which ones to think about.

```markdown
**1. Which environment did this happen in?**
   Recommended: production, since the ticket names the production URL.
   Why it matters: staging runs a newer build, and that changes the answer.
```

Always give them a way out: *"Or say 'just go' and I will take every recommended answer."* "Just go"
is always accepted, at every ceremony level. Then state those assumptions in the output, each one
labelled `[ASSUMPTION, verify]`.

## When to stop

Stop when there is nothing left whose answer would change what you produce.

Not at a fixed number. Some requests need two questions and some need fifteen. A cap either cuts off a
hard problem or feels arbitrary on an easy one.

A useful test: can you now ask about edge cases without having to explain the basics? If yes, you have
enough.

If they say "wrap up", "just go" or "stop asking", stop immediately. State your assumptions and
produce the work. Natural language is the control, not a counter.

## The question you cannot ask

Some questions cannot be settled by talking. "How should this feel?" or "one long page or three short
ones?" Sessions balloon when you try.

Recognise these and switch. Produce a short version and a long version. Draft two openings. Show, then
ask which is closer. Ten seconds of looking beats ten minutes of describing.
