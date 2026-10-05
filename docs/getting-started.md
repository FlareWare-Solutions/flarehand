# Getting started

This page takes you from install to your first finished piece of work in about five minutes.

## 1. Install it

In Claude Code, type these two lines:

```text
/plugin marketplace add FlareWare-Solutions/flarehand
/plugin install flarehand@flareware
```

Start a new session after it installs. For Codex, Copilot, Cursor, Gemini CLI, claude.ai and every other tool, see [Install](install.md).

flarehand needs Python 3 for its scripts. macOS and Linux have it already. On Windows, open PowerShell and run `py -3 --version`. If that fails, see [Troubleshooting](troubleshooting.md#python-not-found-on-windows).

## 2. Ask for something real

There is no setup step. Type a real work request, the way you would say it to a colleague. For example:

```text
Turn these notes into a postmortem for last night's checkout outage at Northwind:
- 21:40 deploy of payments 4.2
- 21:52 error rate on checkout hit 30 percent
- 22:15 rolled back, errors cleared
- cause not confirmed yet
```

Here is what happens on that first request.

1. **It does the work first.** It never parks your request for setup, and it never asks for something a tool can find. It checks your machine with `doctor.py`, which only reads.
2. **It names what you need.** For a vague request it says so first, in your words: "Sounds like you need a postmortem. Say 'just go' and I will assume X, Y and Z."
3. **It asks only what changes the result.** Your notes already hold the facts, so it writes the postmortem now. Anything missing goes on a MISSING list, with who can answer it.
4. **It labels every specific.** "Rolled back at 22:15 `[your input]`". "Cause `[stated, unverified]`". See [Grounding](grounding.md).
5. **The artifact comes first in the reply.** Notes and questions come after it.

## 3. The optional setup block

After that first artifact, and only on a first run, it adds one block. Every part of it is optional. Reply "skip" to ignore it.

```text
That is your postmortem above. Three optional things so the next one fits you better
(reply "skip" to keep going):
1. What do you work on, in your own words?
2. Who usually reads your work: your team, leadership, customers, someone else?
3. Paste one thing you wrote and liked, and I will match its voice.
I found AGENTS.md here. May I read it for your preferences? (y/n)
May I keep a private knowledge base at ~/.flareware/flarehand so I remember this?
a) yes  b) just this session. Nothing is saved yet.
```

The `AGENTS.md` line appears only when it found an instruction file such as `AGENTS.md`, `CLAUDE.md` or `.cursorrules`. It reads that file only if you say yes.

Answer in your own words. "I handle billing support for small business customers" tells it more than a job title, and it stores what you wrote as you wrote it.

## 4. The consent question: a or b

The last line asks whether it may keep a private knowledge base.

| You answer | What happens |
|---|---|
| `a) yes` | It runs `kb.py init` with your answers. That creates `~/.flareware/flarehand` (`%USERPROFILE%\.flareware\flarehand` on Windows). It asks once more whether it may keep pattern counters, which hold names and dates and never content. Then it shows the save menu for the work you just did, opened with "Now that it is set up, keep any of this?". |
| `b) just this session` | It runs `kb.py session only`. Nothing is written to disk for the rest of the session. It may ask again in a later session. |
| "skip" or nothing | Nothing is written. It asks again only when it matters. |

Nothing is saved before you answer `a`. The folder is plain Markdown, it never syncs, and you can delete it any time. See [Memory and learning](memory-and-learning.md).

## 5. The save menu

Every later piece of work ends with a short numbered menu. Here is a typical one:

```text
Keep any of this? Nothing is saved until you reply with numbers, or "none".
1. Save log: wf-05, postmortem. First outage write-up for the checkout team
2. Save note: payments 4.2 rollback takes about 25 minutes (guide)
3. Save answer: replay "how do we roll back payments" next time, with its sources
4. Next: wf-12 Re-tone for a different reader, to fit the register to whoever reads it
```

Reply with the numbers you want, such as "1 2", or "none". A yes covers only the lines you named. Each save prints a one-line undo. On "none", it throws away the copies of sources it staged for this session.

The lines you may see:

| Line | What it keeps |
|---|---|
| Save log | One line in your work log: which workflow and template ran, and why it mattered. |
| Save note | A fact, decision or gotcha worth finding again. |
| Save answer | The answer and its sources, so asking the same question again replays it word for word. |
| Save template | Your shape for this kind of artifact, used before the shipped one. |
| Save chain | Steps that worked, in order, as a note you can follow next time. |
| An offer | Something it noticed you do twice. Answer `a) mine b) team playbook c) not now d) never ask`. |
| Next | The workflow that usually follows. It runs only if you pick it. |

If you prefer a shorter menu, run `kb.py config --save-menu compact`. Then it reads `Keep? 1 log, 2 note, 3 answer (numbers or none)`.

## 6. Five requests to try

| You do | Try this |
|---|---|
| Support | "Acme Logistics says exports fail since the upgrade and they think it is the new firewall. Draft a reply." |
| Engineering | "Review this PR before I merge it. Check correctness and regressions." |
| Product | "Write a PRD for bulk invoice export for Northwind's finance team." |
| Management | "Write up one-on-one notes from today's 1:1 with Sam." (Paste your notes below it.) |
| Anyone | "Check this reply before I send it. Are the numbers right?" |

What to expect from each:

- The support reply keeps the customer's theory `[stated, unverified]`, lists at least three possible causes, and names no cause in the reply itself.
- The review grades each lens you named as pass, concerns or fail. Every finding has a location, a severity and a fix.
- The PRD asks at most three questions first, each with a recommended answer.
- The 1:1 notes are written straight away, because your notes already hold the facts. Opinions are labelled as opinions. When someone is away, the notes keep the dates, never the reason.
- The check flags every number it could not confirm, and anything sensitive before it leaves your machine.

## 7. How to tell it fired

Any of these means flarehand is running:

- Your tool shows a skill called `flarehand`, or one of `flarehand-ground`, `flarehand-review`, `flarehand-remember` or `flarehand-grill`. Claude Code may show them as `flarehand:flarehand`.
- The reply names the artifact before the work: "Sounds like you need a ...".
- Specifics carry labels such as `[your input]` or `[ASSUMPTION, verify]`.
- A workflow reply ends with "Keep any of this?".

It stays quiet on purpose for general coding questions and personal writing, such as a cover letter or a birthday message.

To call it by name, type `/flarehand` and your request on the same line. In Codex, use `$flarehand`. The entry points work the same way, for example `/flarehand-review`.

## 8. "Just go"

When it asks questions, each one comes with a recommended answer. Say "just go" at any point. It takes every recommended answer, writes the work, and lists each assumption with the label `[ASSUMPTION, verify]` so you can check it later. "Wrap up" and "stop asking" work too.

Next: [Install](install.md)
