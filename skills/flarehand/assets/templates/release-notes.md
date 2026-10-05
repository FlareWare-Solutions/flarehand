---
template: release-notes
title: Release notes or changelog entry
workflow: wf-05
serves: [technical-writer, product-manager, release-manager, developer, maintainer]
source_status: mixed
team_sources: []
basis:
  - "Keep a Changelog 1.1.0 (Added, Changed, Deprecated, Removed, Fixed, Security; newest first; ISO dates) - https://keepachangelog.com/en/1.1.0/"
  - "Semantic Versioning 2.0.0 - https://semver.org/"
verified_on: 2026-10-04
tags:
  group: ship
  roles: [product, engineering, documentation, support]
  frequency: per-event
  audience: external
next: [docs-page, launch-plan]
learn:
  - "Do you have release notes or a changelog you like, such as last release's notes? Paste them or tell me where they live, and I will follow their shape."
  - "Who reads these notes: customers, developers using your API or package, internal teams, or all of them?"
  - "Where does the list of changes come from: a milestone, a list of tickets, merged pull requests, or a build report? Should every item show its ticket key?"
---

<!-- Template: release-notes, used by wf-05. The learn questions in the frontmatter come first. -->
<!-- Two modes. Release notes: written for the people who use the product. Changelog: a Keep a Changelog entry for a CHANGELOG.md file. Keep the block you need under Draft. -->
<!-- Copy the release name or version exactly from the source. Never build a version number. -->

# Release notes: <product> <version or release name>

## Draft

<!-- Every subsection below belongs to the draft. Delete any subsection with nothing in it. -->

### Release

- Name or version: <exactly as the source writes it>
- Released: <YYYY-MM-DD, or the date style your readers expect>
- Type: major / minor / patch / hotfix
- Applies to: <products, platforms and editions>

### Who needs to act

- **Self-hosted or on-premises users:** <what to install, and the minimum version to upgrade from>
- **Hosted or cloud users:** <usually no action needed>
- **Deadline:** <upgrade-by date, if there is one>

### Highlights

<!-- Only for releases with something worth a paragraph. One short article per feature. -->

#### <Area> - <Feature name>

- **Why it is useful:** <the problem it solves, in the reader's words>
- **What changed:** <the change, with exact screen, command or setting names>
- **How to use it:** <the steps, or a before and after>
- **Ticket:** <key, if your team shows them>

### Changes

| Area | Summary | Platform | Description |
|---|---|---|---|
| <feature> | <one line> | <web, mobile, API, all> | <what changed, and why it matters> |

### Fixes

| Area | Summary | Platform | Description |
|---|---|---|---|
| <feature> | <the symptom users saw> | <platform> | <what was wrong and what works now> |

### Deprecated or removed

<!-- What goes away, from which version, and what to use instead. -->

### Security

<!-- Security fixes get their own group. Describe the fix and who should upgrade, never the exploit. Name the advisory or CVE id if there is one. -->

### Known issues

| Area | What users will see | Workaround |
|---|---|---|
| | | |

### Changelog entry (Keep a Changelog mode)

<!-- For a CHANGELOG.md. Newest version on top, an Unreleased section above it, ISO dates, and only the groups that have entries. Written for people, not copied from commit messages. -->

    ## [<version>] - <YYYY-MM-DD>

    ### Added
    - <new feature>

    ### Changed
    - <change to existing behaviour>

    ### Deprecated
    - <feature that will be removed later>

    ### Removed
    - <feature removed in this version>

    ### Fixed
    - <bug fix>

    ### Security
    - <vulnerability fixed, and who should upgrade>

## MISSING - you must supply

- <field>: <who has it, and how to get it>

## Notes for the reviewer
<!-- author-only -->

<!-- Tickets you left out and why. Internal-only changes do not belong in customer notes. -->

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
