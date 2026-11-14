# Sony Open PMCA desktop design

Qt (PySide6) with the platform's native style. Palette-driven colours, so light and dark follow the system. One accent: the system highlight.

## Rules

- No cards, badges, gradients, shadows or decorative icons. Structure comes from type size, spacing and hairlines.
- Lists, not grids. Each row: name, one line of detail, one primary action.
- Copy states a fact or an action. No taglines and no helper text that restates the control.
- Destructive or camera-writing actions ask once, in a native dialog, and say what is unverified.
- A disabled control explains why in its tooltip.

## Pages

| Page | Content |
|---|---|
| Camera | Connection steps when nothing is connected; otherwise model, firmware, identity, shutter count with provenance, connection. Refresh and Copy details. |
| Apps | Store list with filter, one-click Install (download, validate, install), Save APK, Source, Install APK file, Check updates. One operation strip at the bottom. |
| Activity | Latest 5,000 lines, filter, Errors only, Copy, Save, Clear. |
| Tools | Updater mode, service mode, firmware update for bodies without PMCA apps. Not verified on physical hardware here. |

Shortcuts: Ctrl/Cmd+1 to 4.

## Behaviour

- One camera operation at a time. Polling pauses during an operation, and closing the window is refused while one runs.
- The monitor reads status every 3 s. Details are read once per camera identity, or on Refresh.
- Downloading never installs by itself. Cancel applies to downloads only; camera writes cannot be cancelled safely.
- macOS keeps the MTP-only libusb context and does not seize a mounted Mass Storage volume.
