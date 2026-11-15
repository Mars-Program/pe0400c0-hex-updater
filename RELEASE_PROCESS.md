# Reviewed website releases

Source is private at https://github.com/Mars-Program/pe0400c0-hex-updater-source.
This repository retains the public 0.1.4/0.1.5 Git history after transfer from MarsTW2.
The current user-facing version is selected by releases/current.json and index.html.

1. Develop and test a feature in a source-repository branch and PR.
2. Obtain user acceptance of its behavior, exact candidate and known validation limits.
3. Prepare a publication PR: new immutable version directory, hash manifest, source
   commit/local ZIP provenance, validation dimensions and release notes.
4. Publication validation must pass; resolve review conversations and merge the PR.
   **Merging or tagging does not deploy.**
5. Manually run **Publish approved website** on main. Enter the accepted version
   and the exact SHA256 of SHA256SUMS.json, both shown in releases/current.json.
6. Review the run summary. MarsTW2 approves the `github-pages` environment for that
   exact candidate; only then is the website updated. No automatic approval.
7. Verify the served version and manifest, record the deployment URL and preserve
   the immutable release tag. Keep old versions for a separately approved rollback.

Main requires PRs, successful publication checks and resolved conversations.
Direct and force pushes/deletion are blocked, including administrators. GitHub
does not allow authors to approve their own PR; when the developer/agent and user
share MarsTW2, the explicit production environment review is the enforceable final
approval gate. Self-review is allowed there so the operator can approve a run they
requested, but tools must not substitute their own decisions for user acceptance.

GitHub Pages is configured for Actions. There is no push/release/tag deployment
trigger. The production environment is restricted to main and disallows admin bypass.
BUILD/OFFLINE checks never imply device, HMI, power-loss or macOS qualification.

The initial migration only re-publishes existing 0.1.5 functionality under the
organization. New features remain unapproved until reviewed in their own release.

The old repository URL redirects, but the old GitHub Pages URL does not. Browser
history, settings and device permissions stay with their original origin. An unknown
device result must be resolved in the original tool, not by switching websites.
