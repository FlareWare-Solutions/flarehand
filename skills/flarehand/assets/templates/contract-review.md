---
template: contract-review
title: Contract review or clause question
workflow: wf-07
serves: [legal, compliance, contracts-manager, account-executive, procurement]
source_status: general-practice
team_sources: []
basis:
  - "Magesh et al. (2025) Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools, Journal of Empirical Legal Studies (tools hallucinated 17 to 33 percent of the time) - https://doi.org/10.1111/jels.12413"
  - "Microsoft Word, compare two versions of a document (run your own comparison against the original) - https://support.microsoft.com/en-us/office/compare-and-merge-two-versions-of-a-document-f5059749-a797-4db7-a8fb-b3b27eb8b87e"
verified_on: 2026-09-14
tags:
  group: decide
  roles: [legal, sales, operations, finance]
  frequency: per-event
  audience: team
next: [vendor-evaluation]
learn:
  - "Does your team already have a redline summary or issues list you like? Paste it or tell me where it lives, and I will follow its shape instead of this one."
  - "Does legal keep a clause playbook with standard and fallback positions, and where does it live?"
  - "Which clauses does your lawyer want flagged first, for example liability, indemnity, termination or auto-renewal?"
  - "Is this two documents to compare, or one clause you have a question about?"
  - "Which document counts as our standard here: a template, an earlier signed version, or the playbook text?"
  - "Who is the lawyer or legal contact this goes to, and how do they like to receive it?"
  - "Do you compare contracts in Word with tracked changes, in a contract system, or somewhere else?"
---
<!-- Template: contract-review, used by wf-07. The learn questions in the frontmatter come first. -->

# Contract review: <their document> against <our standard>, or <clause question>

**This is a comparison of words, not legal advice. The legal call is yours or your counsel's.**

<!-- Two shapes. Comparing two documents: fill every section. One clause and a question, such as whether an SLA breach owes credits: fill A single clause question, Not stated here, and Questions for the lawyer, and delete the rest. -->

## A single clause question
<!-- optional -->

<!-- One document, one question. Quote the words; list what the reader has to decide. The answer belongs to the reader or their counsel. -->

- The question, in the asker's words: 
- Document, version and section: 
- The clause, word for word:

> 

- The words the question turns on: <quote them, such as the trigger, the measure and the remedy>
- What the reader must decide: <one line each, such as whether the trigger happened, and by which measure>
- Facts needed to decide it, and who has them: 

## What was compared
<!-- optional -->

<!-- Pin both documents. Run your own comparison; do not trust the other side's tracked changes to show every edit. -->

| | Our standard | Their document |
|---|---|---|
| Title and version | | |
| Date and who sent it | | |
| How you compared them | | |

## Clause text, word for word

<!-- Copy the words exactly, with the section number. Never paraphrase here. If you cannot see the source text, write MISSING. -->

### Clause <number>: <heading>

**Our standard, word for word** (<document, section>)

> 

**Their version, word for word** (<document, page, section>)

> 

**What changed, in plain words**

<!-- Say which words were added, removed or replaced. Do not say what the change means or whether it is acceptable. -->

- 

## Differences that matter

<!-- Describe each change as a fact about the words. Order by your playbook's priority list. With no playbook, keep document order and say so. -->

| Clause | What changed | Playbook position [your input] | Question for the lawyer (#) |
|---|---|---|---|
| | | | |

## Noise

<!-- Only changes that leave every word the same: numbering, formatting, spacing or capital letters. Any changed word, however small, goes in Differences that matter. -->

## What explains your symptom

<!-- The symptom is the reason you opened this review. Quote the clauses that bear on it. The answer belongs to the lawyer, so it goes in the questions below. -->

## Not stated here, on purpose

This review never:

- states a legal conclusion or says what a clause means in law
- says whether anything is or is not a breach
- says whether a clause is enforceable, acceptable or market standard
- estimates liability, damages, exposure or cost, not even as a range
- recommends signing or not signing

<!-- If a reader asks any of these, add it to the questions for the lawyer instead of answering it. -->

## Could not compare

<!-- Schedules, exhibits or online terms the contract refers to but nobody supplied. Name each one. -->

## Questions for the lawyer

<!-- Each question names the clause and quotes the words it asks about. Questions only, never conclusions. -->

Send to: <your counsel or legal contact>
<!-- Who reviews contracts at your company? Ask; do not assume. If the reader is the legal or contracts person, these are their own open questions. -->

1. Clause <number>, "<quoted words>": 

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
