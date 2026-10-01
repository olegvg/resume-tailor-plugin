#!/usr/bin/env python3
"""Build three deterministic ZIPs, release notes and SHA256SUMS atomically."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import zipfile

from generate_changelog import generate_notes
from validate_plugin import SKILLS, public_paths, validate_plugin


def zip_bytes(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    # ZIP_STORED avoids compression-library version differences between machines.
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)
    return buffer.getvalue()


def build_release(root: Path, history_repo: Path, output: Path, tag: str | None = None,
                  base: str | None = None, preview: bool = False) -> None:
    root, history_repo = Path(root).resolve(), Path(history_repo).resolve()
    original_output = Path(output).absolute()
    output = original_output.resolve()
    for source in (root, history_repo):
        if output.is_relative_to(source) or source.is_relative_to(output):
            raise ValueError("Output must be outside and must not contain the source/history checkout")
    # macOS uses system aliases /tmp -> /private/tmp and /var -> /private/var.
    # Accept those OS paths while rejecting task-created output redirects.
    system_aliases = {Path("/tmp"): Path("/private/tmp"), Path("/var"): Path("/private/var")}
    if any(path.is_symlink() and system_aliases.get(path) != path.resolve()
           for path in (original_output, *original_output.parents)):
        raise ValueError("Output or its parents must not be symlinks")
    if output.exists():
        raise ValueError("Output must not already exist; choose a fresh output directory")
    errors = validate_plugin(root)
    if errors:
        raise ValueError("Plugin validation failed:\n" + "\n".join(errors))
    notes = generate_notes(root, history_repo, tag, base, preview)
    version = json.loads((root / "plugin.json").read_text(encoding="utf-8"))["version"]
    payload = {name: (root / name).read_bytes() for name in public_paths()}
    artifacts = {f"resume-tailor-plugin-{version}.zip": zip_bytes(
        {"resume-tailor-plugin/" + name: content for name, content in payload.items()})}
    for skill in SKILLS:
        prefix = f"skills/{skill}/"
        files = {skill + "/" + name[len(prefix):]: content for name, content in payload.items()
                 if name.startswith(prefix)}
        files[skill + "/LICENSE"] = payload["LICENSE"]
        artifacts[f"{skill}-{version}.zip"] = zip_bytes(files)
    artifacts["CHANGELOG.md"] = notes.encode("utf-8")
    artifacts["release-notes.md"] = notes.encode("utf-8")
    artifacts["SHA256SUMS"] = "".join(
        f"{hashlib.sha256(content).hexdigest()}  {name}\n"
        for name, content in sorted(artifacts.items())
    ).encode("ascii")
    # Validate and construct everything before opening the destination. A failed
    # write removes the staging directory, leaving no partial release output.
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".resume-release-", dir=output.parent) as temporary:
        pending = Path(temporary) / "payload"
        pending.mkdir()
        for name, content in sorted(artifacts.items()):
            (pending / name).write_bytes(content)
        if output.exists() or output.is_symlink():
            raise ValueError("Output appeared during build; refusing to overwrite it")
        os.rename(pending, output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--history-repo", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preview", action="store_true")
    mode.add_argument("--tag")
    parser.add_argument("--base")
    args = parser.parse_args()
    try:
        build_release(args.root, args.history_repo or args.root, args.output,
                      args.tag, args.base, args.preview)
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"Release build failed: {exc}\n")
    print(f"Built six release artifacts in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
