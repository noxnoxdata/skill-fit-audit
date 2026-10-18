# Behavioral Tests

The static pass cannot tell you whether a skill works. These tests can.

Run them for every skill you plan to keep. If you do not run them, mark both behavioral gates `PENDING` and do not call the skill keep.

## What you need

- The same model and harness for every run.
- A fresh session for each run.
- The skill installed for the with-skill run.
- The skill absent for the baseline run.
- A task with a visible output, not a vibe.

## The five prompts

For each skill, write five prompts before you run anything.

**Three should-trigger prompts.** Real requests a user would type. Not "use the skill." Include the messy version: lowercase, a file path, a deadline, a typo, a real context.

**Two near-miss prompts.** Adjacent requests that share keywords but need something else. These are the ones that catch over-triggering. Do not use obviously unrelated prompts.

Example for a skill that audits skill libraries:

| Type | Prompt |
|---|---|
| Should trigger | "my skills folder is a mess, tell me what to delete" |
| Should trigger | "is this SKILL.md worth keeping? it never fires" |
| Should trigger | "review ~/.agents/skills before I publish the pack" |
| Near-miss | "scan this skill for malware" |
| Near-miss | "write a new skill for reading PDFs" |

## The paired test

For each should-trigger prompt:

1. Run the task in a fresh session **without** the skill. Save the output.
2. Run the same task in a fresh session **with** the skill. Save the output.
3. Compare:
   - Did the skill fire?
   - Did the output improve?
   - Did the agent follow the workflow, or improvise?
   - Did it cost more tokens or time? By how much?
   - Did it introduce a new error?

A skill passes proof when the improvement is repeatable on representative tasks, not when one run looked better.

## The near-miss test

For each near-miss prompt:

1. Run it with the skill installed.
2. Record whether the skill fired.
3. If it fired, the skill is over-triggering. Fix the description or the scope.

A skill passes trigger when it catches all three should-trigger prompts and fires on none of the near-misses.

## Recording the result

Use this block in the card:

```markdown
### Behavioral evidence

| Test | Result | Notes |
|---|---|---|
| Should trigger 1 | pass | Fired, followed the workflow |
| Should trigger 2 | fail | Did not fire; description missed "library" |
| Should trigger 3 | pass | Fired |
| Near-miss 1 | pass | Stayed quiet |
| Near-miss 2 | pass | Stayed quiet |
| With vs without | +1 step, same output | No measurable gain |
```

Scores:

- **Trigger 2:** 3/3 should-trigger, 0/2 near-misses.
- **Trigger 1:** catches the main prompt but misses variants, or fires on one near-miss.
- **Trigger 0:** no tests, or fails two should-trigger prompts, or fires on both near-misses.
- **Proof 2:** repeatable improvement on representative tasks.
- **Proof 1:** one run, anecdotal, or improvement on one prompt only.
- **Proof 0:** no test, same output, or worse output.

## Repeat when the decision matters

Agent outcomes vary even at low temperature. If the skill is expensive, high-risk, or central to a workflow, repeat the paired test three times and report the range. A single run is a smoke test, not proof.

## What counts as evidence

- The prompt.
- The model and harness.
- The output, saved.
- The comparison.
- The tokens or time, if available.
- The date.

What does not count:

- "It felt better."
- "The description looks clear."
- "It is popular."
- A test written by the same agent that wrote the skill, with no baseline.

## If you cannot run the tests

Mark the gates `PENDING`. Write the five prompts so the next person can run them. Do not mark a PENDING gate as passed because the skill looks good.
