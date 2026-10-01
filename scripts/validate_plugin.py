#!/usr/bin/env python3
"""Validate the portable release payload using Python's standard library."""
import argparse
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

SKILLS = ("resume-tailor", "onboarding")
REFERENCE_NAMES = (
    "ats-rules.md", "document-export.md", "html-template-en.html",
    "html-template-ru.html", "locale-en.md", "locale-ru.md",
    "profile-contract.md", "research-sources.md", "section-templates.md",
    "voice-and-positioning.md",
)
MANIFESTS = ("plugin.json", ".codex-plugin/plugin.json", ".claude-plugin/plugin.json")
MARKETPLACES = (".agents/plugins/marketplace.json", ".claude-plugin/marketplace.json")
ROOT_FILES = MANIFESTS + MARKETPLACES + (
    "README.md", "README.ru.md", "LICENSE", "PRIVACY.md", "CHANGELOG.md", "AGENTS.md",
    "docs/releasing.md",
)
VERSION_RE = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")
EXPECTED_SKILL_PATHS = ["./skills/" + skill for skill in SKILLS]


def public_paths() -> tuple[str, ...]:
    """An explicit inventory: new release files must be deliberately reviewed."""
    paths = list(ROOT_FILES)
    for skill in SKILLS:
        paths.append(f"skills/{skill}/SKILL.md")
        refs = REFERENCE_NAMES if skill == "resume-tailor" else ("profile-contract.md",)
        paths.extend(f"skills/{skill}/references/{name}" for name in refs)
    return tuple(sorted(paths))


def validate_plugin(root: Path) -> list[str]:
    root = Path(root).resolve()
    errors = []
    allowed = set(public_paths())

    def safe_file(relative):
        components = [root / Path(*Path(relative).parts[:index])
                      for index in range(1, len(Path(relative).parts) + 1)]
        return not any(part.is_symlink() for part in components) and (root / relative).is_file()

    for relative in sorted(allowed):
        path = root / relative
        components = [root / Path(*Path(relative).parts[:index])
                      for index in range(1, len(Path(relative).parts) + 1)]
        if any(parent.is_symlink() for parent in components):
            errors.append(f"{relative}: symlink inputs are not allowed")
            continue
        if not path.is_file():
            errors.append(f"Missing required public file: {relative}")
    # Inspect only public component trees; unrelated checkout files never ship.
    for directory in ("skills", ".codex-plugin", ".claude-plugin", ".agents/plugins"):
        top = root / directory
        if top.is_symlink():
            errors.append(f"{directory}: symlink directory is not allowed")
            continue
        if not top.is_dir():
            errors.append(f"Missing component directory: {directory}")
            continue
        for path in top.rglob("*"):
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                errors.append(f"{relative}: symlink inputs are not allowed")
            elif path.is_dir():
                if not any(name.startswith(relative + "/") for name in allowed):
                    errors.append(f"Unexpected public directory: {relative}")
            elif relative not in allowed:
                errors.append(f"Unexpected public file: {relative}")
            elif not path.is_file():
                errors.append(f"{relative}: only regular files are allowed")

    def read_json(relative):
        path = root / relative
        if not safe_file(relative):
            return None
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError("expected a JSON object")
            return value
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"{relative}: invalid JSON ({exc})")
            return None

    manifests = {relative: read_json(relative) for relative in MANIFESTS}
    canonical = manifests["plugin.json"]
    if canonical is not None:
        if canonical.get("name") != "resume-tailor":
            errors.append("plugin.json: name must be resume-tailor")
        version = canonical.get("version")
        if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
            errors.append("plugin.json: version must be a numeric X.Y.Z without leading zeros")
        if canonical.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
            errors.append("plugin.json: expected the Agent Plugins 1.0.0 schema")
        if canonical.get("license") != "MIT":
            errors.append("plugin.json: license must be MIT")
        if not isinstance(canonical.get("description"), str) or not canonical["description"].strip():
            errors.append("plugin.json: nonempty description is required")

    def check_metadata(data, relative):
        if data is None or canonical is None:
            return
        for key in ("name", "version", "description", "author", "homepage", "repository", "license", "keywords"):
            if key not in canonical or data.get(key) != canonical.get(key):
                errors.append(f"{relative}: {key} must match plugin.json")

    for relative in MANIFESTS[1:]:
        data = manifests[relative]
        check_metadata(data, relative)
        if data is not None and data.get("skills") != EXPECTED_SKILL_PATHS:
            errors.append(f"{relative}: skills must list exactly the two local skill directories")
    for relative in MARKETPLACES:
        data = read_json(relative)
        if data is None:
            continue
        plugins = data.get("plugins")
        if not isinstance(plugins, list) or len(plugins) != 1 or not isinstance(plugins[0], dict):
            errors.append(f"{relative}: exactly one plugin entry is required")
            continue
        entry = plugins[0]
        check_metadata(entry, relative)
        expected_source = {"source": "local", "path": "./"} if relative.startswith(".agents") else "./"
        if entry.get("source") != expected_source:
            errors.append(f"{relative}: source must refer to the local plugin root")
        if relative.startswith(".claude"):
            if entry.get("skills") != EXPECTED_SKILL_PATHS:
                errors.append(f"{relative}: skills must list exactly the two local skill directories")
            metadata = data.get("metadata")
            if not isinstance(metadata, dict):
                errors.append(f"{relative}: metadata must be a JSON object")
            elif canonical is not None and metadata.get("version") != canonical.get("version"):
                errors.append(f"{relative}: metadata version must match plugin.json")

    for skill in SKILLS:
        skill_root = root / "skills" / skill
        path = skill_root / "SKILL.md"
        if not safe_file(path.relative_to(root)):
            continue
        try:
            content = path.read_text(encoding="utf-8")
            frontmatter = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", content, re.S)
            if not frontmatter:
                errors.append(f"skills/{skill}/SKILL.md: missing frontmatter")
            else:
                values = dict(re.findall(r"^([a-z-]+):\s*(.+)$", frontmatter[1], re.M))
                if values.get("name") != skill or not values.get("description", "").strip():
                    errors.append(f"skills/{skill}/SKILL.md: name/description frontmatter is invalid")
            # References in either a skill or its Markdown references must resolve
            # inside that skill's standalone installation, without sibling paths.
            for document in (skill_root / "SKILL.md", *sorted((skill_root / "references").glob("*.md"))):
                if not safe_file(document.relative_to(root)):
                    continue
                text = document.read_text(encoding="utf-8")
                for link in re.findall(r"\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)", text):
                    parsed = urlsplit(link.strip("<>"))
                    if parsed.scheme or parsed.netloc or not parsed.path:
                        continue
                    target = document.parent / unquote(parsed.path)
                    if not target.resolve().is_relative_to(skill_root.resolve()):
                        errors.append(f"{document.relative_to(root)}: reference outside standalone skill: {link}")
                    elif not target.is_file():
                        errors.append(f"{document.relative_to(root)}: missing reference: {link}")
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"skills/{skill}: unable to validate text ({exc})")
    contracts = [root / "skills" / skill / "references/profile-contract.md" for skill in SKILLS]
    if all(safe_file(path.relative_to(root)) for path in contracts):
        if contracts[0].read_bytes() != contracts[1].read_bytes():
            errors.append("The two profile contracts must be byte-identical")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate_plugin(args.root)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("Plugin validation passed (two standalone skills; aligned metadata and contracts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
