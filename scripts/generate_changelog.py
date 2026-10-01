#!/usr/bin/env python3
"""Generate release notes from validated, reachable local Git history."""
import argparse
import json
from pathlib import Path
import re
import subprocess

from validate_plugin import VERSION_RE, public_paths


def git(repo: Path, *args: str, binary: bool = False):
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                            text=not binary)
    if result.returncode:
        raise ValueError(f"Git command failed: {' '.join(args[:2])}; check repository and refs")
    return result.stdout if binary else result.stdout.strip()


def validate_tag(tag: str) -> None:
    if not isinstance(tag, str) or not tag.startswith("v") or not VERSION_RE.fullmatch(tag[1:]):
        raise ValueError("Tag/base must be vX.Y.Z with numeric components and no leading zeros")


def tag_commit(repo: Path, tag: str) -> str:
    validate_tag(tag)
    git(repo, "show-ref", "--verify", f"refs/tags/{tag}")
    return git(repo, "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}")


def is_ancestor(repo: Path, base: str, head: str) -> bool:
    result = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", base, head],
                            capture_output=True)
    if result.returncode not in (0, 1):
        raise ValueError("Unable to verify Git ancestry")
    return result.returncode == 0


def selected_history(root: Path, history_repo: Path, tag: str | None, base: str | None,
                     preview: bool) -> tuple[str, str | None, str]:
    root, history_repo = Path(root).resolve(), Path(history_repo).resolve()
    version = json.loads((root / "plugin.json").read_text(encoding="utf-8")).get("version")
    if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
        raise ValueError("Plugin version must be numeric X.Y.Z without leading zeros")
    if preview == (tag is not None):
        raise ValueError("Choose exactly one of preview or a release tag")
    git_root = Path(git(history_repo, "rev-parse", "--show-toplevel")).resolve()
    if git_root != history_repo:
        raise ValueError("History repository must be its Git checkout root")
    if git(history_repo, "rev-parse", "--is-shallow-repository") != "false":
        raise ValueError("Full Git history is required; fetch tags and unshallow the checkout")
    head = git(history_repo, "rev-parse", "HEAD^{commit}")
    if tag is not None:
        validate_tag(tag)
        if tag[1:] != version:
            raise ValueError("Release tag and plugin version must agree")
        if root != history_repo:
            raise ValueError("Tagged builds require the source and history checkout to be the same root")
        if tag_commit(history_repo, tag) != head:
            raise ValueError("Release tag must point to the selected HEAD release state")
        # Compare every public byte against the tag, including tracked/ignored
        # files; Git's status alone can miss assume-unchanged input changes.
        for relative in public_paths():
            if git(history_repo, "show", f"{head}:{relative}", binary=True) != (root / relative).read_bytes():
                raise ValueError(f"Public input differs from release tag: {relative}")
        if git(history_repo, "status", "--porcelain", "--untracked-files=all"):
            raise ValueError("Tagged builds require a clean source checkout (ignore external build caches)")
    selected_base = None
    if base is not None:
        commit = tag_commit(history_repo, base)
        if commit == head or not is_ancestor(history_repo, commit, head):
            raise ValueError("Base tag must be a strict ancestor of the selected release state")
        selected_base = base
    else:
        candidates = []
        for candidate in git(history_repo, "tag", "--list", "v*").splitlines():
            if not VERSION_RE.fullmatch(candidate[1:]) or candidate == tag:
                continue
            commit = tag_commit(history_repo, candidate)
            if (preview or commit != head) and is_ancestor(history_repo, commit, head):
                distance = int(git(history_repo, "rev-list", "--count", f"{commit}..{head}"))
                candidates.append((distance, tuple(-int(n) for n in candidate[1:].split(".")), candidate))
        if candidates:
            selected_base = min(candidates)[2]
    date = git(history_repo, "show", "-s", "--format=%cs", head)
    return head, selected_base, date


def markdown_subject(subject: str) -> str:
    # Escape user-controlled Git text before embedding it in Markdown notes.
    subject = re.sub(r"[\x00-\x1f\x7f]", " ", subject)
    return re.sub(r"([\\`*_{}\[\]<>])", r"\\\1", subject)


def generate_notes(root: Path, history_repo: Path, tag: str | None, base: str | None,
                   preview: bool) -> str:
    head, selected_base, date = selected_history(root, history_repo, tag, base, preview)
    title = f"Preview for v{json.loads((Path(root) / 'plugin.json').read_text())['version']}" if preview else tag
    lines = [f"# {title}", "", f"History commit date: {date}. Selected commit: `{head}`.", ""]
    if preview:
        lines += ["This preview combines pending curated edits with committed history; it is not a published release.",
                  "", "## Curated unreleased changes", ""]
        changelog = (Path(root) / "CHANGELOG.md").read_text(encoding="utf-8")
        pending = re.search(r"^## \[Unreleased\][^\n]*\n(.*?)(?=^## |\Z)", changelog, re.M | re.S)
        lines += [pending[1].strip() if pending else "No curated unreleased section was supplied.", ""]
    lines += ["## Committed history", ""]
    if selected_base:
        lines += [f"Scope: commits after `{selected_base}` through `{tag or 'HEAD'}`.", ""]
        scope = f"refs/tags/{selected_base}..{head}"
    else:
        lines += ["First release scope: all commits reachable from the selected state; no previous reachable release tag.", ""]
        scope = head
    records = git(history_repo, "log", "--reverse", "--format=%h%x09%s", scope)
    for record in records.splitlines():
        short, subject = record.split("\t", 1)
        lines.append(f"- {markdown_subject(subject)} (`{short}`)")
    if not records:
        lines.append("No new committed changes in this range.")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--history-repo", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preview", action="store_true")
    mode.add_argument("--tag")
    parser.add_argument("--base")
    args = parser.parse_args()
    try:
        print(generate_notes(args.root, args.history_repo or args.root, args.tag, args.base, args.preview), end="")
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"Changelog failed: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
