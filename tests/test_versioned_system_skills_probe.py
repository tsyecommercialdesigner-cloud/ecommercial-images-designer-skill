from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from probe_versioned_system_skills import package, retain_cold_fixture, selected_cache, verify


class VersionedProbeTests(unittest.TestCase):
    def setUp(self):
        self.owned = tempfile.TemporaryDirectory()
        self.addCleanup(self.owned.cleanup)
        self.home = Path(self.owned.name).resolve()
        self.root = self.home / "skills/.system-cache-v2/deadbeef"
        (self.root / "sample").mkdir(parents=True)
        (self.root / "sample/SKILL.md").write_text("owned fixture", encoding="utf-8")
        (self.root / ".codex-system-skills.marker").write_text("deadbeef", encoding="utf-8")
        self.result = {"exit_code": 0, "error": None, "system_skill_install_error": False,
                       "system_skills": [{"path": str(self.root / "sample/SKILL.md")}]}

    def test_actual_selected_root_and_whole_package_are_required(self):
        self.assertEqual(selected_cache(self.home, self.result), self.root)
        verify(self.result, self.root, package(self.root))
        expected = package(self.root)
        (self.root / "sample/SKILL.md").write_text("different bytes", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "content changed"):
            verify(self.result, self.root, expected)

    def test_legacy_or_foreign_root_cannot_be_moved_as_candidate(self):
        for root in (self.home / "skills/.system", self.home.parent / "foreign"):
            result = self.result | {"system_skills": [{"path": str(root / "sample/SKILL.md")}]}
            with self.assertRaises(ValueError):
                selected_cache(self.home, result)
            with self.assertRaises(ValueError):
                retain_cold_fixture(self.home, root)

    def test_split_or_empty_catalog_is_not_a_selected_root(self):
        for skills in ([], self.result["system_skills"] + [{"path": str(self.root.parent / "other/sample/SKILL.md")}]):
            with self.assertRaises(ValueError):
                selected_cache(self.home, self.result | {"system_skills": skills})

    def test_cold_fixture_move_preserves_bytes_and_refuses_existing_target(self):
        before = package(self.root)
        retained = retain_cold_fixture(self.home, self.root)
        self.assertFalse(self.root.exists())
        self.assertEqual(package(retained), before)
        self.root.mkdir()
        with self.assertRaises(ValueError):
            retain_cold_fixture(self.home, self.root)
        self.assertEqual(package(retained), before)

    def test_zero_exit_install_error_or_incomplete_catalog_fails(self):
        expected = package(self.root)
        for result in (self.result | {"system_skill_install_error": True},
                       self.result | {"system_skills": []},
                       self.result | {"system_skills": self.result["system_skills"] * 2}):
            with self.assertRaises(ValueError):
                verify(result, self.root, expected)

    def test_extra_or_missing_file_cannot_pass_matching_marker(self):
        expected = package(self.root)
        (self.root / "unexpected").write_text("fixture", encoding="utf-8")
        with self.assertRaises(ValueError):
            verify(self.result, self.root, expected)
        (self.root / "sample/SKILL.md").unlink()
        with self.assertRaises(ValueError):
            verify(self.result, self.root, expected)
