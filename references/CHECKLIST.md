# The Skill Fit Checklist

Version 0.1.0. Owner: noxnoxdata. Review monthly.

This is the full rubric behind `skill-fit-audit`.

Use it to decide whether a skill earns its place. Not whether it is interesting. Not whether it is safe. Whether it improves the agent on a real task, at a cost you can defend.

## Two passes

**Static pass.** Read the files. Checks contract, scope, cost, safety flags, ownership, and overlap. The script fills these gates.

**Behavioral pass.** Run the skill. Checks trigger and proof. The agent runs these with the protocol in `BEHAVIORAL-TESTS.md`.

A skill cannot be kept without the behavioral pass. If it was not run, the gate is `PENDING` and the maximum score is 12.

## The eight gates

### 1. Contract

**Question:** Is the name valid, and does the description say what it does and when to use it?

**Why it matters:** The name and description are loaded at startup for every installed skill. The description is the routing key. A vague description means the skill is never selected, or is selected for the wrong task.

| Score | Descriptor |
|---|---|
| 0 | Missing `name`; invalid name; name does not match the folder; missing description; description over 1,024 characters. |
| 1 | Valid but vague; no "use when" cue; under 80 characters; no trigger words a real user would type. |
| 2 | Valid name; specific description; says what it does and when to use it; includes trigger words; under 1,024 characters. |

**Evidence:** name, folder, description length, presence of a when cue.

### 2. Trigger

**Question:** Does it catch three real prompts and ignore two near-misses?

**Why it matters:** A skill that fires on the wrong task is worse than no skill. It steals the request from the skill that should have handled it.

| Score | Descriptor |
|---|---|
| 0 | No tests run; or fails two or more should-trigger prompts; or fires on two or more near-misses. |
| 1 | Catches the main prompt but misses variants; or over-fires on one near-miss. |
| 2 | Catches three real prompts; ignores two near-misses; no prompt changes were needed. |

**Evidence:** the five prompts and the observed behavior.

### 3. Scope

**Question:** Is it one workflow with at most three modules?

**Why it matters:** A five-job skill is five skills competing for one trigger. The agent has to guess which job you meant.

| Score | Descriptor |
|---|---|
| 0 | Multiple unrelated jobs; kitchen sink; no clear workflow. |
| 1 | One job but bloated with reference material; or the boundary with adjacent skills is unclear. |
| 2 | One workflow; at most three modules; clear steps; a defined exit or verification. |

**Evidence:** number of H2 sections, body size, workflow steps.

**Note:** This gate is a heuristic in the static pass. The agent must confirm the scope by reading the body.

### 4. Cost

**Question:** Is the description around 100 tokens and the body under 5,000 tokens and 500 lines?

**Why it matters:** The description is loaded at startup. The body is loaded when the skill fires. Both compete with the system prompt, the conversation, and every other skill. In Claude Code, the listing budget defaults to 1% of the context window, and descriptions are shortened first when it is exceeded.

| Score | Descriptor |
|---|---|
| 0 | Body over 5,000 tokens or 500 lines; or description over 1,024 characters; or no progressive disclosure despite the size. |
| 1 | Body 3,500 to 5,000 tokens; description over 150 tokens; references deeper than one level. |
| 2 | Description around 100 tokens; body under 5,000 tokens and 500 lines; references one level deep and loaded on demand. |

**Evidence:** estimated tokens, line count, reference depth.

### 5. Proof

**Question:** Does a with and without test show a repeatable difference?

**Why it matters:** Without a paired test, you have a belief, not evidence. A skill is a claim that the agent performs better with it.

| Score | Descriptor |
|---|---|
| 0 | No paired test; or the output is the same with and without the skill; or it is worse with the skill. |
| 1 | Tested once; anecdotal; or the improvement appears on only one prompt. |
| 2 | Repeatable improvement on representative tasks; with and without runs; the near-miss behavior is preserved. |

**Evidence:** the task, the two outputs, the comparison, and whether the run was repeated.

### 6. Safety

**Question:** Are scripts reviewed, secrets absent, network calls pinned, and permissions least-privilege?

**Why it matters:** Skills can read files, run code, and change behavior. A safe-looking description can hide a dangerous script.

| Score | Descriptor |
|---|---|
| 0 | Unreviewed scripts; secrets; unpinned remote instruction fetch; destructive commands; broad permissions; exfiltration patterns. |
| 1 | Scripts reviewed but provenance incomplete; trusted remote fetch unpinned; `allowed-tools` broader than needed. |
| 2 | No scripts and no network; or scripts reviewed, no secrets, pinned sources, least privilege, source verified. |

**Evidence:** file and line, or the absence of scripts and network calls.

**Note:** This is a static flag, not a security audit. Use Socket, Vett, or `skills-audit` for a real security verdict.

### 7. Ownership

**Question:** Are owner, version, status, and last review recorded?

**Why it matters:** Unowned skills rot. You cannot review what you cannot identify, and you cannot retire what nobody owns.

| Score | Descriptor |
|---|---|
| 0 | No owner, version, status, or review date. |
| 1 | Some fields present; review is stale or has no next date. |
| 2 | Owner, version, status, last reviewed, and next review are recorded. |

**Evidence:** metadata fields.

### 8. Overlap

**Question:** Is the job unique, and is the boundary with adjacent skills explicit?

**Why it matters:** Two skills for one request confuse the router. The agent picks one, and not always the one you meant.

| Score | Descriptor |
|---|---|
| 0 | Duplicate name or direct collision. |
| 1 | Description similarity at or above 0.30 with another skill; or the boundary is undocumented. |
| 2 | Unique job; the boundary with adjacent skills is stated; aliases and deprecations are noted. |

**Evidence:** top match, similarity score, boundary statement.

## Decision rule

Score each gate from 0 to 2. Maximum 16.

- **14 to 16:** keep.
- **11 to 13:** revise.
- **7 to 10:** merge or retire.
- **0 to 6:** delete.
- **Any 0 on Safety:** block. Fix before use.
- **No behavioral test:** maximum 12, so the skill cannot be kept. Mark it revise and list the missing prompts.

When two gates are pending, the practical bands are:

- **8 to 12 static:** revise.
- **5 to 7 static:** merge or retire.
- **0 to 4 static:** delete.

Report `known/12 static, 2 pending`.

## Review cadence

- **Monthly:** static pass on the active library.
- **Quarterly:** behavioral pass on the ten most-used skills.
- **After a model or harness change:** re-test the top ten.
- **Before publishing:** the skill must pass its own checklist.
- **When retiring:** archive first, then test removal with the raw model. Restore in one step if needed.

## Questions the audit should answer

1. What does this skill do that a fresh model would not do by default?
2. When should it fire, and when should it stay quiet?
3. What does it cost before it fires?
4. What does it cost when it fires?
5. What evidence shows it works?
6. What could it read, run, or send?
7. Who owns it, and when was it last reviewed?
8. What other skill is it competing with?

If the card does not answer these, the audit is incomplete.

## What this checklist is not

- It is not a malware scanner.
- It is not a token-budget linter.
- It is not a spec validator.
- It is not a replacement for a human decision.

It is the decision record that sits on top of those tools.
