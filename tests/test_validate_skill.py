import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("validator", Path(__file__).resolve().parents[1] / "scripts/validate_skill.py")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class PackageValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="电商 skill validation ")
        self.addCleanup(self.temp.cleanup)
        self.skill = Path(self.temp.name) / "test-skill"
        self.skill.mkdir()
        self.entry = self.skill / "SKILL.md"
        self.valid_text = "---\nname: test-skill\ndescription: 商品设计验证样例\n---\n\n# 示例\n\n请使用当前商品的事实。\n"
        self.entry.write_text(self.valid_text, encoding="utf-8")

    def test_valid_unicode_path_and_content(self):
        self.assertEqual(validator.validate_skill(self.skill), [])

    def test_empty_description_is_rejected(self):
        self.entry.write_text(self.valid_text.replace("description: 商品设计验证样例", "description: ''"), encoding="utf-8")
        self.assertIn("invalid description", validator.validate_skill(self.skill))

    def test_name_must_match_folder(self):
        self.entry.write_text(self.valid_text.replace("name: test-skill", "name: other-skill"), encoding="utf-8")
        self.assertIn("skill name does not match directory", validator.validate_skill(self.skill))

    def test_duplicate_yaml_keys_are_rejected(self):
        self.entry.write_text(self.valid_text.replace("name: test-skill", "name: test-skill\nname: other-skill"), encoding="utf-8")
        self.assertTrue(any("invalid frontmatter" in e for e in validator.validate_skill(self.skill)))

    def test_unsafe_yaml_tag_is_rejected(self):
        self.entry.write_text("---\n!!python/object/apply:builtins.print ['never execute']\n---\nbody", encoding="utf-8")
        self.assertTrue(any("invalid frontmatter" in e for e in validator.validate_skill(self.skill)))

    def test_missing_resource_is_rejected(self):
        self.entry.write_text(self.valid_text + "\n[方法](references/missing.md)\n", encoding="utf-8")
        self.assertTrue(any("missing linked resource" in e for e in validator.validate_skill(self.skill)))

    def test_link_outside_package_is_rejected(self):
        (self.skill.parent / "outside.md").write_text("outside", encoding="utf-8")
        self.entry.write_text(self.valid_text + "\n[越界](../outside.md)\n", encoding="utf-8")
        self.assertTrue(any("link escapes package" in e for e in validator.validate_skill(self.skill)))

    def test_windows_absolute_path_is_rejected(self):
        self.entry.write_text(self.valid_text + "\n[本机文件](C:/private/source.md)\n", encoding="utf-8")
        self.assertTrue(any("nonportable resource link" in e for e in validator.validate_skill(self.skill)))

    def test_license_must_be_packaged(self):
        self.entry.write_text(self.valid_text.replace("description:", "license: MIT\ndescription:"), encoding="utf-8")
        self.assertIn("MIT license is not bundled", validator.validate_skill(self.skill))

    def test_undiscoverable_reference_is_rejected(self):
        (self.skill / "orphan.md").write_text("unlinked", encoding="utf-8")
        self.assertTrue(any("undiscoverable" in e for e in validator.validate_skill(self.skill)))

    def test_unreachable_reference_cycle_is_rejected(self):
        (self.skill / "a.md").write_text("[B](b.md)", encoding="utf-8")
        (self.skill / "b.md").write_text("[A](a.md)", encoding="utf-8")
        errors = validator.validate_skill(self.skill)
        self.assertEqual(sum("undiscoverable" in e for e in errors), 2)

    def test_nested_discoverable_references_are_valid(self):
        self.entry.write_text(self.valid_text + "\n[A](a.md)\n", encoding="utf-8")
        (self.skill / "a.md").write_text("[B](b.md)", encoding="utf-8")
        (self.skill / "b.md").write_text("end", encoding="utf-8")
        self.assertEqual(validator.validate_skill(self.skill), [])

    def test_resource_symlink_escape_is_rejected(self):
        outside = self.skill.parent / "outside.md"
        outside.write_text("outside fixture", encoding="utf-8")
        try:
            (self.skill / "linked.md").symlink_to(outside)
        except OSError:
            self.skipTest("symlink creation is unavailable in this test environment")
        self.assertTrue(any("escapes package" in e for e in validator.validate_skill(self.skill)))

    def test_placeholder_is_rejected(self):
        self.entry.write_text(self.valid_text + "\n[TODO: write guidance]\n", encoding="utf-8")
        self.assertTrue(any("unfinished scaffold" in e for e in validator.validate_skill(self.skill)))

    def test_invalid_interface_is_rejected(self):
        (self.skill / "agents").mkdir()
        (self.skill / "agents/openai.yaml").write_text("interface: []\n", encoding="utf-8")
        self.assertIn("invalid UI metadata", validator.validate_skill(self.skill))

    def test_duplicate_evaluation_ids_are_rejected(self):
        case = {"id": "E01", "context": "no files", "prompt": "只策划", "expected_stage": "S0", "should_select": True, "must": ["ask"], "must_not": ["submit"]}
        path = self.skill.parent / "cases.json"
        path.write_text(json.dumps({"schema_version": 1, "rubric_version": "1.0", "cases": [case, case]}), encoding="utf-8")
        self.assertTrue(any("duplicate identity" in e for e in validator.validate_cases(path)))


if __name__ == "__main__":
    unittest.main()
