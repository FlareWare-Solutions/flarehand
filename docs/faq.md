# FAQ

Short answers to the questions people ask most, with links to the full story.

## What is flarehand for?

Turning a one-line work request into the deliverable it needs. You type "write up these notes as a postmortem" or "check this reply before I send it". It names the artifact and asks only what changes it. It grounds every specific in a source, checks the draft, and offers to keep what was worth keeping. It is for anyone who ships work: engineering, support, product, operations, sales, marketing, finance, HR, founders, freelancers and students. See [How it works](how-it-works.md).

## Does it send my data anywhere?

flarehand itself has no server, no account and no telemetry. Your knowledge base stays on your machine and never syncs. Its scripts touch the network in three cases only. They fetch a page the agent is citing, re-check a pinned source, or run a link check someone asked for. Every case is listed in [Privacy and data](privacy-and-data.md#what-goes-over-the-network-and-when).

Your AI tool is separate. It sends your conversation to its model provider under its own terms, as it would without flarehand.

## Does it save things without asking?

No. Nothing goes into your knowledge base without a yes. Two standing yeses exist, each asked once: learning counters, which hold pattern names and dates and never content, and autosave for the work log. Both can be turned off. A few bookkeeping writes need no separate yes, such as the git commit that records a save you approved. See [Memory and learning](memory-and-learning.md#consent-first).

## How is it different from a memory plugin?

Most memory tools capture what you say automatically and recall it later. flarehand works the other way round:

| | Many memory tools | flarehand |
|---|---|---|
| What it is for | Remembering the conversation | Producing the deliverable. Memory serves the work. |
| When it saves | Automatically | Only the lines you pick from the save menu |
| What a recall gives you | A summary or snippets, regenerated | A saved answer word for word, or nothing |
| How you know it is still true | You do not | Every saved item carries its sources and when they were last checked, and goes due for a re-check |
| Where it lives | Often a service or a database | Plain Markdown on your machine, with git history |
| What it learns | Whatever it captures | Only after it noticed a pattern twice and you said yes |

## Will two people get the same answer?

The same person asking again gets their saved answer back, word for word. Two different people get the same method and the same facts, shaped for each of them by their role, their team's playbook and their preferences. Saved answers are private, so nobody shares them. See [How it works](how-it-works.md#why-scripts-and-tables).

## Can my team share templates?

Yes, through a playbook: a `.flarehand/` folder committed to your team's repository. It holds templates, a glossary, house rules, source preferences and workflows, and never notes or anything about a person. Your own version of a template still wins for you. Team rules always apply. See [Teams and playbooks](teams-and-playbooks.md).

## How do I turn off the em-dash rule?

Change your voice profile:

```bash
python3 scripts/kb.py config --style none
```

| Profile | Means |
|---|---|
| `plain` | The default: short sentences, plain words, no em dashes |
| `google` | Everything in `plain`, plus the Google developer-docs rules for documents. It keeps the no-em-dash rule. |
| `none` | No house voice. The style checks are off, so it writes the way you or your team write. |

`--voice` and `--style` set the same preference. The rules about facts hold under every profile: it never drops a fact, never invents one, and labels every claim.

The separate em-dash gate, which holds a whole reply until it is rewritten, is off by default. `kb.py config --voice-gate on` turns it on in tools that run plugin hooks, and `off` turns it off. Under the `none` profile, the gate stays off, the per-turn reminder drops the voice rules, and `check.py` skips the style checks.

## Can I use it without Python?

Partly. In claude.ai and Claude Desktop chat, four scripts run in Anthropic's sandbox: `classify.py`, `check_output.py`, `redact.py` and `review.py`. Anywhere else with no shell, every script step has a written by-hand version the agent follows. You lose the knowledge base and the exact checks, so it says so early.

## Why does it ask me questions at all?

Only to settle what no tool can answer: who reads it, which trade-off you prefer, what good looks like. It looks up everything else first. Each question comes with a recommended answer, and "just go" takes them all. A quick lookup gets no questions. See [It asks too many questions](troubleshooting.md#it-asks-too-many-questions).

## Why does it say "I could not confirm this"?

Because it could not, and guessing would be worse. A polished document with an invented number in it is the failure flarehand exists to prevent. The sentence comes with what it would need and where to look. Then you can fill the gap, and it can save the answer for you.

## Why are there labels like `[your input]` in my draft?

So you can tell at a glance which sentences you can act on without checking. Text you will send, such as a customer reply, is shown clean, with the labels listed in the notes after it. `kb.py config --labels compact` gathers them at the end. See [Grounding](grounding.md#the-labels).

## Will it give legal, financial or HR advice?

No. For legal, finance and HR it drafts, summarises and compares. It never states a legal conclusion, computes a liability or an amount owed, or signs off. It shows the source text and says who decides.

## Does it work offline, or with no web access?

Yes. It grounds in your words, your files, the repository, its git history and any MCP servers. It labels everything else `[ASSUMPTION, verify]`, writes no URL it did not see, and ends with what to confirm.

## Can I see what it has learned about me?

`python3 scripts/kb.py about-me` lists every preference, which layer it came from, and the one command that undoes it. Every change to your knowledge base is also in its git history: `git -C ~/.flareware/flarehand log --oneline`.

## Can I edit the files by hand?

Yes. It is plain Markdown. The next `kb.py` command notices the change and rebuilds the index. Keep each note's front matter header intact, because writes refuse a note whose header is missing or never closes. A saved answer you edit by hand stops replaying until you approve it again.

## Can I see my knowledge base as a graph?

Optionally. Open the folder in Obsidian as a vault, and its graph view draws the links between notes. VS Code with the Foam extension and Logseq read the same files. See [Troubleshooting](troubleshooting.md#obsidian-will-not-open-the-folder) if the folder does not open.

## Can I make a workflow of my own?

Yes. Steps you repeat are offered as a saved chain the first time flarehand notices the loop. After the chain has run three times, it offers to promote it into a workflow with its own method, shape and checks. A workflow of your own can add a route or a guardrail, never remove one. See [Memory and learning](memory-and-learning.md#from-a-chain-to-a-workflow).

## Where do I report a bug or suggest a template?

Open an issue at https://github.com/FlareWare-Solutions/flarehand/issues. For a template, say what it does and who would use it. To contribute code, read `CONTRIBUTING.md` and [Architecture](architecture.md).

Next: [Troubleshooting](troubleshooting.md)
