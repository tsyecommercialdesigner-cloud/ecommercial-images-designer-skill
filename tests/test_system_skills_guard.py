"""Exercise cache integrity and fail-closed startup paths without model calls."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from probe_system_skills import inventory
from run_host_smoke import classify_status
from system_skills_guard import (SystemSkillsMismatch, host_suite_lock,
                                 prepare_system_skills, verify_cache, verify_discovery)


def package(home: Path, marker="build-a"):
    cache = home / "skills/.system"
    cache.mkdir(parents=True, exist_ok=True)
    for name in ("skill-creator", "skill-installer"):
        folder = cache / name
        folder.mkdir(exist_ok=True)
        (folder / "SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")
    (cache / ".codex-system-skills.marker").write_text(marker, encoding="utf-8")


def discovery(home):
    return {"error": None, "exit_code": 0, "system_skill_install_error": False,
            "system_skills": [{"name": name, "path": str(home / "skills/.system" / name / "SKILL.md")}
                              for name in ("skill-creator", "skill-installer")]}


class SystemSkillsGuardTests(unittest.TestCase):
    def test_mismatched_build_stops_before_shared_client_and_preserves_cache(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            host = root / "host"
            package(host, "other-build")
            before = inventory(host)
            evidence = root / "evidence"
            evidence.mkdir()
            homes = []

            def fake_client(cli, home, cwd, output):
                homes.append(home)
                self.assertNotEqual(home, host)
                package(home)
                return discovery(home)

            with patch("system_skills_guard.client", side_effect=fake_client):
                with self.assertRaises(SystemSkillsMismatch):
                    prepare_system_skills(Path("not-executed.exe"), host, evidence)
            self.assertEqual(len(homes), 1)
            self.assertEqual(inventory(host), before)
            saved = json.loads((evidence / "system-skills-preflight/preflight.json").read_text())
            self.assertEqual(saved["status"], "failed")
            self.assertFalse(saved["global_cache_repair_attempted"])
            self.assertEqual(saved["model_calls"], 0)

    def test_matching_build_requires_full_discovery_and_preserves_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            host = root / "host"
            package(host)
            before = inventory(host)
            evidence = root / "evidence"
            evidence.mkdir()
            homes = []

            def fake_client(cli, home, cwd, output):
                homes.append(home)
                if home != host:
                    package(home)
                return discovery(home)

            with patch("system_skills_guard.client", side_effect=fake_client):
                actual = prepare_system_skills(Path("not-executed.exe"), host, evidence)
            self.assertEqual(actual, before)
            self.assertEqual(homes[-1], host)
            self.assertEqual(inventory(host), before)

    def test_marker_alone_does_not_establish_package_integrity(self):
        with tempfile.TemporaryDirectory() as temporary:
            host = Path(temporary)
            package(host)
            expected = inventory(host)
            (host / "skills/.system/skill-creator/SKILL.md").write_text("truncated", encoding="utf-8")
            with self.assertRaises(SystemSkillsMismatch):
                verify_cache(host, expected)

    def test_zero_exit_partial_catalog_does_not_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            host = Path(temporary)
            package(host)
            result = discovery(host)
            result["system_skills"].pop()
            with self.assertRaises(SystemSkillsMismatch):
                verify_discovery(result, host, inventory(host))

    def test_system_discovery_outside_cache_does_not_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            host = Path(temporary)
            package(host)
            result = discovery(host)
            result["system_skills"][0]["path"] = str(host / "elsewhere/SKILL.md")
            with self.assertRaises(SystemSkillsMismatch):
                verify_discovery(result, host, inventory(host))

    def test_startup_error_is_failure_even_with_answer_and_zero_exit(self):
        text = "failed to install system skills: io error while remove existing system skills dir: os error 5"
        self.assertEqual(classify_status(0, True, text), "system_skill_install_failed")
        self.assertEqual(classify_status(1, True, text), "system_skill_install_failed")
        self.assertEqual(classify_status(0, True, ""), "completed")
        self.assertEqual(classify_status(0, False, ""), "infrastructure_error")

    def test_existing_resource_and_helper_failures_remain_failures(self):
        self.assertEqual(classify_status(0, True, "blocked by policy"), "resource_blocked")
        self.assertEqual(classify_status(0, True, "helper_sandbox_lock_failed"), "sandbox_setup_failed")
        self.assertEqual(classify_status(0, True, "failed to spawn code-mode host path: os error 2"), "tool_host_unavailable")
        self.assertEqual(classify_status(0, True, "Code Mode is unavailable because host executable was not found"), "tool_host_unavailable")

    def test_competing_process_cannot_enter_runner_lock(self):
        with tempfile.TemporaryDirectory() as temporary:
            lock = Path(temporary) / "host.lock"
            child = ("import sys; sys.path.insert(0, sys.argv[1]); "
                     "from pathlib import Path; from system_skills_guard import host_suite_lock; "
                     "\ntry:\n with host_suite_lock(Path(sys.argv[2]), timeout=0.15): pass"
                     "\nexcept TimeoutError: sys.exit(23)\n")
            with host_suite_lock(lock):
                result = subprocess.run([sys.executable, "-B", "-c", child, str(SCRIPTS), str(lock)],
                                        capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, 23, result.stderr)
            with host_suite_lock(lock):
                pass  # Released locks are reusable; no deletion-based lock races.


if __name__ == "__main__":
    unittest.main()
