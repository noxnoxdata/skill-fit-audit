---
name: skill-fit-audit
description: Audits agent skills and skill libraries for contract, trigger, scope, cost, proof, safety, ownership, and overlap. Use when the user asks to audit, review, prune, or decide whether to keep a skill, or says "is this skill worth it", "why is my agent ignoring this skill", or "review this SKILL.md". Outputs a completed checklist and a decision per skill. Not a security scanner; use Socket, Vett, or skills-audit for that.
license: MIT
compatibility: Requires Python 3.9+ for the static audit script. No network access. Does not execute audited code.
metadata:
  author: noxnoxdata
  version: "0.1.1"
  status: experimental
  last_reviewed: "2026-10-18"
---

# Skill Fit Audit

Audit a skill library and produce a decision record.

Most audits answer "is it valid?" or "is it safe?" This one answers "does it earn its place?" It produces a completed checklist per skill, marks untested gates PENDING, and ends with one verdict: keep, revise, merge, retire, or delete.

## When to use

Use this skill when the user:

- Asks to audit, review, prune, clean up, or rationalize a skill library.
- Asks whether a skill is worth keeping.
- Asks why the agent ignores a skill, or picks the wrong one.
- Wants a repeatable review before publishing a skill.
- Inherits a library and needs to know what to keep.

## When not to use

- Malware, credential theft, or supply chain scanning. Use Socket, Vett, or `skills-audit`.
- Token budgets, trigger collisions, or CI gates across a large library. Use `skillaudit`.
- Creating a new skill. Use `skill-creator`.
- General code review. Use a code review skill.

## What you produce

Always produce four artifacts:

1. `checklist.md`: the blank reusable checklist.
2. `audit-report.md`: one completed card per skill, then the library summary.
3. `audit.json`: machine-readable results.
4. `behavioral-tests.md`: the exact prompts still to run.

If the user only asks about one skill, still produce the card for that skill. Do not answer with a score alone.

## Workflow

Copy this checklist and track progress:

```text
Audit progress:
- [ ] Step 1: Scope the audit
- [ ] Step 2: Read the skills
- [ ] Step 3: Run the static pass
- [ ] Step 4: Run or mark the behavioral pass
- [ ] Step 5: Decide and report
- [ ] Step 6: Verify the report
```

### Step 1: Scope the audit

Confirm what is being audited:

- One skill directory.
- A library directory.
- A specific `SKILL.md` file.

Ask only if the target is ambiguous. Do not scan the user's home directory unless they point at it.

### Step 2: Read the skills

For each skill, read:

- `SKILL.md` frontmatter and body.
- Any `scripts/`, `references/`, and `assets/`.
- The repository source, license, and last commit if available.

Do not execute audited scripts. Read them.

### Step 3: Run the static pass

Run the script when Python is available:

```bash
python scripts/audit.py <target> --out ./audit
```

It produces the four artifacts and fills the mechanical gates: contract, scope, cost, safety, ownership, and overlap.

Use `python scripts/audit.py <target> --checklist` to emit only the blank checklist.

If Python is unavailable, fill the same gates by hand using `references/CHECKLIST.md`. Do not skip a gate because it is inconvenient.

### Step 4: Run or mark the behavioral pass

Read `references/BEHAVIORAL-TESTS.md`.

For each skill, run:

- Three real prompts the skill should catch.
- Two near-miss prompts it should ignore.
- The same task with and without the skill.

Record the result in the card. If the tests were not run, write `PENDING`. Never mark a behavioral gate as passed without evidence.

### Step 5: Decide and report

Apply the decision rule below. Write one card per skill, then the library summary. Order the report by decision severity: BLOCK, DELETE, MERGE OR RETIRE, REVISE, KEEP.

### Step 6: Verify the report

Before finishing:

- Every finding cites a file, line, or metric.
- Every PENDING gate has the prompt that would close it.
- The library summary matches the cards.
- The JSON parses.
- No score appears without its card.

## The eight gates

| Gate | Question | Why it matters |
|---|---|---|
| 1. Contract | Is the name valid, and does the description say what it does and when to use it? | The description is the routing key. A vague one means the skill never fires or fires wrongly. |
| 2. Trigger | Does it catch three real prompts and ignore two near-misses? | A skill that fires on the wrong task is worse than no skill. |
| 3. Scope | Is it one workflow with at most three modules? | A five-job skill is five skills competing for one trigger. |
| 4. Cost | Is the description around 100 tokens and the body under 5k tokens and 500 lines? | The description loads at startup. The body loads on invocation. Both compete with everything else. |
| 5. Proof | Does a with and without test show a repeatable difference? | Without a paired test, you have a belief, not evidence. |
| 6. Safety | Are scripts reviewed, secrets absent, network calls pinned, and permissions least-privilege? | Skills can read files, run code, and change behavior. |
| 7. Ownership | Are owner, version, status, and last review recorded? | Unowned skills rot. You cannot review what you cannot identify. |
| 8. Overlap | Is the job unique, and is the boundary with adjacent skills explicit? | Two skills for one request confuse the router. |

The full rubric, with 0, 1, and 2 descriptors, is in `references/CHECKLIST.md`.

## The decision rule

Score each gate from 0 to 2. Maximum 16.

- **14 to 16:** keep.
- **11 to 13:** revise.
- **7 to 10:** merge or retire.
- **0 to 6:** delete.
- **Any 0 on Safety:** block. Fix before use.
- **No behavioral test:** maximum 12, so the skill cannot be kept. Mark it revise and list the missing prompts.

When two gates are PENDING, the practical bands are:

- **8 to 12 static:** revise.
- **5 to 7 static:** merge or retire.
- **0 to 4 static:** delete.

Report `known/12 static, 2 pending`. Do not inflate it to a 16-point score.

## Output contract

Use the exact templates in `assets/`:

- `assets/checklist-template.md` for the blank checklist.
- `assets/report-template.md` for the cards and summary.

Every card has:

- Skill name and path.
- Decision and reason.
- A table with gate, score, evidence, finding, and action.
- The behavioral prompts still to run, or the evidence that they passed.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "It is only one skill." | One skill still costs metadata on every request and can steal another skill's trigger. |
| "The description is fine." | Fine to you is not fine to a router choosing from 100 options. Test it with real prompts. |
| "We will test it later." | Later never comes. Mark it PENDING and do not call it keep. |
| "More skills means more capability." | More skills means more competition for attention. Focused beats exhaustive. |
| "It is safe because it is popular." | Popularity is not fit, and installs are not a security audit. |
| "The body is long but it only loads when used." | Then the body must be worth the invocation. Check that it is a workflow, not an essay. |
| "We can clean it up later." | The audit is the cleanup. Archive first, then test removal. |

## Red flags

- A description that says "helps with" anything.
- A body that is an essay with no steps or exit criteria.
- Five skills with overlapping descriptions.
- Scripts nobody has read.
- A skill with no owner, version, or review date.
- A "temporary" skill still installed a year later.
- A score with no evidence.

## Related tools

- `skillaudit` for per-turn budgets, trigger collisions, and CI gates.
- Socket, Vett, and `skills-audit` for malware and supply-chain scanning.
- `find-skills` for discovery.
- `skill-creator` for authoring and evals.

This skill is the decision layer. It does not replace any of them.

## Reference files

- `references/CHECKLIST.md`: the full eight-gate rubric.
- `references/BEHAVIORAL-TESTS.md`: the with and without protocol.
- `references/EVIDENCE.md`: the sources behind the gates.
- `references/EXAMPLE-AUDIT.md`: a completed card and library summary.
- `assets/checklist-template.md`: the blank checklist.
- `assets/report-template.md`: the report template.
