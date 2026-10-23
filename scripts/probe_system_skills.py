"""Model-free app-server system-skill startup probe in disposable child homes.

Only initialize/initialized/skills/list are sent. No thread or turn is created,
no MCP is configured, and the caller's Codex home/configuration is not changed.
The child-process CODEX_HOME setting is confined to a newly created test fixture.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import time


def inventory(home: Path) -> dict:
    root = home / "skills/.system"
    marker = root / ".codex-system-skills.marker"
    files = {}
    if root.exists():
        for path in sorted(root.rglob("*")):
            if path.is_file():
                try:
                    files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
                except OSError as exc:
                    files[path.relative_to(root).as_posix()] = {"error": str(exc)}
    try:
        fingerprint = marker.read_text(encoding="utf-8").strip()
    except OSError:
        fingerprint = None
    return {"marker": fingerprint, "files": files}


def client(cli: Path, home: Path, cwd: Path, output: Path,
           barrier: threading.Barrier | None = None) -> dict:
    output.mkdir()
    env = os.environ.copy()
    env["CODEX_HOME"] = str(home)
    command = [str(cli), "-c", 'approval_policy="never"',
               "-c", 'sandbox_mode="read-only"', "-c", 'windows.sandbox="elevated"',
               "-c", "features.apps=false", "-c", "features.plugins=false",
               "-c", "features.hooks=false", "-c", "features.image_generation=false",
               "app-server", "--stdio"]
    (output / "command.json").write_text(json.dumps(command, indent=2), encoding="utf-8")
    responses: queue.Queue = queue.Queue()
    error = None
    response = None
    process = None
    requests = []
    started = time.monotonic()
    if barrier:
        barrier.wait(timeout=30)
    with (output / "stdout.jsonl").open("w", encoding="utf-8") as stdout_log, \
            (output / "stderr.txt").open("w", encoding="utf-8") as stderr_log:
        try:
            process = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=stderr_log,
                                       text=True, encoding="utf-8")

            def read_stdout():
                for line in process.stdout:
                    stdout_log.write(line)
                    stdout_log.flush()
                    try:
                        responses.put(json.loads(line))
                    except json.JSONDecodeError:
                        responses.put({"invalid_json": line})
                responses.put({"eof": True})

            reader = threading.Thread(target=read_stdout, daemon=True)
            reader.start()

            def send(request):
                if request["method"] not in {"initialize", "initialized", "skills/list"}:
                    raise ValueError("Only model-free skill discovery is permitted")
                requests.append(request)
                process.stdin.write(json.dumps(request) + "\n")
                process.stdin.flush()

            def receive(request_id):
                deadline = time.monotonic() + 30
                while True:
                    item = responses.get(timeout=max(0.01, deadline - time.monotonic()))
                    if item.get("id") == request_id:
                        if "error" in item:
                            raise RuntimeError(json.dumps(item["error"]))
                        return item["result"]
                    if item.get("eof") or "invalid_json" in item:
                        raise RuntimeError("App-server closed or returned invalid JSON")
                    if time.monotonic() >= deadline:
                        raise TimeoutError("App-server response deadline exceeded")

            send({"id": 1, "method": "initialize", "params": {
                "clientInfo": {"name": "system_skills_probe", "version": "1"}}})
            receive(1)
            send({"method": "initialized", "params": {}})
            send({"id": 2, "method": "skills/list", "params": {
                "cwds": [str(cwd)], "forceReload": True}})
            response = receive(2)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        finally:
            if process:
                process.stdin.close()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.terminate()  # Only the child started by this probe.
                    process.wait(timeout=5)
                reader.join(timeout=5)
    (output / "requests.json").write_text(json.dumps(requests, indent=2), encoding="utf-8")
    stderr = (output / "stderr.txt").read_text(encoding="utf-8", errors="replace")
    system_skills = [skill for entry in (response or {}).get("data", [])
                     for skill in entry.get("skills", [])
                     if skill.get("scope", "").lower() == "system"]
    result = {"cli": str(cli), "child_home": str(home), "seconds": round(time.monotonic()-started, 3),
              "exit_code": process.returncode if process else None, "error": error,
              "system_skill_install_error": "failed to install system skills" in stderr,
              "remove_error": "remove existing system skills dir" in stderr,
              "system_skills": [{"name": skill["name"], "path": skill["path"]} for skill in system_skills],
              "requests": [request["method"] for request in requests]}
    (output / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cli", required=True, type=Path)
    parser.add_argument("--peer-cli", type=Path)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--clients", type=int, default=2)
    parser.add_argument("--mode", choices=["cold", "warm", "mixed"], default="cold")
    args = parser.parse_args()
    root = args.output.resolve()
    if root.exists() or not 1 <= args.rounds <= 12 or not 1 <= args.clients <= 4:
        parser.error("Use a new output directory, 1-12 rounds and 1-4 clients")
    if args.mode == "mixed" and not args.peer_cli:
        parser.error("Mixed mode requires an explicit peer CLI")
    root.mkdir(parents=True)
    versions = {str(cli): subprocess.check_output([str(cli), "--version"], text=True).strip()
                for cli in [args.cli] + ([args.peer_cli] if args.peer_cli else [])}
    batches = []
    for index in range(args.rounds):
        work = root / f"round-{index+1}"
        work.mkdir()
        home = work / "child-home"
        home.mkdir()
        cache = home / "skills/.system"
        cache.mkdir(parents=True)
        (cache / "stale-fixture.txt").write_text("Owned disposable stale cache fixture", encoding="utf-8")
        # Initialize unrelated SQLite state serially. Cold mode invalidates only
        # this disposable system cache, so database migration races cannot mask
        # the skill installer being investigated.
        seeded = client(args.cli, home, work, work / "seed")
        if seeded["error"] or seeded["system_skill_install_error"]:
            raise RuntimeError("Seed failed; inspect its logs")
        if args.mode == "cold":
            (cache / ".codex-system-skills.marker").write_text("owned-stale-fixture\n", encoding="utf-8")
        before = inventory(home)
        barrier = threading.Barrier(args.clients)
        with ThreadPoolExecutor(max_workers=args.clients) as pool:
            futures = [pool.submit(client,
                       args.peer_cli if args.mode == "mixed" and n % 2 else args.cli,
                       home, work, work / f"client-{n+1}", barrier) for n in range(args.clients)]
            results = [future.result() for future in futures]
        batch = {"round": index+1, "before": before, "after": inventory(home), "clients": results}
        batches.append(batch)
        (work / "summary.json").write_text(json.dumps(batch, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"round": index+1, "results": [
            {key: result[key] for key in ("exit_code", "error", "system_skill_install_error", "remove_error")}
            | {"system_skill_count": len(result["system_skills"])} for result in results]}, ensure_ascii=False), flush=True)
    (root / "run.json").write_text(json.dumps({"mode": args.mode, "versions": versions,
        "model_calls": 0, "mcp_calls": 0, "batches": batches}, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0  # Diagnostic failures are evidence, never silently called passes.


if __name__ == "__main__":
    raise SystemExit(main())
