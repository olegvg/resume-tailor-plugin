# Release preparation

Release tooling needs Python 3.10+ and Git. It uses only the Python standard
library. Normal resume drafting needs neither the build tooling nor export
packages.

Run from the checkout root:

```bash
python3 scripts/validate_plugin.py
python3 -m unittest discover -s tests -v
```

The validator checks matching portable/Codex/Claude versions and metadata,
exactly two skills, every bundled reference/template, standalone reference
resolution, identical profile contracts, and the public file inventory.
Unknown files in skill, asset or manifest component trees and symlink inputs fail.
Files outside that inventory do not enter ZIPs. Keep all candidate profiles,
sources and generated resumes in the user's selected workspace.

## Local preview

Use a fresh directory outside the checkout; the builder rejects output paths
inside, containing or overlapping the source/history checkout. Existing output
directories are also rejected so a failed build cannot damage earlier assets.

```bash
python3 scripts/build_release.py --preview --output ../resume-tailor-preview-1
python3 scripts/generate_changelog.py --preview
```

A preview can use an isolated prepared source tree and a separate read-only
Git history checkout:

```bash
python3 scripts/build_release.py --root /path/to/staged-plugin --history-repo /path/to/history-checkout --preview --output /path/to/fresh-preview
```

Preview notes label curated `CHANGELOG.md` Unreleased edits separately from
committed history. Dates come from the selected HEAD commit, not the build
clock. A prepared version does not establish that a release exists. Two builds
from identical source/history inputs produce identical bytes, including notes
and checksums. ZIP entries use sorted paths, a fixed 1980 timestamp, Unix regular
file permissions `0644`, and stored data to avoid compressor-version variation.

## Tagged build

After an authorized release tag already exists locally, check out its release
commit and build:

```bash
python3 scripts/build_release.py --tag v1.1.0 --output ../resume-tailor-v1.1.0
```

Only numeric `X.Y.Z` versions and `vX.Y.Z` tags without leading zeros are
supported. The tag must exist, match every manifest version and resolve to
HEAD. Tagged inputs must be the same Git checkout as the history root, have
all public bytes equal to the tag, and have a clean Git status. A separate
`--history-repo` is intended for previews. Generated Python caches are ignored.
The tools never create tags or commits, push, install or publish anything.

History uses the nearest reachable numeric release tag as its base. The first
release explicitly includes all reachable commits. An optional `--base v1.0.0`
selects an existing strict ancestor; missing, unrelated or equal-state bases
fail. Full history is required: a shallow checkout fails with an actionable
message instead of silently truncating the changelog.

Each successful build produces exactly:

- `resume-tailor-plugin-1.1.0.zip`: one `resume-tailor-plugin/` directory with
  public manifests, docs, license, changelog and both complete skills. It includes
  the security policy and Codex icon. The maintainer guide `AGENTS.md` preserves
  README links; the checkout-only `CLAUDE.md` pointer is omitted to permit strict
  native package validation.
- `resume-tailor-1.1.0.zip` and `onboarding-1.1.0.zip`: one skill directory per
  archive with `SKILL.md`, all of that skill's references/templates and the
  unmodified MIT `LICENSE`. No sibling skill or maintainer guide is required.
- `CHANGELOG.md` and `release-notes.md`: the generated, Git-scoped notes. The
  curated source changelog remains unchanged and is included in the full ZIP.
- `SHA256SUMS`: SHA-256 hashes for all five other files.

Verify every asset from the output directory on Linux:

```bash
sha256sum -c SHA256SUMS
```

On macOS:

```bash
shasum -a 256 -c SHA256SUMS
```

For a portable Python check, run in that output directory:

```bash
python3 - <<'PY'
import hashlib
from pathlib import Path
for line in Path("SHA256SUMS").read_text().splitlines():
    expected, name = line.split("  ")
    actual = hashlib.sha256(Path(name).read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f"Checksum mismatch: {name}")
    print(f"{name}: OK")
PY
```

## GitHub workflow

CI validates PRs and pushes to `master`, exercises the temporary Git fixtures,
and verifies a preview build. Both workflows fetch complete Git history.
The release workflow validates and builds on numeric release tags and manual
dispatch. Build jobs have `contents: read`; only the publication job receives
`contents: write`. Tags are validated before checkout and passed through
environment variables rather than interpolated into shell source.

Once this workflow and the selected tag exist on the remote repository, an
explicitly authorized build-only remote check uses:

```bash
gh workflow run release.yml --ref master -f tag=v1.1.0 -f publish=false
```

Manual `publish` defaults to `false`; build-only runs upload checked artifacts
without creating a GitHub release. Setting `publish=true` or pushing a `v*` tag
invokes publication. Both are external actions requiring explicit authorization.
Publication checks downloaded asset hashes and selected tag/commit consistency.
A new release uses `--verify-tag --notes-file`; an existing release updates its
notes/title and replaces the six named assets. Download artifacts from the
workflow run to review them before authorizing publication.

## Failure diagnosis

Resolve validation errors by correcting the named file, metadata or reference.
Do not bypass a failure by copying candidate data into the public trees. A
version error means manifests/tag disagree; a source-state error means the
checkout differs from the selected tag. Inspect `git status --short` and the
diff, then use a preview for uncommitted edits. A missing/base history error
requires checking tag existence and ancestry with `git tag --list` and
`git log --oneline --decorate`. Fetching a full remote history, creating tags,
or dispatching/publishing workflows remain separately authorized actions.

For native distribution QA, extract the full plugin ZIP into a disposable
directory and validate its `.claude-plugin/plugin.json` with the available
Claude CLI's `--strict` option. Source checkouts retain `CLAUDE.md` for
maintainers; their expected context warning is separate from runtime-package
validation. Keep extraction and install tests project-scoped and disposable.
