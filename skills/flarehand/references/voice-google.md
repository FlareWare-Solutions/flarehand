# voice-google - the Google developer-docs profile

**Scope.** An opt-in set of writing rules for documents and technical write-ups. It sits on top of
the default `plain` profile in `voice.md` and never replaces it. It does not cover chat replies,
customer replies or case notes. Those keep the plain voice, with or without this profile.

**Attribution.** This file and `assets/style-words-google.tsv` adapt the Google developer
documentation style guide, https://developers.google.com/style, by Google. Google publishes it under
CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Everything here is paraphrased and
shortened, and changed where it clashes with the plain profile. Google does not endorse this skill.

## Contents

- When it applies
- How it is offered
- What wins when rules disagree
- The rules
- How to check
- What stays a judgement call

---

## When it applies

The profile is for a finished document someone will read more than once:

- Support: knowledge articles, known errors, repro steps and RCAs.
- Delivery: runbooks, docs pages, cutover plans, data migration plans and closeout reports.
- Product and QA: release notes, functional specs, test plans and user stories.
- Everyone else: course material, SQL build notes and plans from wf-09.

`assets/style-profiles.tsv` holds that list, and a team can add a template to it.

Four ways turn it on, strongest first:

1. **This request.** They said "in Google style". `classify.py` reports it under `style.asked`.
2. **A saved template.** Its front matter says `style: google`. `kb.py template get --json` prints it.
3. **The person.** `prefs.style` is `google` in `config.json`. Set it with `kb.py config --style google`.
   `plain` is the default, and `none` turns the house voice off. `voice.md` says what each one means.
4. **The offer.** Nothing above is set, and `classify.py` reports `style.offer`. Ask once, as below.

## How it is offered

Ask it as one optional question in the same round as the interview, never as a round of its own. On a
first run it takes the second of the two question slots in the first reply:

```text
Optional: want this in the Google developer-docs style? It tightens headings, steps and wording
for a document others will reuse. Say yes for this one, always, or no.
```

- **Yes** applies it to this document only.
- **Always** runs `kb.py config --style google`, which asks for their yes like any other write.
- **No**, or no answer, keeps the plain voice. Do not ask again this session.

Once `prefs.style` is set, do not offer again. Say which style you used in one line, the way
`adaptation.md` says every remembered choice is said out loud.

## What wins when rules disagree

House rules first, then the team's template, then this profile, then a dictionary.

- **No em dashes, the same as the plain profile.** Google uses them. Rewrite every Google example you
  borrow.
- **Rule 9 still wins.** Never drop a fact to fit a rule here.
- **Spelling follows the team.** Use the spelling the team's house rules or template name. Google
  assumes US English.
- **On-screen labels are bold** and do not count against the one-bold-per-section habit.
- **The MISSING heading is in sentence case too.** Under this profile, write it as "Missing: you must
  supply". The contract check accepts either form.
- **Product names win.** Write a screen, tab or field exactly as the product shows it. That holds
  even when Google's word list would change the word.

## The rules

**Headings.** Sentence case: capitalise the first word and names only. A task heading starts with a
bare verb, such as "Post a batch". Never skip a level, and never end a heading with a period.

**Lists, tables and code blocks.** Introduce each one with a full sentence that ends in a colon. Keep
list items parallel: all start with a verb, or all are nouns. Punctuate them the same way. Say
whether the items are required or optional.

**Steps.** One action per step. Name the screen or field first, then the action. Put the goal before
the action: "To reopen the period, click **Reopen**." Inside a step, the order is: the action, the
command, what to replace, the expected result, then how to check it worked.

**Notices.** Use Note, Caution and Warning on purpose. A step that cannot be undone carries a
Warning inside the step, not after it. Never put two notices in a row.

**Tense and time.** Describe what the product does now, in the present tense: "the screen shows the
total", not "will show". Tie "new", "latest" and "currently" to a version or a date, or cut them.
Never promise a release, a fix or a date that no source confirms.

**Precise verbs.** Must means required. Can means optional. Might means possible. "We recommend"
means recommended. Avoid "should", because readers cannot tell which of those you meant. Recommend
one path instead of listing every option.

**UI wording.** Click a button, select or clear a checkbox, enter text in a field, turn a setting on
or off. Do not write uncheck, or toggle as a verb. Do not point with above, below, left or right:
name the section or the label. Write a key combination as Ctrl+Shift+S.

**Code and commands.** Code font for anything the reader types. A command the reader copies must run
as pasted. Leave out square brackets for optional parts. Leave out angle brackets too, because a
shell reads them as a redirect. Write placeholders in capitals, such as `ENV_NAME`. Explain each one
after the block, under "Replace the following:". Keep input and output in separate blocks.

**Links.** Write "For more information about the batch screen, see Posting batches." Link text names
the page it opens. Give short help in place before sending anyone away. When you rename a heading,
keep the old anchor, because links and citations point at it.

**Global readers.** No idioms, seasons or cultural references. Subject, then verb, then object. Put
"only" next to the word it limits. Avoid stacks of three nouns, and keep "that" where it helps.

**Accessibility.** Every image has alt text. Nothing is carried only by an image or only by colour.
Headings form a real hierarchy. No forced line breaks inside a paragraph.

**Punctuation.** Use the serial comma in a list of three or more. Use straight quotes, so pasted text
still works. Use few semicolons and no exclamation marks. Do not end a sentence with a URL or a path.
Contractions are fine.

**Reference docs.** Cover every method, parameter, return value and error. Name the permission
the call needs, and what happens without it. A deprecation names its replacement first.

**The document itself.** Say who it is for in the first lines. Software does things. It does not
think, want or know.

## How to check

```bash
python3 scripts/check_output.py --style --profile google path/to/doc.md
```

It runs every house rule first. Then it adds `assets/style-words-google.tsv` and seven warnings:

- future tense and directional words
- heading case and heading periods
- spaced hyphens used as dashes, curly quotes and exclamation marks

The profile only adds warnings. The house rules still decide whether the file passes.

## What stays a judgement call

The checker counts and matches. These stay yours:

- Is each step one action, with the screen named first?
- Does every list and table have an introducing sentence?
- Did any "should" hide a requirement that must be a "must"?
- Did a Google rule cost the reader a fact? Then rule 9 wins. Keep the fact and rewrite the sentence.
