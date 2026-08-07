# Attributions — CCA-F prep curriculum

The lesson prose in `cca/lessons/` is originally authored by Intent
Solutions. Where it was *informed by* MIT-licensed open-source study materials,
those projects are credited below per their license terms. No MIT-licensed prose
is copied verbatim; we cite the projects as references that informed structure
and coverage. Graded questions come from `cca/banks/` — some authored in-house,
some **contributed by named authors and used under a permission grant**. See
"Question banks" below; the two are licensed differently and the difference
matters.

---

## hamzafarooq/claude-certified-architect — MIT License

Practice-exam structure, per-domain cheat sheets, and sample question shapes
informed the organization of our lessons and practice sections.

Repository: https://github.com/hamzafarooq/claude-certified-architect

```
MIT License

Copyright (c) hamzafarooq and contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

> Verify the exact copyright line against the upstream `LICENSE` file before any
> public release; the notice above reproduces the standard MIT terms the project
> is published under.

---

## timothywarner-org/claude-architect — MIT License

Study-material structure, code-example patterns, and per-domain scenarios
informed our lesson coverage.

Repository: https://github.com/timothywarner-org/claude-architect

```
MIT License

Copyright (c) timothywarner-org and contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

> Verify the exact copyright line against the upstream `LICENSE` file before any
> public release.

---

## Question banks

Not every bank is ours, and the distinction is a licensing one — so it is stated
here rather than inferred from a filename.

Every question in every bank carries its own `source` field, which the importer
appends to the question's explanation. Attribution therefore reaches the learner
in the UI rather than living only in a file header, and a bank cannot be rendered
with its credit stripped.

### Intent Solutions banks — our IP

`questions.json`, `questions-associate.json`, `questions-developer.json`,
`questions-architect-professional.json` are Intent Solutions IP, authored
in-house from the official Exam Guide blueprint. No question is reproduced from
Anthropic's exam, its published samples, or any third-party bank.

### Contributed banks — the author's work, used with permission

These are **not** Intent Solutions IP. Each author retains their rights; we use
the work under a permission grant recorded in the bank's own `source` field, and
credit is a condition of that grant. Do not merge a contributed bank into an
in-house one, and do not strip or rewrite its `source`.

| Bank | Author | Grant |
|---|---|---|
| `rick-practice-exams.json` | Rick Hightower — Intent Solutions team, first cohort member to pass CCA-F | Reuse granted by Rick + Jeremy, 2026-07-21 |
| `matthew-purcell-practice-exams.json` | Matthew Purcell — community author, sat and passed CCAO-F ([linkedin.com/in/purcellmatthew](https://linkedin.com/in/purcellmatthew)) | Reuse granted by Matthew + Jeremy, 2026-08-06, on condition of credit |

**Matthew Purcell — CCAO-F practice set.** A 60-item practice exam written
against the *public* CCAO-F Exam Guide v1.0 (July 2026) and its blueprint
objectives, matched to the live exam's item count and domain weights. His own
notice travels with the bank in `authorDisclaimer` and must be carried into any
surface that presents it: these are original questions, **not** actual exam
content, **not** drawn from the live item bank, and they reproduce no question
encountered on the exam. Exam content is confidential and NDA-protected. No
practice set guarantees a pass.

Adding another contributed bank: obtain explicit permission first, record it in
the bank's `source` with a date, add a row above, and keep the evidence of that
permission with whoever obtained it.

## Official Anthropic documentation

Facts and APIs described in the lessons are grounded in Anthropic's official
documentation (`docs.claude.com`, `code.claude.com`, `anthropic.com`). These are
cited as canonical references in each lesson's "Further reading"; no documentation
prose is reproduced verbatim.
