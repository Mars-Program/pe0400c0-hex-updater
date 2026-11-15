# Reviewed website releases

Source is private at https://github.com/Mars-Program/pe0400c0-hex-updater-source.
This repository retains the public 0.1.4/0.1.5 Git history after transfer from MarsTW2.
The current user-facing version is selected by releases/current.json and index.html.

1. Develop and test a feature in a source-repository branch and PR. Publish the
   checked candidate to https://mars-program.github.io/pe0400c0-hex-updater-preview/
   through that repository's checked preview PR; production stays unchanged.
2. Give the user the permanent candidate URL and known validation limits. Obtain
   explicit acceptance identifying that candidate and its candidate.json SHA256.
3. On a production release branch, run scripts/promote_preview.py with --candidate,
   --record-sha256 and --approval-reference. It verifies the hosted candidate,
   copies the exact runtime files and creates the release records/manifest.
   It does not rebuild, commit or deploy. Review the resulting publication PR.
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

Publication checks require new versions to match their accepted preview's source,
ZIP, validation dimensions and runtime assets. Both PR validation and manual
deployment verify the candidate manifest is actually served by the fixed preview
site. The exact existing 0.1.5 manifest remains an immutable bootstrap exception.
A different candidate cannot overwrite an existing production version.

The preview is a separate repository and deployment, with a permanent banner around
unchanged runtime files. GitHub Pages project paths share mars-program.github.io:
browser journals, settings, permissions and cross-tab device locks are shared.
Do not clear them or rename a database to work around an uncertain update.

The initial migration only re-publishes existing 0.1.5 functionality under the
organization. New features remain unapproved until reviewed in their own release.

The old repository URL redirects, but the old GitHub Pages URL does not. Browser
history, settings and device permissions stay with their original origin. An unknown
device result must be resolved in the original tool, not by switching websites.
