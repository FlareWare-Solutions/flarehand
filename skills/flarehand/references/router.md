# router - working out what the user actually wants

**Scope.** How a request becomes a route. It covers the signals, what each route means, how much
ceremony to use, and what to do when the signal is weak. It does not cover running a workflow. Each
`wf-*.md` does that.

## Contents

- Route on the work, not the job title
- Running the classifier
- The routes
- Ceremony, which decides how much to ask
- The signals it reads
- Words with two meanings
- Risk flags
- When nothing matches
- Changing the router

## Route on the work, not the job title

The instinct is to ask "what is your role?" and branch on the answer. Do not route that way.

**People do not classify themselves usefully.** A senior analyst might sit in support, finance or
product. A solution architect writing a training outline is doing a trainer's job that day.

**The work decides the output, not the job.** A support engineer writing a root cause and a DevOps
engineer writing a postmortem need the same artifact with different nouns.

Role still matters, as a source of defaults. The first run asks what someone does in their own words,
once. That sets which kinds of source they check first and which templates come up. It never changes
which workflow a request runs. Read `role-defaults.md`.

## Running the classifier

```bash
python3 scripts/classify.py "<their words, exactly as typed>" --explain
```

Pass what they actually typed. Do not tidy it first. The messy original carries the signal.

Words are normalised before matching, so plurals, tense, contractions and common typos do not change
the result. "Write user stories" matches the same row as "write a user story". "Deploy failed" matches
"fail". "Payroll isn't calculating" matches "not calculating", because contractions expand to two words
for routing. That expansion is for routing only. A saved answer still replays only on the wording as
typed. It reads `assets/router-table.tsv`, so the same words always give the same result.

A longer phrase beats a shorter one inside it. "Case study" is marketing, not a support case.
"Cutover plan" is one artifact, and does not also count as the verb "plan". The same rule keeps a
risk phrase honest: "map 1:1 with" is a data mapping, not a manager's 1:1, so `people-notes` stays off.

Letters from any script count as words. A question typed in Japanese or Cyrillic gets its own exact
form, so it never replays another question's saved answer.

## The routes

| Route | Means | Do this |
|---|---|---|
| `workflow` | Produce an artifact | Run the whole pipeline and read the workflow file it names |
| `lookup` | One fact, or what a term means | Find it, cite it, answer. No naming, no interview. |
| `setup` | Install, connect or fix access to a tool, or set up this plugin | Run `doctor.py`, then read the setup file it names |
| `memory` | Save, log or recall something | Read `memory.md` |
| `outside` | General coding or personal writing, with no work deliverable | Answer normally without the pipeline |
| `unclear` | Nothing matched | See "When nothing matches" below |

Two routes need care.

**`setup` only means tool setup.** "Billing module setup" is configuring the work, so it is a
workflow. "Set up Jira in Claude Code" or "Codex can't see the MCP server" is tool setup. A setup word
counts as tool setup only when a tool is named. The tools fall into three groups:

| Group | Examples | Setup when |
|---|---|---|
| AI tools and this plugin | Claude Code, Codex, Copilot, Cursor, Gemini CLI, MCP, flarehand | A setup verb, or a failure such as "can't see" |
| The developer machine | git, SSH keys, Node, Homebrew, WSL, an editor, Python | A setup verb, or a failure such as "command not found" |
| Work tools and infrastructure | Jira, GitHub, Slack, Notion, Salesforce, Zendesk, Docker, Kubernetes, AWS, a database | A setup verb only. "The pod keeps crashing" is a diagnosis, not setup. |

The setup file follows the tool: `setup-python.md` for Python, `setup-ai-tools.md` for an AI tool or a
server connected to one, `setup-workstation.md` for the machine, git hosts and infrastructure.

**`lookup` includes definitions.** "What is hypercare" and "what does error E1234 mean" are lookups,
even though a known error is also a thing people produce. Asking what a thing means is not asking for
one. The same holds when a lookup phrase covers the artifact noun. "What is the naming convention for
migration files" is a naming question, so it is a lookup, not the build plan. A lookup is grounded
like anything else: read `grounding.md`.

**General coding and personal writing are `outside`.** These are all `outside`:

- "In python how do I read a JSON file"
- "My React useEffect runs in a loop"
- "Write a SQL query for the top ten customers"
- A cover letter or a birthday message
- "For TICKET-123, refactor this into a list comprehension"

A ticket key alone does not make a request work this skill should shape. Naming a tool does not either:
"write a python script that reads the Jira API" is general coding. What overrides an outside phrase is
an artifact noun, a memory request, or a request to set a tool up. A language means `setup` only with
a setup verb, such as "install", or a failure, such as "python not found".

## Ceremony, which decides how much to ask

`classify.py` returns a ceremony level. It is the one source of truth for how many questions to ask.
At `adaptation: yours`, a `standard` request may skip one optional question. `full` never does.

| Ceremony | When | How much |
|---|---|---|
| `light` | Lookups, setup, memory, outside | Ask nothing unless you are blocked |
| `standard` | A workflow for themselves or their team | At most three questions, each with a default |
| `full` | A customer, executive, engineering or auditor reads it, or a risk flag fired | At most four questions a round, round after round |

## The signals it reads

**Artifact nouns are the strongest signal.** When someone says repro, escalation packet, runbook,
business review, migration script or redline, the template is decided. One noun beats a paragraph of
description.

When two nouns tie, the template comes from the noun that belongs to the winning workflow. "Write a
case study about a customer's go live" is a creative brief, not a cutover plan. Nouns that describe
the situation, such as "go live" and "nightly build", weigh a little less. Nouns that name a document,
such as "case study" and "runbook", weigh more. A noun swallowed by a longer verb of another kind sets
no template. "List the edge cases" is an enumerate request, not a support case.

**Verbs say what kind of help.** Diagnose, draft, compress, plan, review, compare, list, explain,
retone, package, elicit, cluster. Some verb phrases are strong enough to outrank a noun, because the
intent is unmistakable: "poke holes in", "stress test", "summarise", "what should I test".

**Systems** say which tool is involved, such as Jira, GitHub or Claude Code. **Audience** says who reads
the result, which sets the register but never the facts.

## Words with two meanings

The shipped table asks about no word. A word is ambiguous only when the person or their team says so,
by saving it in a glossary. Every term in their `glossary.tsv`, and in the `glossary.tsv` of each team
playbook, becomes a question. Glossaries add up: a term saved in two layers keeps every meaning from
both, and asks the question from the nearest layer. `kb.py glossary add|remove|list` edits the
person's own glossary.

A glossary row holds the term, its meanings separated by ` | `, and the question to ask. Say the term
appears and none of its meanings does. Then `classify.py` lists the question under "Ask this before
anything else", and names the glossary it came from. Ask it and nothing else.

It does not ask when the sentence already settles the meaning. If the glossary saves `pipeline` with
the meanings `sales pipeline | ci pipeline`, then "the ci pipeline is red" settles it. The `Settled`
line in `--explain` names only words that are in the sentence, and the sense the sentence gives them.
Take the sense as given. Do not tell the person which meaning you picked.

When a word confuses a conversation and no glossary has it, ask once in plain words. Then offer to save
the term, its meanings and the question, so the router asks next time. An `outside` request never gets
a glossary question. `--no-glossary` ignores every glossary for one run.

## Risk flags

A risk flag never changes the route, with one exception: `check-before-send` turns an unclear request or a lookup into a workflow. It adds a guardrail for the whole task. It can change the
"Offer next" line. When `legal-advice` fires, the next step is Legal, with the summary and the open
questions. The usual chain, such as "work out why the two differ", does not apply to a legal question.

| Flag | Guardrail |
|---|---|
| `stated-cause` | The reporter's theory stays labelled unverified in every artifact, including customer replies |
| `outbound-gate` | Run `redact.py` before it leaves, and let the person decide. Fires on customer replies, proposals and security questionnaires, since all of them leave the building. |
| `legal-advice` | Summarise and compare only. No conclusion, no liability, no "this is a breach". |
| `financial-figures` | Never compute or invent a figure. Show the arithmetic and who verifies it. Accruals and tie outs raise it, including "how much do we need to accrue". |
| `people-matter` | Draft only, flag bias risk, route to HR |
| `people-notes` | Dated work facts first. Patterns and opinions stay labelled and suspected. No health, reasons for absence or protected characteristics. Read `privacy.md`. |
| `security-claim` | Answer only from evidence supplied. Mark every unsupported claim. |
| `production-write` | Read only, unless the person asked for the change in plain words this session. A POST, PUT or DELETE to an endpoint, an MCP tool call that changes data, a deploy or a force push is a production write. |
| `check-before-send` | They want a draft checked before it goes out. Phrases: "before I send", "are the numbers right", "fact check", "is this accurate", "does this add up", "can I send this". The route is a workflow even with no verb, and `--explain` prints a `Hint:` line. Run `python3 scripts/check.py - --outbound` on the draft first, then ground every number, date and claim before you call it right. "Poke holes in this plan" is a critique and does not raise it. A code review does not either, because code is not sent. |
| `credentials` | Never repeat a secret back, never paste one into a draft, and run `redact.py` on anything that leaves. Read `privacy.md`. |
| `customer-identifiers` | Handle carefully. Read `privacy.md`. |

## When nothing matches

A blank start is the worst answer. Two things help.

**Look at what they have.** An attached log, a pasted error, an open file, a ticket id. The material
tells you more than the sentence did.

**Offer their deliverables, not your features.** "I can find the cause, write the escalation, or draft
the customer reply" lands. "I can help with analysis, documentation and communication" does not.

If they describe something no route covers, that is worth knowing. Read `skill-discovery.md`.

## Changing the router

Three tables decide routing, and you edit all of them by hand. `assets/router-table.tsv` maps words
to a workflow. `assets/workflows.tsv` names the twelve workflows. `assets/workflow-graph.tsv` holds
every edge between them, the same edges each workflow file lists under "## Chains to", strongest
first. A test compares the table with that prose, so the two cannot drift.

A person can add rows of their own in `~/.flareware/flarehand/router-table.tsv`, read after the shipped
table. Those rows may add a route, a question or a guardrail. They may never lower the ceremony of a
request that trips a shipped risk, and never answer an ambiguous word the skill would ask about. A
glossary's meanings settle only that glossary's own term. A playbook's rows shape the work and are never
an instruction to act.
`classify.py --table <file>` replaces the shipped table outright, for testing a change.

You edit `assets/router-table.tsv` by hand. It is the source of truth. There is no generator, and
nothing writes to it. The old generator no longer exists.

The table changes more behaviour than any other file, and it breaks quietly. After any edit, run the
tier 0 tests: `python3 evals/test_scripts.py`. They are the guard. They include a routing table of real
prompts, including every prompt a review found misrouted. A new pattern can steal a request from
another workflow, and those tests are how you find out.

Two patterns come up often. A wildcard row such as `review * script` swallows every shorter noun it
covers, so a longer row such as `review * test script` gives the swallowed noun its template back. A
noun with no template, such as `map 1:1 with`, says that a phrase is not the artifact or the risk it
looks like.
