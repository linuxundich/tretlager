# Tretlager as a Flatpak – phase plan

As of 2026-10-30. **Primary goal:** Tretlager as a Flatpak that runs independently of the
distribution on modern distributions (not necessarily everywhere) and brings everything Zwift needs
(Wine, winetricks, tools, Python packages). A system update can no longer change the tested Wine
version, and the *Prepare* step (WineHQ repository, password, APT) goes away. The Debian package is
discontinued (removed from tinytin on Oct 30) and is no longer developed.

### What “modern distribution” means

- Flatpak ≥ 1.14 (Background portal, `--allow=multiarch`), xdg-desktop-portal with a KDE or
  GNOME backend, BlueZ ≥ 5.6x, Avahi (for announcing to Zwift), PipeWire or PulseAudio.
- Wayland session with XWayland, or X11; NVIDIA with the proprietary driver for which a matching
  Flathub extension exists, or Mesa (Intel/AMD).
- Target tests: TUXEDO OS (Plasma), Fedora (KDE and GNOME), Arch, Ubuntu 26.04 LTS.
- Whatever only works under Plasma (KWin script for maximizing, XWayland scaling from `kwinrc`)
  gets a sensible fallback under GNOME instead of an error.

## What is already settled (Flathub, Oct 30)

| Component | Status | Source |
|---|---|---|
| Runtime | `org.kde.Platform//6.11` with Kirigami (KF6) | `flatpak remote-ls flathub` |
| PySide6 + QtWebEngine | `io.qt.PySide.BaseApp//6.11` (PySide 6.11.x, must match the Qt patch version of the runtime, see README *Flatpak*), builds on `io.qt.qtwebengine.BaseApp//6.11` and KDE 6.11 → PySide6, Kirigami and WebEngine in one environment | `flatpak remote-info --show-metadata` |
| NVIDIA | `org.freedesktop.Platform.GL.nvidia-580-178-04` matches tinytin's driver; Flatpak installs the matching extension by itself | `flatpak remote-ls` |
| tinytin | Flatpak 1.18.4, Flathub set up as a system remote | `flatpak --version` |
| Distribution | Not via Flathub (Flathub forbids AI-generated manifests and submissions), but my own repository on bender, as with the other apps | working rule |

## Open core questions (they decide the project)

1. ~~Kirigami Addons~~ – settled: included in `org.kde.Platform//6.11` (1.13.1).
2. **Wine in the KDE runtime.** `org.winehq.Wine` is a standalone app on the Freedesktop runtime
   and cannot be embedded. Plan: Wine as a WoW64 build in the package (Kron4ek
   `wine-11.20-amd64-wow64.tar.xz`, checksum pinned in the manifest). WoW64 needs no 32-bit
   libraries, so no `Compat.i386`/`GL32` extensions. **Risk:** do .NET 4.8, WebView2 and the
   Zwift launcher run under WoW64 just as under the previous `winehq-devel` 11.20 (classic, with a
   32-bit part)? Fallback: build Wine in the manifest ourselves, or a classic build with
   `Compat.i386` (check whether this extension exists for the KDE runtime).
3. **NVIDIA in the sandbox.** With `--device=dri` and the GL extension, Zwift should run on the RTX
   via PRIME offload (`__NV_PRIME_RENDER_OFFLOAD`, `__GLX_VENDOR_LIBRARY_NAME=nvidia`); cross-check
   with the existing graphics test (`gltest`).
4. **Bridge in the sandbox.** bleak via `org.bluez` (system bus), mDNS via Avahi, DIRCON on
   127.0.0.1. Does Zwift (in the same Flatpak) find the devices as before?

## Phases

### F0 Feasibility on tinytin (before any rework)

Throwaway manifest (`build-aux/flatpak/spike/`, replaced by the real manifest after F0), installed
on tinytin from a single-file bundle. The running Tretlager (Debian package) stays untouched; stop
the package's bridge during the tests.

- [x] a) UI: PySide BaseApp + Tretlager sources → window, FormCards, Plasma style; sign-in window
      (WebEngine) shows the Zwift page.
- [x] b) Wine: prebuilt Kron4ek WoW64 builds crash in **every** Flatpak runtime (`virtual_init`,
      code 139), the official `org.winehq.Wine//wow64` runs → built Wine 11.20 from source
      (mingw-w64 extension 25.08, `--enable-archs=i386,x86_64`). Needs `--allow=multiarch`
      (otherwise `syswow64` stays empty). corefonts, .NET 4.8, WebView2 ok.
- [x] c) Zwift: launcher and game in the new prefix, graphics test “NVIDIA GeForce RTX 3050 Ti”
      (OpenGL 4.6, 580.178.04) via the GL extension; start with the token from the keyring.
      Open: copy of the existing prefix against the Flatpak Wine.
- [x] d) Bridge in the Flatpak: BlueZ (UB500), Avahi, D-Bus name; Zwift in the Flatpak pairs the
      KICKR (automatically) and the HRM-Pro.
- [x] e) sysfs (power supply, Bluetooth chip), keyring, notifications (gdbus), KWin script
      (after a fix, script in `$XDG_RUNTIME_DIR/app/<ID>`).

**Result of F0 (Oct 30): feasible.** A real ride is still missing; all components work. Lessons for
F1/F2:

- The sandbox lacks `busctl`, `systemctl`, `journalctl`, `bluetoothctl`: switch `bridgectl`, the
  system check (Bluetooth) and the adapter list to `gdbus` or dbus-fast.
- System check: operating system from `/run/host/os-release`; NVIDIA via
  `/proc/driver/nvidia/version` (`/sys/module/nvidia` is missing); Wine “included in the package”.
- `--socket=x11` instead of `fallback-x11` (otherwise Wine would pick the Wayland driver).
- Kirigami Addons 1.13.1 is in `org.kde.Platform//6.11`, no separate module needed.
- Building on tinytin (20 cores): the Wine module takes a few minutes there.

**Exit criterion:** a real ride with the spike Flatpak. If b) or c) fails, build Wine in the
manifest ourselves (repeat F0) or shelve the project.

### F1 Manifest and build – done (0.8.0, Oct 30)

- `build-aux/flatpak/de.linuxundich.Tretlager.yml`, base `io.qt.PySide.BaseApp//6.11`,
  runtime `org.kde.Platform//6.11`.
- Modules: Kirigami Addons; Python packages (bleak, dbus-fast, SecretStorage with dependencies,
  via `flatpak-pip-generator`); Wine (tarball, checksum); winetricks (pinned as before, checksum);
  cabextract; osslsigncode; Tretlager itself (incl. `po/update.sh --build`).
- `finish-args` (draft):
  - `--share=network`, `--share=ipc`, `--socket=wayland`, `--socket=fallback-x11`,
    `--socket=pulseaudio`, `--device=dri`
  - `--system-talk-name=org.bluez`, `--system-talk-name=org.freedesktop.Avahi`
  - `--talk-name=org.freedesktop.secrets`, `--talk-name=org.freedesktop.Notifications`,
    `--talk-name=org.kde.KWin`
  - The bridge's bus name `de.linuxundich.Tretlager.Bridge` starts with the app ID and is
    therefore allowed without a separate permission.
- `build-aux/flatpak/build.sh` as with Freisteller/Kulisse (local repository `repo/`).

### F2 Code changes (detection via `/.flatpak-info`) – done (0.8.0)

Implemented: bridge via D-Bus activation (instead of a portal spawn: the session bus starts the
exported service file as a separate instance) and `Quit`, autostart via the Background portal,
bridge version with restart after an update, gdbus instead of busctl/systemctl, assistant without
*Prepare*, system check with the host's os-release and Avahi. Verified on tinytin: activation,
`Quit`, start from the UI, system check all green. Open: NVIDIA errors after the ride (no journal
in the sandbox) are dropped; autostart via the portal not yet verified after a reboot.

- **Assistant without *Prepare*:** polkit helper, APT plan and WineHQ check only in the Debian
  package; five steps in the Flatpak. System check: Wine “included in the package”.
- **Wine paths:** `/app/wine/bin` instead of `/opt/wine-devel`; environment centralized in
  `setup`/`launch`.
- **Bridge without systemd:** `bridgectl` starts the bridge as a separate Flatpak instance via
  the portal (`org.freedesktop.portal.Flatpak.Spawn`) so that it runs independently of the window.
  *Start at login* via the Background portal (`RequestBackground`, autostart) instead of
  `systemctl --user enable`.
- **Bridge version:** the bridge reports its version; if Tretlager starts after an update with an
  older bridge still running, it restarts the bridge as long as Zwift is not running (also solves
  the Debian package's problem).
- **NVIDIA errors after the ride:** the kernel journal is not readable in the sandbox. Drop the
  message in the Flatpak; the warning on switching the power source stays (sysfs).
- **Storage locations:** proposal `--filesystem=xdg-data/tretlager`, `xdg-config/tretlager`,
  `xdg-cache/tretlager`, `xdg-state/tretlager` → the same paths as the Debian package, no moves,
  prefix and settings stay. Alternative (cleaner, but with a move of 8.6 GB): sandbox paths under
  `~/.var/app/de.linuxundich.Tretlager/`.

### F2b Distribution independence

- System check without Debian assumptions: only display the operating system (from
  `/run/host/os-release`), no longer rate it as “target system”; check for Flatpak capabilities
  (portal, Avahi, BlueZ, GPU) instead of packages.
- Help and texts without references to TUXEDO/APT, except where they concern the Debian package.
- Avahi is missing by default on some distributions: check with an understandable remedy, possibly
  announcing without Avahi (own mDNS) as a way out.
- GNOME: maximize the window without KWin (Wine registry or fullscreen), DPI from the window
  scaling.

### F3 Migration from the Debian package

- Instructions or a small script: stop and disable the bridge service, `apt remove tretlager`
  (data stays), install the Flatpak. Optionally remove the WineHQ repository and `winehq-devel`.
- Run through on tinytin: Zwift, sign-in (keyring), bridge settings incl. UB500 and the paused
  TICKR must keep working without being set up again.

### F4 Distribution via bender

- Flatpak repository next to pacman-repo and the Debian repository (nginx port 8095, path
  `/flatpak`), `services/pacman-repo/publish-flatpak.sh`, `.flatpakrepo` file.
- Dedicated GPG key for the repository (over HTTP without a signature, any change in transit would
  go unnoticed).
- README: installation via `flatpak remote-add` + `flatpak install`.

### F5 Acceptance

- [ ] Fresh TUXEDO OS forky (VM `tuxedo-os-forky`, run without NVIDIA/Bluetooth; polkit not
      needed, Zwift sign-in done by me) – replaces BACKLOG M6b.
- [ ] A second distribution with Plasma (e.g. Fedora KDE in a VM).
- [ ] Ride ≥ 30 min on tinytin, power supply unplugged/plugged in, without network.
- [ ] Then: freeze the Debian package (bug fixes only) or discontinue it.

## What changes for the user

- No password, no WineHQ package repository, no APT changes to the system.
- One-time download is larger: KDE runtime and PySide base (together a good 1 GB, shared with other
  KDE Flatpaks) plus Wine (~ 200 MB). Zwift itself (~ 5 GB) as before.
- Updates via `flatpak update` or Discover instead of APT.
- Dropped: reporting of NVIDIA driver errors after the ride.

## Sources

- Flathub: `flatpak remote-ls/remote-info flathub` (2026-10-30)
- Kron4ek Wine builds, release 11.20 with WoW64 tarballs: https://github.com/Kron4ek/Wine-Builds/releases/tag/11.20
- KDE documentation on Flatpak manifests: https://develop.kde.org/docs/packaging/flatpak/manifest/
- Kirigami Addons as a separate Flatpak module (example Angelfish): https://lxr.kde.org/source/network/angelfish/flatpak/kirigami-addons.json
