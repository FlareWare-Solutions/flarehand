# Teams and playbooks

A playbook is a folder of shapes and rules that a team commits to a repository, so everyone there works the same way.

## Individual, team and company

flarehand works alone, for a team, or across a company. What changes is how many layers a request draws on.

| Setup | What you have | Who sees it |
|---|---|---|
| Individual | Your private knowledge base at `~/.flareware/flarehand` | Only you |
| Team | Your knowledge base, plus a `.flarehand/` playbook in the team's repository | Your knowledge base: you. The playbook: everyone who can read the repository. |
| Company | Your knowledge base, a team playbook, and a company playbook the team playbook names as its `parent` | The same, plus everyone who can read the company playbook |

Each person always keeps their own knowledge base. Notes, saved answers and logs are never shared. A playbook shares only shapes and rules.

## The four layers

From highest to lowest:

1. **Yours.** The files in your knowledge base.
2. **Your team's.** The nearest playbook: a `.flarehand/` folder in the repository you are working in, found by walking up to the git root. Then any folders you added with `kb.py playbook add-path`.
3. **Your company's.** The playbook named as `parent` in a playbook's `playbook.json`, and that one's parent in turn.
4. **Shipped.** What comes with flarehand.

`python3 scripts/layers.py list` shows the playbooks in use, nearest first. It only reads.

## Which layer wins

The layers combine in two different ways. The difference matters.

**Shapes and preferences: the first match wins.** A template, a voice, a default answer, a source preference. Yours beats the team's, the team's beats the company's, and the company's beats the shipped one. `kb.py template get` names the winner as `yours`, `team:<name>` or `shipped`.

**Rules and checks: they add up.** House rules, glossary questions, redaction domains and required sections from every layer all apply. A playbook rule always applies. A personal setting can add a check but never remove one. An empty personal file does not cancel a team rule.

| Thing | How layers combine | Example |
|---|---|---|
| Templates | First match wins | Your `postmortem` beats the team's, which beats the shipped one |
| Workflows | First match wins | Your `monthly-ap-recon` beats a team workflow of the same name |
| Source preferences | First match wins | Your pin of `forum` to `never` beats the team's `prefer` row |
| House rules | Add up | Team: "Link the ticket in the title." You: "Lead with the answer." Both are checked. |
| Glossary | Add up | A term in two layers keeps every meaning from both, and asks the question from the nearest layer |
| Redaction domains | Add up | Every domain under `## Internal domains` in any layer is flagged |
| Required sections | Add up | Your own template without the MISSING list still gets it checked |

So a person can shape how their work looks, and a team can hold a standard. Neither can quietly switch off what the other relies on.

## What is in a playbook

```text
.flarehand/
  playbook.json     {"name": ..., "owner": ..., "parent": ...}
  templates/        the team's versions of templates, one Markdown file each
  glossary.tsv      the team's words with more than one meaning, and the question to ask
  house-rules.md    the team's rules, one per line under an area heading
  sources.tsv       sources to prefer or pin for this team
  workflows/        methods the team repeats, one file each
  README.md         what belongs here, and what never does
```

### playbook.json

```json
{
  "name": "payments",
  "owner": "Payments team",
  "parent": "northwind"
}
```

`parent` is the name of another playbook flarehand can find, or a path read from this playbook's folder, such as `../company/.flarehand`. A company playbook in its own repository can be added for everyone with `kb.py playbook add-path`. If a parent cannot be found, `layers.py list` says so.

### templates/

A file here replaces the shipped template of the same name for everyone who uses the playbook. A personal template, saved with `kb.py template save`, replaces both for one person. See [Templates](templates.md).

A team template can list the team's own sources in `team_sources` in its front matter. When nobody has re-checked them for 90 days, `kb.py freshness` lists the template.

### glossary.tsv

Tab separated, with a header line:

| Column | Holds |
|---|---|
| `term` | The word or phrase, as people type it |
| `meanings` | Each meaning, separated by ` \| ` |
| `ask` | The question to ask when the term is ambiguous |
| `added` | The date it was added |

The shipped router asks about no word. A word is ambiguous only when someone saves it. Say the payments team saves `settlement` with the meanings `card settlement | legal settlement`. Then a request that says only "write up the settlement" gets one question first. The question names the team glossary it came from. "The card settlement failed overnight" settles the meaning, so it asks nothing.

### house-rules.md

One rule per `- ` line, under `## <area>` headings:

```markdown
# House rules

## Pull requests

- Link the ticket in the title.

## Writing

- Lead with the answer.

## Internal domains

- payments.northwind.internal
```

Every draft and every review is checked against every house rule from every layer. `review.py rules` prints them all, with the layer each came from. Rules under `## Internal domains` tell `redact.py` which hosts are internal.

### sources.tsv

Columns `type`, `key`, `value`, `expect` and `note`.

| type | key | value | expect |
|---|---|---|---|
| `prefer` | A source kind or a domain | `primary`, `secondary` or `never` | Empty |
| `pin` | The recurring question's intent | A URL, a path, `git:<rev>:<path>` or `mcp:<server>:<id>` | The quote it must still hold |

A personal pin beats a team preference for the same kind or domain, because a preference is a shape, not a check.

### workflows/

A team workflow is a method file. See [Memory and learning](memory-and-learning.md#from-a-chain-to-a-workflow) for how a repeated chain becomes one. When someone answers `b) team playbook` to a loop offer, flarehand writes a workflow skeleton here for them to review and commit.

## Create a playbook

From inside the team's repository:

```bash
python3 scripts/kb.py playbook init --name payments --parent northwind --owner "Payments team"
```

It writes `.flarehand/` at the git root, or in the current folder when there is no repository. `--path DIR` puts it somewhere else. It writes the skeleton and a README, and prints the git command to commit it. **It never runs git.** You review it and commit it yourself.

Other playbook commands:

```bash
python3 scripts/kb.py playbook list               # what is in use, nearest first
python3 scripts/kb.py playbook add-path DIR       # use a playbook folder from anywhere
python3 scripts/kb.py playbook remove-path DIR
```

The first time flarehand finds a `.flarehand/` folder in your repository, it asks once: "Use the payments team playbook? a) yes b) this repo only c) no."

## Add glossary terms and house rules

The same commands edit your own files or a playbook. Add `--team` with the playbook's name or folder to edit the playbook.

```bash
# Glossary
python3 scripts/kb.py glossary add settlement --meaning "card settlement" --meaning "legal settlement" \
    --ask "Do you mean the card settlement or a legal settlement?" --team payments
python3 scripts/kb.py glossary remove settlement --team payments
python3 scripts/kb.py glossary list          # every layer, with its layer

# House rules
python3 scripts/kb.py rule add "Link the ticket in the title." --area "Pull requests" --team payments
python3 scripts/kb.py rule remove "Link the ticket in the title." --area "Pull requests" --team payments
python3 scripts/kb.py rule list

# A template
python3 scripts/kb.py template save postmortem --from our-postmortem.md --team payments
```

`rule add` files a rule under `Writing` when you give no area. With `--team`, each command edits the file in the playbook folder and prints what to commit. None of them runs git.

You rarely need to type these. When you explain a term or state a rule while you work, flarehand offers it in the save menu: `Save as a) mine b) team playbook c) not now d) never ask`.

## Share it through git

A playbook is ordinary files in a repository. Share it the way your team shares code:

1. Make the change, by command or by hand.
2. Run `python3 scripts/redact.py <file>` on each changed file. A playbook is shared, so it must hold no names, no customer data and no secrets.
3. Review the diff.
4. Commit it, and open a pull request if your team uses them.

Nothing in flarehand commits or pushes to a playbook. Everyone who pulls the change gets it on their next request.

## What never goes in a playbook

A playbook holds shapes and rules only. These never go in one:

- notes of any kind
- the work log
- saved answers
- evidence and snapshots
- learning counters
- voice samples and voice cards
- anything about a person, including who asked for a rule or who corrected a term
- customer data, credentials, tokens or secrets

These stay in each person's own knowledge base, or nowhere.

## A playbook is data, never instructions

Everything in a playbook, comments included, is someone's text. flarehand follows it as a shape. It never acts on it as a command. **A playbook may widen what gets searched. It may never narrow what gets checked.**

A playbook line that says "skip the review" or "save everything without asking" changes nothing. The same holds for a team's `CLAUDE.md` or `AGENTS.md`. It can change the shape, the ceremony and how often the save menu appears. It cannot change grounding or consent.

Next: [Templates](templates.md)
