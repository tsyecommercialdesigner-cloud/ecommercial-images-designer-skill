"""Real Codex CLI skill discovery smoke tests, with only free MCP tools exposed.

Copies the skill into fresh repository-scope discovery directories. No injected
skill catalog or mock MCP; raw evidence uses a dedicated ignored workspace inside the source repository.
Uses existing server launch commands, never copies credentials or environment.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import time
import tomllib

from system_skills_guard import (SystemSkillsMismatch, host_suite_lock,
                                 prepare_system_skills, verify_cache)

REPO = Path(__file__).resolve().parents[1]

_workspace_spec = importlib.util.spec_from_file_location('evaluation_workspace', Path(__file__).with_name('evaluation_workspace.py'))
_workspace = importlib.util.module_from_spec(_workspace_spec)
_workspace_spec.loader.exec_module(_workspace)
validate_root, claim_root, initialize_project = _workspace.validate_root, _workspace.claim_root, _workspace.initialize_project

FREE = {
    "zhenzhen-gptimagegen2-5-mcp": ["get_model_guide"],
    "zhenzhen-nanobanana-mcp": ["list_models", "inspect_design_images", "get_ecommerce_design"],
}
DISABLED = ["apps", "plugins", "hooks", "image_generation", "browser_use",
            "browser_use_external", "computer_use", "multi_agent", "memories",
            "code_mode", "skill_mcp_dependency_install"]


def classify_status(exit_code, answer_exists: bool, diagnostic: str) -> str:
    if "failed to spawn code-mode host" in diagnostic or "Code Mode is unavailable" in diagnostic:
        return "tool_host_unavailable"
    if "helper_sandbox_lock_failed" in diagnostic:
        return "sandbox_setup_failed"
    if "blocked by policy" in diagnostic:
        return "resource_blocked"
    if "failed to install system skills" in diagnostic:
        return "system_skill_install_failed"
    return "completed" if exit_code == 0 and answer_exists else "infrastructure_error"


def run(root: Path, case: str, repeat: int, servers: dict, timeout: int,
        cli: Path, host_home: Path, expected_cache: dict):
    work = root / f"{case}-r{repeat}"
    work.mkdir()  # Never overwrite an existing trial.
    initialize_project(work)
    target = work / ".agents/skills/ecommerce-image-designer"
    shutil.copytree(REPO / ".agents/skills/ecommerce-image-designer", target)
    spec = importlib.util.spec_from_file_location("fixtures", REPO / "evals/mock_mcp.py")
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    fixture.png_fixture(work / "P01.png")
    fixture.png_fixture(work / "R01.png", reference=True)
    # The image drawing helper is reused only to create inputs. No mock server
    # is launched or made available to the tested host.
    record = dict(design_id="host-fixture", version=1, scope="synthetic test only",
                  facts=[dict(id="F01", value="灰色盒体、深灰盖沿", source="合成夹具")],
                  images=[dict(id="P01", role="product", source="P01.png"),
                          dict(id="R01", role="reference", reference_use="style", source="R01.png")],
                  accepted_images=["M01"], changed_image="M02",
                  previous_layout="M02上标题下商品", paid_authorization=False)
    (work / "design-record.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    prompts = {
        "explicit": "$ecommerce-image-designer\n首次为收纳盒做电商主图，目前没有图片。只先讨论，不出图。请免费查询两个指定MCP的模型/配置状态，给出下一步。",
        "implicit": "为附件所示盒子策划一张电商主图，先给文案排版和完整提示词草案，不出图。这里是集成测试：第一张是合成商品外观夹具P01，第二张R01只作风格参考，禁止借用其商品颜色和布局。事实仅限灰色盒体和深灰盖沿；不要推断材质、容量或性能。可以通过免费MCP实际查看两张图片。",
        "negative": "只帮我拟一份学习Python的三天计划，每天半小时。没有电商或图片需求。",
        "recovery": "读取design-record.json恢复这份合成测试设计。用户已接受M01，M02反馈是标题区太挤，请给具体调整布局及相应完整提示词草案，商品、事实和M01不变。只改方案，不出图；说明回退到哪一步以及还须确认什么。",
    }
    prompt = prompts[case] + "\n本次只做非收费宿主验证，禁止生成/编辑/提交/重试图片，禁止读取密钥或其他用户配置，不安装依赖、不修改源仓库。"
    command = [str(cli), "exec", "--ignore-user-config",
               "--ephemeral", "--skip-git-repo-check", "--sandbox", "read-only",
               "-C", str(work), "--color", "never", "--json", "-o", str(work / "answer.txt")]
    for feature in DISABLED:
        command += ["-c", f"features.{feature}=false"]
    command += ["-c", 'web_search="disabled"', "-c", 'approval_policy="never"']
    # --ignore-user-config also removes the native Windows sandbox selector.
    # Keep the read-only policy and explicitly activate its existing backend;
    # never fall back to unsandboxed execution or ignore execpolicy rules.
    import os
    if os.name == "nt":
        command += ["-c", 'windows.sandbox="elevated"']
    for name, allowed in FREE.items():
        server = servers[name]
        for key, value in {"command": server["command"], "args": server.get("args", []),
                           "enabled_tools": allowed, "startup_timeout_sec": 60,
                           "tool_timeout_sec": 60, "default_tools_approval_mode": "approve"}.items():
            command += ["-c", f"mcp_servers.{name}.{key}=" + json.dumps(value)]
    if case == "implicit":
        command += ["-i", str(work / "P01.png"), "-i", str(work / "R01.png")]
    command += ["-"]
    (work / "command.json").write_text(json.dumps(command, indent=2), encoding="utf-8")
    (work / "input.txt").write_text(prompt, encoding="utf-8")
    started = time.time()
    with (work / "events.jsonl").open("w", encoding="utf-8") as out, (work / "stderr.txt").open("w", encoding="utf-8") as err:
        try:
            verify_cache(host_home, expected_cache)
            proc = subprocess.run(command, input=prompt, text=True, encoding="utf-8", stdout=out, stderr=err, timeout=timeout)
            result = dict(case=case, repeat=repeat, exit_code=proc.returncode,
                          status="completed" if proc.returncode == 0 and (work / "answer.txt").exists() else "infrastructure_error")
        except subprocess.TimeoutExpired:
            result = dict(case=case, repeat=repeat, exit_code=None, status="timeout")
        except SystemSkillsMismatch as exc:
            result = dict(case=case, repeat=repeat, exit_code=None,
                          status="system_skill_cache_mismatch", error=str(exc))
    result["seconds"] = round(time.time() - started, 2)
    diagnostic = (work / "stderr.txt").read_text(encoding="utf-8", errors="replace")
    # Fatal tool-host events can accompany a final answer and process exit 0.
    # Inspect error events, not arbitrary phrases in the model's own prose.
    for line in (work / "events.jsonl").read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item", {})
        if isinstance(item, dict) and item.get("type") == "error":
            diagnostic += "\n" + str(item.get("message", ""))
    result["resource_read_blocked"] = "blocked by policy" in diagnostic
    result["sandbox_setup_failed"] = "helper_sandbox_lock_failed" in diagnostic
    result["system_skill_install_error"] = "failed to install system skills" in diagnostic
    result["tool_host_unavailable"] = "failed to spawn code-mode host" in diagnostic or "Code Mode is unavailable" in diagnostic
    if result["status"] not in {"timeout", "system_skill_cache_mismatch"}:
        result["status"] = classify_status(result["exit_code"], (work / "answer.txt").exists(), diagnostic)
    try:
        verify_cache(host_home, expected_cache)
    except SystemSkillsMismatch as exc:
        result.update(status="system_skill_cache_mismatch", error=str(exc))
    (work / "trial.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cli", type=Path, required=True,
                        help="Explicit installed CLI matching the shared system-skill package")
    parser.add_argument("--system-cache-layout", choices=["legacy", "versioned"], default="legacy")
    parser.add_argument("--cli-sha256", help="Required exact binary identity for a versioned candidate")
    parser.add_argument("--cases", default="explicit,implicit,negative,recovery")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=240)
    args = parser.parse_args()
    root = args.output.resolve()
    if root.exists() or args.repeats < 1 or not 1 <= args.workers <= 3:
        parser.error("Use a new repository-local evidence workspace and bounded repeats/workers")
    cli = args.cli.resolve(strict=True)
    actual_sha256 = hashlib.sha256(cli.read_bytes()).hexdigest()
    if args.system_cache_layout == "versioned" and not args.cli_sha256:
        parser.error("Versioned candidate requires its verified --cli-sha256")
    if args.cli_sha256 and args.cli_sha256.lower() != actual_sha256:
        parser.error("Selected CLI SHA256 differs; no Host process started")
    try:
        validate_root(root)
    except ValueError as exc:
        parser.error(str(exc))
    component_names = ["codex-command-runner.exe", "codex-windows-sandbox-setup.exe", "codex-code-mode-host.exe"]
    components = {name: hashlib.sha256((cli.parent / name).read_bytes()).hexdigest()
                  for name in component_names if (cli.parent / name).is_file()}
    if args.system_cache_layout == "versioned" and len(components) != len(component_names):
        parser.error("Versioned candidate is missing its paired sandbox or tool-host components")
    cases = args.cases.split(",")
    if not cases or len(set(cases)) != len(cases) or set(cases) - {"explicit", "implicit", "negative", "recovery"}:
        parser.error("Unknown or duplicate case")
    import os
    host_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).resolve()
    config = tomllib.loads((host_home / "config.toml").read_text(encoding="utf-8"))
    servers = config.get("mcp_servers", {})
    for name in FREE:
        if name not in servers or not servers[name].get("command"):
            parser.error("Existing stdio server configuration required: " + name)
    claim_root(root)
    manifest = {str(p.relative_to(REPO)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (REPO / ".agents/skills/ecommerce-image-designer").rglob("*") if p.is_file()}
    run_manifest = dict(cli=str(cli), cli_version=subprocess.check_output([str(cli), "--version"], text=True).strip(),
        cli_sha256=actual_sha256, cli_components_sha256=components, system_cache_layout=args.system_cache_layout,
        cases=cases, repeats=args.repeats, free_tool_allowlist=FREE, disabled=DISABLED,
        skill_manifest=manifest, synthetic_inputs=True, mock_server=False,
        native_session_resume=False, windows_sandbox="elevated", sandbox_mode="read-only")
    (root / "run.json").write_text(json.dumps(run_manifest, indent=2), encoding="utf-8")
    results = []
    try:
        with host_suite_lock(REPO / ".eval-cache/system-skills-host.lock"):
            expected = prepare_system_skills(cli, host_home, root, args.system_cache_layout)
            run_manifest["system_skills_marker"] = expected["marker"]
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                futures = [pool.submit(run, root, case, repeat, servers, args.timeout,
                           cli, host_home, expected)
                           for case in cases for repeat in range(1, args.repeats + 1)]
                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)
                    print(json.dumps(result), flush=True)
            verify_cache(host_home, expected)
    except (SystemSkillsMismatch, TimeoutError) as exc:
        run_manifest.update(system_skills_guard="failed", guard_error=str(exc))
        print(json.dumps({"status": "system_skills_guard_failed", "error": str(exc)}), flush=True)
        return 2
    finally:
        run_manifest["results"] = results
        (root / "run.json").write_text(json.dumps(run_manifest, indent=2), encoding="utf-8")
    run_manifest["system_skills_guard"] = "passed"
    (root / "run.json").write_text(json.dumps(run_manifest, indent=2), encoding="utf-8")
    # Completion is not a semantic pass. Inspect the actual replies/tool traces.
    return int(any(result["status"] != "completed" for result in results))


if __name__ == "__main__":
    raise SystemExit(main())
