# Example Audit

A synthetic library of two skills. The names are invented. The findings show what a completed checklist looks like.

## pdf-table-extractor

Path: `skills/pdf-table-extractor/SKILL.md`

Decision: **REVISE**. Behavioral tests pending.

| Gate | Score | Evidence | Finding | Action |
|---|---|---|---|---|
| 1 Contract | 2/2 | 212 chars; "Extract tables from PDFs. Use when..." | Clear what and when | Keep |
| 2 Trigger | PENDING | No prompts run | Not tested | Run 3 prompts and 2 near-misses |
| 3 Scope | 2/2 | One extraction workflow; 2 modules; 180 body lines | Focused | Keep |
| 4 Cost | 2/2 | 1,240 body tokens; 180 lines; references one level deep | Within limits | Keep |
| 5 Proof | PENDING | No with/without run | Not tested | Run paired test |
| 6 Safety | 2/2 | No scripts; no network | Static only | Keep |
| 7 Ownership | 1/2 | Version present; status and review date missing | Incomplete | Add status and next review |
| 8 Overlap | 2/2 | Top match 0.12 | Unique | Keep |

Known score: **11/12 static**. Two gates pending.

Behavioral prompts still to run:

- "pull the tables out of this annual report PDF and give me a CSV"
- "the table on page 14 is split across two pages, can you fix it"
- "extract every table from these files in the reports folder"
- Near-miss: "summarize this PDF"
- Near-miss: "fill in the form fields in this PDF"

## helper

Path: `skills/helper/SKILL.md`

Decision: **DELETE**. The skill has no job, no trigger, and no owner.

| Gate | Score | Evidence | Finding | Action |
|---|---|---|---|---|
| 1 Contract | 1/2 | 41 chars; "Helps with documents." | No what, no when | Rewrite or delete |
| 2 Trigger | PENDING | No prompts run | Not tested | Not worth testing until the description exists |
| 3 Scope | 0/2 | 9 H2 sections; 2,900 body tokens | Kitchen sink | Split or delete |
| 4 Cost | 1/2 | 2,900 body tokens; 310 lines | Borderline | Reduce if kept |
| 5 Proof | PENDING | No with/without run | Not tested | Not worth testing until scope exists |
| 6 Safety | 2/2 | No scripts; no network | Static only | Keep |
| 7 Ownership | 0/2 | No owner, version, status, or review date | Unowned | Delete |
| 8 Overlap | 1/2 | 0.41 similarity with `docx` | Boundary unclear | Delete or state boundary |

Known score: **5/12 static**. Two gates pending. Decision: **DELETE**.

## Library summary

- 2 skills.
- 253 description tokens.
- 1 skill with a PENDING trigger gate.
- 1 skill with a PENDING proof gate.
- 1 overlap candidate at or above 0.20.
- 1 skill with no owner.
- 0 skills keepable until the behavioral tests are run.

The summary is deliberately blunt. A library with no behavioral evidence has no keepers.

## A real library run

On 18 October 2026, the script audited a personal library of 60 skills. Static only, no behavioral tests.

- 7,765 estimated description tokens.
- 2 descriptions over 1,024 characters.
- 40 descriptions over 400 characters.
- 1 duplicate name.
- 1 missing name.
- 1 body over 5k tokens.
- 11 skills with scripts.
- 7 overlap candidates at or above 0.20.
- 48 revise, 12 merge or retire, 0 keep.
- 60 skills with behavioral evidence pending.

The counts are anonymized. The point is not the specific library. It is that a library can look healthy and still be full of unresolved decisions.
