# Backlog

## Decisions

- [x] **E1 Wine source.** Approved 2026-10-29 for tinytin (T2). Debian forky has no Wine. Recommendation: WineHQ repo (`winehq-devel`,
  suite forky) via a pkexec helper with a fixed action, a pinned key and
  explicit consent. Alternative: umu-launcher + Proton in the user directory (no
  root, but Steam Runtime container and less proven with Zwift).
- [x] **E2 Sign-in.** My decision 2026-10-29: browser sign-in is offered as an explicit option with
  a reference to ToS §5 (the official sign-in does not work under Wine, see T2). Starting via
  `RunFromProcess` (game as a child of the launcher) is part of it.
- [x] **E3 Sensors.** Implemented (tretlager/bridge, since 0.8.0 via D-Bus activation instead of systemd). Own lean bridge (Python, bleak, systemd user service) BlueZ →
  DIRCON instead of qdomyos-zwift. Project licence GPL-3, so that qdomyos protocol code may be
  adopted as a reference.
- [x] **E4 Desktop.** My decision 2026-10-29: GTK4/libadwaita or Qt/Plasma, both allowed.
  Implementation as in Stafette: core as a UI-free Python library (diagnostics, installation,
  updates, bridge control), with GTK/libadwaita and Qt/Kirigami on top. Which UI comes
  first is decided in phase C; the target machine tinytin runs Plasma.
- [x] **E5 Test hardware.** Machine settled: `testt@tinytin` (forky, Plasma, Intel + RTX 3050 Ti
  with PRIME offload, driver 580, AX201). Devices: Wahoo KICKR V4, Garmin HRM-Pro Plus
  (BLE + ANT+), built-in adapter; plus Wahoo TICKR and USB stick TP-Link UB500 (Oct 30).
- [x] **E6 Language.** Python (core, bridge), Debian package.
- [x] **E8 Distribution.** My decision 2026-10-29: for now only a locally built Debian package; later a
  package source on bender (the Arch repo `pacman-repo` already runs there).
- [x] **E9 UI first.** My decision 2026-10-29: Kirigami (target Plasma). The GTK UI of the
  bridge stays and will be adapted to the core later.
- [x] **E10 Wine policy.** My decision 2026-10-29: always the latest `winehq-devel`, no pinning.
  Consequence: Tretlager checks itself after every Wine update (GL test, start test) and reports breakage.
  In the Flatpak (since 0.8.0), Wine comes with the Tretlager version; “latest Wine” there means: bump Wine in the
  manifest with every Tretlager version and test beforehand. After the switch, Tretlager reconciles
  the environment by itself (docs/updates.md).
- [ ] **E7 Name.** Working title “Tretlager”.

## Phases

- [x] A Feasibility (research) – [FEASIBILITY.md](FEASIBILITY.md)
- [x] D' Feasibility tests T1–T7 (FEASIBILITY.md, section 9): Zwift, graphics, sign-in and bridge run on tinytin (Oct 29/30)
- [x] B Read-only system diagnostics (core/systemcheck.py; in the Flatpak without Debian assumptions) (os-release, sysfs/DRM, nvidia-smi, EGL test, BlueZ via D-Bus,
  Wine version + stub check, space, existing prefixes)
- [x] ~~C GTK4 prototype~~ dropped: my decision 2026-10-30, it stays with the Kirigami UI
- [x] ~~D Installation: PackageKit~~ dropped in the Flatpak (Wine in the package); implemented are (simulation + installation), pkexec helper for the WineHQ source,
  download + Authenticode, prefix, launcher, steps with resume (core/setup.py)
- [x] E Bridge BLE → DIRCON with real hardware (power, cadence, ERG, heart rate; test rides Oct 29/30)
- [x] F Updates (SilentLaunch, `Zwift_ver_cur.xml`, reconciliation before the start, progress; plan docs/updates.md, 0.9.0)
- [ ] G End-to-end on a fresh TUXEDO OS Forky → merged into F5 (Flatpak acceptance)
- [ ] later: native ANT+ in the bridge (openant/libusb)

## Bridge (T5/T6)

- [x] Bridge core (DIRCON, GATT proxy, avahi, D-Bus, systemd user service)
- [x] UI: service on/off, autostart, search/add/remove devices, live values
- [ ] HRM-Pro Plus on tinytin: LE 1M cross-check (`btmgmt phy`), otherwise test a USB Bluetooth stick
  (warning since 0.6.2 via `core/btcompat.py`; add new findings there)
- [x] Switch the bridge to a selectable adapter (0.6.3; switching, missing adapter and fallback
  verified on tinytin, not yet with a real USB stick)
- [x] Test with a real USB Bluetooth stick (Oct 30, TP-Link UB500): HRM-Pro Plus via the stick ok,
  switching, turning the stick off and on ok
- [ ] Pull the stick during a ride in Zwift (real unplugging instead of switching off)
- [ ] HRM-Pro Plus via UB500 unreliable: on the morning of Oct 30 connected twice (after 40–120 s),
  at midday despite signal (−74 dBm), without phone Bluetooth, worn alone and after restarting the stick
  only timeouts; KICKR on the same stick connected immediately. Approaches: btmon capture (root),
  force LE 1M (`btmgmt phy`), connection parameters/timeout of the bridge, a second stick of a different make.
  After restarting tinytin, connected again immediately (30 s, 62 bpm) → stuck state in BlueZ
  or in the controller (restarting the stick via Powered was not enough). Next time try
  `systemctl restart bluetooth` first; possibly a Tretlager notice “Restart Bluetooth” for a device that is
  found but never connects.
  Live test Oct 30 12:3x (Flatpak): stuck again, BlueZ reports `Connected=true` on the UB500,
  `ServicesResolved=false` → GATT service discovery hangs as on the AX201, even after RemoveDevice and
  replugging the stick. Next step: btmon capture and force LE 1M (`btmgmt --index 1 phy`,
  root); the bridge could do a targeted disconnect + clear cache when service discovery hangs
- [ ] After switching, the first connection attempt of the HRM-Pro sometimes needs one more round
  (incomplete service discovery → wait time grows); possibly reset the wait time after an adapter change
- [x] Package update does not restart the running bridge → solved in the Flatpak: Tretlager restarts an
  older bridge on opening (version comparison, since 0.8.0; requires a new version number)
- [x] Sensors page: the *Sensor bridge* switch looked off under Plasma although `checked` was true
  (Oct 30, still FormCardPage); rendered correctly since the new page layout (0.6.4), not seen again since
- [x] Check TICKR with a clean signal (electrodes moistened: values like the heart rate watch)
- [x] Zwift pairs KICKR (power, cadence) and heart rate strap via DIRCON, values realistic (2026-10-29)
- [x] ERG and gradient simulation via FTMS control point (response in the write response, 2026-10-29)
- [ ] UI: notice on hanging service discovery (“unclip the strap briefly”) instead of an endless “Connecting …”
- [ ] UI: Plasma polish (icons checked, remove button new)
- [x] Network change: close connections whose local address has disappeared
- [ ] Test without any network connection (announcement on lo present)
- [ ] Check a longer ride (≥ 30 min) for stability
- [x] Network change during the ride: announcement on 127.0.0.1, listening only on loopback (2026-10-29)
- [ ] Repeat the network change test: cable off/on during the ride

## Operation (concept: docs/ux-concept.md)

- [x] Decisions: E2 yes, local .deb (later bender), Kirigami first, latest Wine (2026-10-29)
Implementation in milestones (core Python `tretlager/core`, UI PySide6 + Kirigami `tretlager/kde`):

- [x] M1 System check in the core (without root) + Kirigami skeleton: Welcome, check page with traffic lights (verified on tinytin 2026-10-29)
- [x] M2 Prepare: Polkit helper `setup-system` (WineHQ source, package list via APT simulation), page with list of changes — run on tinytin with the Polkit dialog (2026-10-29, after fixing the gpg working directory)
- [x] M3 Set up Zwift (core): steps with resume, download + signature, prefix, winetricks, launcher, game, GL test — end-to-end on tinytin in 459 s, second run 2 s (2026-10-29)
- [x] M3 Page “Set up Zwift” clicked through in the UI (all steps “already done”)
- [x] M4 Sign-in: browser sign-in with notice, takeover from the clipboard, token in the keyring (ksecretd), renewal — verified on tinytin (2026-10-29)
- [ ] Clarify Breeze warnings “ProgressBar.qml: Cannot read property 'top' of null” while building pages
- [x] M5 Sensors page (bridge via D-Bus) + main window “Start Zwift” — on tinytin: start with token from the keyring, NVIDIA, window maximised via KWin, resolution kept, launcher leftovers ended (2026-10-29)
- [x] Security: token never on command lines/in logs (file + `--token=@`), signing out ends the session at Zwift
- [x] Bridge restart on install briefly disconnects sensors → restart only if Zwift is not running (0.8.0)
- [x] End of a Zwift session: bridge stops if not in autostart (verified with direct start)
- [x] M6a Debian package `tretlager` (`build-aux/build-deb.sh`), 0.2.0 installed on tinytin, bridge from the package runs (2026-10-29)
- [x] ~~M6b End-to-end Debian package~~ dropped (Debian package discontinued) → F5; fresh first installation
  in the Flatpak ran through twice on tinytin (Oct 30, 15 min)
- [x] Direct start “Zwift (Tretlager)” verified on tinytin: start after 15 s, NVIDIA, window/resolution ok, no token in the journal, Tretlager quit after the ride, bridge stopped (2026-10-29)
- [x] Only one Tretlager instance (second invocation uses the existing window; 0.3.0)
- [x] Package source on bender (Debian): `services/pacman-repo/publish-deb.sh`, `http://bender:8095/debian` (0.3.0)
- [x] Range: notice in the UI on frequent dropouts (≥ 3 in 10 min) with a remedy (0.3.0)
- [x] UI: switch “Offer on the network” (`local_only`), D-Bus `SetLocalOnly` (0.3.0)
- [x] ~~Update the bridge's GTK UI~~ dropped: GTK UI removed in 0.5.1 (my decision 2026-10-30)

## Languages

- [x] English UI (0.7.0, gettext, `po/en.po`)
- [x] English as the source language, German as `po/de.po` (2026-10-31)
- [ ] New strings: `po/update.sh` (on the Arch machine with gettext), add the translation to `po/de.po`;
  `tests/test_i18n.py` reports gaps

## Flatpak (plan: docs/flatpak.md)

- [x] F0 Feasibility on tinytin (Oct 30): all building blocks work (Wine from source, multiarch); open: a real ride, copy of the existing prefix
- [x] F1 Manifest and build (0.8.0): Wine from source, Python wheels pinned, metainfo, build.sh on tinytin
- [x] F2 Code (0.8.0): bridge via D-Bus activation + Quit, autostart portal, bridge version, gdbus, assistant without Prepare
- [ ] Check autostart of the bridge via the Background portal after a reboot of tinytin
- [ ] F2b Distribution-independent: system check without Debian assumptions, Avahi check, GNOME fallbacks (maximise, DPI)
- [x] F3 Switch-over on tinytin: Debian package removed, old package data (36 GB) deleted (Oct 30)
- [ ] F4 Flatpak source on bender with GPG key
- [ ] F5 Acceptance: fresh TUXEDO OS, Fedora KDE + GNOME, Arch, long ride; switch off the Debian source on bender
- [x] **Startup abort on nanhlanu (Arch, GNOME 51, Oct 31):** bundle (master ce6b144, built on tinytin) installs in 19 s but does not start: `QtCore.abi3.so: undefined symbol _ZN14QObjectPrivateC2E16QtPrivate_6_11_2, version Qt_6_PRIVATE_API`. nanhlanu has `org.kde.Platform//6.11` from Oct 31 (commit fb23e178), tinytin an older one (76fa01ac). PySide from `io.qt.PySide.BaseApp` depends on the private Qt API of the patch version → any runtime update can break Tretlager. Find a solution: rebuild against the current runtime + BaseApp, pin the runtime commit, or build PySide ourselves against the runtime; make startup errors visible (no window, no log). Fixed: built against BaseApp 6.11.3 (test build #47), notice on startup abort
- [ ] Switch BaseApp on tinytin back to Flathub stable once flathub/io.qt.PySide.BaseApp#47 is merged (`flatpak uninstall --user io.qt.PySide.BaseApp//6.11` + `flatpak install --user flathub io.qt.PySide.BaseApp//6.11`), then rebuild
- [x] Crash at sign-in in the Flatpak (nanhlanu Oct 31): `QtWebEngineProcess` not found → variables in the manifest; embedded Zwift page opens
- [x] GNOME: icons were missing (portal reports Adwaita, not in the KDE runtime) → Plasma platform theme outside Plasma (Breeze)
- [x] GNOME: take over light/dark from GNOME: `KDE_COLOR_SCHEME_PATH` + palette from Breeze(Dark).colors, portal signal for the switch (kdeglobals approaches fail: in the Flatpak the Plasma theme only reads the portal)
- [x] GNOME: font from GNOME (portal `font-name`, Adwaita Sans 12) instead of Noto Sans
- [x] nanhlanu: graphics test on the GTX 1050 after envycontrol hybrid + GL.nvidia-580-196-07 (--user) ok (Oct 31)
- [ ] nanhlanu: Zwift ride on the GTX 1050. First attempt Oct 31 16:13–16:25: Zwift on the GTX 1050 (60 FPS), finds KICKR + TICKR via mDNS immediately (16:14:09); pairing only at 16:24 (power, then heart rate; heart rate never reached the bridge). Power adapter on at 16:13, off at 16:24:09 → 20 FPS, Zwift freezes at 16:25:12 (log stops), no Xid. TLP on nanhlanu: battery = PCIE_ASPM powersave, RUNTIME_PM_ENABLE=00:01.0 (port of the GTX 1050) → suspicion as on tinytin: power source change during the ride. Repeat: on the power adapter throughout, pair controls by hand
- [ ] Fresh Zwift prefix: Zwift only pairs the selected role (Power); on tinytin, Cadence + Controllable Trainer only come from saved pairings (“Reconnected and selected”). Select by hand the first time → notice in Help/Done page; check whether the Controllable list via DIRCON shows the KICKR (my note: “resistance not found”)
- [ ] “Log of the last start”: take over pairing lines and FPS from Zwift's Log.txt (without tokens), so that findings like this one are visible without SSH
- [ ] GNOME: check light/dark switching while running on a real desktop (verified offscreen via call)
- [ ] Before every release (F4): compare the Qt version of runtime and BaseApp; after a Qt patch update of the runtime, rebuild and publish promptly, otherwise Tretlager does not start for users

## In-app notices

- [x] Add a liability notice about the sensor bridge (my decision Oct 30): Zwift may not be
  happy that a software bridge sends data to Zwift that could be
  manipulated. Therefore make it clear: use at your own risk – so nobody loses the XP and drops
  they earned with a lot of sweat (account suspension or reset cannot be ruled out).
  Complements the “Not for races” notice (Welcome, Overview, About Tretlager, Help, README,
  metainfo); tone relaxed but unambiguous.
- [x] On first start, a warning that must be accepted (my decision Oct 30), with all
  liability notices together: Tretlager is not an official Zwift app and is not supported by Zwift;
  use at your own risk (XP and drops); not for races, no guarantee for the
  values of the sensor bridge; signing in through Tretlager's own window contradicts Zwift's terms of use.
  Remember the acceptance in the state; show it again when the notice text changes (version marker).

## Security

- [ ] Zwift receives the token as a command line argument (`ZwiftApp.exe --token={…}`); it therefore appears in the
  process list and is readable by every local user (`ps`). Check whether RunFromProcess can pass the token
  differently (file/pipe) or whether Zwift only accepts it this way; otherwise mention it in the help.
  (Seen Oct 30 during the Flatpak test; never print `pgrep -fa Zwift` or similar.)

## QA audit 2026-10-30 (docs/qa-audit-2026-10-30.md)

- [x] B-01 absent sensor blocked Bluetooth for 40 s (measured, fixed)
- [x] Z-01/Z-02, L-01, L-02, B-02, B-03, U-01, U-02, S-01, I-01, I-02 fixed
- [x] B-04 keep the device for Zwift for 45 s on a short BLE dropout (verified live with a disconnected KICKR)
- [ ] B-05 test standby/resume and pulling the stick during the ride
- [ ] F-01 replace or justify `--talk-name=org.kde.KWin` (only for maximising)
- [ ] Bridge state via QtDBus signal `Changed` instead of gdbus polling; split up `Backend`
- [x] C-01 `setup.Context.run`: enforce the timeout even without output
- [x] C-02 DIRCON: limit the send buffer when Zwift is not reading
- [x] U-03 Larger start button, live values as key figures (within the HIG); still look at the highlighting under real Plasma (screen was locked)
- [ ] Metainfo: screenshots (release description since 0.9.0)

## Updates (docs/updates.md)

- [x] No snapshots; reconcile the setup before every start (Wine change → `wineboot -u` + graphics test)
- [ ] Report a new Tretlager version in the program (Flatpak portal) – deliberately open, no Flathub planned (my decision Oct 30)
- [x] Progress during the Zwift update from the Zwift manifest
- [ ] Observe the progress during a real Zwift update
- [x] Keep the previous Wine version (one) and make it selectable in Overview
- [ ] Renew a Windows component selectively (revision marker per verb, `winetricks --force`)
- [ ] Run through a real Wine switch on tinytin (build Tretlager with a different Wine version)

## Next features (2026-10-31)

- [ ] **Use the Companion app instead of the bridge.** Option to switch off the sensor bridge completely
  and pair trainer and heart rate strap through the Zwift Companion app on the phone instead.
  - Setting in Sensors (or Overview): “Sensors via: Tretlager bridge / Companion app”
  - With Companion: never start the bridge (no D-Bus activation, no autostart, no DIRCON announcement),
    skip the Bluetooth checks in the system check, adapt start page and help (phone and PC in the same network)
  - Check whether Zwift under Wine finds the Companion app at all (network, mDNS from the prefix)
- [ ] **MyWhoosh support.** Same workflow as for Zwift, only for MyWhoosh: system check, dependencies,
  download, installation, updates, setup in its own prefix. Start through Tretlager, with a choice
  between Zwift and MyWhoosh when both are installed.
  - Feasibility first (like FEASIBILITY.md for Zwift): does MyWhoosh run under Wine (graphics API, anti-cheat,
    sign-in), where does the Windows installer come from (Store or direct download), how are updates detected,
    does MyWhoosh accept sensors via DIRCON from the bridge (otherwise: Companion/link app only)
  - Core: separate the game-specific parts (`setup`, updates, start, sign-in) behind a common interface
    instead of copying them; Zwift becomes one implementation
  - UI: game selection in the assistant (set up one or both), start button per game or a selection on start;
    texts and liability notices no longer Zwift-only
  - Naming: app description and README mention both games
