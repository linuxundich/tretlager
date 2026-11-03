# Changelog

All notable changes to Tretlager. Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- *Keep screen on during the ride* (main window, on by default): while Zwift starts and runs,
  Tretlager asks the desktop through the Inhibit portal not to dim, blank or lock the screen and
  not to suspend, also during a break without touching mouse or keyboard. Works on Plasma
  (PowerDevil) and GNOME (session manager); the inhibition ends with the ride or when Tretlager
  quits (`core/awake.py`).

- Notice when Bluetooth headphones (or any other device) are connected through the bridge's
  adapter while a sensor is still waiting: audio crowds the sensors out (tinytin: KICKR plus
  headphones on the AX201, the TICKR timed out for ten minutes until the headphones were removed).
  The bridge reports these devices in its status (`other_devices`); the adapter reset after a
  stuck controller names them as the reason instead of resetting.

### Fixed
- Sensor bridge: a heart rate strap that lost its connection during a break did not come back,
  even after removing and adding it again (tinytin, Intel AX201, kernel 7.2). Every attempt ran
  into the kernel's 20 s connection timeout while the strap was advertising; the kernel logged
  "ACL packet for unknown connection handle", i.e. the controller kept a link that the kernel had
  given up on. After three timeouts in a row of a device that is found, the bridge now switches
  the adapter off and on (at most every ten minutes, not while other Bluetooth devices such as
  headphones are connected; then it asks the user to do it). The other sensors reconnect and Zwift
  keeps them thanks to the grace period.
- The bridge logs the trainer's control point answers at debug level only; at one line per second
  they pushed everything else out of `bridge.log` during a long ride.

## [0.11.0] - 2026-11-01

### Added
- Error reports for testers: *About Tretlager* → *Error reports* → *Save error report…* writes one
  ZIP file (save dialog, via the portal in the Flatpak) with `report.txt` (version and build, host
  system, desktop, screens and scaling, graphics, Wine and Zwift versions, sensor bridge status,
  system check, Flatpak info) and the logs of Tretlager, the sensor bridge, Wine and Zwift plus
  `state.json` and the bridge's device list. Tokens, passwords and e-mail addresses are masked in
  every file; large logs keep their beginning and their last 5 MB (`core/report.py`).
- Debug mode (*Detailed logging* under *About Tretlager*, menu action *Start with detailed
  logging* or `--debug`, stays on until switched off): launch steps in `tretlager.log`, the
  bridge's own messages at debug level, Wine also logs exceptions (`-all,err+all,warn+seh`).
- The sensor bridge also writes `bridge.log` next to `tretlager.log` (the journal cannot be read
  from inside the Flatpak).
- Help: *Reporting a problem* and *Zwift's picture sticks out over the edge of the screen*.
- Wine's output of the Zwift launcher and game goes to `zwift-wine.log` next to `tretlager.log`
  (errors only; the previous launch's log is kept as `zwift-wine.old.log`). Zwift's own crash handler does not work under Wine,
  so this is the only trace of a crash. `TRETLAGER_WINE_DEBUG` sets other WINEDEBUG channels,
  e.g. `-all,err+all,+seh` to log exceptions.
- Zwift opens on the monitor it was on during the last ride: a KWin script reports the window's
  monitor over D-Bus while Zwift runs (`de.linuxundich.Tretlager`, `SetOutput`), the next launch
  moves the window there first and maximises it a few seconds later.

### Fixed
- Zwift's picture stuck out over the edge of the screen after the start: Tretlager maximised the
  window while Zwift was still loading, and Zwift only took the new size much later or not at all.
  Tretlager now waits until Zwift's log reports the interface as ready (`noesisGUI->OnResize end`,
  at most 2 minutes). Possibly also the cause of crashes when loading the world (two monitors,
  tinytin).

## [0.10.0] - 2026-10-31

### Added
- First public release: Flatpak bundle `tretlager-0.10.0-x86_64.flatpak` on the GitHub releases
  page.
- Public repository on GitHub (linuxundich/tretlager) with an English project page as the
  README (features, screenshots, demo video 3:43 in `docs/tretlager-demo.mp4`) and
  `docs/HARDWARE.md` (tested computers, graphics cards, systems, sensors and versions). The
  former German README now lives in `docs/technical-notes.md`.
- All documentation translated into English: changelog, backlog, feasibility study, technical
  notes, UX concept (`docs/ux-concept.md`, formerly `bedienkonzept.md`), Flatpak plan, update
  plan and QA audit.
- Warnings on first start that must be accepted (otherwise *Quit*): not an official Zwift
  app; at your own risk – Zwift may not be happy about a software bridge whose data could be
  manipulated, a suspension including XP and drops cannot be ruled out; not for races; sign-in
  outside the launcher. With a stylised warning sign “Gradient 12 %”
  (`data/icons/tretlager-warning.svg`). Shown again when the text changes (`DISCLAIMER_VERSION`);
  available at any time under *About Tretlager → Show warnings*. Until accepted, Zwift does not
  start automatically.
- Notice “At your own risk” (XP and drops) also in Overview, Welcome, About Tretlager, Help,
  README and metainfo.
- Subtle silhouette of a group of riders behind the page header of Overview and the Welcome page:
  three tone levels from a photo (`build-aux/make-backdrop.py`), in the text colour of the colour
  scheme at 7–9 % opacity, fits both light and dark.
- Version display with the build ID of the Flatpak (*Version 0.9.0 · Build 6a84bf1*, as in
  `flatpak info`) on Welcome and *About Tretlager*, also in the log at startup.
- If PySide does not match the Qt of the installed runtime, Tretlager reports this through a
  notification and in the log instead of silently exiting without a window.

### Changed
- English is now the source language of the interface; the German interface comes from
  `po/de.po` (formerly English from `po/en.po`). Help files: `help.md` (English) and
  `help.de.md`. Comments, docstrings, log messages and scripts are English throughout.
- Internal names in English: sensor states over D-Bus (`connected`, `connecting`,
  `disconnected`, `error`, `paused`), the kept Wine copy `wine-kept` (an existing
  `wine-bewaehrt` is taken over on the first start) and a damaged bridge configuration is moved
  aside as `bridge.broken`.
- Sensor bridge: connects the trainer first and gives up on a sensor after 20 s instead of
  40 s (only the Garmin HRM-Pro keeps 40 s for its slow service discovery). On nanhlanu a sleeping
  TICKR held up the KICKR for 40 s.
- Outside Plasma (e.g. GNOME), Tretlager in the Flatpak uses the Plasma platform theme: Breeze style
  and the complete Breeze icons. Previously the portal reported the GNOME icon theme Adwaita, which
  is missing from the KDE runtime: status and step icons stayed empty, buttons in Fusion style,
  window title bar in monospace. The theme is set explicitly because Flatpak passes through a
  `QT_QPA_PLATFORMTHEME` from the host (on nanhlanu `qt5ct` from `~/.bash_profile`).
- Outside Plasma, Tretlager follows the desktop's light/dark setting (portal
  `org.freedesktop.appearance`, also when switching while running) and takes over GNOME's
  font (`tretlager/kde/desktopstyle.py`).

- The graphics step remembers the graphics chips including drivers and runs again as soon as this
  changes (e.g. NVIDIA switched on via envycontrol); PRIME offload only if the driver and the
  Flatpak GL extension are present. The system check reports a missing extension (`flatpak update`)
  and, with Intel-only graphics, points to switched-off NVIDIA cards; help entry “Zwift on the
  NVIDIA card”. The “Hybrid graphics” row only promises the NVIDIA card if it is usable. Detected
  on nanhlanu (GTX 1050, envycontrol hybrid): graphics test afterwards “NVIDIA GeForce GTX 1050”,
  OpenGL 4.6.

### Fixed
- Crash when opening the sign-in in the Flatpak (SIGABRT): Qt did not find the `QtWebEngineProcess`
  from the BaseApp. `QTWEBENGINEPROCESS_PATH` and `QTWEBENGINE_DICTIONARIES_PATH` are now set in the
  manifest (and as a default in the program). This went unnoticed on tinytin because the session
  was still in the keyring from the days of the Debian package.
- Startup on systems with the KDE runtime 6.11 from Oct 31 (Qt 6.11.3): built against the
  PySide BaseApp 6.11.3 (Flathub test build from flathub/io.qt.PySide.BaseApp#47, until it is
  merged). Previously Tretlager aborted on nanhlanu (Arch) with `undefined symbol …QtPrivate_6_11_2`.

## [0.9.0] - 2026-10-30

QA audit (`docs/qa-audit-2026-10-30.md`), update plan without snapshots (`docs/updates.md`),
reworked Overview and “Not for races” notice.

### Changed
- App icon with silver chainrings and a dark edge: the former, entirely dark icon was hard to
  make out on a dark Plasma panel.
- Updates without snapshots (plan in `docs/updates.md`): before every start, Tretlager reconciles
  the setup. After a Tretlager update with a new Wine, `wineboot -u` adapts the Zwift
  environment and the graphics test runs again; missing Windows components or parts of Zwift are
  reinstalled. The snapshot before Zwift updates is dropped (without Btrfs it cost a full copy of
  7–9 GB), old snapshots are deleted. Tretlager no longer downloads the installer again if the
  Zwift launcher is already installed; it reads installed components directly from
  `winetricks.log` (2 s faster).
- Help “Heart rate far too high”: additionally the tip to replace the strap's battery.
- Notice “Not for races”: there is no guarantee that the sensor bridge passes power, cadence and
  heart rate to Zwift correctly; do not take part in races and ranked competitions with Tretlager.
  Shown in Overview below *Start Zwift*, on the Welcome page, under *About Tretlager*, in Help,
  in the README and in the metadata.
- Overview weighted more towards sport: *Start Zwift* as a large, single highlighted button (has
  keyboard focus), sensor readings as key figures (large digits, unit below).
- Overview: “Ready to ride” only if all enabled sensors are connected, otherwise
  “Almost ready” with the sensors still being searched for.
- Understandable error messages instead of BlueZ/D-Bus messages for sensors and bridge; raw text
  goes to the log.
- During the ride and with the window minimised, the UI polls the bridge only every 15 s
  (UI during the ride 0.4 % CPU).
- Remaining setup texts translated; Debian notice on the sensors page removed.
- README: requirements, updating, uninstalling, data locations, network connections,
  troubleshooting, known limitations.

### Added
- Progress during the Zwift update and the first installation: Tretlager reads the manifest of the
  Zwift version, compares it with the Zwift folder and shows “… 1.2 of 3.4 GB” with a
  progress bar (`core/manifest.py`); without a manifest the duration or, as before, an estimate.
- Previous Wine version: Tretlager keeps the last proven Wine version (exactly one, ≈ 500 MB).
  After a Tretlager update with a new Wine, *Use previous Wine version* in Overview starts
  Zwift with the old one again; after two rides with the new Wine, it replaces the copy.
- Short log of the UI (`core/applog.py`, `$XDG_STATE_HOME/tretlager/tretlager.log`):
  start, second invocations, Zwift running/exited, close, quit – for troubleshooting, without tokens.
- Closing during a ride only after confirmation: in the Flatpak, Zwift runs in the same instance and
  ends with the window.

### Fixed
- Short Bluetooth dropouts: the bridge keeps the device announced to Zwift for 45 s and the
  connection to Zwift open; after reconnecting, data keeps flowing without Zwift having to search
  for the device again (verified on tinytin with an artificially disconnected KICKR: 17 s pause,
  connection held). Previously the device disappeared from Zwift on every dropout.
- Setup: cancel and timeout also take effect when a program hangs silently.
- Bridge: if Zwift stops reading, it discards readings instead of letting the send buffer grow.
- An absent sensor (strap not worn) blocked Bluetooth for up to 40 s per attempt: the
  search in the UI took 40–63 s instead of 3 s, and another sensor that wanted to reconnect
  dropped out for up to a minute. The bridge now searches for the address for at most 8 s,
  separately from establishing the connection (QA audit B-01, `docs/qa-audit-2026-10-30.md`).
- End of ride: Tretlager detects Zwift via `/proc` (argv[0]) instead of launching `wine tasklist`
  every 5 s; an error while checking no longer ends the monitoring (otherwise the UI hung at
  “Zwift running”). Cleanup also happens on unexpected startup errors.
- Without internet and with an expired access token, Tretlager asked for a new sign-in; now it
  says that the Zwift sign-in is not reachable.
- Without a running keyring, the sign-in page got stuck while loading; now there is a message.
- A corrupted `bridge.json` prevented the bridge from starting; it is moved aside as
  `bridge.defekt`.
- Single instance only accepts commands from the same user (`SO_PEERCRED`).
- The bridge kept running after closing if the window was closed before the post-ride cleanup:
  Tretlager now also stops it on quit (except in autostart or while Zwift is running).
- System check in the Flatpak reported too little free space (17 instead of 900 GB on tinytin): it
  measured `~`, which inside the sandbox without permission is just a small tmpfs. It now measures
  the data folder (`XDG_DATA_HOME`) that holds the Zwift environment.

## [0.8.0] - 2026-10-30

First version as a Flatpak (`build-aux/flatpak/de.linuxundich.Tretlager.yml`); the Debian package
is discontinued. Plan and test results in `docs/flatpak.md`.

### Added
- Flatpak with its own Wine 11.20 (built from source as WoW64, mingw-w64), cabextract,
  osslsigncode and the Python packages as pinned wheels (`gen-python-deps.py`); runtime KDE 6.11
  with PySide BaseApp 6.11. Build on tinytin: `build-aux/flatpak/build.sh`.
- Sensor bridge via D-Bus activation (`de.linuxundich.Tretlager.Bridge.service`): its own instance,
  runs independently of the window; new D-Bus method `Quit`; the bridge reports its version, and
  Tretlager restarts an older running bridge after an update (as long as Zwift is not running).
- *Start at login* via the Background portal.
- System check “Device announcement”: without Avahi, Zwift does not find the sensors.

### Changed
- Bridge control, adapter list and Bluetooth check via `gdbus` instead of `busctl`/`systemctl`
  (both missing in the sandbox).
- Assistant in the Flatpak without *Prepare* (Wine is in the package): five steps, the numbers
  follow from the step ID.
- System check: operating system from `/run/host/os-release` and only displayed, no longer rated
  as “target system”; NVIDIA driver also from `/proc/driver/nvidia/version`; Wine “included in the
  Flatpak”.
- Wine DPI reads `~/.config/kwinrc` from the Flatpak as well (read-only permission).
- Help: storage locations under `~/.var/app/de.linuxundich.Tretlager/`, setup in five steps.

### Fixed
- Zwift window in the Flatpak not maximised (cut off at the bottom): the KWin script was in the
  sandbox's private `/tmp`, which KWin cannot see. It now lives in `$XDG_RUNTIME_DIR/app/<App-ID>`.

### Removed
- Flatpak spike from F0 (`build-aux/flatpak/spike/`), replaced by the real manifest.

## [0.7.1] - 2026-10-30

### Added
- Wine windows at screen size on HiDPI (`core/display.py`): Tretlager sets
  `HKCU\Control Panel\Desktop\LogPixels` to 96 × scale, after creating the
  Wine environment, when resuming the setup and before every start (only if it differs).
  The scale comes from KWin's XWayland setting (`kwinrc`, `[Xwayland] Scale`), otherwise from
  the window scale of the UI; `TRETLAGER_DPI` forces a value. On tinytin (1.6×)
  now 154 instead of 96; Zwift starts unchanged with it.

## [0.7.0] - 2026-10-30

### Added
- English UI. Translation via gettext (domain `tretlager`, `tretlager/i18n.py`):
  German remains the source language; without a German system language, English appears;
  `TRETLAGER_LANG` forces a language. All 382 strings from QML (`i18n()`, concatenated strings as
  placeholders `%1`) and Python (`_()`, status messages, errors, system check, setup,
  sign-in, bridge states) are translated, plus the help (`hilfe.en.md`) and the
  desktop files. The Zwift sign-in page appears in the language of the UI.
- `build-aux/msgfmt.py`: compiles catalogues without gettext (missing on tinytin); `po/update.sh`
  collects strings and syncs catalogues; test for completeness and placeholders.

### Changed
- Sign-in page: the sentence saying Tretlager checks the official sign-in after every launcher
  update has been removed – this check does not exist. The help text on the sign-in in Overview
  names Tretlager's own sign-in window instead of the browser.

### Verified
- Embedded sign-in with real credentials (by me, Oct 30).

## [0.6.10] - 2026-10-30

### Fixed
- *Check setup* in the sidebar switched off the sidebar; there was no way back out of the
  assistant. Assistant mode and sidebar are now separate
  (`inWizard` and `navigation` in `Main.qml`): after the setup is complete, the
  sidebar stays usable, the entry is highlighted, and the footer has *Close assistant*.
  Only the first-time setup runs without the sidebar.

### Changed
- After setup, *Check setup* starts right at step 1 (check system) instead of
  at the Welcome page.

## [0.6.9] - 2026-10-30

### Changed
- Help without running text: one card per section with entries made of a bold keyword and a short
  sentence, problem cases with an icon at the bottom across the full width in two columns, paths in
  monospace. The text is restructured (overview, riding, sensors, sign-in,
  privacy and storage locations, setup, when something goes wrong) and much shorter.
- `data/hilfe.md` has a simple format (section, optional icon and `wide`, introduction,
  entries `- [symbol] **Stichwort**: Text`); `core/helpdoc.py` parses it and distributes the
  sections across the two columns by estimated height.

## [0.6.8] - 2026-10-30

### Added
- Pause sensors (button on every paired sensor): the bridge does not search for a paused
  sensor, does not connect it and does not offer it to Zwift; the pairing is kept.
  Meant for sensors that are not in use at the moment, as a step before removing them. Paused
  sensors appear dimmed with “Paused”, also in Overview. Uses the existing
  D-Bus method `SetDeviceEnabled`.
- *Troubleshooting*: entries “Sensor not in use right now” and “Zwift does not find the sensors”;
  help extended.

### Changed
- Device row: third line now only “In Zwift: …” (the icon shows the role), value column
  somewhat narrower. “Connecting …” is now called the same in Help and the problem list as in the
  row: “Searching for the device…”.

## [0.6.7] - 2026-10-30

### Changed
- Sensors: search at the top left (*Sensors nearby*), below it *Paired sensors*.
- Device rows with fixed dimensions (Overview and Sensors): name, state and role with Zwift name
  each on one line, long error messages shortened (in full in the tooltip together with an
  explanation of the state); readings in a fixed-width column with two reserved lines,
  number in bold with the unit next to it, a dash without a value. Previously the height changed
  as soon as values came or went or the state changed.
- Search results: signal as “strong/medium/weak” with dBm; known chip problems as one line
  (`compat_short`), the detailed warning appears on the paired device.
- Texts of the sensors page tightened (bridge, Bluetooth adapter, network, messages, Troubleshooting);
  the adapter selection only shows the chip, the address only when there are two identical sticks.

## [0.6.6] - 2026-10-30

### Changed
- Sensors: *Troubleshooting* sits below both columns across the full width, the four cases in
  two columns. Previously a gap remained on the left below the search, while the right side had
  to be scrolled.
- About Tretlager: *Non-free software* moved to the left column so both columns are of similar
  length.

## [0.6.5] - 2026-10-30

### Changed
- A switched-off Bluetooth adapter counts as missing just like an unplugged one: the bridge
  falls back to the default adapter and returns as soon as it is back on. If an adapter is
  selected, it checks this every ten seconds (previously only while it was missing).
- Readable names for Realtek RTL8761B sticks, including TP-Link UB500.

### Verified
- On tinytin with a TP-Link UB500 (RTL8761BU) as a second adapter: switching while
  running, switching the stick off (fallback to AX201 after about ten seconds) and
  switching it back on. The Garmin HRM-Pro Plus connects through the stick and delivers heart rate,
  on the built-in AX201 it still hangs.

## [0.6.4] - 2026-10-30

### Changed
- Uniform page layout for all pages (`ColumnsPage.qml`, modelled on Overview): messages
  and page header across the full width, two columns below, stacked on narrow windows;
  the same width everywhere (window up to `gridUnit * 62`, centred beyond that). Previously
  all pages except Overview were narrow lists with a lot of empty space on the left and right.
  - Sensors: devices and search on the left, bridge settings and troubleshooting help on the right.
  - Assistant: Welcome and Done with a page header like Overview; Prepare with packages
    in the right column; sign-in with the own browser as the second column.
  - Help: each section as a card, distributed across two columns, the table below.
  - About Tretlager: its own page instead of the narrow standard page, licence text in a dialog.
- Shared components `PageHero.qml` and `PageMessage.qml`; `PageContent.qml` is gone.

### Fixed
- *Check setup* from the sidebar showed an empty list until you chose *Check again*.

## [0.6.3] - 2026-10-30

### Added
- Selectable Bluetooth adapter for the sensor bridge (Sensors → *Bluetooth adapter*), e.g. a
  USB stick on an extension cable next to the trainer, or as a way out with a chip that does not
  get along with a sensor. The adapter's address is stored (`adapter` in `bridge.json`), not
  hciN, because the number can change when replugging. If the selected adapter is missing, the
  bridge uses the default adapter, shows a warning and switches back by itself as soon as it is
  there again. New D-Bus method `SetAdapter`.
- The chip warning refers to the selected adapter and names the USB stick as a remedy.

### Fixed
- The bridge was hardwired to `hci0`; an additional USB stick went unused.

## [0.6.2] - 2026-10-30

### Added
- Warning for known problematic combinations of Bluetooth chip and sensor
  (`tretlager/core/btcompat.py`). Tretlager identifies the adapter's chip by its USB ID and
  matches it against a list of verified cases. First entry: Garmin HRM-Pro on Intel AX201
  (on tinytin the service discovery hangs, on the AX200 the strap works).
  - Search: the result carries a warning icon and the notice before it is added.
  - Sensors page: warning directly on the device instead of an endless “Connecting …”.
  - Overview: warning for enabled devices with a known problem.
- System check names the Bluetooth chip.
- Help and sensors page: entry “Device never connects”.

## [0.6.1] - 2026-10-30

### Added
- Notices about power supply on laptops (`tretlager/core/power.py`). Reason: on tinytin,
  Zwift hung after the power adapter was unplugged or plugged in during startup; the NVIDIA driver
  reported dozens of “Xid 69” at the time. The graphics do not switch to the Intel chip, the TCC
  profile stays the same; presumably nvidia-powerd changes the power budget.
  - Overview on battery: recommendation to start with the power adapter and keep it connected.
  - Power source change during startup or ride: desktop notification and warning with
    remedy (Alt+F4, restart with the power adapter).
  - After the ride: if the NVIDIA driver reports errors in the kernel journal, Overview shows them
    with the likely cause.
- Help: section on the power adapter and table entry “Zwift hangs after unplugging or plugging in”.

## [0.6.0] - 2026-10-30

### Changed
- Sign-in to Zwift without an error page: the sign-in page opens in an embedded,
  private window (QtWebEngine, without cookies on disk), as in the official launcher.
  Tretlager intercepts the redirect before “Bad Request” appears; copying the address
  is no longer needed. Zwift does not allow other redirect addresses.
- The sign-in page appears in the system language (`ui_locales`).
- Error codes from Zwift (e.g. `login_required`, `access_denied`) appear as plain text.
- The own browser remains as a fallback, e.g. for password managers or signing in with
  Google or Apple.
- New package dependencies: `python3-pyside6.qtwebenginequick`, `qml6-module-qtwebengine`.

## [0.5.1] - 2026-10-30

### Removed
- GTK4/libadwaita UI of the bridge (`tretlager-sensoren-gtk`, recommends `python3-gi`,
  `gir1.2-gtk-4.0`, `gir1.2-adw-1`). The bridge is now controlled only through the Kirigami UI;
  its sensor icons now live in `tretlager/data/icons`.

### Changed
- The help no longer addresses the reader with the informal “du” (KDE HIG) and uses the new names
  (Overview, sidebar, *Sign in again…*).
- Help: section on dropping connections added, UI names in italics.

## [0.5.0] - 2026-10-30

### Changed
- UI reworked according to the current KDE Human Interface Guidelines:
  - Sidebar (Kirigami GlobalDrawer) with Overview, Sensors, Help, Check setup
    and About Tretlager; the assistant remains a linear flow with one page and a
    back button.
  - Settings, devices and lists as FormCards from Kirigami Addons instead of custom cards;
    explanations behind help buttons (ContextualHelpButton) instead of long blocks of text.
  - Overview: start without a frame at the top, sensors and Zwift in two columns below.
  - Remove buttons stay visible, logs open in a dialog.
  - Texts short and impersonal, units spelled out, ellipses on actions
    that require further input.
  - Assistant pages with a progress bar “Step n of 6” and a uniform footer.
- About Tretlager uses KDE's standard about page (Kirigami Addons) with the licence text.
- New package dependencies: `qml6-module-org-kde-kirigamiaddons-formcard` and
  `-components`; recommended `qml6-module-org-kde-desktop`.

### Added
- Replacement for KLocalizedContext (`tretlager/kde/i18n.py`): Kirigami Addons shows its own
  labels translated, even though PySide has no KI18n binding.
- `TRETLAGER_INSTANCE` starts a second instance next to the running one for testing.

## [0.4.1] - 2026-10-30

### Added
- Page “About Tretlager” (menu and Welcome page): version, notice that Tretlager is not an
  official Zwift program and is used at your own risk, licence, and the
  free and non-free components with their licences.
- Licence GPL-3.0-or-later (`LICENSE`), in the Debian package as `copyright`.
- The Welcome page shows the notice about Zwift and liability right before the setup.

### Changed
- New icon in the style of today's road bike cranks: four-arm spider, two chainrings,
  tapered crank arms, horizontal clipless pedals centred on the crank eye. Generated by
  `build-aux/make-icon.py`.

## [0.4.0] - 2026-10-30

### Changed
- New Overview for the desktop: “Start Zwift” with an explanation at the top, below it cards in two
  columns for sensors, Zwift version, graphics, sign-in, and help and maintenance; each card
  briefly explains what is behind it.
- Sensors page restructured: bridge with its switches, your devices as large cards with
  state, readings and Zwift names, search for new devices, “If something goes wrong”.
- At startup, Overview and Sensors sit side by side, the window opens larger.
- Setup pages with limited reading width; explanations as calm notes instead of blue
  message boxes.
- Icon: the pedals are horizontal, the rear one sits behind the crank arm and chainring.

## [0.3.2] - 2026-10-30

### Changed
- In a wide window, the main window shows the sensors right next to it.

## [0.3.1] - 2026-10-30

### Changed
- Tretlager opens wide enough for the main window and sensors or help to fit side by side,
  provided the screen has room.

## [0.3.0] - 2026-10-30

### Added
- Only one Tretlager instance: a second invocation brings the open window to the front;
  “Zwift (Tretlager)” then starts Zwift in the existing window.
- Switch “Offer on the network” on the sensors page: the bridge also announces its devices on the
  LAN (e.g. bridge on a computer next to the trainer, Zwift on another device).
- Notice on weak radio: if a sensor connection drops three or more times in 10 minutes,
  the sensors page and main window show a notice with a remedy.
- Debian package source on the home network: `deb [trusted=yes] http://bender:8095/debian ./`.

## [0.2.1] - 2026-10-29

### Fixed
- Sensor bridge: devices that fall asleep again while connecting (trainer after a pause) are
  retried after 10 s instead of with a growing pause of up to 60 s.

## [0.2.0] - 2026-10-29

### Added
- Own app icon in Breeze style (crankset with chainring, two crank arms and
  pedals).
- Help in the app (menu → Help, Welcome page): setup, everyday use, pairing in Zwift,
  sign-in, troubleshooting, privacy, storage locations.
- Start menu entry “Zwift (Tretlager)” and quick action “Start Zwift”: starts Zwift directly
  (`tretlager --start`) and quits Tretlager after the ride.

### Changed
- The sensor bridge starts as soon as the main window opens, so that trainer and strap are
  connected when you get on the bike.
- The main window checks for a Zwift update in the background and shows it before the start.
- During the ride, Tretlager minimises itself and comes back to the front afterwards.

## [0.1.0] - 2026-10-29

First version, tested on TUXEDO OS forky (tinytin) with Wahoo KICKR V4 and Wahoo TICKR.

### Added
- Setup assistant for Plasma (PySide6 + Kirigami): system check, system preparation with
  a single Polkit prompt (WineHQ source, Wine), Zwift setup with resume,
  sign-in, sensors, completion.
- Main window with “Start Zwift”: bridge, token renewal, update with prefix snapshot,
  start on the NVIDIA card (GLX + PRIME offload), maximise window (KWin), cleanup.
- Installer verification via Authenticode signature (Zwift, Inc.).
- Sensor bridge `tretlager-bridge` (systemd user service): BLE devices via BlueZ as Wahoo
  Direct Connect (DIRCON) for Zwift, including FTMS control (gradient, ERG); announcement on
  127.0.0.1; GTK UI `tretlager-sensoren-gtk`.
- Optional sign-in via the browser (at your own risk), token in the keyring.

### Security
- Token never on command lines or in logs; signing out ends the session at Zwift.
