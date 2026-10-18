# skill-fit-audit

[![skills.sh](https://skills.sh/b/noxnoxdata/skill-fit-audit)](https://skills.sh/noxnoxdata/skill-fit-audit)

**Safe and valid is not the same as worth keeping.**

An agent skill can pass the spec, pass the security scanner, and still be a bad skill. It can be vague, duplicate another skill, fire on the wrong task, or cost attention on every request without earning it.

`skill-fit-audit` audits the fit.

It produces a completed eight-gate checklist per skill and one decision: keep, revise, merge, retire, or delete. Untested behavioral gates are marked `PENDING`. No behavioral test, no keep.

## Why this exists

The ecosystem is getting good at two questions:

- **Discovery:** which skill should I install? `find-skills` and skills.sh answer this.
- **Security:** is this skill safe? Socket, Vett, and `skills-audit` answer this.

The quieter question is fit: **does this skill earn its place in my library?**

A skill that is safe but vague still steals a trigger. A skill that is valid but duplicated still confuses the router. A skill that is popular but never used still costs metadata on every request. A skill with no owner still rots.

That is the gap this skill fills.

## What it does

1. Reads the frontmatter, body, scripts, references, and metadata.
2. Runs a static pass: contract, scope, cost, safety flags, ownership, overlap.
3. Runs or marks the behavioral pass: three real prompts, two near-misses, with and without.
4. Produces four artifacts: `checklist.md`, `audit-report.md`, `audit.json`, `behavioral-tests.md`.
5. Ends with one decision per skill and one library summary.

The checklist is the product. The score is only the summary.

## Install

```bash
npx skills add noxnoxdata/skill-fit-audit
```

Or clone the repo and point your agent at the directory.

Requires Python 3.9+ for the static script. No network access. No dependencies.

## Quick start

Ask your agent:

```text
audit my skill library
```

```text
is this SKILL.md worth keeping?
```

```text
review these skills and tell me what to delete
```

Or run the static pass directly:

```bash
python scripts/audit.py ~/.agents/skills --out ./audit
```

```bash
python scripts/audit.py ./my-skill --format json
```

```bash
python scripts/audit.py --checklist
```

## What the output looks like

```markdown
## pdf-table-extractor

Decision: REVISE. Behavioral tests pending.

| Gate | Score | Evidence | Finding | Action |
|---|---|---|---|---|
| 1 Contract | 2/2 | 212 chars, says what and when | Clear trigger | Keep |
| 2 Trigger | PENDING | No prompts run | Not tested | Run 3 prompts and 2 near-misses |
| 3 Scope | 2/2 | One extraction workflow, 2 modules | Focused | Keep |
| 4 Cost | 2/2 | 1,240 body tokens, 180 lines | Within limits | Keep |
| 5 Proof | PENDING | No with/without run | Not tested | Run paired test |
| 6 Safety | 2/2 | No scripts, no network | Static only | Keep |
| 7 Ownership | 1/2 | Version present, status missing | Incomplete | Add status and review date |
| 8 Overlap | 2/2 | No close match | Unique | Keep |

Known score: 11/12 static. Two gates pending.
```

The full example is in [`references/EXAMPLE-AUDIT.md`](references/EXAMPLE-AUDIT.md).

## The eight gates

| Gate | Question | Why it matters |
|---|---|---|
| 1. Contract | Is the name valid, and does the description say what it does and when to use it? | The description is the routing key. |
| 2. Trigger | Does it catch three real prompts and ignore two near-misses? | A skill that fires on the wrong task is worse than no skill. |
| 3. Scope | Is it one workflow with at most three modules? | A five-job skill is five skills competing for one trigger. |
| 4. Cost | Is the description around 100 tokens and the body under 5k tokens and 500 lines? | The description loads at startup. The body loads on invocation. |
| 5. Proof | Does a with and without test show a repeatable difference? | Without a paired test, you have a belief, not evidence. |
| 6. Safety | Are scripts reviewed, secrets absent, network calls pinned, and permissions least-privilege? | Skills can read files, run code, and change behavior. |
| 7. Ownership | Are owner, version, status, and last review recorded? | Unowned skills rot. |
| 8. Overlap | Is the job unique, and is the boundary with adjacent skills explicit? | Two skills for one request confuse the router. |

The full rubric, with 0, 1, and 2 descriptors, is in [`references/CHECKLIST.md`](references/CHECKLIST.md).

## Decision rule

- **14 to 16:** keep.
- **11 to 13:** revise.
- **7 to 10:** merge or retire.
- **0 to 6:** delete.
- **Any 0 on Safety:** block. Fix before use.
- **No behavioral test:** maximum 12, so the skill cannot be kept.

When two gates are pending, the practical bands are:

- **8 to 12 static:** revise.
- **5 to 7 static:** merge or retire.
- **0 to 4 static:** delete.

Report `known/12 static, 2 pending`. Do not inflate it to a 16-point score.

## Boundaries

`skill-fit-audit` is not:

- A malware scanner. Use [Socket](https://socket.dev/), [Vett](https://vett.sh/), or [`skills-audit`](https://skills.sh/shieldon-dev/skills/skills-audit).
- A token-budget or collision linter. Use [`skillaudit`](https://github.com/baronguyen001/skill-library-audit).
- A skill authoring tool. Use [`skill-creator`](https://github.com/anthropics/skills/tree/main/skills/skill-creator).
- A general code review tool.

It does not execute audited code. It does not make network calls. Its safety gate is a static flag, not a security verdict.

## Related work

- [`baronguyen001/skill-library-audit`](https://github.com/baronguyen001/skill-library-audit): the `skillaudit` CLI for per-turn budgets, trigger collisions, 26 static rules, SARIF, and CI gates.
- [`shieldon-dev/skills-audit`](https://skills.sh/shieldon-dev/skills/skills-audit): a local security scanner for credential theft, exfiltration, dangerous commands, and obfuscation.
- [Socket](https://socket.dev/) and [Vett](https://vett.sh/): supply-chain scanning and runtime isolation.
- [`find-skills`](https://skills.sh/vercel-labs/skills/find-skills): discovery and install.
- [`skill-creator`](https://github.com/anthropics/skills/tree/main/skills/skill-creator): authoring, evals, and description optimization.
- The [Agent Skills specification](https://agentskills.io/specification): the format and limits this audit checks against.
- [SkillsBench](https://arxiv.org/abs/2602.12670): paired evaluation and focused skills.

## Requirements

- Python 3.9 or later for the static script.
- A coding agent that can read files, for the behavioral pass.
- No API keys.
- No network access.

## Design principles

- **Evidence over score.** Every finding cites a file, line, or metric.
- **PENDING over false pass.** If a gate was not tested, say so.
- **The checklist is the product.** The score is the summary.
- **Static only by default.** The script never executes audited code.
- **One job.** This skill audits fit. It does not replace security or budget tools.

## Self-audit

Run on 18 October 2026 with `python scripts/audit.py --self`:

| Gate | Score |
|---|---|
| 1. Contract | 2/2 |
| 2. Trigger | PENDING |
| 3. Scope | 2/2 |
| 4. Cost | 2/2 |
| 5. Proof | PENDING |
| 6. Safety | 2/2 |
| 7. Ownership | 2/2 |
| 8. Overlap | 2/2 |

Decision: **REVISE**. 12/12 static. Trigger and proof are pending, so it cannot be kept under its own rule.

The tool does not get a pass it would not give another skill.

## Status

Experimental, version 0.1.0. The static pass is implemented. The behavioral pass is a protocol the agent runs, not a script. If you use it on a library, open an issue with the card and what you learned.

## License

MIT. See [LICENSE](LICENSE).
