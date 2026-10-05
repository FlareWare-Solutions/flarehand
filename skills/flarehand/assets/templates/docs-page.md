---
template: docs-page
title: Documentation page or README
workflow: wf-05
serves: [technical-writer, developer, devops, developer-advocate, support-engineer, it-helpdesk]
source_status: mixed
team_sources: []
basis:
  - "Diataxis, the four kinds of documentation (tutorials, how-to guides, reference, explanation), CC BY-SA, paraphrased here - https://diataxis.fr/"
  - "Diataxis, How-to guides - https://diataxis.fr/how-to-guides/"
  - "Diataxis, Tutorials - https://diataxis.fr/tutorials/"
  - "Standard Readme specification (section order for a README), MIT - https://github.com/RichardLitt/standard-readme/blob/main/spec.md"
  - "Google developer documentation style guide, Procedures, CC BY 4.0 - https://developers.google.com/style/procedures"
verified_on: 2026-10-04
tags:
  group: build-run
  roles: [engineering, devops, support, documentation]
  frequency: per-event
  audience: external
next: [release-notes]
learn:
  - "Do you already have a docs page or README you like, or a docs site with its own templates? Paste one or tell me where it lives, and I will follow its shape."
  - "Who reads this page, and what will they already have installed or know?"
  - "Which operating systems or environments must it cover, and which steps need someone else, such as IT or an admin?"
---
<!-- Template: docs-page, used by wf-05. The learn questions in the frontmatter come first. -->
<!-- Pick one mode. Keep the sections that mode uses and delete the rest, so the page holds only what its reader sees. Mixing modes is the commonest docs failure: a tutorial that stops to explain theory, or reference that tries to teach. -->
<!-- Tutorial: a lesson that always works, for a beginner. How-to: steps to reach one goal, for someone who knows what they want; this mode replaces the old setup guide. Reference: facts to look up, complete and dry. Explanation: the why and the background. README: the front page of a project. -->
<!-- Describe only what you can see in the product, the code or a source. Never invent a menu, a button, a command or an output. If you cannot confirm one, leave a placeholder and put the question on the MISSING list. -->

# <Page title: "Get started with X", "How to set up X", "X reference", "About X", or the project name>

<One or two sentences: what this page helps the reader do or understand, and who it is for.>

## Before you begin
<!-- optional -->

<!-- Tutorial, how-to and README install. Accounts, access, tools with versions, and the machine. -->

- 

## Steps
<!-- optional -->

<!-- Tutorial and how-to. One action per step, starting with a verb. In a tutorial every step works as written and shows a visible result. In a how-to, where platforms differ, show each one, and say who must do a step the reader cannot. -->

1. <action>
   - Windows: <exact steps>
   - macOS: <exact steps>
   - Linux: <exact steps>
   - You see: <expected result>
2. <step someone else must do, such as an admin>: send them "<exact request>".

## Undo the change
<!-- optional -->

<!-- How-to only. How to uninstall or reverse it, or a plain statement that it cannot be undone. -->

## <Item name>
<!-- optional -->

<!-- Reference only. One section per item, the same shape every time. Describe; do not instruct. -->

| Name | Type | Default | Description |
|---|---|---|---|
| | | | |

## <Question the page answers, such as "Why X works this way">
<!-- optional -->

<!-- Explanation only. The background, the design reasons and the trade-offs. Link to how-to and reference pages instead of repeating them. -->

## Install
<!-- optional -->

<!-- README only. Standard Readme order: title, short description, background, install, usage, then API, maintainers, contributing and license. Add the later sections as the project needs them. -->

## Usage
<!-- optional -->

## Troubleshooting
<!-- optional -->

| Problem or exact error | What to do |
|---|---|
| | |

## Next steps
<!-- optional -->

- <the next page in the sequence>

## Draft notes
<!-- author-only -->

<!-- For the author and reviewers only. Leave this section out of the published page. -->

- Mode: tutorial / how-to / reference / explanation / README
- Owner, and who updates the page when the product changes:
- Tested against: <product version, operating system, date>
- Sources checked, such as the code, the changelog or the product:
- State: draft / in review / published

## MISSING - you must supply

- <step, version or output you could not confirm>: <who can confirm it>

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
