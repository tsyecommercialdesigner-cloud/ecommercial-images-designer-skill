"""Refuse destructive cross-build cache replacement during real Host checks.

Derive the selected binary's system package in a disposable child home, compare
the shared cache, then verify real discovery without starting a model or MCP.
Never remove a cache, edit ACLs, disable bundled skills, or copy credentials.
"""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import time

from probe_system_skills import client, inventory


class SystemSkillsMismatch(RuntimeError):
    pass


@contextmanager
def host_suite_lock(path: Path, timeout: float = 10):
    """Coordinate this repository's runners; other applications do not use it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        handle.seek(0, 2)
        if not handle.tell():
            handle.write(b"0")
            handle.flush()
        deadline = time.monotonic() + timeout
        while True:
            try:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise TimeoutError("Another Host suite holds the repository lock")
                time.sleep(0.1)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def verify_cache(home: Path, expected: dict) -> dict:
    if expected.get("cache_layout") == "versioned":
        from versioned_system_skills_guard import verify_versioned_cache
        return verify_versioned_cache(home, expected)
    cache = home / "skills/.system"
    if cache.is_symlink() or (hasattr(cache, "is_junction") and cache.is_junction()):
        raise SystemSkillsMismatch("Shared system cache is a link; stop for review")
    observed = inventory(home)
    if not expected["marker"] or observed != expected:
        raise SystemSkillsMismatch(
            "Selected CLI's bundled system package differs from the shared cache; "
            "use the matching installed Host CLI and retain the existing cache. "
            f"Expected marker={expected['marker']}, observed marker={observed['marker']}")
    return observed


def verify_discovery(result: dict, home: Path, expected: dict):
    if expected.get("cache_layout") == "versioned":
        from versioned_system_skills_guard import verify_versioned_discovery
        return verify_versioned_discovery(result, home, expected)
    if result["error"] or result["exit_code"] != 0 or result["system_skill_install_error"]:
        raise SystemSkillsMismatch("System-skill startup failed; inspect the preflight logs")
    root = (home / "skills/.system").resolve()
    actual_paths = []
    try:
        actual_paths = [Path(skill["path"]).resolve().relative_to(root).as_posix()
                        for skill in result["system_skills"]]
    except ValueError as exc:
        raise SystemSkillsMismatch("System discovery returned a path outside its cache") from exc
    expected_paths = {path for path in expected["files"] if path.endswith("/SKILL.md")}
    if not expected_paths or len(actual_paths) != len(expected_paths) or set(actual_paths) != expected_paths:
        raise SystemSkillsMismatch("System-skill catalog is incomplete or contains unexpected paths")


def prepare_system_skills(cli: Path, host_home: Path, root: Path, cache_layout="legacy") -> dict:
    if cache_layout == "versioned":
        from versioned_system_skills_guard import prepare_versioned_system_skills
        return prepare_versioned_system_skills(cli, host_home, root)
    if cache_layout != "legacy":
        raise SystemSkillsMismatch("Unknown system cache layout")
    preflight = root / "system-skills-preflight"
    preflight.mkdir()
    child_home = preflight / "child-home"
    child_home.mkdir()
    record = {"selected_cli": str(cli), "host_home": str(host_home),
              "model_calls": 0, "mcp_calls": 0, "global_cache_repair_attempted": False}
    try:
        isolated = client(cli, child_home, root, preflight / "isolated")
        expected = inventory(child_home)
        record["expected"] = expected
        verify_discovery(isolated, child_home, expected)
        record["shared_before"] = inventory(host_home)
        verify_cache(host_home, expected)  # Stop BEFORE a mismatched build can replace it.
        observed = client(cli, host_home, root, preflight / "shared-discovery")
        record["shared_discovery"] = observed
        verify_discovery(observed, host_home, expected)
        record["shared_after"] = verify_cache(host_home, expected)
        record["status"] = "passed"
        return expected
    except Exception as exc:
        record.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        (preflight / "preflight.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
