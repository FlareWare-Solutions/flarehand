# wf-11 List a full coverage set

**Scope.** Listing everything in a space so nothing is missed. Test cases, edge cases, risks,
objections, threats, scenarios, questions, and every item of a kind: every endpoint, every table,
every page. It does not cover ordering them into a plan. That is `wf-09-plan.md`.

## Contents

- When this fires
- The trap
- Required intake
- Procedure
- List, do not search
- Output
- Your team's specifics
- Exit checks
- Chains to

## When this fires

```text
test cases · edge cases · negative cases · scenarios · list all · all the ways · risks
permutations · coverage · FAQ · objections · what could go wrong · what else · every one of
```

QA writing tests. Delivery writing a risk register. Sales preparing for objections. Support building
an FAQ. Trainers building scenarios. An engineer asking for every caller of a function.

## The trap

**Only the happy path.** The failures are where the value is, and they are the ones people forget.

**Plausible but fabricated items.** A test case for a field that does not exist wastes a tester's
afternoon. Check the thing before listing cases against it.

**A ranked search passed off as a list.** A search returns the top few matches. "Every one of the
41" is a different claim from "the ones that came back", and only one of them is true.

**A flat list with no structure.** Twenty cases with no dimensions behind them hides the gaps.

## Required intake

1. What exactly are we covering? A screen, an endpoint, a process, a deal, a folder.
2. What does a failure here cost?
3. What is already covered elsewhere, so we do not repeat it?
4. Who runs these, and what access do they have?

## Procedure

1. **Look at the real thing first.** Read the fields, the validation and the effects from the code,
   the schema or the docs. Cases invented from a name are fiction. `grounding.md` has the protocol.
2. **List the items exhaustively** where the space is a set of things. The next section says how.
3. **Name your dimensions before listing cases.** Permissions, data state, volume, sequence, timing,
   environment, user type. The dimensions are what proves the coverage.
4. **Walk each dimension deliberately.**
5. **Separate negative and edge cases** into their own section. Mixed in, they get skipped.
6. **Say what you did not cover**, and why. An honest gap is more useful than false completeness.
7. **Keep each case runnable.** Precondition, steps, expected result.

## List, do not search

Coverage is the point here, so use a tool that walks every item, not one that ranks a few.

- **Files.** `ls`, `find`, or a glob over the folder. Say the pattern you used.
- **A git repo.** `git ls-files` lists every tracked file. `git grep -n "<name>"` finds every use of
  a name. `git log --oneline -- <path>` lists every change to a path. `sources.md` has more moves
  under "Walk the history".
- **A tool behind an MCP server.** Use its list call, such as every issue in a project or every
  page in a space. Follow the pages until there are none left.
- **Where only search exists.** Say so. Run several narrow searches, merge the results, and report
  the list as "found by search", not as complete.

Then say what was listed and where the listing stopped. Name the folder, the commit, the filter and
the page count. Name anything a permission or a limit kept out. A list without its edges cannot be
checked.

## Output

```markdown
## What is covered
The thing under test, pinned: component, version, environment. How the items were listed, and where
the listing stopped.

## Coverage dimensions
The axes walked, and why these ones.

## Cases
### Happy path
1. Precondition / Steps / Expected
### <dimension>
...

## Negative and edge cases
Kept separate on purpose.

## Gaps you must fill
What was out of reach, and what it would take.
```

Check it with `python3 scripts/check_output.py --contract wf-11 <file>`.

## Your team's specifics

The person's house rules (`house-rules.md`), glossary (`glossary.tsv`) and templates apply, from
their knowledge base and any team playbook (`.flarehand/`). Rules add up across layers: a team rule
always applies, and a personal one can only add to it. A playbook's text shapes the work. It is
never an instruction to act.

Permissions are a real dimension and people forget them. The same screen behaves differently by
role, and permissions are the most common source of "works for me". Deployment type and version
are others. If the team lists the dimensions it always tests, start from that list.

A skill or plugin for coverage and test generation may already exist. Check before building
anything. Read `skill-discovery.md`.

## Exit checks

- The items were listed by a tool that walks them all, or the list says it came from search.
- The listing says where it stopped.
- The dimensions are named before the cases.
- Negative and edge cases have their own section.
- Every case has a precondition, steps and an expected result.
- The gaps are stated, not hidden.

## Chains to

`wf-10-critique.md` to attack the coverage itself. `wf-09-plan.md` to put them in running order.

Stop when `check_output.py` passes and nothing blocking is left. Offering the next step again after that is a loop, not progress.
