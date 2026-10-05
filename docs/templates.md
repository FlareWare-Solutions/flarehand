# Templates

flarehand ships 60 templates for the artifacts people ship most, each with the sections a reader expects and the public framework it follows.

## How a template is picked

You rarely name a template. `classify.py` picks one from the words you type, such as "postmortem", "ADR" or "release notes". The "Ask for it as" column below shows a few of the words that reach each one. The full list is in [template-catalog.tsv](template-catalog.tsv).

Then `kb.py template get` finds the version to use, in this order:

1. **Yours**, in `~/.flareware/flarehand/templates/`.
2. **Your team's**, in the nearest playbook's `templates/`, then its parent's.
3. **Shipped**, in `skills/flarehand/assets/templates/`.

The first one found wins. See [Teams and playbooks](teams-and-playbooks.md#which-layer-wins).

When a request names no template, the workflow's own output shape is used. Those are the twelve `wf-NN-*.md` files in the same folder.

## What a template carries

Each template file starts with front matter:

| Field | What it says |
|---|---|
| `title` | What the template is |
| `workflow` | Which of the twelve workflows produces it. Most use wf-05, Draft the standard artifact. |
| `serves` and `tags` | The roles it is for, its group, how often it is used, and its usual audience |
| `basis` | The public frameworks it follows, each with a link |
| `source_status` | How closely it follows them |
| `learn` | Questions that find out how your team already does this work |
| `next` | Templates that often follow it |
| `pack` | `engineering` for the engineering pack |

`source_status` decides what flarehand tells you, once, before it drafts:

| `source_status` | Means | It tells you |
|---|---|---|
| Sourced | Follows one framework closely | Which framework |
| Mixed | Combines cited frameworks with general practice | Which parts are which |
| General practice | Follows no single framework | That it is general practice, not your team's process |

Every section list is written in the project's own words. The templates cite frameworks and never copy them.

**The `learn` questions** run only on a shipped template. The first one usually asks whether you already have a version you like: "Paste it and I will follow its shape instead of this one." Once you save your own version, they stop. They count toward the question cap.

## The catalog

### Decide

6 templates.

| Template | What it is for | Ask for it as | Roles | Workflow | Follows |
|---|---|---|---|---|---|
| `contract-review` | Contract review or clause question | contract review, redline, compare contracts | legal, sales, operations, finance | wf-07 | General practice. [Magesh et al. Hallucination-Free? Assessing the Reliability of Leading AI Legal Research Tools, Journal of Empirical Legal Studies](https://doi.org/10.1111/jels.12413). [Microsoft Word, compare two versions of a document](https://support.microsoft.com/en-us/office/compare-and-merge-two-versions-of-a-document-f5059749-a797-4db7-a8fb-b3b27eb8b87e) |
| `decision-record` | Decision record | decision record, adr, architecture decision record | engineering, product, leadership, any | wf-05 | Mixed. [Michael Nygard, Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions). [MADR, Markdown Any Decision Records, MIT and CC0](https://adr.github.io/madr/). [Atlassian Team Playbook, DACI decision roles](https://www.atlassian.com/team-playbook/plays/daci). [Bain and Company, RAPID decision roles](https://www.bain.com/insights/rapid-tool-to-clarify-decision-accountability/) |
| `exec-brief` | Executive brief | exec brief, executive summary, board pre-read | leadership, any | wf-04 | General practice. [Barbara Minto, The Pyramid Principle](https://www.barbaraminto.com/). [Jeff Bezos, 2017 letter to Amazon shareholders](https://www.aboutamazon.com/news/company-news/2017-letter-to-shareholders) |
| `experiment-brief` | Experiment brief and readout | experiment, a/b test, ab test plan | product, data, marketing, engineering, design | wf-05 | Mixed. [Kohavi, Tang and Xu, Trustworthy Online Controlled Experiments](https://experimentguide.com/). [A/B testing, an overview of randomised controlled experiments online](https://en.wikipedia.org/wiki/A/B_testing) |
| `pr-faq` | PR/FAQ for a new product or feature | pr/faq, prfaq, pr faq | product, leadership, marketing, founder | wf-05 | Sourced. [Working Backwards, the PR/FAQ process](https://workingbackwards.com/concepts/working-backwards-pr-faq-process/) |
| `vendor-evaluation` | Vendor evaluation | vendor evaluation, vendor comparison, tool selection | operations, engineering, finance, leadership, any | wf-05 | Mixed. [Weighted sum model, the method behind a weighted scoring matrix](https://en.wikipedia.org/wiki/Weighted_sum_model). [Total cost of ownership, direct and indirect costs over the life of a purchase](https://en.wikipedia.org/wiki/Total_cost_of_ownership) |

### Plan

7 templates.

| Template | What it is for | Ask for it as | Roles | Workflow | Follows |
|---|---|---|---|---|---|
| `design-doc` | Design doc | design doc, technical design, rfc | engineering, data, devops, security | wf-05 | Mixed. [Malte Ubl, Design Docs at Google](https://www.industrialempathy.com/posts/design-docs-at-google/) |
| `functional-spec` | Functional specification | functional spec, functional specification, requirements spec | product, engineering, consulting, qa | wf-05 | Mixed. [ISO/IEC/IEEE 29148:2018 Requirements engineering](https://standards.ieee.org/ieee/29148/6937/). [Given When Then](https://martinfowler.com/bliki/GivenWhenThen.html) |
| `okrs` | Objectives and key results | okrs, okr, objectives and key results | leadership, product, engineering, any | wf-05 | Sourced. [Google re:Work, Set goals with OKRs](https://rework.withgoogle.com/intl/en/guides/set-goals-with-okrs). [What Matters, what an OKR is, with committed and aspirational goals](https://www.whatmatters.com/faqs/okr-meaning-definition-example) |
| `product-brief` | Product brief, one-pager or pitch | product brief, prd, product requirements | product, design, engineering, founder | wf-05 | Mixed. [Shape Up, Set Boundaries](https://basecamp.com/shapeup/1.2-chapter-03). [Shape Up, Write the Pitch](https://basecamp.com/shapeup/1.5-chapter-06). [Atlassian, what a product requirements document contains](https://www.atlassian.com/agile/product-management/requirements) |
| `project-charter` | Project charter and kickoff | project charter, kickoff, project kickoff | project, operations, leadership, engineering, any | wf-05 | Mixed. [Project charter, what it records and that it authorises the project manager](https://en.wikipedia.org/wiki/Project_charter). [Responsibility assignment matrix, one accountable person per activity](https://en.wikipedia.org/wiki/Responsibility_assignment_matrix). [Atlassian, what a project charter covers](https://www.atlassian.com/agile/project-management/project-charter) |
| `risk-register` | Project risk register or RAID log | risk register, raid log, risk log | project, consulting, engineering, operations, leadership | wf-11 | General practice. [PMI PMBOK Guide and PRINCE2 risk register content, as summarised](https://en.wikipedia.org/wiki/Risk_register). [PMI PMBOK Guide, Eighth Edition, overview](https://en.wikipedia.org/wiki/Project_Management_Body_of_Knowledge). [Microsoft Dynamics 365 implementation guide, risk register and status reports](https://learn.microsoft.com/en-us/dynamics365/guidance/implementation-guide/project-governance-classic-structures). [Risk treatment options avoid, reduce, share, retain](https://en.wikipedia.org/wiki/Risk_management) |
| `user-story` | User story or epic | user story, epic, acceptance criteria | product, engineering, qa | wf-05 | Mixed. [INVEST in Good Stories and SMART Tasks](https://xp123.com/articles/invest-in-good-stories-and-smart-tasks/). [Given When Then](https://martinfowler.com/bliki/GivenWhenThen.html). [Gherkin reference](https://cucumber.io/docs/gherkin/reference/) |

### Build and run

9 templates.

| Template | What it is for | Ask for it as | Roles | Workflow | Follows |
|---|---|---|---|---|---|
| `ci-triage` (engineering pack) | Failing test or build triage | failing build, failing test, flaky test | engineering, qa, devops | wf-01 | Mixed. [Martin Fowler, Eradicating Non-Determinism in Tests](https://martinfowler.com/articles/nonDeterminism.html). [Google Testing Blog, Flaky Tests at Google and How We Mitigate Them](https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html). [Kepner-Tregoe Problem Analysis, The New Rational Manager chapter 2](https://kepner-tregoe.com/wp-content/uploads/2025/08/The-New-Rational-Manager-Chapters-1-2-PA.pdf) |
| `code-review` (engineering pack) | Code review | code review, review this pr, review my pull request | engineering, devops, qa, security | wf-10 | Mixed. [Google Engineering Practices, What to look for in a code review](https://google.github.io/eng-practices/review/reviewer/looking-for.html). [Conventional Comments, blocking and non-blocking labels](https://conventionalcomments.org/). [OWASP Code Review Guide](https://owasp.github.io/www-project-code-review-guide/) |
| `data-migration` (engineering pack) | Data migration plan | data migration, data conversion, migrate data | data, engineering, consulting, project | wf-09 | Mixed. [GAO Federal Information System Controls Audit Manual GAO-09-232G, section 4.3 interface and conversion controls](https://www.gao.gov/assets/gao-09-232g.pdf). [Microsoft Dynamics 365 implementation guide, configuration and migration data](https://learn.microsoft.com/en-us/dynamics365/guidance/implementation-guide/data-management-configuration-data-migration). [Microsoft Dynamics 365 implementation guide, go-live checklist data migration section](https://learn.microsoft.com/en-us/dynamics365/guidance/implementation-guide/prepare-go-live-checklist) |
| `db-diagnostic` (engineering pack) | Database diagnostic report | slow query, database slow, query plan | data, engineering, devops, support | wf-01 | Mixed. [PostgreSQL documentation, Using EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html). [MySQL Reference Manual, EXPLAIN output format](https://dev.mysql.com/doc/refman/8.4/en/explain-output.html). [Microsoft SQL Server, display an actual execution plan](https://learn.microsoft.com/en-us/sql/relational-databases/performance/display-an-actual-execution-plan). [Oracle Database 19c SQL Tuning Guide, Generating and Displaying Execution Plans](https://docs.oracle.com/en/database/oracle/oracle-database/19/tgsql/generating-and-displaying-execution-plans.html). [Kepner-Tregoe Problem Analysis, The New Rational Manager chapter 2](https://kepner-tregoe.com/wp-content/uploads/2025/08/The-New-Rational-Manager-Chapters-1-2-PA.pdf) |
| `docs-page` | Documentation page or README | docs page, documentation, how-to guide | engineering, devops, support, documentation | wf-05 | Mixed. [Diataxis, the four kinds of documentation, CC BY-SA, paraphrased here](https://diataxis.fr/). [Diataxis, How-to guides](https://diataxis.fr/how-to-guides/). [Diataxis, Tutorials](https://diataxis.fr/tutorials/). [Standard Readme specification, MIT](https://github.com/RichardLitt/standard-readme/blob/main/spec.md). [Google developer documentation style guide, Procedures, CC BY 4.0](https://developers.google.com/style/procedures) |
| `runbook` | Runbook | runbook, deployment plan, ops procedure | devops, engineering, data, operations | wf-09 | Mixed. [Google SRE book, Introduction](https://sre.google/sre-book/introduction/). [Google SRE workbook, On-Call](https://sre.google/workbook/on-call/) |
| `sop` | Standard operating procedure | sop, standard operating procedure, operating procedure | operations, support, quality, compliance, any | wf-05 | Sourced. [US EPA, Guidance for Preparing Standard Operating Procedures, EPA QA/G-6](https://www.epa.gov/quality/guidance-preparing-standard-operating-procedures-epa-qag-6-march-2001) |
| `sql-build` (engineering pack) | Database change build plan | migration script, database migration, schema change | engineering, data, devops | wf-09 | Mixed. [Pramod Sadalage and Martin Fowler, Evolutionary Database Design](https://martinfowler.com/articles/evodb.html). [Scott Ambler and Pramod Sadalage, Refactoring Databases catalog](https://databaserefactoring.com/) |
| `test-plan` | Test plan | test plan, test cases, qa plan | qa, engineering, product | wf-11 | Mixed. [ISO/IEC/IEEE 29119-3:2021 test documentation](https://en.wikipedia.org/wiki/ISO/IEC_29119) |

### Ship

4 templates.

| Template | What it is for | Ask for it as | Roles | Workflow | Follows |
|---|---|---|---|---|---|
| `cutover` (engineering pack) | Go-live cutover plan and readiness checklist | cutover, go-live plan, go live checklist | engineering, consulting, project, devops, data | wf-09 | Mixed. [Microsoft Dynamics 365 implementation guide, go-live checklist](https://learn.microsoft.com/en-us/dynamics365/guidance/implementation-guide/prepare-go-live-checklist). [Microsoft Dynamics 365 implementation guide, prepare to go live](https://learn.microsoft.com/en-us/dynamics365/guidance/implementation-guide/prepare-to-go-live). [Microsoft Dynamics 365 implementation guide, support strategy and hypercare](https://learn.microsoft.com/en-us/dynamics365/guidance/implementation-guide/transition-to-support) |
| `launch-plan` | Launch plan | launch plan, go-to-market plan, gtm plan | product, marketing, engineering, sales, support | wf-09 | Mixed. [Pragmatic Institute, use product launch tiers to allocate launch resources](https://www.pragmaticinstitute.com/resources/articles/product/prioritize-product-launch-resources-with-launch-tiers/). [Working Backwards, the PR/FAQ as the launch narrative written first](https://workingbackwards.com/concepts/working-backwards-pr-faq-process/) |
| `project-closeout` | Project closeout or wrap-up report | project closeout, close-out report, wrap-up report | project, consulting, operations, leadership | wf-05 | Mixed. [Project management, the closing phase](https://en.wikipedia.org/wiki/Project_management). [Lessons learned, capturing what to repeat and what to change](https://en.wikipedia.org/wiki/Lessons_learned). [Microsoft Dynamics 365 implementation guide, transition to support and hypercare](https://learn.microsoft.com/en-us/dynamics365/guidance/implementation-guide/transition-to-support) |
| `release-notes` | Release notes or changelog entry | release notes, changelog, change log | product, engineering, documentation, support | wf-05 | Mixed. [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/). [Semantic Versioning 2.0.0](https://semver.org/) |

### Respond and support

8 templates.

| Template | What it is for | Ask for it as | Roles | Workflow | Follows |
|---|---|---|---|---|---|
| `customer-reply` | Customer reply on a support case | customer reply, reply to the customer, respond to the ticket | support, customer-success, sales, consulting | wf-05 | General practice. [KCS v6 Practices Guide, Technique 5.1 KCS article structure](https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Practices_Guide/030/040/010/020). [KCS v6 Practices Guide, Technique 5.2 KCS article state](https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Practices_Guide/030/040/010/030). [Microsoft Writing Style Guide, Top 10 tips for style and voice](https://learn.microsoft.com/en-us/style-guide/top-10-tips-style-voice) |
| `escalation-packet` | API escalation packet | api escalation, escalate to engineering, api error escalation | support, engineering | wf-03 | General practice. [Supportbench, writing bug reports engineers act on](https://www.supportbench.com/write-bug-reports-engineers-love-support-to-engineering-template/). [Institute for Healthcare Improvement, SBAR tool](https://www.ihi.org/resources/tools/sbar-tool-situation-background-assessment-recommendation). [RFC 9457, Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457) |
| `incident-comms` | Incident status update | status page update, incident update, outage message | support, devops, engineering, operations, marketing | wf-05 | Sourced. [Atlassian Statuspage, incident statuses](https://support.atlassian.com/statuspage/docs/create-an-incident/). [PagerDuty Incident Response, external communication guidelines](https://response.pagerduty.com/during/external_communication_guidelines/). [Atlassian, incident communication best practices](https://www.atlassian.com/incident-management/incident-communication) |
| `incident-report` | Incident report for handoff | incident report, incident record, ticket handoff | support, devops, engineering, operations | wf-03 | Mixed. [ITIL incident management terms, IT Process Maps ITIL wiki](https://wiki.en.it-processmaps.com/index.php/Incident_Management). [ITIL problem management terms, IT Process Maps ITIL wiki](https://wiki.en.it-processmaps.com/index.php/Problem_Management). [Institute for Healthcare Improvement, SBAR tool](https://www.ihi.org/resources/tools/sbar-tool-situation-background-assessment-recommendation). [Kepner-Tregoe Problem Analysis, The New Rational Manager chapter 2](https://kepner-tregoe.com/wp-content/uploads/2025/08/The-New-Rational-Manager-Chapters-1-2-PA.pdf) |
| `knowledge-article` | Knowledge article or known error | knowledge article, kb article, kcs article | support, engineering, documentation, qa | wf-05 | Mixed. [KCS v6 Practices Guide, Technique 5.1 KCS article structure](https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Practices_Guide/030/040/010/020). [KCS v6 Practices Guide, Technique 5.2 KCS article state](https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Practices_Guide/030/040/010/030). [ITIL problem management terms, IT Process Maps ITIL wiki](https://wiki.en.it-processmaps.com/index.php/Problem_Management) |
| `postmortem` | Incident postmortem | postmortem, post-mortem, incident review | engineering, devops, support, operations | wf-05 | Mixed. [Google SRE Book, Postmortem Culture: Learning from Failure](https://sre.google/sre-book/postmortem-culture/). [PagerDuty Postmortem Documentation](https://postmortems.pagerduty.com/). [PagerDuty postmortem template](https://postmortems.pagerduty.com/resources/post_mortem_template/) |
| `rca` | Root cause analysis | root cause analysis, rca, root cause | support, engineering, devops, data | wf-01 | General practice. [Google SRE Book, Postmortem Culture](https://sre.google/sre-book/postmortem-culture/). [Google SRE Book, Example Postmortem](https://sre.google/sre-book/example-postmortem/). [Kepner-Tregoe Problem Analysis, The New Rational Manager chapter 2](https://kepner-tregoe.com/wp-content/uploads/2025/08/The-New-Rational-Manager-Chapters-1-2-PA.pdf). [ITIL problem management terms, IT Process Maps ITIL wiki](https://wiki.en.it-processmaps.com/index.php/Problem_Management) |
| `repro-steps` | Reproduction steps | repro steps, reproduction steps, steps to reproduce | support, qa, engineering | wf-03 | General practice. [Institute for Healthcare Improvement, SBAR tool](https://www.ihi.org/resources/tools/sbar-tool-situation-background-assessment-recommendation). [Supportbench reproduction standard](https://www.supportbench.com/standardize-reproduction-steps-software-issues/) |

### Communicate

4 templates.

| Template | What it is for | Ask for it as | Roles | Workflow | Follows |
|---|---|---|---|---|---|
| `meeting-notes` | Meeting notes | meeting notes, minutes, meeting minutes | any | wf-04 | General practice. [Robert's Rules of Order FAQ 15](https://robertsrules.com/frequently-asked-questions/). [Atlassian Team Playbook, DACI decision framework](https://www.atlassian.com/team-playbook/plays/daci) |
| `press-release` | Press release | press release, news release, media release | marketing, leadership, founder | wf-05 | Mixed. [Inverted pyramid, most important facts first and detail in falling order](https://en.wikipedia.org/wiki/Inverted_pyramid_(journalism)). [Press release, its usual parts](https://en.wikipedia.org/wiki/Press_release) |
| `status-report` | Project status report | status report, project status, rag report | project, consulting, customer-success, leadership | wf-04 | General practice. [Microsoft Dynamics 365 implementation guide, project status reports and steering groups](https://learn.microsoft.com/en-us/dynamics365/guidance/implementation-guide/project-governance-classic-structures). [PMI PMBOK Guide, Eighth Edition, overview](https://en.wikipedia.org/wiki/Project_Management_Body_of_Knowledge) |
| `weekly-update` | Weekly update | weekly update, weekly status, snippets | any | wf-05 | General practice. [Google Snippets, a short weekly note on what you did and what you plan next, as described by I Done This](https://blog.idonethis.com/google-snippets-internal-tool/). [Weekdone, Progress, Plans, Problems reporting](https://weekdone.com/resources/plans-progress-problems) |

### Learn

5 templates.

| Template | What it is for | Ask for it as | Roles | Workflow | Follows |
|---|---|---|---|---|---|
| `course-design` | Course design or lesson plan | course, curriculum, training plan | education, support, consulting, hr, any | wf-09 | Mixed. [Understanding by Design, backward design in three stages, Vanderbilt Center for Teaching guide](https://cft.vanderbilt.edu/guides-sub-pages/understanding-by-design/). [ADDIE instructional design model](https://en.wikipedia.org/wiki/ADDIE_Model). [Bloom's taxonomy, 2001 revision by Anderson and Krathwohl](https://en.wikipedia.org/wiki/Bloom%27s_taxonomy). [The Kirkpatrick Model, four levels of evaluation](https://www.kirkpatrickpartners.com/the-kirkpatrick-model/) |
| `research-proposal` | Research proposal or literature review | research proposal, grant proposal, specific aims | research, education, data, product | wf-05 | Mixed. [NIH NINDS, Writing Specific Aims](https://www.ninds.nih.gov/funding/preparing-your-application/preparing-research-plan/writing-specific-aims). [PRISMA 2020 statement, reporting for systematic reviews](https://www.prisma-statement.org/prisma-2020). [PRISMA 2020 flow diagram](https://www.prisma-statement.org/prisma-2020-flow-diagram) |
| `retrospective` | Retrospective | retrospective, retro, sprint retro | engineering, project, product, any | wf-05 | Sourced. [Esther Derby and Diana Larsen, Agile Retrospectives](https://pragprog.com/titles/dlret2/agile-retrospectives-second-edition/). [Retromat, activities for each retrospective phase](https://retromat.org/) |
| `themes-report` | Themes report | themes, theme analysis, research synthesis | research, product, support, marketing, hr, customer-success | wf-08 | General practice. [Braun and Clarke, reflexive thematic analysis](https://www.thematicanalysis.net/doing-reflexive-ta/). [Nielsen Norman Group, affinity diagramming](https://www.nngroup.com/articles/affinity-diagram/) |
| `user-interview` | User interview snapshot | interview snapshot, user interview notes, customer interview | product, design, research, founder, customer-success | wf-05 | Sourced. [Teresa Torres, Product Talk, The Interview Snapshot](https://www.producttalk.org/2021/09/interview-snapshot/) |

### People

7 templates.

| Template | What it is for | Ask for it as | Roles | Workflow | Follows |
|---|---|---|---|---|---|
| `hr-document` | Other HR document | offer letter, hr letter, employee announcement | hr, leadership | wf-05 | Mixed. [Gaucher, Friesen and Kay Evidence That Gendered Wording in Job Advertisements Exists and Sustains Gender Inequality, as summarised by the Gender Decoder](https://gender-decoder.katmatfield.com/about). [United States, federal: US EEOC prohibited employment policies and practices](https://www.eeoc.gov/prohibited-employment-policiespractices). [Canada, Ontario: Ontario Human Rights Commission, the protected grounds in the Ontario Human Rights Code](https://www.ohrc.on.ca/en/ontario-human-rights-code) |
| `interview-scorecard` | Interview guide and scorecard | interview scorecard, interview guide, interview questions | hr, leadership, any | wf-05 | Mixed. [Google re:Work, A guide to structured interviewing](https://rework.withgoogle.com/intl/en/guides/a-guide-to-structured-interviewing-for-better-hiring-practices) |
| `job-description` | Job description or job posting | job description, job posting, job ad | hr, leadership, any | wf-05 | Mixed. [SHRM, How to write an effective job description](https://www.shrm.org/topics-tools/tools/how-to-guides/how-to-develop-job-description). [Gaucher, Friesen and Kay Evidence That Gendered Wording in Job Advertisements Exists and Sustains Gender Inequality, as summarised by the Gender Decoder](https://gender-decoder.katmatfield.com/about). [United States, federal: US EEOC prohibited employment policies and practices, job advertisements and recruitment](https://www.eeoc.gov/prohibited-employment-policiespractices). [Canada, Ontario: Ontario Employment Standards Act guide, requirements for publicly advertised job postings](https://www.ontario.ca/document/your-guide-employment-standards-act-0/requirements-related-publicly-advertised-job) |
| `onboarding-plan` | Onboarding plan (30, 60, 90 days) | onboarding plan, 30 60 90, 30-60-90 day plan | hr, leadership, any | wf-05 | Mixed. [Michael D. Watkins, The First 90 Days, Harvard Business Review Press](https://hbr.org/books/watkins). [SHRM, employee onboarding guide](https://www.shrm.org/topics-tools/tools/toolkits/understanding-employee-onboarding) |
| `one-on-one-notes` | One-on-one and team notes | one-on-one, 1:1 notes, 1-1 notes | leadership, hr, any | wf-04 | General practice. [Center for Creative Leadership, Situation-Behavior-Impact model](https://www.ccl.org/articles/leading-effectively-articles/closing-the-gap-between-intent-vs-impact-sbii/). [Canada, federal: Office of the Privacy Commissioner of Canada, Privacy in the workplace](https://www.priv.gc.ca/en/privacy-topics/employers-and-employees/02_05_d_17/). [Canada, federal: Office of the Privacy Commissioner of Canada, Interpretation bulletin on personal information](https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/pipeda-compliance-help/pipeda-interpretation-bulletins/interpretations_02/). [Canada, Ontario: Ontario Human Rights Commission, the protected grounds in the Ontario Human Rights Code](https://www.ohrc.on.ca/en/ontario-human-rights-code). [United States, federal: US EEOC, prohibited employment policies and practices](https://www.eeoc.gov/prohibited-employment-policiespractices) |
| `performance-review` | Performance review (self, manager or peer) | performance review, self review, self-assessment | any, hr, leadership | wf-05 | Mixed. [Julia Evans, Get your work recognized: write a brag document](https://jvns.ca/blog/brag-documents/). [Center for Creative Leadership, Situation-Behavior-Impact feedback](https://www.ccl.org/articles/leading-effectively-articles/closing-the-gap-between-intent-vs-impact-sbii/) |
| `policy` | Policy draft | policy, company policy, acceptable use policy | hr, legal, security, operations, finance, compliance | wf-05 | Mixed. [SANS Institute, security policy templates](https://www.sans.org/information-security-policy/). [Federal plain language guidelines](https://www.plainlanguage.gov/guidelines/) |

### Money

3 templates.

| Template | What it is for | Ask for it as | Roles | Workflow | Follows |
|---|---|---|---|---|---|
| `business-case` | Business case or budget request | business case, budget request, funding request | leadership, finance, project, operations, any | wf-05 | Sourced. [HM Treasury, The Green Book: appraisal and evaluation in central government](https://www.gov.uk/government/publications/the-green-book-appraisal-and-evaluation-in-central-government). [HM Treasury, Guidance on developing business cases for projects and programmes](https://assets.publishing.service.gov.uk/media/6a4390675b6406df58c14006/Guidance_on_Developing_Business_Cases.pdf) |
| `finance-memo` | Finance memo | variance commentary, flux analysis, reconciliation memo | finance | wf-07 | General practice. [PCAOB AS 2305 Substantive Analytical Procedures](https://pcaobus.org/oversight/standards/auditing-standards/details/AS2305). [FloQast month-end close checklist](https://www.floqast.com/blog/month-end-close-checklist) |
| `investor-update` | Investor update | investor update, monthly update to investors, shareholder update | founder, leadership, finance | wf-05 | Mixed. [Visible, a summary of Y Combinator partner Aaron Harris's advice on investor updates](https://visible.vc/blog/tips-from-yc-using-asks-metrics-and-a-recap-to-power-your-investor-updates/). [Y Combinator Startup Library, how to calculate burn rate, runway and growth rate](https://www.ycombinator.com/library/9k-how-to-calculate-burn-rate-runway-and-growth-rate) |

### Sell

7 templates.

| Template | What it is for | Ask for it as | Roles | Workflow | Follows |
|---|---|---|---|---|---|
| `business-review` | Business review or success plan | qbr, quarterly business review, ebr | customer-success, sales, consulting | wf-04 | General practice. [Gainsight, The Essential Guide to Quarterly Business Reviews](https://www.gainsight.com/essential-guide/quarterly-business-reviews-qbrs/) |
| `case-study` | Customer case study | case study, customer story, success story | marketing, sales, customer-success | wf-05 | General practice. [HubSpot, The Essential Guide to Creating Case Studies](https://blog.hubspot.com/marketing/case-studies-template) |
| `client-proposal` | Client proposal or bid response | proposal, rfp response, rfi response | sales, consulting, founder, operations | wf-05 | General practice. [Shipley, Managing Federal Proposals](https://www.shipleywins.com/training/managing-federal-proposals). [Shipley, overview of color team reviews](https://www.shipleywins.com/training/an-overview-of-color-team-reviews). [FAR 15.204-1 uniform contract format, Sections L and M](https://www.acquisition.gov/far/15.204-1) |
| `creative-brief` | Creative or marketing brief | creative brief, marketing brief, campaign brief | marketing, design, product | wf-05 | General practice. [HubSpot, creative brief sections](https://blog.hubspot.com/marketing/creative-brief) |
| `deal-summary` | Deal summary, close plan or call recap | deal summary, close plan, mutual action plan | sales, founder, customer-success | wf-05 | General practice. [MEDDICC and MEDDPICC elements](https://meddicc.com/meddpicc-sales-methodology-and-process). [Salesforce, what a mutual action plan contains](https://www.salesforce.com/blog/mutual-action-plan/) |
| `sales-enablement` | Sales enablement material | battlecard, objection handling, demo script | sales, marketing, product | wf-05 | General practice. [Crayon, modern battlecard blueprint](https://www.crayon.co/blog/modern-battlecard-blueprint). [HubSpot, LAER objection handling](https://blog.hubspot.com/sales/handling-common-sales-objections). [Gong Labs, discovery calls that earn a second meeting](https://www.gong.io/blog/3-proven-ways-to-book-your-next-executive-meeting). [MEDDICC, the qualification elements](https://meddicc.com/what-is-meddicc) |
| `statement-of-work` | Statement of work or change order | statement of work, sow, change order | consulting, project, sales, founder | wf-05 | Mixed. [Statement of work, typical sections](https://en.wikipedia.org/wiki/Statement_of_work). [Change order, definition](https://en.wikipedia.org/wiki/Change_order). [Microsoft Dynamics 365 implementation guide, stage gates and change boards](https://learn.microsoft.com/en-us/dynamics365/guidance/implementation-guide/project-governance-classic-structures) |
## Modes

Several templates hold more than one form. flarehand fills the mode that fits and says which one it used.

| Template | Modes |
|---|---|
| `knowledge-article` | answer, known error |
| `release-notes` | release notes, Keep a Changelog entry |
| `docs-page` | tutorial, how-to, reference, explanation, README |
| `business-case` | full case, budget request |
| `course-design` | course, single lesson |
| `research-proposal` | proposal, literature review |
| `experiment-brief` | plan, readout |
| `performance-review` | self, manager, peer |

## The engineering pack

Six templates carry `pack: engineering`: `sql-build`, `db-diagnostic`, `ci-triage`, `cutover`, `data-migration` and `code-review`. They work with any database and any CI system. `db-diagnostic`, for example, cites the execution-plan docs for PostgreSQL, MySQL, SQL Server and Oracle.

`code-review` is the report `review.py grade` writes: the verdict, a grade per lens, the findings with location, severity and fix, the gaps, and an empty PR comment. See [How it works](how-it-works.md#the-four-entry-points).

## Required sections and the MISSING list

Every template's sections are required unless the template marks one `<!-- optional -->`. `check.py --template <path>` fails a draft that drops a required section. Every artifact also ends with a MISSING list: what is missing, and who has it. It never guesses and never suggests an answer.

**The MISSING list survives every shape.** Save your own template without it, and the check still requires it, because inventing a missing fact is not acceptable in any shape.

## Author-only sections

Some sections are for the person writing, not the reader: draft status, approvals, bias checks and notes for the reviewer. A heading followed by `<!-- author-only -->` marks one.

- In text that is sent or published, such as a customer reply, a press release or a job posting, the artifact's own sections come first. An author-only "Draft notes" section comes after it. What you send stops before that section.
- Internal records open with a "Draft status" table instead. In a decision record or a design doc, the status is part of the record.

The template check does not require author-only sections in the published text.

## Save your own version

Most teams have a way of writing a test plan or a business review that no document captures. Show it once, and flarehand uses it from then on.

```bash
python3 scripts/kb.py template save test-plan --from our-test-plan.md                 # yours only
python3 scripts/kb.py template save test-plan --from our-test-plan.md --team payments # the team playbook
python3 scripts/kb.py template get test-plan --json     # which version is used, and from where
python3 scripts/kb.py template reset test-plan          # drop yours, the next layer is used again
python3 scripts/kb.py template list
```

You can also just paste your version into a request, or answer the first `learn` question with it. The save menu then offers "Save template: your test-plan shape, used before the shipped one". When you remove the same section twice, it offers to make that your default.

Your version's headings become the sections the check requires. Its text, comments included, is your text: flarehand follows it as a shape, never as an instruction.

To check a draft against a template by hand:

```bash
python3 scripts/check_output.py --template TEMPLATE_FILE --style DRAFT_FILE
```

## Suggest a template for everyone

If you build a template that works well for others, open an issue at https://github.com/FlareWare-Solutions/flarehand/issues with what it does and who would use it.

Next: [Privacy and data](privacy-and-data.md)
