"""Guard the explicitly selected versioned-cache CLI without replacing legacy caches."""
import json
from pathlib import Path
import re

from probe_system_skills import client, inventory
from probe_versioned_system_skills import package, selected_cache


def cache_root(home: Path, expected: dict) -> Path:
    from system_skills_guard import SystemSkillsMismatch
    relative = expected.get("cache_relative_path", "")
    if not re.fullmatch(r"skills/\.system-cache-v2/[0-9a-f]+", relative):
        raise SystemSkillsMismatch("Invalid versioned cache path")
    root = home / relative
    if root.name != expected["marker"]:
        raise SystemSkillsMismatch("Cache path does not match its package fingerprint")
    for path in (home / "skills", root.parent, root):
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            raise SystemSkillsMismatch("Versioned cache contains a link; stop for review")
    if not root.resolve().is_relative_to(home.resolve()):
        raise SystemSkillsMismatch("Versioned cache escaped its home")
    return root


def verify_versioned_cache(home: Path, expected: dict) -> dict:
    from system_skills_guard import SystemSkillsMismatch
    root = cache_root(home, expected)
    try:
        observed = package(root)
    except (OSError, ValueError) as exc:
        raise SystemSkillsMismatch("Versioned system package is missing or unreadable") from exc
    if observed != {key: expected[key] for key in ("marker", "files")}:
        raise SystemSkillsMismatch("Versioned system package changed; no repair attempted")
    if inventory(home) != expected["legacy_cache"]:
        raise SystemSkillsMismatch("Existing legacy cache changed; retain evidence and stop")
    return observed


def verify_versioned_discovery(result: dict, home: Path, expected: dict):
    from system_skills_guard import SystemSkillsMismatch
    root = cache_root(home, expected)
    if result["error"] or result["exit_code"] != 0 or result["system_skill_install_error"]:
        raise SystemSkillsMismatch("Versioned system-skill startup failed")
    try:
        paths = [Path(skill["path"]).resolve().relative_to(root.resolve()).as_posix()
                 for skill in result["system_skills"]]
    except ValueError as exc:
        raise SystemSkillsMismatch("System discovery escaped the selected fingerprint") from exc
    wanted = {path for path in expected["files"] if path.endswith("/SKILL.md")}
    if not wanted or len(paths) != len(wanted) or set(paths) != wanted:
        raise SystemSkillsMismatch("Versioned system catalog is incomplete or unexpected")


def prepare_versioned_system_skills(cli: Path, host_home: Path, root: Path) -> dict:
    from system_skills_guard import SystemSkillsMismatch
    preflight = root / "system-skills-preflight"
    preflight.mkdir()
    child_home = preflight / "child-home"
    child_home.mkdir()
    record = {"selected_cli": str(cli), "host_home": str(host_home),
              "model_calls": 0, "mcp_calls": 0, "global_cache_repair_attempted": False,
              "cache_layout": "versioned", "new_fingerprint_created": False}
    try:
        isolated = client(cli, child_home, root, preflight / "isolated")
        try:
            selected = selected_cache(child_home, isolated)
            expected = package(selected)
        except (ValueError, OSError) as exc:
            raise SystemSkillsMismatch("CLI did not expose a valid isolated versioned cache") from exc
        expected.update(cache_layout="versioned",
                        cache_relative_path=selected.relative_to(child_home.resolve()).as_posix(),
                        legacy_cache=inventory(host_home))
        verify_versioned_discovery(isolated, child_home, expected)
        record["expected"] = expected
        shared = cache_root(host_home, expected)
        # Existing invalid data is never repaired. A missing fingerprint can be
        # created by this verified CLI in its distinct, immutable namespace.
        if shared.exists():
            record["shared_before"] = verify_versioned_cache(host_home, expected)
        else:
            record["shared_before"] = None
            record["new_fingerprint_created"] = True
        observed = client(cli, host_home, root, preflight / "shared-discovery")
        record["shared_discovery"] = observed
        verify_versioned_discovery(observed, host_home, expected)
        record["shared_after"] = verify_versioned_cache(host_home, expected)
        record["status"] = "passed"
        return expected
    except Exception as exc:
        record.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        (preflight / "preflight.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
