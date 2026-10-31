# Tretlager – technical notes

The project page is [README.md](../README.md). This file collects requirements, everyday use
with the Flatpak, troubleshooting and developer notes.

A native Qt/Kirigami application that sets up, starts and keeps up to date the official Windows
client of **Zwift** on Linux: Wine, runtime, graphics diagnostics (NVIDIA), sensors over
Bluetooth LE without the Zwift Companion app.

**Goal (since 2026-10-30): a Flatpak** that runs on modern distributions and brings everything
Zwift needs (its own Wine, winetricks, tools). Plan and status in
[docs/flatpak.md](flatpak.md). Developed and tested on TUXEDO OS Forky (Plasma) on
tinytin; Plasma is the main target, GNOME should work.

**Status (2026-10-30):** 0.9.0 as a Flatpak on tinytin; Zwift runs (opt-in token login, NVIDIA
via GLX + PRIME offload), the **sensor bridge** pairs trainer and heart rate strap over Wahoo
Direct Connect, without the Companion app. Feasibility in [FEASIBILITY.md](../FEASIBILITY.md),
UX concept in [docs/ux-concept.md](ux-concept.md), QA audit in
[docs/qa-audit-2026-10-30.md](qa-audit-2026-10-30.md), open items in [BACKLOG.md](../BACKLOG.md).

**Not an official Zwift app, use at your own risk:** Zwift may not be happy that a software
bridge sends data to Zwift that could be manipulated. Restrictions up to a suspended account
cannot be ruled out – including the XP and drops you worked hard for. **Not for races:** there
is no guarantee that the sensor bridge passes power, cadence and heart rate to Zwift correctly.
At the first start Tretlager shows these notes as a warning that has to be accepted (again
whenever the text changes); they also appear in the overview under *Start Zwift*, on the welcome
page, under *About Tretlager* and in the help.

Key findings:
- Zwift runs only experimentally under Wine (11.x, built from source in the Flatpak).
- The game uses OpenGL 3.1, DXVK is unnecessary.
- Direct BLE from Wine does not work (GATT notifications and writes are missing). Sensors come
  through a dedicated bridge that presents itself as a Wahoo “Direct Connect” device.
- The official sign-in in the launcher (WebView2) does not work under Wine; Tretlager signs in
  through its own sign-in window (only after consent; contradicts §5 of Zwift's terms of service).

## Requirements on the computer

Tretlager brings Wine, winetricks, Python packages and tools. The system only provides:

- Flatpak ≥ 1.14 with Flathub (for `org.kde.Platform//6.11`, `io.qt.PySide.BaseApp//6.11` and,
  with NVIDIA, the matching `GL.nvidia-…` extension) and xdg-desktop-portal.
- **BlueZ** (Bluetooth service) and a Bluetooth LE adapter, built in or as a USB stick.
- **Avahi** (`avahi-daemon`): this is how Zwift finds the sensors. The system check warns if it is missing.
- A **keyring** following the Secret Service standard (KWallet/ksecretd on Plasma, GNOME
  Keyring) for the Zwift session.
- x86-64, a Wayland session with XWayland or X11; NVIDIA with the proprietary driver or Mesa.

Tested are TUXEDO OS Forky with Plasma 6.7 (tinytin) and Arch with GNOME 51 on Intel graphics
(nanhlanu, Oct 31: installation, setup of Wine and Zwift, sign-in page; a ride is still pending).
Under GNOME Tretlager shows the Breeze style but follows GNOME's light/dark mode and font. Fedora, Ubuntu and openSUSE are targets but untested
(phase F5 in [docs/flatpak.md](flatpak.md)).

## Everyday use with the Flatpak

- **Updating:** `flatpak update de.linuxundich.Tretlager`; Wine and all other components
  come with Tretlager. Before every start Tretlager brings the Zwift environment in line (new
  Wine → `wineboot -u` and graphics test) and installs Zwift updates through the Zwift launcher.
  No snapshots. Tretlager keeps the last working Wine version (one, ≈ 500 MB); if a new Wine
  causes problems, the switch *Use previous Wine version* in the overview starts Zwift with it
  again. Plan: [docs/updates.md](updates.md).
- **Uninstalling:** `flatpak uninstall de.linuxundich.Tretlager`; the Zwift environment (a good
  10 GB), settings and logs are deleted by `flatpak uninstall --delete-data de.linuxundich.Tretlager`.
  Use *Sign out* in Tretlager beforehand to remove the Zwift session from the keyring.
- **Data:** everything under `~/.var/app/de.linuxundich.Tretlager/` – `data/tretlager/prefix`
  (Zwift), `config/tretlager/bridge.json` (sensors), `.local/state/tretlager/` (state,
  log `tretlager.log`). The bridge log is in the journal:
  `journalctl --user -t de.linuxundich.Tretlager.Bridge`.
- **Network:** Tretlager does not phone home. Connections only go to Zwift (version check
  `cdn.zwift.com`, sign-in `secure.zwift.com`, game updates through the Zwift launcher), to GitHub
  (winetricks, once) and to the download sources of winetricks (Microsoft and others for fonts,
  .NET and WebView2, once during setup).

## Troubleshooting

| Problem | Remedy |
|---|---|
| Sensor stays at “Searching for the device…” | Pedal the trainer briefly, moisten and put on the strap. *Pause* sensors you are not using. |
| Sensor never connects (Garmin HRM-Pro on Intel AX201) | Known chip incompatibility; plug in a USB Bluetooth stick and choose it as the adapter under *Sensors*. If it still hangs afterwards: `systemctl restart bluetooth` (root) or reboot. |
| Zwift finds no sensors | The bridge must be running (*Sensors*), Avahi must be running; in Zwift pair “Wahoo KICKR …” or “Wahoo HRM …”. |
| “No keyring available” | Start and unlock KWallet or GNOME Keyring. |
| Zwift hangs after switching between power supply and battery | NVIDIA driver (Xid); quit Zwift with Alt+F4 and restart it on the power supply. |

## Known limitations

- Bluetooth LE only (FTMS, Cycling Power, CSC, Heart Rate); no ANT+.
- Actually tested: Wahoo KICKR V4 (FTMS, ERG, climbs), Wahoo TICKR, Garmin HRM-Pro Plus
  (reliable only through a USB stick). Other devices with these standard services should work
  but are untested.
- Maximising the window and Wine DPI from the XWayland scaling are only available on Plasma.
- Zwift receives the session as a command line argument (visible in the process list, BACKLOG).

## Principles

No bypassing of sign-in, DRM or licence checks, no modified Zwift files, no telemetry, no silent
system changes. Anything that does not work is shown as such.

## Trying the bridge (user installation)

    build-aux/install-user.sh          # into ~/.local, systemd user service tretlager-bridge
    systemctl --user start tretlager-bridge

Dependencies (Debian forky): `python3-bleak`, `python3-dbus-fast`, a running `avahi-daemon`
and BlueZ. The bridge is controlled through the Sensors page of the Kirigami interface.
Tests: `python -m pytest tests`.

## Interface (Kirigami)

    PYTHONPATH=. python3 -m tretlager.kde

Additionally needs `python3-pyside6.qtqml`, `python3-pyside6.qtquick`,
`python3-pyside6.qtquickcontrols2`, `python3-pyside6.qtgui`, `qml6-module-org-kde-kirigami` and
`qml6-module-org-kde-kirigamiaddons-formcard` (plus `-components`). The interface follows the
KDE Human Interface Guidelines: sidebar after setup, FormCards, help buttons, the assistant as a
linear flow. `TRETLAGER_INSTANCE=test` starts a second instance next to the running one, for
example for testing from the source tree.

### Languages

The source language is English, with German in addition (`po/de.po`, help in
`tretlager/data/help.de.md`; English help in `help.md`). Without a catalogue for the system
language Tretlager shows English;
`TRETLAGER_LANG=en` or `de` forces a language. QML strings are in `i18n()`, Python strings
in `_()` (bridge strings in `N_()`, translated only in the interface).

    po/update.sh          # collect strings (po/tretlager.pot), merge catalogues; needs gettext
    po/update.sh --build  # po/*.po → tretlager/data/locale/*.mo, pure Python (also on tinytin)

`build-deb.sh` compiles the catalogues itself. `tests/test_i18n.py` fails if a string has no
English translation or the placeholders do not match.

## Flatpak

    build-aux/flatpak/build.sh            # on tinytin: build and install for the user
    build-aux/flatpak/build.sh --bundle   # additionally tretlager.flatpak (single file)
    flatpak run de.linuxundich.Tretlager

Needs `flatpak-builder` as well as (`build.sh` fetches them itself) `org.kde.Sdk//6.11`,
`io.qt.PySide.BaseApp//6.11` and `org.freedesktop.Sdk.Extension.mingw-w64//25.08`. Wine is built
from source (a few minutes on tinytin). New Python dependencies:
`build-aux/flatpak/gen-python-deps.py` rewrites `python-deps.json`.

**Qt patch version:** PySide in the BaseApp is bound to the private Qt API of exactly the Qt
version it was built against (`QObjectPrivate(QtPrivate_6_11_N)`). If Flathub moves the KDE
runtime to a new Qt patch version, an old Tretlager no longer starts until the BaseApp has caught
up and Tretlager has been rebuilt. So when building, bring runtime, SDK and BaseApp to the same
level (`flatpak info --user io.qt.PySide.BaseApp//6.11` → version = Qt of the runtime). If
Tretlager does not start for this reason, it reports it through a notification and in the log.

The sensor bridge starts through D-Bus activation as a separate instance:
`flatpak run --command=tretlager-bridge de.linuxundich.Tretlager` starts it by hand.

## Debian package (discontinued)

The Debian package (up to 0.7.1) was the first way of shipping Tretlager and is no longer
developed; it only stays until the Flatpak has passed acceptance (F5). On tinytin it has been
removed since 2026-10-30.

    build-aux/build-deb.sh            # → dist/tretlager_<Version>_all.deb (needs dpkg-deb)
    sudo apt install ./dist/tretlager_<Version>_all.deb

On the home network it is easier through my own package repository on bender (unsigned, LAN only):

    echo 'deb [trusted=yes] http://bender:8095/debian ./' | sudo tee /etc/apt/sources.list.d/linuxundich.list
    sudo apt update && sudo apt install tretlager

Publishing a new version: build the package, then `services/pacman-repo/publish-deb.sh`.

Afterwards the application menu shows **Tretlager** (assistant/main window) and **Zwift (Tretlager)** (direct start).
The version is in `CHANGELOG.md`.

## Licence and disclaimer

Tretlager is licensed under the GPL-3.0-or-later (`LICENSE`); this also applies to the icon
(`build-aux/make-icon.py`). The background image `tretlager/data/backdrop.png` is generated by
`build-aux/make-backdrop.py` from a photo that is not in the repository
(`build-aux/make-backdrop.py foto.jpg`).
Tretlager is not a product of Zwift Inc. and is not supported by Zwift; use it at your own risk.
Zwift, .NET Framework, WebView2 and the other Windows components are non-free software.
Tretlager does not ship them; the setup downloads them from the vendor. An overview of all
components and licences is available in the app under *About Tretlager*.
