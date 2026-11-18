# HEX Updater Web 0.1.11

[Open HEX Updater in desktop Chrome](https://mars-program.github.io/pe0400c0-hex-updater/)

Connect a USB device attached to your computer and identify its firmware before
choosing an APP file. The initial page is generic: project information and
available operations appear only after a supported BOOT or BOOT+APP has been
identified. USB descriptors, file names and remembered settings do not select a
project. There is no manual board selector.

**Choose COM & identify** opens Chrome's port chooser each time. After identifying
a device, use **Change COM device** to select another port. Selecting a new
device clears the prepared file and requires a fresh identity check. If both
read-only APP queries receive zero bytes, the tool stops and offers a diagnostic
log. It leaves firmware untouched. If an EAO device reports only
its APP, select **Verify BOOT** to enter BOOT, read its identity and return to the
unchanged APP. This separate, explicit step does not write firmware. Unknown or
incomplete identities do not enable update actions.

## Supported APP update flows

- **EAO-R02:** select a compatible PRESERVE v5 `.dataimgAPP` package or APP HEX.
  The tool verifies the package and connected BOOT, shows transfer progress,
  checks the MCU verification/commit result and confirms the restarted XIP APP.
  The supported BOOT 0.1.0 and RTC-fixed headless APP can enter update mode over
  FT234XD USB UART without ST-LINK or manual power cycling. BOOT self-update,
  media-enabled APPs and display operations are not supported by this adapter.
- **PE0400C0:** the existing APP HEX RESET flow remains available after compatible
  firmware identification. RESET replaces the APP and resets image/video
  catalogs; media must be installed again afterward. Image/video sending is not
  implemented here. BOOT direction affects only BOOT waiting/update/recovery
  screens, not APP orientation.

Board identity, BOOT/APP versions and the shared updater version remain separate.
Exact live capabilities, contract, Flash geometry and package checks are required
before an update. Transfer progress reaching 100% alone is not success.

HEX parsing, package creation and serial communication happen on your computer.
Firmware is not uploaded to GitHub. The website is publicly accessible; its URL
is not access control. Users do not need to install .NET or Node.

Use one updater at a time. Preview and production pages on
`mars-program.github.io` share browser journals, permissions and device locks;
local tools use a separate origin. Resolve an interrupted or uncertain result in
the original tool. Do not clear its history or switch tools to retry. Export the
diagnostic log for engineering review if the device result is unknown.

## Accepted release

Version **0.1.11** promotes candidate **0.1.11-20261117-001**, approved on
2026-11-18. When an EAO APP has a quiet startup, the updater can request a
fresh APP identity after a silent legacy probe or a recognized EAO reply.
EAO project actions still require a verified BOOT 0.1.0. Boards waiting for
activation must complete activation before an APP update.
[Fixed 0.1.11 website](https://mars-program.github.io/pe0400c0-hex-updater/versions/0.1.11/) ·
[Accepted preview](https://mars-program.github.io/pe0400c0-hex-updater-preview/candidates/0.1.11-20261117-001/)

The frozen build passed 1,002 C# checks and 45 JavaScript checks.
All 78 Windows Chrome checks with simulated serial ports passed on its
WebAssembly runtime. The operator confirmed COM reselection. A field session
recorded zero received bytes and stopped before any firmware update. A complete
field-board update with this version, physical HMI, power-loss behavior and
macOS execution remain unverified.
[Previous 0.1.10 release and hardware evidence](https://github.com/Mars-Program/pe0400c0-hex-updater/releases/tag/v0.1.10)

## Development and publication

Owned by **Mars-Program**. The private `pe0400c0-hex-updater-source` repository
contains source and matching local packages. The original CI ZIP name and hash
are retained, including its DRAFT suffix, to preserve accepted artifact identity.
This public repository contains only reviewed website assets and release records.

See [release procedure](RELEASE_PROCESS.md) and
[current artifact identities](releases/current.json). Publication requires checked
PRs, exact user acceptance, manual workflow dispatch and the protected production
environment review. Merging or tagging alone does not deploy.

`SHA256SUMS.json` binds the published files. Third-party notices are in `notices/`;
they do not grant a license for project-specific updater code. No device firmware,
HEX fixtures, raw diagnostics or developer QA is published here. Browser runtime
code is downloadable.
