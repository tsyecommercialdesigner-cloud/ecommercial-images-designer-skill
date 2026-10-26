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

    def test_chained_guidance_is_rejected_until_directly_indexed(self):
        (self.skill / "references").mkdir()
        self.entry.write_text(self.valid_text + "\n[A](references/a.md)\n", encoding="utf-8")
        (self.skill / "references/a.md").write_text("[B](references/b.md)", encoding="utf-8")
        (self.skill / "references/b.md").write_text("end", encoding="utf-8")
        self.assertTrue(any("not directly indexed" in e for e in validator.validate_skill(self.skill)))
        with self.entry.open('a', encoding='utf-8') as output:
            output.write("\n[B](references/b.md)\n")
        self.assertEqual(validator.validate_skill(self.skill), [])

    def test_legacy_or_nested_layout_is_rejected(self):
        for path in ('reference/a.md', 'references/nested/a.md'):
            with self.subTest(path=path):
                resource = self.skill / path
                resource.parent.mkdir(parents=True)
                resource.write_text('guidance', encoding='utf-8')
                self.entry.write_text(self.valid_text + f'\n[A]({path})\n', encoding='utf-8')
                self.assertTrue(any('resource directory' in e for e in validator.validate_skill(self.skill)))
                resource.unlink()
                resource.parent.rmdir()

    def test_executable_must_be_indexed_and_flat(self):
        (self.skill / 'scripts').mkdir()
        (self.skill / 'scripts/check.py').write_text('pass', encoding='utf-8')
        self.assertIn('resource not directly indexed: scripts/check.py', validator.validate_skill(self.skill))
        self.entry.write_text(self.valid_text + '\n[Check](scripts/check.py)\n', encoding='utf-8')
        self.assertEqual(validator.validate_skill(self.skill), [])

    def test_templates_and_assets_are_flat_and_directly_indexed(self):
        for folder, name in [('templates', 'report-template.json'), ('assets', 'logo.svg')]:
            resource = self.skill / folder / name
            resource.parent.mkdir()
            resource.write_text('{}', encoding='utf-8')
            self.assertIn(f'resource not directly indexed: {folder}/{name}', validator.validate_skill(self.skill))
            with self.entry.open('a', encoding='utf-8') as output:
                output.write(f'\n[Resource]({folder}/{name})\n')
            self.assertEqual(validator.validate_skill(self.skill), [])
            nested = resource.parent / 'nested'
            nested.mkdir()
            self.assertTrue(any('nested resource directory' in e for e in validator.validate_skill(self.skill)))
            nested.rmdir()

    def test_body_budget_counts_blank_and_code_lines(self):
        header = '---\nname: test-skill\ndescription: 商品设计验证样例\n---\n'
        self.entry.write_text(header + '# Title\n' + '\n' * 499, encoding='utf-8')
        self.assertEqual(validator.validate_skill(self.skill), [])
        self.entry.write_text(header + '# Title\n' + '\n' * 500, encoding='utf-8')
        self.assertTrue(any('500 lines' in e for e in validator.validate_skill(self.skill)))

    def test_link_case_is_portable_even_on_windows(self):
        (self.skill / 'references').mkdir()
        (self.skill / 'references/rules.md').write_text('guidance', encoding='utf-8')
        self.entry.write_text(self.valid_text + '\n[Rules](references/Rules.md)\n', encoding='utf-8')
        self.assertTrue(validator.validate_skill(self.skill))
        self.entry.write_text(self.valid_text + '\n[Rules](references/rules.md)\n', encoding='utf-8')
        self.assertEqual(validator.validate_skill(self.skill), [])

    def test_description_xml_and_metadata_non_string_are_rejected(self):
        self.entry.write_text(self.valid_text.replace('商品设计验证样例', '<tool>design</tool>'), encoding='utf-8')
        self.assertIn('description contains XML tags', validator.validate_skill(self.skill))
        self.entry.write_text(self.valid_text.replace('---\n\n#', 'metadata:\n  version: 1\n---\n\n#'), encoding='utf-8')
        self.assertIn('metadata must map strings to strings', validator.validate_skill(self.skill))

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
