---
template: customer-reply
title: Customer reply on a support case
workflow: wf-05
serves: [support-analyst, support-engineer, escalation-engineer, customer-success, account-manager, consultant]
source_status: general-practice
team_sources: []
basis:
  - "KCS v6 Practices Guide, Technique 5.1 KCS article structure (issue in the requestor's words) - https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Practices_Guide/030/040/010/020"
  - "KCS v6 Practices Guide, Technique 5.2 KCS article state (not validated and validated) - https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Practices_Guide/030/040/010/030"
  - "Microsoft Writing Style Guide, Top 10 tips for style and voice - https://learn.microsoft.com/en-us/style-guide/top-10-tips-style-voice"
verified_on: 2026-09-14
tags:
  group: respond-support
  roles: [support, customer-success, sales, consulting]
  frequency: daily
  audience: external
next: [knowledge-article]
learn:
  - "Do you have a customer reply you were happy with? Paste it and I will follow its tone and shape instead of this one."
  - "Where does this reply go: the case portal, an email, or a note after a call, and does your team use a set greeting, sign-off or way of writing the case number?"
  - "Does anyone check replies before they go out, for example on escalated cases?"
  - "How formal is this customer, and does their contact expect a particular style?"
---
<!-- Template: customer-reply, used by wf-05. The learn questions in the frontmatter come first. -->

# Customer reply: <case id and subject>

## Draft

**Subject:** <case id>: <the problem, in the customer's words>

Hi <name>,

<!-- 1. Show you understood. Restate the problem in their words, and the business effect if they told you. -->

<!-- 2. Say what is known. Keep only the line that matches the Cause row, and delete the other two. -->
- Confirmed: We have confirmed the cause. <one plain sentence>
- Suspected: We are checking one possible cause, <one plain sentence>. We have not confirmed it yet.
- Unknown: We have not found the cause yet. So far we have checked <what you checked>.

<!-- 3. If they suggested a cause, thank them and say you are checking it. Never present it as the answer. -->

<!-- 4. What they can do now. Numbered, exact steps, with what they should see after each one. -->
1.
2.

<!-- 5. What you need from them. Ask for everything in one message, and say why each item helps. -->

<!-- 6. What happens next, and when you will update them. Promise only dates you control. -->

Kind regards,
<your name>

<!-- General practice: lead with the answer, write like you speak, and describe what the system did, not what the customer did wrong. -->
<!-- If your team has a triage guide with set wording for each outcome, start from that. -->
<!-- Do not promise a log, a feature or a fix before checking it exists for the customer's version. -->

## Fact check
<!-- author-only -->

| Statement | Status | Source |
|---|---|---|
| The problem, in the customer's words | reported | [your input] |
| The customer's theory of the cause | reported, not verified | [your input] |
| The cause | confirmed / suspected / unknown | |
| The fix or workaround | tested / not tested / none yet | |
| The next update | date agreed / not agreed | |

<!-- Fill this before you write the reply. It is for you, not the customer. Every sentence in the draft must match a row and its status. -->
<!-- A cause counts as confirmed only when a reproduction or a working fix proved it. The customer's theory never counts on its own. -->

## MISSING - you must supply

- <fact the draft needs>: <who has it>

## Notes for the reviewer
<!-- author-only -->

<!-- Every promise the reply makes, any line that could read as blame, and anything you left out on purpose. -->
<!-- Never name another customer or paste their data. Run the redaction check and decide before you send. -->

---

<!-- Label every claim: [verified: source], [your input], or [ASSUMPTION, verify]. -->
<!-- Before this leaves your machine: python3 scripts/redact.py <file> -->
