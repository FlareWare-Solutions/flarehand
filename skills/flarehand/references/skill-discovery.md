# skill-discovery - check before you build

**Scope.** Finding an existing skill or tool before writing anything, and what to do when nothing
covers the need. For where to look for facts, read `sources.md`.

## Contents

- Look before you build
- Tools you do not know
- When nothing covers it
- Writing a new skill
- Sharing it
- Keep what you learn

## Look before you build

Someone may already have built what they need. Rebuilding it by hand is a wasted afternoon, and the
result is usually worse than the one that exists.

Before writing anything that looks like a tool, a generator, a checklist or a documented procedure,
spend one look in each of these places.

1. **What they already have.** The skills and plugins installed in their AI tool. In Claude Code,
   `/plugin` and the skills list show them. Other tools list theirs in their own settings.
2. **Their team.** A playbook's `workflows/` and `templates/` folders, and any skills folder in the
   repository they work in.
3. **The plugin marketplaces they have added.** Each one lists its plugins and the skills inside them.
4. **Public skill directories**, if they have web access. Search for the job, not for a product name.

When you find one, say so, and give the install command from that plugin's own README exactly as it
appears there. Do not write an install command from memory. Plugin names and install syntax both
change, and a command that almost works wastes more time than no command.

## Tools you do not know

People use systems this skill does not know about. When a request hints at a tool you do not
recognise, ask which one rather than guessing. Then check whether any source you can reach describes
it: their files, an MCP server they connected, or the tool's official documentation. If none does,
say so and work from what they tell you, labelled `[your input]` rather than as verified process.

Do not invent a process for a system you cannot see. The guess will get repeated.

## When nothing covers it

A gap that keeps appearing is worth closing. Three levels, depending on how big it is.

**A chain, for a workflow you put together that worked.** A chain is a saved note of type `chain`.
Next time, `kb.py search` finds it and you follow its steps in order.

```bash
python3 scripts/kb.py note "Monthly reconciliation" --type chain --why "Ran this three times now."
```

It lives in the knowledge base, on their machine, and only after they say yes. This is the personal
half of consistency, and it costs nothing.

**A workflow, once a chain has proved itself.** After the third run, offer
`kb.py workflow promote <permalink>`. That gives it four things: a method file, a shape, a set of
checks, and a row in their router table. The skill then routes to it by name, instead of waiting to
be searched for. Read `wf-authoring.md`. Offer it on evidence, never on a guess: the work log counts
the runs. A team can keep the same workflow in its playbook's `workflows/` folder.

**A new skill, for something many people would use.** Read the next section.

## Writing a new skill

Follow the Agent Skills format the tool documents. The rules that matter most, because each one fails
silently:

- the folder name and the `name:` field match exactly, lowercase with hyphens
- the name never contains `anthropic` or `claude`, because the spec reserves those words
- the description is a quoted string of 1020 characters or fewer
- the body stays under 500 lines, with detail in `references/`
- `references/` files sit one level below `SKILL.md`, and `SKILL.md` names each one it uses
- scripts use the standard library only, with nothing to install

This skill's reference files point at each other, for example `interview.md` to `wf-02-elicit.md`.
That is a deliberate choice. Every file is still one level deep and still named in `SKILL.md`, so a
reader who starts at the router never has to guess a path.

`python3 scripts/validate_skill.py` checks a skill folder against these rules.

## Sharing it

Promotion is a human step on purpose. Something many people rely on should have a person's name
against it, and someone should read it before it ships.

- **For their team**, put it in the team's playbook or a shared repository, and let the team review it
  the way they review any change.
- **For everyone who uses flarehand**, suggest they open an issue at
  https://github.com/FlareWare-Solutions/flarehand/issues, with a line on what it does and who would
  use it.

Never post or open anything for them. Draft the text, and they decide.

## Keep what you learn

When you work out something about their team that was not written down anywhere, that is exactly what
the knowledge base is for. Offer to save it. A term goes in the glossary, a rule goes in house rules,
and a fact goes in a note. Read `memory.md` for what is worth keeping.

Every real process someone walks you through is one that nobody on their team has to guess at again.
