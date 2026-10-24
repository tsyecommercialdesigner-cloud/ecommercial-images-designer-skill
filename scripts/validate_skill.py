"""Validate a skill package and evaluation data; never call a provider or mutate input."""

from __future__ import annotations

import argparse
import re
from pathlib import Path, PureWindowsPath
from urllib.parse import unquote, urlsplit

import yaml

REPO = Path(__file__).resolve().parents[1]
DEFAULT_SKILL = REPO / ".agents/skills/ecommerce-image-designer"
FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
STAGES = {f"S{i}" for i in range(6)} | {"outside"}


class UniqueLoader(yaml.SafeLoader):
    """Reject ambiguous duplicate mapping keys as well as unsafe YAML tags."""


def unique_mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str) or key in result:
            raise ValueError("YAML keys must be unique strings")
        result[key] = loader.construct_object(value_node)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def read_mapping(text: str) -> dict:
    value = yaml.load(text, Loader=UniqueLoader)
    if not isinstance(value, dict):
        raise ValueError("expected a mapping")
    return value


def validate_skill(directory: Path) -> list[str]:
    directory = directory.resolve()
    errors: list[str] = []
    entry = directory / "SKILL.md"
    if not entry.is_file():
        return ["missing SKILL.md"]
    if not entry.resolve().is_relative_to(directory):
        return ["SKILL.md escapes the package"]
    try:
        text = entry.read_text(encoding="utf-8")
        match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
        if not match:
            return ["invalid YAML frontmatter delimiters"]
        meta = read_mapping(match[1])
    except (OSError, UnicodeError, yaml.YAMLError, ValueError) as exc:
        return [f"invalid frontmatter: {type(exc).__name__}"]

    if set(meta) - FIELDS:
        errors.append("unsupported frontmatter fields")
    name = meta.get("name")
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
        errors.append("invalid skill name")
    if name != directory.name:
        errors.append("skill name does not match directory")
    description = meta.get("description")
    if not isinstance(description, str) or not 1 <= len(description.strip()) <= 1024:
        errors.append("invalid description")
    elif re.search(r"<[^>]*>", description):
        errors.append("description contains XML tags")
    for key in ("license", "allowed-tools", "compatibility"):
        if key in meta and (not isinstance(meta[key], str) or not meta[key].strip()):
            errors.append(f"invalid {key}")
    if isinstance(meta.get("compatibility"), str) and len(meta["compatibility"]) > 500:
        errors.append("compatibility exceeds 500 characters")
    if "metadata" in meta and (not isinstance(meta["metadata"], dict) or any(not isinstance(v, str) for v in meta["metadata"].values())):
        errors.append("metadata must map strings to strings")
    if not text[match.end():].strip():
        errors.append("empty skill body")
    if len(text[match.end():].splitlines()) > 500:
        errors.append("skill body exceeds the project budget of 500 lines")
    if meta.get("license") == "MIT" and not (directory / "LICENSE").is_file():
        errors.append("MIT license is not bundled")

    # All Markdown runtime links are expressed from the skill root by convention.
    markdown_files = list(directory.rglob("*.md"))
    links: dict[Path, set[Path]] = {}
    for md in markdown_files:
        if not md.resolve().is_relative_to(directory):
            errors.append(f"resource escapes package: {md.name}")
            continue
        content = md.read_text(encoding="utf-8")
        links[md.resolve()] = set()
        unfenced = re.sub(r"(?ms)^\s*(`{3,}|~{3,})[^\n]*\n.*?^\s*\1\s*$", "", content)
        if re.search(r"(?m)^\s*\[TODO:[^\n]*\]\s*$", unfenced):
            errors.append(f"unfinished scaffold: {md.name}")
        for target in re.findall(r"!?\[[^\]\n]*\]\(([^)\n]+)\)", unfenced):
            target = target.strip().strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme in {"https", "http"}:
                continue
            if parsed.scheme or PureWindowsPath(target).is_absolute() or "\\" in target:
                errors.append(f"nonportable resource link in {md.name}")
                continue
            if not parsed.path:
                continue
            resolved = (directory / unquote(parsed.path)).resolve()
            if not resolved.is_relative_to(directory):
                errors.append(f"link escapes package in {md.name}")
            elif not resolved.is_file():
                errors.append(f"missing linked resource in {md.name}: {parsed.path}")
            else:
                current = directory
                for part in Path(unquote(parsed.path)).parts:
                    if part not in {p.name for p in current.iterdir()}:
                        errors.append(f"resource link case or spelling mismatch in {md.name}: {parsed.path}")
                        break
                    current = current / part
                links[md.resolve()].add(resolved)

    # Project policy: required guidance must be directly indexed by SKILL.md.
    # Cross-resource links may provide navigation, never hide another dependency.
    reached = {entry.resolve()} | links.get(entry.resolve(), set())
    for md in markdown_files:
        if md.resolve() not in reached:
            errors.append(f"undiscoverable Markdown resource (not directly indexed): {md.name}")
    for resource in directory.rglob("*"):
        if not resource.resolve().is_relative_to(directory):
            errors.append(f"resource escapes package: {resource.name}")
        relative = resource.relative_to(directory)
        if resource.is_dir() and (len(relative.parts) != 1 or relative.name not in {"reference", "scripts", "assets", "agents"}):
            errors.append(f"unsupported or nested resource directory: {relative.as_posix()}")
        if resource.is_file():
            if len(relative.parts) == 1 and resource.name not in {"SKILL.md", "LICENSE"}:
                errors.append(f"unexpected root resource: {relative.as_posix()}")
            if relative.parts[0] in {"scripts", "assets"} and resource.resolve() not in reached:
                errors.append(f"resource not directly indexed: {relative.as_posix()}")
    names = [p.relative_to(directory).as_posix().casefold() for p in directory.rglob("*")]
    if len(names) != len(set(names)):
        errors.append("case-insensitive resource name collision")

    ui = directory / "agents/openai.yaml"
    if ui.exists() and ui.resolve().is_relative_to(directory):
        try:
            data = read_mapping(ui.read_text(encoding="utf-8"))
            interface = data.get("interface", {})
            if not isinstance(interface, dict):
                raise ValueError("invalid interface")
            display = interface.get("display_name")
            short = interface.get("short_description")
            if not isinstance(display, str) or not display.strip():
                errors.append("invalid UI display name")
            if not isinstance(short, str) or not 25 <= len(short) <= 64:
                errors.append("invalid UI short description")
            default = interface.get("default_prompt")
            if default is not None and (not isinstance(default, str) or f"${name}" not in default):
                errors.append("default prompt does not name this skill")
        except (OSError, UnicodeError, ValueError, yaml.YAMLError):
            errors.append("invalid UI metadata")
    return list(dict.fromkeys(errors))


def validate_cases(path: Path) -> list[str]:
    import json

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return ["evaluation data cannot be read"]
    if not isinstance(data, dict) or data.get("schema_version") != 1 or data.get("rubric_version") not in {"1.0", "2.0-core"}:
        return ["invalid evaluation schema or rubric version"]
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        return ["evaluation cases must not be empty"]
    errors, seen = [], set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"case {index} is not an object")
            continue
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            errors.append(f"case {index} has invalid or duplicate identity")
        else:
            seen.add(case_id)
        for key in ("prompt", "context"):
            if not isinstance(case.get(key), str) or not case[key].strip():
                errors.append(f"case {index} lacks {key}")
        if case.get("expected_stage") not in STAGES or type(case.get("should_select")) is not bool:
            errors.append(f"case {index} has invalid routing")
        for key in ("must", "must_not"):
            value = case.get(key)
            if not isinstance(value, list) or not value or any(not isinstance(v, str) or not v.strip() for v in value):
                errors.append(f"case {index} lacks {key} assertions")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", type=Path, default=DEFAULT_SKILL)
    parser.add_argument("--evals", type=Path)
    args = parser.parse_args()
    errors = validate_skill(args.skill)
    if args.evals:
        errors.extend(validate_cases(args.evals))
    for error in errors:
        print(f"FAIL: {error}")
    print(f"{'FAIL' if errors else 'PASS'}: package structure and resource checks only")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
