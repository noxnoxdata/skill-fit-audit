import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"

spec = importlib.util.spec_from_file_location("audit", ROOT / "scripts" / "audit.py")
audit = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = audit
spec.loader.exec_module(audit)


def analyze_fixtures(behavioral=None):
    return audit.analyze(FIXTURES, [], behavioral)


def by_name(skills, name):
    matches = [s for s in skills if s.name == name]
    return matches


class FixtureTests(unittest.TestCase):
    def test_folded_description_is_parsed(self):
        skill = audit.load_skill(FIXTURES / "folded-desc" / "SKILL.md")
        self.assertGreater(len(skill.desc), 100)
        self.assertTrue(skill.desc.startswith("Summarizes meeting notes"))
        self.assertEqual(skill.gates.get("contract"), None)

    def test_good_skill_passes_static_gates(self):
        skills = analyze_fixtures()
        skill = by_name(skills, "good-skill")[0]
        self.assertEqual(skill.gates["contract"].score, 2)
        self.assertEqual(skill.gates["scope"].score, 2)
        self.assertEqual(skill.gates["cost"].score, 2)
        self.assertEqual(skill.gates["safety"].score, 2)
        self.assertEqual(skill.gates["ownership"].score, 2)
        self.assertEqual(skill.gates["overlap"].score, 2)
        self.assertEqual(skill.gates["trigger"].score, None)
        self.assertEqual(skill.gates["proof"].score, None)
        self.assertEqual(skill.decision["verdict"], "REVISE")
        self.assertEqual(skill.decision["max_score"], 12)

    def test_vague_description_scores_one(self):
        skills = analyze_fixtures()
        skill = by_name(skills, "vague-skill")[0]
        self.assertEqual(skill.gates["contract"].score, 1)

    def test_missing_name_scores_zero(self):
        skills = analyze_fixtures()
        skill = [s for s in skills if s.dir_name == "missing-name"][0]
        self.assertEqual(skill.gates["contract"].score, 0)
        self.assertNotEqual(skill.decision["verdict"], "KEEP")

    def test_duplicate_names_score_zero_overlap(self):
        skills = analyze_fixtures()
        matches = by_name(skills, "duplicate-skill")
        self.assertEqual(len(matches), 2)
        for skill in matches:
            self.assertEqual(skill.gates["overlap"].score, 0)

    def test_network_script_blocks(self):
        skills = analyze_fixtures()
        skill = by_name(skills, "network-script")[0]
        self.assertEqual(skill.gates["safety"].score, 0)
        self.assertEqual(skill.decision["verdict"], "BLOCK")

    def test_remote_fetch_is_a_safety_flag(self):
        skills = analyze_fixtures()
        skill = by_name(skills, "remote-fetch")[0]
        self.assertEqual(skill.gates["safety"].score, 1)

    def test_broad_tools_is_a_safety_flag(self):
        skills = analyze_fixtures()
        skill = by_name(skills, "broad-tools")[0]
        self.assertEqual(skill.gates["safety"].score, 1)

    def test_expected_decisions(self):
        expected = json.loads((ROOT / "tests" / "expected.json").read_text())
        skills = analyze_fixtures()
        seen = set()
        for skill in skills:
            key = skill.name or skill.dir_name
            if key in seen:
                continue
            seen.add(key)
            self.assertIn(key, expected)
            self.assertEqual(skill.decision["verdict"], expected[key]["verdict"])
            self.assertEqual(skill.decision["score"], expected[key]["score"])
            self.assertEqual(skill.decision["max_score"], expected[key]["max_score"])

    def test_no_keep_without_behavioral_evidence(self):
        skills = analyze_fixtures()
        for skill in skills:
            if skill.gates["trigger"].score is None or skill.gates["proof"].score is None:
                self.assertNotEqual(skill.decision["verdict"], "KEEP")


class OutputTests(unittest.TestCase):
    def test_checklist_has_all_gates(self):
        text = audit.checklist_text()
        for label in (
            "1. Contract",
            "2. Trigger",
            "3. Scope",
            "4. Cost",
            "5. Proof",
            "6. Safety",
            "7. Ownership",
            "8. Overlap",
        ):
            self.assertIn(label, text)

    def test_markdown_report_has_cards_and_summary(self):
        skills = analyze_fixtures()
        text = audit.report(skills, str(FIXTURES))
        self.assertIn("## Library summary", text)
        self.assertIn("PENDING", text)
        self.assertIn("good-skill", text)

    def test_json_shape(self):
        skills = analyze_fixtures()
        payload = audit.to_json(skills, str(FIXTURES))
        self.assertIn("summary", payload)
        self.assertIn("skills", payload)
        self.assertIn("gates", payload["skills"][0])
        self.assertIn("decision", payload["skills"][0])

    def test_card_contains_pending(self):
        skills = analyze_fixtures()
        skill = by_name(skills, "good-skill")[0]
        text = audit.card(skill)
        self.assertIn("PENDING", text)
        self.assertIn("Decision", text)


class ThresholdTests(unittest.TestCase):
    def make_skill(self, name, desc, body, metadata=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / name / "SKILL.md"
        path.parent.mkdir(parents=True)
        meta = metadata or {}
        lines = ["---", f"name: {name}", f"description: {desc}"]
        if meta:
            lines.append("metadata:")
            for key, value in meta.items():
                lines.append(f'  {key}: "{value}"')
        lines.extend(["---", "", body])
        path.write_text("\n".join(lines), encoding="utf-8")
        return audit.load_skill(path)

    def test_oversized_description_fails_contract_and_cost(self):
        skill = self.make_skill(
            "oversized-desc",
            "x" * 1200,
            "Do the thing.",
            {"version": "1.0.0", "status": "active", "last_reviewed": "2026-10-01"},
        )
        self.assertEqual(audit.gate_contract(skill).score, 0)
        self.assertEqual(audit.gate_cost(skill).score, 0)

    def test_oversized_body_fails_scope_and_cost(self):
        skill = self.make_skill(
            "oversized-body",
            "Does one job with a long body. Use when the user asks for it.",
            "word " * 22000,
            {"version": "1.0.0", "status": "active", "last_reviewed": "2026-10-01"},
        )
        self.assertEqual(audit.gate_scope(skill).score, 0)
        self.assertEqual(audit.gate_cost(skill).score, 0)

    def test_behavioral_evidence_can_produce_keep(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "skills": {
                        "good-skill": {
                            "trigger": 2,
                            "proof": 2,
                            "evidence": "3/3 should-trigger, 0/2 near-miss; paired test improved",
                        }
                    }
                },
                f,
            )
            path = f.name
        try:
            skills = analyze_fixtures(path)
            skill = by_name(skills, "good-skill")[0]
            self.assertEqual(skill.gates["trigger"].score, 2)
            self.assertEqual(skill.gates["proof"].score, 2)
            self.assertEqual(skill.decision["verdict"], "KEEP")
            self.assertEqual(skill.decision["score"], 16)
        finally:
            Path(path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
