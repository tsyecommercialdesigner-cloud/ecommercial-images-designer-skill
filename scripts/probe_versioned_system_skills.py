"""Model-free validation for the explicit 76d.7 versioned-cache candidate CLI.

Only the existing app-server discovery client is used. Never operates on the
user's real cache; retained cold fixtures are renamed inside their owned home.
The original legacy probe and production Host guard remain unchanged.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import subprocess
import threading

from probe_system_skills import client, inventory


def selected_cache(home: Path, result: dict) -> Path:
    roots = {Path(skill["path"]).resolve().parent.parent
             for skill in result["system_skills"]}
    if len(roots) != 1:
        raise ValueError("No single complete system root was discovered")
    root = roots.pop()
    parent = home.resolve() / "skills/.system-cache-v2"
    if root.parent != parent or not re.fullmatch(r"[0-9a-f]+", root.name):
        raise ValueError("Candidate must use its fingerprint-scoped cache in the owned home")
    for path in (root, parent, parent.parent):
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            raise ValueError("Cache links are not accepted")
    return root


def package(root: Path) -> dict:
    files = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            raise ValueError("Package contains a link")
        if path.is_file():
            files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"marker": (root / ".codex-system-skills.marker").read_text(encoding="utf-8").strip(),
            "files": files}


def verify(result: dict, root: Path, expected: dict):
    if result["exit_code"] != 0 or result["error"] or result["system_skill_install_error"]:
        raise ValueError("App-server startup failed; inspect the retained evidence")
    actual = [Path(skill["path"]).resolve().relative_to(root.resolve()).as_posix()
              for skill in result["system_skills"]]
    wanted = {name for name in expected["files"] if name.endswith("/SKILL.md")}
    if not wanted or len(actual) != len(wanted) or set(actual) != wanted:
        raise ValueError("Incomplete or unexpected system catalog")
    if package(root) != expected:
        raise ValueError("Package content changed or came from the wrong build")


def retain_cold_fixture(home: Path, root: Path) -> Path:
    """Move only this round's owned versioned package; keep all original bytes."""
    parent = home.resolve() / "skills/.system-cache-v2"
    target = root.with_name("owned-prior-" + root.name)
    if root.resolve().parent != parent or target.resolve().parent != parent:
        raise ValueError("Cold fixture move escaped its explicitly owned home")
    if target.exists() or root.is_symlink() or (hasattr(root, "is_junction") and root.is_junction()):
        raise ValueError("Cold fixture target exists or source is a link")
    root.rename(target)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cli", required=True, type=Path)
    parser.add_argument("--peer-cli", type=Path)
    parser.add_argument("--mode", choices=["cold", "warm", "mixed"], default="cold")
    parser.add_argument("--rounds", type=int, default=8)
    parser.add_argument("--clients", type=int, default=2)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not 1 <= args.rounds <= 12 or not 1 <= args.clients <= 4:
        parser.error("Use a new output directory, 1-12 rounds, 1-4 clients")
    if args.mode == "mixed" and (not args.peer_cli or args.clients < 2):
        parser.error("Mixed mode requires an explicit legacy peer and at least two clients")
    output.mkdir(parents=True)
    record = {"mode": args.mode, "model_calls": 0, "mcp_calls": 0, "batches": [],
              "versions": {str(cli): subprocess.check_output([str(cli), "--version"], text=True).strip()
                           for cli in [args.cli] + ([args.peer_cli] if args.peer_cli else [])}}
    try:
        for index in range(args.rounds):
            work = output / f"round-{index + 1}"
            work.mkdir()
            home = work / "child-home"
            home.mkdir()
            seed = client(args.cli, home, work, work / "seed")
            root = selected_cache(home, seed)
            expected = package(root)
            verify(seed, root, expected)
            legacy = home / "skills/.system"
            legacy.mkdir()
            (legacy / "owned-sentinel.txt").write_text("retained legacy fixture", encoding="utf-8")
            peer_expected = None
            if args.mode == "mixed":
                peer_home = work / "peer-package-home"
                peer_home.mkdir()
                peer_seed = client(args.peer_cli, peer_home, work, work / "peer-seed")
                peer_expected = inventory(peer_home)
                verify(peer_seed, peer_home / "skills/.system", peer_expected)
            prior = retain_cold_fixture(home, root) if args.mode != "warm" else None
            barrier = threading.Barrier(args.clients)
            with ThreadPoolExecutor(max_workers=args.clients) as pool:
                futures = [pool.submit(client,
                           args.peer_cli if args.mode == "mixed" and number % 2 else args.cli,
                           home, work, work / f"client-{number + 1}", barrier)
                           for number in range(args.clients)]
                results = [future.result() for future in futures]
            errors = []
            for number, result in enumerate(results):
                try:
                    if args.mode == "mixed" and number % 2:
                        verify(result, legacy, peer_expected)
                    else:
                        verify(result, root, expected)
                except (ValueError, OSError) as exc:
                    errors.append(f"client-{number + 1}: {exc}")
            if prior and package(prior) != expected:
                errors.append("Retained prior package changed")
            if args.mode != "mixed" and (legacy / "owned-sentinel.txt").read_text() != "retained legacy fixture":
                errors.append("Candidate changed the legacy cache")
            batch = {"round": index + 1, "clients": results, "candidate_package": expected,
                     "peer_package": peer_expected, "retained_prior": str(prior) if prior else None,
                     "errors": errors}
            record["batches"].append(batch)
            (work / "summary.json").write_text(json.dumps(batch, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({"round": index + 1, "clients": len(results), "errors": errors}), flush=True)
        record["status"] = "failed" if any(batch["errors"] for batch in record["batches"]) else "passed"
        return 0 if record["status"] == "passed" else 1
    except Exception as exc:
        record.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        (output / "run.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
