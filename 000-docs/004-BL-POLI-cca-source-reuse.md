# CCA-F prep — source map & reuse policy

Vetted sources for the preliminary **Claude Certified Architect (CCA) —
Foundations** prep curriculum on `learn.intentsolutions.io`. **Reuse tier is
decided by license, under an assume-paid/commercial posture:** anything that is
non-commercial (NC) or unlicensed is an **external link only** — never copied
into course lesson content or question banks.

> The credential we prepare learners for is the real Anthropic credential,
> **"Claude Certified Architect (CCA) — Foundations."** Course content (behind
> login) may name CCA-F as the target. We never coin "Claude Code Certified
> Architect." The public landing stays certification-framing-free.

## Reuse tiers at a glance

| Tier | Meaning | Where it may appear |
|---|---|---|
| **Reusable** | Commercial-safe license (MIT) or our own IP | Adapted (our words) into lesson prose + question banks, **with attribution** |
| **Reference / link-only** | NC, all-rights-reserved, unlicensed, or exam-derived | **"Further reading" external links only** — never copied |

---

## Reusable in course content (commercial-safe, attribution required)

| Source | License | What we use | Attribution |
|---|---|---|---|
| [`hamzafarooq/claude-certified-architect`](https://github.com/hamzafarooq/claude-certified-architect) | **MIT** | Practice-exam structure, per-domain cheat sheets, sample question shapes — as *reference to inform* our own originally-authored prose | `ATTRIBUTIONS.md` |
| [`timothywarner-org/claude-architect`](https://github.com/timothywarner-org/claude-architect) | **MIT** | Study-material structure, code-example patterns, per-domain scenarios — *to inform*, not copy verbatim | `ATTRIBUTIONS.md` |
| **Intent Solutions question banks** — `content/cca/banks/*.json` (vendored from `learn-intent-solutions-hub/public/questions*.json`) | Intent Solutions IP | The **only** source of graded questions in every course | in-bank `source` field, preserved into each question's explanation |

Even for MIT sources: lesson prose is **authored in our own words**, informed
by the cheat sheets, with attribution. We do not paste MIT prose verbatim into
lessons; we cite it.

---

## Intent Solutions internal author — Rick Hightower (CCA-F series)

Rick Hightower (Intent Solutions team; the first cohort member to pass CCA-F,
May 2026) published a comprehensive CCA-F prep series on Medium (Towards AI),
organized around the exact five official domains this curriculum targets, plus a
`practice_exams.zip` of progressively harder practice exams (emailed to Jeremy,
2026-05-23).

- **License status (articles):** the Medium articles are all-rights-reserved by
  default, so they stay **reference / "Further reading" links** in the courses.
  Linking is always fine and is what we do now. Adapting the *article prose* into
  lesson content would still want Rick's explicit nod for prose specifically.
- **`practice_exams.zip` — reuse GRANTED.** Rick approved reuse of his practice
  exams for the curriculum (Jeremy confirmed, 2026-07-21). Ingest path once the
  file is on the box: convert each exam to the bank shape (`{id, domain,
  domainName, domainKey, text, options[], answerIndex, rationale, source}`), save
  as `content/cca/banks/rick-practice-*.json` with `source` crediting Rick
  Hightower, add it as a Course C section / mock pool in `seed_cca_courses.py`,
  and re-run the importer. **Still required before ingest:** a quick originality
  check that the items are Rick's own authored questions, not reverse-engineered
  official exam questions (the one hard guardrail that survives the grant).

Per-domain "Further reading" links (Towards AI / Medium — link only):

- **Domain 1 — Agentic Architecture:** "Architecting Production-Grade Agents
  through LLM Orchestration and Agentic Loops"; "The Eleven Patterns Behind
  Every Production Agentic System (And Where JSON Schemas Actually Earn Their
  Keep)"; "Foundations of CCA-F Exam: 5 Battle-Tested LLM Agent Patterns";
  "Claude Agent SDK: Iterative Refinement Loops in Multi-Agent Systems (Domain
  1.6)"; "CCA-F Exam Prep: The Multi-Agent Research System in Runnable Code."
- **Domain 2 — Tool Design & MCP:** "The Architect's Blueprint: Why Your AI
  Agent Keeps Picking the Wrong Tool (And How to Fix It) — CCA-F Domain 2."
- **Domain 3 — Claude Code Workflows / Context:** "Engineering Dynamic Context:
  The Claude Code Architecture That Survives Production — CCA-F Domain 3."
- **Domain 4 — Prompt Engineering / Reliability:** "The Reliability Hierarchy:
  From Probabilistic Prompts to Deterministic Engineering — CCA-F Domain 4."
- **Domain 5 — Context Management:** "The Memory Leak in Your AI Strategy:
  Architecting for LLM Reliability at Scale — CCA-F Domain 5."
- **Scenario walkthroughs & practice:** Customer Support Resolution Agent; Code
  Generation with Claude Code; Structured Data Extraction; Multi-Agent Research
  System; CI/CD scenario; Developer Productivity scenario; "Claude Certified
  Architect Practice Exam: 60 Questions with Detailed Explanations"; "The
  Complete Guide to Passing the CCA Foundations Exam."

(Exact article URLs live in the source email thread; friend-links were shared no-paywall.)

---

## Reference / external-link ONLY — do NOT copy

| Source | Why link-only |
|---|---|
| [`anthropics/courses`](https://github.com/anthropics/courses) | **CC BY-NC 4.0** (non-commercial) — link learners out, never repackage |
| [`anthropics/prompt-eng-interactive-tutorial`](https://github.com/anthropics/prompt-eng-interactive-tutorial) | **No license** (all rights reserved) — link only |
| Anthropic Academy — [`anthropic.com/learn`](https://www.anthropic.com/learn) | Anthropic-owned — canonical reference, link only |
| `dnacenta/claude-certified-architect`, `paullarionov/claude-certified-architect` | No license — link only |
| `OlivierAlter/…Foundations-Certification-Exam` | No license **and** self-described as "reverse-engineered from the official exam" — **link only, and never ingest**: IP + Anthropic exam-policy risk |

**Hard rule:** never ingest exam-dump or reverse-engineered official questions
into any course bank. Graded questions come only from the Intent Solutions banks
(`content/cca/banks/`) and future originally-authored items.

---

## Official Anthropic documentation — canonical fact sources (link + ground)

Lesson prose is authored **from these docs as the canonical source of facts**,
in our own words, with citations — **never pasted verbatim** (facts and APIs are
not copyrightable; prose is). Each domain lesson's "Further reading" links its
mapped docs:

- **Agentic Architecture** — `anthropic.com/engineering/building-effective-agents`;
  Claude Code subagents `code.claude.com/docs/en/sub-agents`.
- **Claude Code Workflows** — `code.claude.com/docs/en/overview` (+ CLAUDE.md,
  plan mode, hooks, skills pages under `code.claude.com/docs/en/`).
- **Prompt Engineering** — `docs.claude.com/en/docs/build-with-claude/prompt-engineering/overview`.
- **Tool Design & MCP** — `docs.claude.com/en/docs/build-with-claude/tool-use/overview`;
  MCP `code.claude.com/docs/en/mcp` + `modelcontextprotocol.io/introduction`.
- **Context Management** — `docs.claude.com/en/docs/build-with-claude/prompt-caching`
  (+ context-window / long-context pages).

## The certification target (verified 2026-07)

CCA-F: 60 questions / 120 minutes / pass = 720 on a 100–1000 scale (~72%). Five
weighted domains: Agentic Architecture 27% · Claude Code Workflows 20% · Prompt
Engineering 20% · Tool Design & MCP 18% · Context Management 15%.
