# OM0RX-xNexus

**[Nexus](https://github.com/kd9taw/Nexus) by KD9TAW, built to work beside
OM0RX-xLog.** It is the full upstream Nexus, with its own name, data folders
and version (`1.25.0-xlog.N`), so it installs next to an upstream Nexus without
sharing settings.

Nexus is a free, all-mode operations centre: a WSJT-X-parity **FT8/FT4**
cockpit, more WSJT-X modes that transmit as well as receive, RTTY, SSTV, APRS,
CW with a neural decoder, an SSB cockpit, rig control and an award-computing
logbook. See the [upstream project](https://github.com/kd9taw/Nexus) for the
complete feature list and operator manual.

## What xNexus adds

- **CS and DS columns** in the Call Roster and Band Activity: call and DXCC
  status from your log, in xLog's codes and colours, so needed stations stand
  out at a glance.
- **xLog stays the master logbook.** Every contact Nexus logs is reported to
  xLog over the WSJT-X UDP API, and xLog's sync agent feeds new xLog contacts
  back to Nexus.
- Native Windows build and installer tooling.

*A screenshot of xNexus beside xLog will be added here.*

## Download

<!-- xsuite:downloads -->
- **Windows** — 1.25.0-xlog.17: [installer](https://github.com/oliverbross/OM0RX-xSuite/releases/download/xnexus-v1.25.0-xlog.17/OM0RX-xNexus_1.25.0-xlog.17_x64-setup.exe) 276 MB
- **macOS:** not published yet
- **Linux:** not published yet
<!-- /xsuite:downloads -->

The Windows installer bundles WebView2 and Hamlib and installs per user,
without admin rights. macOS and Linux builds of xNexus are not published yet;
upstream Nexus offers them in the meantime.

xNexus is GPL-3.0, like upstream Nexus. Its full source is also public at
[oliverbross/OM0RX-xNexus](https://github.com/oliverbross/OM0RX-xNexus). This is
not an upstream Nexus release: please report xNexus problems
[here](https://github.com/oliverbross/OM0RX-xSuite/issues), not to KD9TAW.

## Release history

<!-- xsuite:history -->
| Version | Date | Platforms | Notes | Source |
|---|---|---|---|---|
| 1.25.0-xlog.17 | 2026-11-19 | Windows | [release notes](https://github.com/oliverbross/OM0RX-xSuite/releases/tag/xnexus-v1.25.0-xlog.17) | [source ZIP](https://github.com/oliverbross/OM0RX-xSuite/releases/download/xnexus-v1.25.0-xlog.17/OM0RX-xNexus-1.25.0-xlog.17-source.zip) `d66a1bc7ad` |
<!-- /xsuite:history -->
