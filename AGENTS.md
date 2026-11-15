# Public publication contract

This repository contains reviewed static website assets, publication checks and
release records. Full source remains in Mars-Program/pe0400c0-hex-updater-source.

- Inspect status; develop publication changes on codex/<change> and use a PR.
- Do not edit/delete old versions or move/delete version tags. Add a new version
  directory, regenerate the manifest, and update releases/current.json.
- No source, HEX, developer QA, credentials, raw logs or private build paths here.
- Validate manifest hashes, exact source/local-package provenance, retained assets,
  the stable redirect and applicable evidence before proposing release.
- A merge, tag, green check or agent-created approval comment does not authorize
  publication. Obtain explicit user acceptance of the exact candidate first.
- Production uses only the manually dispatched Publish approved website workflow
  and its github-pages reviewer gate. Never bypass protections or self-approve a
  deployment with the user's credentials without their explicit candidate approval.
- The one-time organization migration re-publishes already accepted 0.1.5 bytes;
  it does not approve future functionality or promote firmware versions.
- Preserve origin-specific recovery journals and all device/recovery checks.

See RELEASE_PROCESS.md and releases/current.json.
