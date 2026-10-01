# Privacy

Resume Tailor is a package of agent instructions, references and templates. It does not operate a backend, send telemetry or require a plugin API key. Core drafting and profile work do not require external resume services or paid scanners.

The agent host you choose processes the prompts, candidate records and tool results you provide under its own account, retention and privacy settings. Running this plugin does not make that processing local or change those policies. Enabled file, web, export or upload tools have their own behavior and permissions; fetching a supplied URL contacts its destination. Optional export tools can run locally when available, and the plugin does not require uploading records to a conversion service.

Candidate records may include contact information, employment history, confidential names and NDA-covered details. Supply only records you are authorized to use. Preserve approved public wording independently from private aliases. Do not place sensitive material in public issues, pull requests, examples or release assets.

Profiles and generated documents belong in the user's selected workspace, never in installed plugin/skill assets or caches. A supplied profile path has priority; new profiles default to `resume/<candidate-label>/master-profile.md` in that workspace. Check your workspace's sharing, backups and version-control settings before saving personal records. A neutral candidate label does not supply a person's identity.

Creating or updating a profile requires an explicit request. Tailoring, exporting and chat-only drafting do not imply profile persistence. The skills read relevant supplied sources, preserve unknowns and disclosure restrictions, and avoid unrelated candidate files. Sending an application, publishing a profile, uploading private documents or changing account/credential settings requires separate authorization.

For removal, delete candidate files from the workspace and manage conversations, backups, connected services and host retention through their respective controls. Uninstalling the plugin does not delete those records. The plugin maintainer has no access to your workspace or host conversations through this package.

Report package issues through the [repository](https://github.com/olegvg/resume-tailor-plugin/issues) using redacted or synthetic examples. This document describes the package's behavior; consult your agent host and enabled tools for their data-processing policies.
