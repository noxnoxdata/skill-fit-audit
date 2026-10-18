# Security

## What this skill does with your files

`scripts/audit.py` reads local files. It does not execute audited code. It does not open a network connection. It does not send telemetry.

The safety gate is a static flag. It looks for common danger patterns in scripts and for remote instruction fetches. It is not a security audit and it does not prove a skill is safe.

For a real security review, use Socket, Vett, or `skills-audit`.

## Audit history

The first Snyk audit on 18 October 2026 flagged two test fixtures:

- `tests/fixtures/network-script/scripts/install.sh`, a curl-pipe-sh fixture.
- `tests/fixtures/remote-fetch/SKILL.md`, a remote URL fixture.

Both were removed in 0.1.1. The safety tests now generate those strings at runtime, in a temporary directory, so the repository contains no dangerous command and no runtime instruction to fetch a remote URL.

The first audit is a false positive caused by the fixtures. A re-audit has been requested in [vercel-labs/skills#2531](https://github.com/vercel-labs/skills/issues/2531). Gen Agent Trust Hub passed the first audit, and Socket returned a warning about the same fixtures.

This is also a useful example of the skill's own boundary: a static scanner cannot tell a test fixture from a live instruction without context.

## Reporting a vulnerability

Open a private security advisory on GitHub:

https://github.com/noxnoxdata/skill-fit-audit/security/advisories/new

Please include:

- The affected version.
- A minimal reproduction.
- Whether the issue is in the parser, the output, or the documented behavior.

Do not open a public issue for a vulnerability.
