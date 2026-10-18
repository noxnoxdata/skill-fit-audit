#!/usr/bin/env python3
"""Static fit audit for agent skills.

Reads local files only. Does not execute audited code. Does not use the network.
The safety gate is a static flag, not a security verdict.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

VERSION = "0.1.0"

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "dist",
    "build",
    ".next",
    ".cache",
    ".idea",
    ".vscode",
}

CODE_EXTS = {
    ".py",
    ".sh",
    ".bash",
    ".zsh",
    ".js",
    ".mjs",
    ".cjs",
    ".ts",
    ".rb",
    ".pl",
    ".ps1",
}

WHEN_RE = re.compile(
    r"(?i)\b(use when|use this|when the user|when you|when asked|when working|trigger|for tasks)\b"
)

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

REMOTE_FETCH_RE = re.compile(r"(?is)\b(fetch|download|curl|wget)\b.{0,180}?https?://")

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "then",
    "there",
    "these",
    "this",
    "to",
    "use",
    "used",
    "user",
    "using",
    "was",
    "when",
    "where",
    "which",
    "who",
    "will",
    "with",
    "you",
    "your",
}

SAFETY_CRITICAL: List[Tuple[str, str]] = [
    ("os.system", r"os\.system\s*\("),
    ("curl pipe", r"curl[^\n|]{0,200}\|\s*(?:sh|bash|zsh)"),
    ("wget pipe", r"wget[^\n|]{0,200}\|\s*(?:sh|bash|zsh)"),
    ("rm -rf root", r"rm\s+-rf\s+[/~]"),
    ("ssh keys", r"~/\.ssh"),
    ("aws creds", r"~/\.aws"),
    ("webhook.site", r"webhook\.site"),
    ("discord webhook", r"discord(?:app)?\.com/api/webhooks"),
    ("powershell encoded", r"powershell[^\n]{0,80}-enc"),
]

SAFETY_REVIEW: List[Tuple[str, str]] = [
    ("shell=True", r"shell\s*=\s*True"),
    ("eval", r"\beval\s*\("),
    ("exec", r"\bexec\s*\("),
    ("base64 decode", r"base64\s+(?:-d|--decode)"),
    ("dotenv", r"(?:^|[\s/])\.env\b"),
    ("remote post", r"requests\.post\s*\("),
]

GATE_ORDER = [
    "contract",
    "trigger",
    "scope",
    "cost",
    "proof",
    "safety",
    "ownership",
    "overlap",
]

GATE_LABELS = {
    "contract": "1. Contract",
    "trigger": "2. Trigger",
    "scope": "3. Scope",
    "cost": "4. Cost",
    "proof": "5. Proof",
    "safety": "6. Safety",
    "ownership": "7. Ownership",
    "overlap": "8. Overlap",
}

DECISION_ORDER = {
    "BLOCK": 0,
    "DELETE": 1,
    "MERGE OR RETIRE": 2,
    "REVISE": 3,
    "KEEP": 4,
}


@dataclass
class Gate:
    score: Optional[int]
    evidence: str
    finding: str
    action: str


@dataclass
class Skill:
    name: str
    path: str
    dir_name: str
    desc: str
    body: str
    metadata: Dict[str, str]
    data: Dict[str, object]
    desc_chars: int = 0
    desc_tokens: int = 0
    body_tokens: int = 0
    body_lines: int = 0
    h2_count: int = 0
    files: int = 0
    scripts: List[str] = field(default_factory=list)
    gates: Dict[str, Gate] = field(default_factory=dict)
    decision: Dict[str, object] = field(default_factory=dict)
    overlap_top: Optional[Tuple[str, float]] = None

    def finalize(self) -> None:
        self.desc_chars = len(self.desc)
        self.desc_tokens = round(len(self.desc) / 4)
        self.body_tokens = round(len(self.body) / 4)
        self.body_lines = self.body.count("\n") + 1
        self.h2_count = len(re.findall(r"^##\s+", self.body, re.M))
        skill_dir = Path(self.path).parent
        all_files = [p for p in skill_dir.rglob("*") if p.is_file()]
        self.files = len(all_files)
        self.scripts = []
        for p in all_files:
            rel = p.relative_to(skill_dir).as_posix()
            if rel.startswith("scripts/") or p.suffix.lower() in CODE_EXTS:
                self.scripts.append(rel)


def split_frontmatter(text: str) -> Tuple[List[str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return [], text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], "\n".join(lines[i + 1 :])
    return [], text


def collect_block(lines: List[str], start: int) -> Tuple[List[str], int]:
    buf: List[str] = []
    i = start
    while i < len(lines):
        line = lines[i]
        if line.strip() == "":
            buf.append("")
            i += 1
            continue
        if not line.startswith((" ", "\t")):
            break
        buf.append(line.strip())
        i += 1
    return buf, i


def join_block(buf: List[str], style: str) -> str:
    if style == "|":
        return "\n".join(buf).strip()
    parts: List[str] = []
    for line in buf:
        if line:
            parts.append(line)
    return " ".join(parts)


def clean_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_frontmatter(lines: List[str]) -> Dict[str, object]:
    data: Dict[str, object] = {}
    nested: Optional[str] = None
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if line.startswith((" ", "\t")):
            if nested:
                m = re.match(r"^\s+([A-Za-z0-9_-]+):\s*(.*)$", line)
                if m:
                    key, value = m.group(1), clean_scalar(m.group(2))
                    bucket = data.setdefault(nested, {})
                    if isinstance(bucket, dict):
                        bucket[key] = value
            i += 1
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key, raw = m.group(1), m.group(2).strip()
        if raw in {">", ">-", ">+", "|", "|-", "|+"}:
            block, i = collect_block(lines, i + 1)
            data[key] = join_block(block, raw[0])
            nested = None
            continue
        if raw == "":
            data[key] = {}
            nested = key
            i += 1
            continue
        data[key] = clean_scalar(raw)
        nested = None
        i += 1
    return data


def load_skill(path: Path) -> Skill:
    text = path.read_text(encoding="utf-8", errors="replace")
    fm_lines, body = split_frontmatter(text)
    data = parse_frontmatter(fm_lines)
    name = str(data.get("name", "") or "")
    desc = data.get("description", "")
    if not isinstance(desc, str):
        desc = ""
    metadata = data.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    meta: Dict[str, str] = {}
    for key in ("author", "version", "status", "last_reviewed", "license"):
        value = data.get(key)
        if isinstance(value, str) and value:
            meta[key] = value
    for key, value in metadata.items():
        if isinstance(value, str) and value:
            meta[key] = value
    skill = Skill(
        name=name,
        path=str(path),
        dir_name=path.parent.name,
        desc=desc,
        body=body,
        metadata=meta,
        data=data,
    )
    skill.finalize()
    return skill


def discover(target: Path, excludes: List[str]) -> List[Path]:
    target = target.resolve()
    if target.is_file():
        if target.name.lower() == "skill.md":
            return [target]
        raise ValueError(f"not a SKILL.md file: {target}")
    if (target / "SKILL.md").is_file():
        return [target / "SKILL.md"]
    paths: List[Path] = []
    for p in sorted(target.rglob("SKILL.md")):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        rel = p.as_posix()
        if any(x and x in rel for x in excludes):
            continue
        paths.append(p)
    return paths


def read_script_text(path: Path) -> str:
    try:
        if path.stat().st_size > 2_000_000:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def gate_contract(skill: Skill) -> Gate:
    problems: List[str] = []
    warnings: List[str] = []
    if not skill.name:
        problems.append("missing name")
    else:
        if len(skill.name) > 64:
            problems.append("name over 64 characters")
        if not NAME_RE.match(skill.name):
            problems.append("name is not lowercase kebab-case")
        if skill.name != skill.dir_name:
            problems.append(f"name does not match folder ({skill.dir_name})")
        if "anthropic" in skill.name or "claude" in skill.name:
            problems.append("name uses a reserved word")
    if not skill.desc:
        problems.append("missing description")
    elif len(skill.desc) > 1024:
        problems.append("description over 1,024 characters")
    else:
        if len(skill.desc) < 80:
            warnings.append("description under 80 characters")
        if not WHEN_RE.search(skill.desc):
            warnings.append("no 'use when' cue")
    if problems:
        return Gate(
            0,
            f"{skill.desc_chars} chars; name {skill.name!r}; folder {skill.dir_name!r}",
            "; ".join(problems),
            "Fix the frontmatter before anything else",
        )
    if warnings:
        return Gate(
            1,
            f"{skill.desc_chars} chars",
            "; ".join(warnings),
            "Make the description specific and add a when cue",
        )
    return Gate(
        2,
        f"{skill.desc_chars} chars; name matches folder",
        "Clear what and when",
        "Keep",
    )


def gate_scope(skill: Skill) -> Gate:
    if skill.body_tokens > 5000 or skill.h2_count >= 16:
        return Gate(
            0,
            f"{skill.body_tokens} body tokens; {skill.h2_count} H2 sections",
            "Likely kitchen sink",
            "Split into separate skills or move detail to references",
        )
    if skill.body_tokens > 3500 or skill.h2_count >= 12:
        return Gate(
            1,
            f"{skill.body_tokens} body tokens; {skill.h2_count} H2 sections",
            "Scope is broad or the body is reference-heavy",
            "Confirm one job; split reference material",
        )
    return Gate(
        2,
        f"{skill.body_tokens} body tokens; {skill.h2_count} H2 sections",
        "Focused",
        "Keep",
    )


def gate_cost(skill: Skill) -> Gate:
    if skill.body_tokens > 5000 or skill.body_lines > 500 or skill.desc_chars > 1024:
        return Gate(
            0,
            f"{skill.body_tokens} body tokens; {skill.body_lines} lines; {skill.desc_chars} desc chars",
            "Over the recommended limits",
            "Move detail to references and trim the description",
        )
    if skill.body_tokens > 3500 or skill.body_lines > 350 or skill.desc_tokens > 150:
        return Gate(
            1,
            f"{skill.body_tokens} body tokens; {skill.body_lines} lines; {skill.desc_tokens} desc tokens",
            "Borderline cost",
            "Check whether every section earns its tokens",
        )
    return Gate(
        2,
        f"{skill.body_tokens} body tokens; {skill.body_lines} lines; {skill.desc_tokens} desc tokens",
        "Within limits",
        "Keep",
    )


def gate_safety(skill: Skill, excludes: List[str]) -> Gate:
    skill_dir = Path(skill.path).parent
    critical: List[str] = []
    review: List[str] = []
    for rel in skill.scripts:
        if any(x and x in rel for x in excludes):
            continue
        text = read_script_text(skill_dir / rel)
        for label, pattern in SAFETY_CRITICAL:
            if re.search(pattern, text):
                critical.append(f"{rel}: {label}")
        for label, pattern in SAFETY_REVIEW:
            if re.search(pattern, text):
                review.append(f"{rel}: {label}")
    remote = bool(REMOTE_FETCH_RE.search(skill.body))
    allowed = str(skill.data.get("allowed-tools", "") or "")
    broad_tools = bool(re.search(r"(?i)\bbash\b", allowed)) and "Bash(" not in allowed
    if critical:
        return Gate(
            0,
            "; ".join(critical[:5]),
            "Critical pattern found in a script",
            "Block until the script is reviewed; run a real security scanner",
        )
    reasons = list(review)
    if skill.scripts:
        reasons.append(f"{len(skill.scripts)} script file(s)")
    if remote:
        reasons.append("remote instruction fetch")
    if broad_tools:
        reasons.append("broad allowed-tools")
    if reasons:
        return Gate(
            1,
            "; ".join(reasons[:5]),
            "Needs manual review",
            "Read the scripts and pin the source",
        )
    return Gate(2, "No scripts; no network", "Static pass", "Keep")


def gate_ownership(skill: Skill) -> Gate:
    fields = ["version", "status", "last_reviewed"]
    present = [f for f in fields if skill.metadata.get(f)]
    missing = [f for f in fields if not skill.metadata.get(f)]
    if not present:
        return Gate(
            0,
            "No version, status, or review date",
            "Unowned",
            "Add metadata: version, status, last_reviewed",
        )
    if missing:
        return Gate(
            1,
            f"Present: {', '.join(present)}; missing: {', '.join(missing)}",
            "Incomplete ownership",
            "Add the missing fields",
        )
    return Gate(
        2,
        f"version {skill.metadata.get('version')}; status {skill.metadata.get('status')}",
        "Owned and reviewed",
        "Keep",
    )


def tokenize(text: str) -> List[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if len(w) > 2 and w not in STOPWORDS]


def build_vectors(skills: List[Skill]) -> Dict[int, Dict[str, float]]:
    docs = {id(s): tokenize(f"{s.name} {s.desc}") for s in skills}
    vocab = {w for words in docs.values() for w in words}
    n = max(len(docs), 1)
    df = {w: sum(1 for words in docs.values() if w in words) for w in vocab}
    idf = {w: math.log((1 + n) / (1 + df[w])) + 1 for w in vocab}
    vectors: Dict[int, Dict[str, float]] = {}
    for key, words in docs.items():
        tf: Dict[str, int] = {}
        for word in words:
            tf[word] = tf.get(word, 0) + 1
        vectors[key] = {
            word: (1 + math.log(count)) * idf[word] for word, count in tf.items()
        }
    return vectors


def cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    num = sum(a.get(word, 0.0) * b.get(word, 0.0) for word in set(a) | set(b))
    denom_a = math.sqrt(sum(value * value for value in a.values()))
    denom_b = math.sqrt(sum(value * value for value in b.values()))
    if not denom_a or not denom_b:
        return 0.0
    return num / (denom_a * denom_b)


def apply_overlap(skills: List[Skill]) -> None:
    counts: Dict[str, int] = {}
    for s in skills:
        counts[s.name] = counts.get(s.name, 0) + 1
    vectors = build_vectors(skills)
    for s in skills:
        best_name = ""
        best_score = 0.0
        for other in skills:
            if other is s:
                continue
            score = cosine(vectors[id(s)], vectors[id(other)])
            if score > best_score:
                best_name, best_score = other.name or other.dir_name, score
        s.overlap_top = (best_name, round(best_score, 2)) if best_name else None
        if counts.get(s.name, 0) > 1:
            s.gates["overlap"] = Gate(
                0,
                f"duplicate name {s.name!r}",
                "Duplicate name",
                "Keep one; retire the other",
            )
        elif best_score >= 0.30:
            s.gates["overlap"] = Gate(
                1,
                f"top match {best_name} at {best_score:.2f}",
                "Description overlap",
                "State the boundary or merge",
            )
        else:
            s.gates["overlap"] = Gate(
                2,
                f"top match {best_name or 'none'} at {best_score:.2f}",
                "Unique",
                "Keep",
            )


def decide(skill: Skill) -> Dict[str, object]:
    scores = {key: gate.score for key, gate in skill.gates.items()}
    pending = [key for key in GATE_ORDER if scores.get(key) is None]
    known = sum(v for v in scores.values() if v is not None)
    max_known = 2 * (len(GATE_ORDER) - len(pending))
    if scores.get("safety") == 0:
        return {
            "verdict": "BLOCK",
            "score": known,
            "max_score": max_known,
            "pending": pending,
            "reason": "Safety gate is 0. Fix before use.",
        }
    if pending:
        if known >= 8:
            verdict = "REVISE"
        elif known >= 5:
            verdict = "MERGE OR RETIRE"
        else:
            verdict = "DELETE"
        return {
            "verdict": verdict,
            "score": known,
            "max_score": max_known,
            "pending": pending,
            "reason": f"{known}/{max_known} static. Pending: {', '.join(pending)}. No behavioral test, no keep.",
        }
    if known >= 14:
        verdict = "KEEP"
    elif known >= 11:
        verdict = "REVISE"
    elif known >= 7:
        verdict = "MERGE OR RETIRE"
    else:
        verdict = "DELETE"
    return {
        "verdict": verdict,
        "score": known,
        "max_score": 16,
        "pending": [],
        "reason": f"{known}/16.",
    }


def apply_behavioral(skills: List[Skill], path: Optional[str]) -> None:
    if not path:
        return
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    results = payload.get("skills", payload)
    if not isinstance(results, dict):
        raise ValueError("behavioral file must contain a skills object")
    for skill in skills:
        item = results.get(skill.name)
        if not isinstance(item, dict):
            continue
        for gate_name in ("trigger", "proof"):
            if gate_name not in item:
                continue
            raw = item[gate_name]
            try:
                score = int(raw)
            except (TypeError, ValueError):
                continue
            if score < 0 or score > 2:
                continue
            evidence = str(item.get("evidence", "Behavioral test recorded"))
            action = "Keep" if score == 2 else "Revise and retest"
            skill.gates[gate_name] = Gate(score, evidence, evidence, action)


def analyze(target: Path, excludes: List[str], behavioral: Optional[str]) -> List[Skill]:
    paths = discover(target, excludes)
    skills = [load_skill(p) for p in paths]
    if excludes:
        for skill in skills:
            skill.scripts = [
                rel
                for rel in skill.scripts
                if not any(x and x in rel for x in excludes)
            ]
    for skill in skills:
        skill.gates["contract"] = gate_contract(skill)
        skill.gates["trigger"] = Gate(
            None, "No prompts run", "Not tested", "Run 3 prompts and 2 near-misses"
        )
        skill.gates["scope"] = gate_scope(skill)
        skill.gates["cost"] = gate_cost(skill)
        skill.gates["proof"] = Gate(
            None, "No with/without run", "Not tested", "Run the paired test"
        )
        skill.gates["safety"] = gate_safety(skill, excludes)
        skill.gates["ownership"] = gate_ownership(skill)
    apply_overlap(skills)
    apply_behavioral(skills, behavioral)
    for skill in skills:
        skill.decision = decide(skill)
    skills.sort(key=lambda s: (DECISION_ORDER.get(str(s.decision["verdict"]), 9), s.name))
    return skills


def summary(skills: List[Skill]) -> Dict[str, object]:
    decisions: Dict[str, int] = {}
    for s in skills:
        verdict = str(s.decision.get("verdict", "UNKNOWN"))
        decisions[verdict] = decisions.get(verdict, 0) + 1
    duplicate_names = sorted({s.name for s in skills if sum(1 for x in skills if x.name == s.name) > 1})
    overlap_pairs: List[Tuple[str, str, float]] = []
    for s in skills:
        if s.overlap_top and s.overlap_top[1] >= 0.20 and s.overlap_top[0] != (s.name or s.dir_name):
            pair = tuple(sorted([s.name or s.dir_name, s.overlap_top[0]])) + (s.overlap_top[1],)
            if pair not in overlap_pairs:
                overlap_pairs.append(pair)
    return {
        "skills": len(skills),
        "description_tokens": sum(s.desc_tokens for s in skills),
        "description_over_1024": sum(1 for s in skills if s.desc_chars > 1024),
        "description_over_400": sum(1 for s in skills if s.desc_chars > 400),
        "duplicate_names": duplicate_names,
        "missing_names": [s.dir_name for s in skills if not s.name],
        "body_over_5k": [s.name or s.dir_name for s in skills if s.body_tokens > 5000],
        "with_scripts": sum(1 for s in skills if s.scripts),
        "no_version": [s.name or s.dir_name for s in skills if not s.metadata.get("version")],
        "overlap_pairs": [
            {"a": a, "b": b, "score": score} for a, b, score in sorted(overlap_pairs, key=lambda x: -x[2])
        ],
        "decisions": decisions,
        "behavioral_pending": sum(
            1 for s in skills if s.gates["trigger"].score is None or s.gates["proof"].score is None
        ),
    }


def card(skill: Skill) -> str:
    lines: List[str] = []
    lines.append(f"### {skill.name or '(missing name)'}")
    lines.append("")
    lines.append(f"Path: `{skill.path}`")
    lines.append(
        f"Decision: **{skill.decision['verdict']}**. {skill.decision['reason']}"
    )
    lines.append("")
    lines.append("| Gate | Score | Evidence | Finding | Action |")
    lines.append("|---|---|---|---|---|")
    for key in GATE_ORDER:
        gate = skill.gates[key]
        score = "PENDING" if gate.score is None else f"{gate.score}/2"
        lines.append(
            f"| {GATE_LABELS[key]} | {score} | {gate.evidence} | {gate.finding} | {gate.action} |"
        )
    lines.append("")
    return "\n".join(lines)


def report(skills: List[Skill], target: str) -> str:
    data = summary(skills)
    lines: List[str] = []
    lines.append("# Skill Fit Audit")
    lines.append("")
    lines.append(f"Target: `{target}`")
    lines.append(f"Skills audited: {data['skills']}")
    lines.append(f"Estimated description tokens: {data['description_tokens']}")
    lines.append("")
    lines.append(
        "Static pass only unless behavioral evidence was supplied. PENDING means not tested, not passed."
    )
    lines.append("")
    lines.append("## Skills")
    lines.append("")
    for skill in skills:
        lines.append(card(skill))
    lines.append("## Library summary")
    lines.append("")
    lines.append(f"- Skills: {data['skills']}")
    lines.append(f"- Description tokens: {data['description_tokens']}")
    lines.append(f"- Descriptions over 1,024 chars: {data['description_over_1024']}")
    lines.append(f"- Descriptions over 400 chars: {data['description_over_400']}")
    lines.append(f"- Duplicate names: {', '.join(data['duplicate_names']) or 'none'}")
    lines.append(f"- Missing names: {', '.join(data['missing_names']) or 'none'}")
    lines.append(f"- Bodies over 5k tokens: {', '.join(data['body_over_5k']) or 'none'}")
    lines.append(f"- Skills with scripts: {data['with_scripts']}")
    lines.append(f"- Skills with no version: {len(data['no_version'])}")
    pairs = data["overlap_pairs"]
    if pairs:
        pair_text = "; ".join(f"{p['a']} <-> {p['b']} ({p['score']:.2f})" for p in pairs)
    else:
        pair_text = "none"
    lines.append(f"- Overlap candidates at or above 0.20: {pair_text}")
    lines.append(
        "- Decisions: "
        + ", ".join(f"{k} {v}" for k, v in sorted(data["decisions"].items()))
    )
    lines.append(f"- Skills with behavioral evidence pending: {data['behavioral_pending']}")
    lines.append("")
    lines.append("## Actions")
    lines.append("")
    actions: List[str] = []
    for skill in skills:
        if skill.decision["verdict"] in {"BLOCK", "DELETE"}:
            actions.append(f"- {skill.decision['verdict']}: `{skill.name or skill.dir_name}`")
        elif skill.decision["verdict"] in {"REVISE", "MERGE OR RETIRE"}:
            actions.append(f"- {skill.decision['verdict']}: `{skill.name or skill.dir_name}`")
    if not actions:
        actions.append("- No blocking actions. Run the behavioral tests before keeping anything.")
    lines.extend(actions)
    lines.append("")
    return "\n".join(lines)


def behavioral_markdown(skills: List[Skill]) -> str:
    lines: List[str] = ["# Behavioral Tests", ""]
    lines.append(
        "Run these for every skill you plan to keep. If you do not run them, mark the gates PENDING and do not call the skill keep."
    )
    lines.append("")
    for skill in skills:
        lines.append(f"## {skill.name or skill.dir_name}")
        lines.append("")
        lines.append("Should trigger:")
        lines.append("")
        lines.append("1. ")
        lines.append("2. ")
        lines.append("3. ")
        lines.append("")
        lines.append("Near-miss:")
        lines.append("")
        lines.append("1. ")
        lines.append("2. ")
        lines.append("")
        lines.append("Paired test:")
        lines.append("")
        lines.append("- [ ] Ran without the skill and saved the output")
        lines.append("- [ ] Ran with the skill and saved the output")
        lines.append("- [ ] Compared correctness, steps, tokens, and time")
        lines.append("- [ ] Repeated if the decision matters")
        lines.append("")
    return "\n".join(lines)


def checklist_text() -> str:
    path = Path(__file__).resolve().parent.parent / "assets" / "checklist-template.md"
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return "# Skill Fit Checklist\n\nFill the eight gates in references/CHECKLIST.md.\n"


def to_json(skills: List[Skill], target: str) -> Dict[str, object]:
    return {
        "version": VERSION,
        "target": target,
        "summary": summary(skills),
        "skills": [
            {
                "name": s.name,
                "path": s.path,
                "metrics": {
                    "description_chars": s.desc_chars,
                    "description_tokens": s.desc_tokens,
                    "body_tokens": s.body_tokens,
                    "body_lines": s.body_lines,
                    "h2_sections": s.h2_count,
                    "files": s.files,
                    "scripts": s.scripts,
                },
                "metadata": s.metadata,
                "gates": {
                    key: {
                        "score": s.gates[key].score,
                        "evidence": s.gates[key].evidence,
                        "finding": s.gates[key].finding,
                        "action": s.gates[key].action,
                    }
                    for key in GATE_ORDER
                },
                "decision": s.decision,
            }
            for s in skills
        ],
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Static fit audit for agent skills. No network. Does not execute audited code."
    )
    parser.add_argument("target", nargs="?", default=".", help="skill, library, or SKILL.md")
    parser.add_argument("--checklist", action="store_true", help="print the blank checklist and exit")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--out", help="write checklist.md, audit-report.md, audit.json, behavioral-tests.md")
    parser.add_argument("--exclude", action="append", default=[], help="substring to exclude")
    parser.add_argument("--behavioral", help="JSON file with trigger and proof results")
    parser.add_argument("--min-score", type=int, help="exit 1 if any skill is below this known score")
    parser.add_argument("--self", action="store_true", dest="self_audit", help="audit this repository")
    parser.add_argument("--version", action="version", version=f"skill-fit-audit {VERSION}")
    args = parser.parse_args(argv)

    if args.checklist:
        print(checklist_text())
        return 0

    excludes = list(args.exclude)
    target = Path(args.target)
    if args.self_audit:
        target = Path(__file__).resolve().parent.parent
        excludes.extend(["tests/", "scripts/audit.py"])
    try:
        skills = analyze(target, excludes, args.behavioral)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not skills:
        print("error: no SKILL.md found", file=sys.stderr)
        return 2

    data = summary(skills)
    if args.format == "json":
        print(json.dumps(to_json(skills, str(target)), indent=2))
    elif not args.out:
        print(report(skills, str(target)))
        print()
        print(behavioral_markdown(skills))

    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "checklist.md").write_text(checklist_text(), encoding="utf-8")
        (out / "audit-report.md").write_text(report(skills, str(target)), encoding="utf-8")
        (out / "audit.json").write_text(
            json.dumps(to_json(skills, str(target)), indent=2), encoding="utf-8"
        )
        (out / "behavioral-tests.md").write_text(behavioral_markdown(skills), encoding="utf-8")
        decisions = ", ".join(f"{k} {v}" for k, v in sorted(data["decisions"].items()))
        print(f"Skill Fit Audit: {len(skills)} skills. {decisions}.")
        print(f"Wrote {out}/checklist.md, audit-report.md, audit.json, behavioral-tests.md")

    if args.min_score is not None:
        for skill in skills:
            known = int(skill.decision["score"])
            if known < args.min_score:
                print(
                    f"error: {skill.name or skill.dir_name} scored {known}, below {args.min_score}",
                    file=sys.stderr,
                )
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
