# Evidence

The gates are not invented. They come from the format specification, the authoring guidance, the benchmark literature, and the security tools.

Accessed 18 October 2026.

## Format and authoring

**Agent Skills specification.** https://agentskills.io/specification

- `name`: 1 to 64 characters, lowercase letters, numbers, and hyphens. Must match the parent directory.
- `description`: 1 to 1,024 characters. Should describe what the skill does and when to use it.
- Metadata: about 100 tokens, loaded at startup for every installed skill.
- Body: under 5,000 tokens recommended. Keep `SKILL.md` under 500 lines.
- References: one level deep. Keep individual reference files focused.
- Validation: `skills-ref validate`.

**Anthropic, "Equipping agents for the real world with Agent Skills."** 16 October 2025. https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills

- Progressive disclosure: metadata first, body on demand, bundled files as needed.
- The description is the trigger.
- Start with evaluation. Build skills incrementally against real gaps.
- Split files to reduce token usage.
- Audit skills from untrusted sources. Malicious skills can exfiltrate data.

**Anthropic, "Skill authoring best practices."** https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

- Write descriptions in the third person, with what and when.
- Keep the body under 500 lines.
- Use workflows with checklists, feedback loops, and verification.
- Use examples and exact output templates.
- Test with the models you plan to use.
- Build evaluations before writing extensive documentation.

**Microsoft Learn, "Skills overview for agents (GitHub Copilot)."** Updated 12 October 2026. https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/skills-overview

- Skills are portable packages of instructions, scripts, and resources.
- The agent activates a skill when the user's request matches the skill's purpose.
- Agentic skills apply to agents on the GitHub Copilot harness.

## Measurement

**SkillsBench.** arXiv:2602.12670, submitted 13 February 2026, revised 14 June 2026. https://arxiv.org/abs/2602.12670

- Curated skills raised the average pass rate from 33.9% to 50.5%, +16.6 percentage points.
- Focused skills with at most three modules outperformed larger or exhaustive bundles.
- Smaller models with skills can match larger models without them.

This is why the checklist rewards focus and paired evaluation, not volume.

**Anson Biggs, "You're probably using Agent Skills wrong."** 16 February 2026. https://notes.ansonbiggs.com/youre-probably-using-agent-skills-wrong/

- Two reasons to make a skill: remembering a novel problem, and avoiding repetition.
- A skill written by a fresh agent about a task it has not struggled with adds little.

This is why the proof gate asks for a real difference, not a plausible description.

## Security and supply chain

**find-skills.** https://github.com/vercel-labs/skills/blob/main/skills/find-skills/SKILL.md

- Verify install count, source reputation, and GitHub stars before recommending a skill.
- Do not recommend a skill based solely on search results.

This is why ownership and provenance are gates, not footnotes.

**Socket, "Socket Brings Supply Chain Security to skills.sh."** 17 February 2026. https://socket.dev/blog/socket-brings-supply-chain-security-to-skills

- 60,000+ skills indexed at the time.
- A safe-looking skill hid `curl | sh` inside a Python script.
- Scanning must cover every file and language a skill references.

**Vett.** https://vett.sh/

- 40+ static analysis rules at the AST level.
- Sigstore signing.
- 739 skills with critical findings out of 8,271 analyzed.

**skills-audit.** https://skills.sh/shieldon-dev/skills/skills-audit

- Local security scan for credential theft, exfiltration, dangerous commands, and obfuscation.
- 39 detection patterns.
- Returns SAFE, REVIEW, or BLOCK.

This is why the safety gate points to dedicated scanners and does not pretend to replace them.

## Review discipline

**Addy Osmani, "Audit your Agent files."** 27 August 2026. https://addyosmani.com/blog/audit-your-agent-files/

- Agent configuration has a half-life. Models and harnesses change.
- Run an audit every few weeks. Archive first. Test removal with the raw model.
- Installing a useful skill and keeping it forever are separate decisions.
- In Claude Code, the skill listing has a budget that defaults to 1% of the context window. Descriptions are shortened first when over budget.
- The cost of an unused skill is confusion, not thousands of tokens per prompt. That is still enough reason to remove it.

This is why the checklist has a cadence and why it treats overlap and confusion as first-class costs.

**baronguyen001/skill-library-audit.** https://github.com/baronguyen001/skill-library-audit

- A CLI for per-turn budget, trigger collisions, scope shadowing, static rules, SARIF, and CI gates.
- 26 rules across structure, discovery, hygiene, library, and safety.
- Zero dependencies, offline.

This is the closest related work. Use it for budget and collision depth. This skill is the decision layer above it.
