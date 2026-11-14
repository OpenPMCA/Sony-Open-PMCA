# Sony Open PMCA

[![Native CI](https://github.com/OpenPMCA/Sony-Open-PMCA/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/OpenPMCA/Sony-Open-PMCA/actions/workflows/build.yml)
[![Version](https://img.shields.io/github/v/release/OpenPMCA/Sony-Open-PMCA)](https://github.com/OpenPMCA/Sony-Open-PMCA/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE.txt)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

Native desktop application to install custom apps and read camera diagnostics on Sony digital cameras supporting **PlayMemories Camera Apps (PMCA)**.

Built on the open-source reverse-engineering research of [Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE) by ma1co and the OpenMemories community.

---

## Table of Contents

- [Supported Cameras](#supported-cameras)
- [Installation & Downloads](#installation--downloads)
- [Quick Start](#quick-start)
- [Features](#features)
- [Build from Source](#build-from-source)
- [Safety & Disclaimer](#safety--disclaimer)
- [Attribution & License](#attribution--license)

---

## Supported Cameras

Only Sony cameras with the built-in Android-based PlayMemories Camera Apps subsystem can run PMCA apps:

| Series | Supported Camera Models | Model Codes | Shutter Counter |
| :--- | :--- | :--- | :---: |
| **Alpha Full-Frame** | α7, α7R, α7S, α7 II, α7R II, α7S II | `ILCE-7`, `7R`, `7S`, `7M2`, `7RM2`, `7SM2` | Tag 9050a / 9050b |
| **Alpha APS-C** | α5000, α5100, α6000, α6300, α6500, QX1 | `ILCE-5000`, `5100`, `6000`, `6300`, `6500`, `QX1` | Tag 9050a / 9050b |
| **NEX Series** | NEX-5R, NEX-5T, NEX-6 | `NEX-5R`, `NEX-5T`, `NEX-6` | — |
| **Cyber-shot Series** | RX100 III/IV/V, RX10 II/III, RX1R II, HX60, HX90, HX400, WX500 | `DSC-RX100M3-M5`, `RX10M2-M3`, `RX1RM2`, `HX60`, `HX90`, `HX400`, `WX500` | — |

> **Compatibility is model-specific, not a release-year rule.** Known non-PMCA bodies (for example α7 III, α7R III, α9, α6400, α6600 and original RX100/RX10) cannot be switched into the installer. Unlisted models remain unconfirmed unless a genuine Sony installer protocol is already detected. Only ILCE-7 with RecipeLab has physical installation evidence here; image counters describe an examined existing photo, not guaranteed lifetime history. See [camera support details](docs/camera-support.md).

---

## Installation & Downloads

Every release is built and tested by CI on all three platforms and published automatically from a version tag, with SHA-256 checksums. Get it from the [latest release](https://github.com/OpenPMCA/Sony-Open-PMCA/releases/latest).

| Platform | File | Notes |
| :--- | :--- | :--- |
| macOS (Apple Silicon) | `Sony-Open-PMCA-<version>-macos-arm64.dmg` | Open it and drag the app to Applications. Ad-hoc signed, not notarized: follow macOS's normal security prompts rather than disabling Gatekeeper. |
| Windows (x64) | `Sony-Open-PMCA-<version>-windows-x64.exe` | Single file, no installer. Uses the Windows Portable Devices driver. |
| Linux (x86_64) | `Sony-Open-PMCA-<version>-linux-x86_64.AppImage` | `chmod +x` and run. Built on Ubuntu 22.04: needs glibc 2.35 or newer. Without FUSE 2 run it with `--appimage-extract-and-run`. |

Homebrew:

```bash
brew tap OpenPMCA/Sony-Open-PMCA https://github.com/OpenPMCA/Sony-Open-PMCA
brew install --cask sony-open-pmca
```

---

## Quick Start

```
1. Set Camera USB Mode    → Menu → Setup (wrench) → USB Connection → MTP
2. Connect Camera to PC   → Use a USB data cable (camera powered on)
3. Launch Sony Open PMCA  → App automatically detects and connects
4. Choose an Action       → Camera (details) | Apps (one-click install) | Activity (log) | Tools (older bodies)
```

### MTP or Mass Storage?

Mass Storage normally exposes the camera's storage volume, not its full operating system or internal app-install database. This backend also supports legacy Sony vendor commands over MSC/SCSI on accessible compatible drivers, but app transfer still uses the MTP installer proxy after the camera changes mode.

The macOS desktop defaults to MTP to avoid capturing mounted storage. Choose MTP for the desktop workflow; a Mass Storage mode mismatch is not a reason to kill camera services or disable OS protections. Legacy MSC availability on Windows/Linux must be verified by the actual driver/model, not inferred from a drive appearing in Explorer/Finder.

---

## Features

* **Automatic Detection**: Real-time camera connection and disconnection monitoring over MTP.
* **Camera Diagnostics**: Reads model name, vendor, firmware version, serial number, lens info, and PTP capabilities.
* **Shutter Count Reader**: Extracts actuation count from existing photos on storage using MakerNote Tag 9050a/b.
* **Safe App Installation**: Model-eligibility gating prevents switching unsupported cameras into installer mode. Preflights APK package ID, Android API baseline (1–10), and signing certificates.
* **Built-in App Store**: Direct downloads for 26 curated open-source camera apps (OpenMemories Tweak, BetterManual, RecipeLab, etc.).
* **Activity Logs**: Batched, searchable logs with level filtering and explicit latest-5,000-line retention/omission notice; Copy/Export describe the retained current-view scope.
* **Native Qt UI**: sidebar, hairline-separated lists and system controls that follow the OS light/dark theme. One-click install from the Store, an inline progress strip and a 5,000-line Activity log. Layout and module map: [architecture](docs/architecture.md).
* **Local Download Cancellation**: Cooperatively cancel downloads without replacing existing files or installing an app. Camera writes are not given a false Cancel/rollback promise.
* **Standalone Binaries**: Self-contained executables for macOS, Windows, and Linux — no Python environment required.

---

## Build from Source

```bash
git clone --recurse-submodules https://github.com/OpenPMCA/Sony-Open-PMCA.git
cd Sony-Open-PMCA

python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

python pmca-app.py              # Launch the desktop app (Qt)
python -W error::ResourceWarning -m unittest discover -s tests -v
```

---

## Safety & Disclaimer

* **Keep Connected:** Do not disconnect the cable or power off the camera while an app is installing.
* **Desktop Safety:** The GUI does not modify firmware or service-mode settings. Installations require user confirmation; the separate CLI retains advanced tools and is not an unrestricted-access permission.
* **No Root Needed:** Operates strictly on the connected USB device without requiring `sudo` or system modifications.
* **Disclaimer:** Independent open-source project. Sony, PlayStation, and PlayMemories are trademarks of Sony Corporation. Use at your own risk.

---

## Attribution & License

Released under the **MIT License**. Copyright (c) 2015 ma1co and OpenPMCA contributors. See [LICENSE.txt](LICENSE.txt).

Special thanks to:
* **ma1co** for the original [Sony-PMCA-RE](https://github.com/ma1co/Sony-PMCA-RE) reverse-engineering research.
* **nex-hack** community for initial camera subsystem documentation.
* **OpenMemories** community for custom camera applications and framework.
