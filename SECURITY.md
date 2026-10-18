# Security

## What this skill does with your files

`scripts/audit.py` reads local files. It does not execute audited code. It does not open a network connection. It does not send telemetry.

The safety gate is a static flag. It looks for common danger patterns in scripts and for remote instruction fetches. It is not a security audit and it does not prove a skill is safe.

For a real security review, use Socket, Vett, or `skills-audit`.

## Reporting a vulnerability

Open a private security advisory on GitHub:

https://github.com/noxnoxdata/skill-fit-audit/security/advisories/new

Please include:

- The affected version.
- A minimal reproduction.
- Whether the issue is in the parser, the output, or the documented behavior.

Do not open a public issue for a vulnerability.
