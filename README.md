# PE0400C0 HEX Updater Web 0.1.5

[Open in desktop Chrome](https://marstw2.github.io/pe0400c0-hex-updater/)

Engineering preview for Windows 11 and macOS 27 desktop Chrome. Select an APP HEX,
wait for automatic validation, select your USB serial device, review the target,
and explicitly confirm the RESET update. The device must be connected to your own
computer. macOS execution and physical serial/hardware qualification remain NOT_RUN.

HEX parsing, package creation and serial communication happen on your computer.
Firmware is not uploaded to GitHub. This website has public anonymous access;
knowing the link is not an access-control mechanism.

BOOT direction affects only waiting, update and recovery screens. APP display
orientation is unchanged. RESET replaces the APP and resets image/video catalogs;
install media again afterward. Only a matching MCU verification/commit result is
success; transfer 100% is not success.

Web and local tools have separate histories, settings, tab locks and device
permissions. Resolve any interrupted or uncertain update in the original tool
before continuing. Use only one updater at a time. This reminder appears in the
final update confirmation; selecting Update once acknowledges it. There is no
separate firmware-step checkbox. The confirmation cannot inspect another origin
or clear a known unresolved session. Export a log and ask
engineering to diagnose an unknown device result; do not switch tools to retry.

Runtime: .NET 10 LTS 10.0.15; build SDK: 10.0.404. Users install neither .NET nor
Node. Original downloadable local packages remain available from the project
maintainer; this repository contains only the reviewed static web publication.

## Deployment and maintenance

GitHub Pages publishes the root of `main` with `.nojekyll` and HTTPS. The fixed
entry redirects to `versions/0.1.5/`; retain version directories unchanged.
Deploy each reviewed future release in a new version directory, then update the
entry redirect. Keep the same origin to retain browser history and preferences.
Rollback redirects only to a separately validated release; never clear journals.

`SHA256SUMS.json` binds the published files; runtime licensing notices are in
`notices/`. This repository contains no device firmware, developer QA, raw logs,
debug symbols or original BOOT/APP project. Compiled browser code is downloadable.
Third-party notices do not grant a license for the project-specific updater code.

Verification: 210 C# checks, 19 JavaScript checks, 6 launcher cases, Chrome offline
workflow tests and independent desktop verification of actual WASM packages.
BUILD/OFFLINE evidence does not establish TRANSPORT, HARDWARE, HMI or POWER_LOSS.
