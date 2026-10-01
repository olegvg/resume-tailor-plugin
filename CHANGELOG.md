# Changelog

Curated pending changes are listed below. Release tooling combines them with committed history for previews; publishing a release requires a matching version tag. Preparing manifest version 1.1.0 does not mean the release has been published.

## [Unreleased]

### Added

- Standalone `onboarding` skill for creating and updating candidate master profiles from supplied evidence.
- Identical portable profile contracts bundled with both independently usable skills.
- Agent Plugins 1.0.0 root manifest, Claude source marketplace, Russian README and package-specific privacy guidance.
- Reproducible plugin and standalone skill archives, checksum generation, release notes and CI/release validation tooling.

### Changed

- Resume tailoring now reviews job fit, factual reliability and document quality separately, with no aggregate ATS score or keyword/achievement quotas.
- Profile routing honors explicit paths and existing schemas; new profiles use the selected workspace's `resume/<candidate-label>/master-profile.md`.
- Provenance, contribution, date precision, public-name restrictions, visibility and scoped overrides remain attached to candidate facts.
- Task-specific drafting, section edits, reviews and application notes do not require saved profiles or trigger unrelated artifacts.
- PDF and DOCX generation use optional available tooling, clean content and checks of the actual files.
- Codex, Claude Code and Skills CLI installation and upgrade examples distinguish project scope, plugins, standalone skills and conditional release pinning.
