from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from probe_system_skills import inventory
from system_skills_guard import SystemSkillsMismatch, prepare_system_skills, verify_cache, verify_discovery
from versioned_system_skills_guard import cache_root


def create_package(home):
    root = home / "skills/.system-cache-v2/abc123"
    (root / "sample").mkdir(parents=True, exist_ok=True)
    (root / "sample/SKILL.md").write_text("fixture", encoding="utf-8")
    (root / ".codex-system-skills.marker").write_text("abc123", encoding="utf-8")
    return {"exit_code": 0, "error": None, "system_skill_install_error": False,
            "system_skills": [{"name": "sample", "path": str(root / "sample/SKILL.md")}]}


class VersionedGuardTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.base = Path(self.folder.name).resolve()
        self.host = self.base / "host"
        old = self.host / "skills/.system"
        old.mkdir(parents=True)
        (old / "sentinel").write_text("original", encoding="utf-8")
        self.before = inventory(self.host)

    def prepare(self, client=None):
        evidence = self.base / "evidence"
        evidence.mkdir()
        def fake(cli, home, cwd, output):
            return create_package(home)
        with patch("versioned_system_skills_guard.client", side_effect=client or fake):
            return prepare_system_skills(Path("not-executed.exe"), self.host, evidence, "versioned")

    def test_new_namespace_created_without_modifying_legacy(self):
        expected = self.prepare()
        self.assertEqual(verify_cache(self.host, expected)["marker"], "abc123")
        self.assertEqual(inventory(self.host), self.before)
        verify_discovery(create_package(self.host), self.host, expected)

    def test_existing_incomplete_cache_stops_before_shared_startup(self):
        root = self.host / "skills/.system-cache-v2/abc123"
        root.mkdir(parents=True)
        (root / ".codex-system-skills.marker").write_text("abc123", encoding="utf-8")
        calls = []
        def fake(cli, home, cwd, output):
            calls.append(home)
            self.assertNotEqual(home, self.host)
            return create_package(home)
        with self.assertRaises(SystemSkillsMismatch):
            self.prepare(fake)
        self.assertEqual(len(calls), 1)
        self.assertFalse((root / "sample/SKILL.md").exists())
        self.assertEqual(inventory(self.host), self.before)

    def test_legacy_drift_does_not_pass_intact_versioned_cache(self):
        expected = self.prepare()
        (self.host / "skills/.system/sentinel").write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(SystemSkillsMismatch, "legacy cache changed"):
            verify_cache(self.host, expected)

    def test_package_changes_or_extra_catalog_paths_fail(self):
        expected = self.prepare()
        result = create_package(self.host)
        result["system_skills"].append({"path": str(self.host / "skills/.system/other/SKILL.md")})
        with self.assertRaises(SystemSkillsMismatch):
            verify_discovery(result, self.host, expected)
        (cache_root(self.host, expected) / "sample/SKILL.md").write_text("changed", encoding="utf-8")
        with self.assertRaises(SystemSkillsMismatch):
            verify_cache(self.host, expected)

    def test_path_traversal_and_fingerprint_mismatch_are_rejected(self):
        expected = self.prepare()
        for path in ("../foreign", "skills/.system", "skills/.system-cache-v2/ffff"):
            with self.assertRaises(SystemSkillsMismatch):
                cache_root(self.host, expected | {"cache_relative_path": path})

    def test_failed_discovery_is_not_success_even_with_complete_files(self):
        expected = self.prepare()
        result = create_package(self.host)
        for change in ({"system_skill_install_error": True}, {"exit_code": 1}, {"system_skills": []}):
            with self.assertRaises(SystemSkillsMismatch):
                verify_discovery(result | change, self.host, expected)

    def test_runner_rejects_unpinned_candidate_before_startup(self):
        script = Path(__file__).resolve().parents[1] / "scripts/run_host_smoke.py"
        for extra in ([], ["--cli-sha256", "0" * 64]):
            output = self.base / ("missing-pin" if not extra else "wrong-pin")
            proc = subprocess.run([sys.executable, "-B", str(script), "--output", str(output),
                                   "--cli", sys.executable, "--system-cache-layout", "versioned", *extra],
                                  capture_output=True, text=True, timeout=15)
            self.assertEqual(proc.returncode, 2, proc.stderr)
            self.assertIn("sha256", proc.stderr.lower())
            self.assertFalse(output.exists())
