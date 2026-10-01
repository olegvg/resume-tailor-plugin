# Maintainer instructions

This repository packages two independent instruction-based skills: `resume-tailor` and `onboarding`. Keep changes focused, preserve unrelated edits, and keep candidate/private session data out of source, tests, fixtures, archives and history.

## Runtime contract

- `skills/resume-tailor/SKILL.md` handles resumes, section edits, reviews and requested application text. `skills/onboarding/SKILL.md` handles requested profile creation/update; it is not a mandatory intake step.
- Both skills must work alone. Their `references/profile-contract.md` files must remain byte-identical and all required references must resolve within each standalone skill tree.
- An explicit profile path wins. Accept existing schemas and paths. New profiles default to `resume/<candidate-label>/master-profile.md` in the user's selected workspace, with a safe collision-free label. Candidate identity must be established before merging; the candidate is not assumed to be the plugin author or user.
- Candidate files and exports never belong in the installed plugin/skill/cache. Tailoring and chat-only work do not imply profile persistence or extra artifacts.
- Preserve provenance, date precision, contribution, evidence qualifications, approved public names and unresolved conflicts. Numbers, contacts, photos and a full questionnaire are not mandatory. A JD requirement is not candidate evidence.
- Keep job fit, factual reliability and document quality separate. Do not add aggregate ATS scores, interview probabilities, keyword quotas or fixed language/market pairs.
- Preserve durable restrictions separately from one-output overrides and existing visibility/variant definitions. Keep `reference-only` content out of final output and exclusion reports.
- Core drafting requires no export dependency or external service. PDF/DOCX tooling is optional; generate the real format and inspect the actual artifact before claiming success. Missing tooling must remain visible.

## Metadata and docs

Keep shared name, version, description and author aligned in root `plugin.json`, `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json` and both marketplace indexes. The plugin name is `resume-tailor`; the only skill directories are `skills/resume-tailor` and `skills/onboarding`.

Root `plugin.json` uses Agent Plugins schema 1.0.0 and portable `skills/` discovery. With no inline `extensions.com.openai`, `.codex-plugin/plugin.json` supplies compatibility settings. Claude manifests explicitly expose both skill directories. Privacy metadata points to this repository's `PRIVACY.md`; retain the public author identity and license.

Maintain English/Russian README parity for installation, profiles, task scope, exports and privacy. Check CLI syntax against current official docs or local help before changing commands. Root `CLAUDE.md` is only a pointer to this file for maintainers; installed runtime guidance belongs in the skills.

## Verification and release

After metadata changes, parse every manifest as JSON and check shared metadata, component paths and references. Run native Claude validation against explicit manifests:

```bash
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .claude-plugin/marketplace.json --strict
```

The source checkout retains a root `CLAUDE.md` pointer. Native Claude validation warns that it is not loaded as plugin context, so strict validation of the source plugin can fail on that warning. Report the warning accurately; a passing marketplace check does not prove strict plugin validation. The full runtime archive omits `CLAUDE.md` but includes `AGENTS.md` as linked human documentation; the extracted runtime package receives its own strict validation.

Run the focused repository checks and a build-only preview:

```bash
python3 scripts/validate_plugin.py
python3 -m unittest discover -s tests -v
python3 scripts/build_release.py --preview --output /tmp/resume-tailor-preview
```

Read [docs/releasing.md](docs/releasing.md) for tagged builds, reproducibility checks, archive allowlists, changelog generation and publication requirements. Build tooling uses Python 3.10+ standard library; do not add a runtime dependency to either skill for release tooling. Keep curated pending changes under `## [Unreleased]` in `CHANGELOG.md`.

A prepared version is not a published release. Do not create or retarget tags, commit, push, publish, install globally, change credentials/configuration or write to external accounts unless the user explicitly authorizes that action. Local verification must use disposable projects and must not modify the maintainer's real agent configuration. Do not add AI `Co-Authored-By` trailers to commits.
