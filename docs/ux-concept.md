# UX concept: from an empty computer to a running Zwift

Status: 2026-10-29. The target is TUXEDO OS based on Debian testing (forky) with Plasma, as on
tinytin. It is based on the tests in [FEASIBILITY.md](../FEASIBILITY.md); all times and sizes
were measured there.

## 1. Guiding principles

1. **One way, no choice where none is needed.** Tretlager decides for itself whatever can be
   measured: GPU path, Wine version, window behaviour. It only asks when the user has a real
   decision to make: system changes, sign-in method, sensors.
2. **One password, not five.** All system changes are bundled through *one* helper with *one*
   Polkit prompt.
3. **Waiting is fine, guessing is not.** Long steps (download, prefix) run without user
   interaction, with real progress and remaining time, not with a bar that hangs at 99 %.
4. **Be honest.** What does not work on Linux (official sign-in, ANT+) is stated clearly, along
   with what is possible instead.
5. **Everyday use = one button.** After setup, *one* click starts the bridge, updates, sign-in
   and Zwift in the right order.

## 2. What the user does in the end

| # | Action | Duration |
|---|---|---|
| 1 | Install Tretlager (Discover or double-click the .deb) | 1 min |
| 2 | Start Tretlager, *Set up* | – |
| 3 | Confirm the system changes, password **once** | 1 min |
| 4 | Wait: Wine, components, Zwift (no interaction) | approx. 10 min |
| 5 | Choose the sign-in method, sign in to Zwift in the browser | 1 min |
| 6 | Wake up the trainer, put on the strap, adopt the devices | 2 min |
| 7 | *Start Zwift*, pair once in Zwift | 2 min |

Measured on tinytin: Wine packages 289 MB, prefix with winetricks **297 s**, Zwift game 4.9 GB
in 1–2 min (fibre), total disk usage about 10.5 GB (1.8 GB system, 8.6 GB prefix).

## 3. Getting Tretlager

| Way | Assessment |
|---|---|
| **Debian package `tretlager`** (recommended) | fits the system integration: systemd user service, Polkit action, BlueZ, avahi. Dependencies from Debian: `python3-gi`, `gir1.2-adw-1`, `python3-bleak`, `avahi-daemon`, `bluez`, `osslsigncode`, `cabextract`. Wine is **not** a dependency (not in forky) but comes through the assistant |
| Own APT repository (like `pacman-repo` for Arch) | automatic updates through Discover; worth it after the first users |
| Inclusion in the TUXEDO repository | best way for TUXEDO OS users (one source, no third-party key); requires coordination |
| Flatpak | unsuitable: Polkit helper, system packages, systemd user service and Wine on the host do not fit into the sandbox |

After installation: application menu entry **Tretlager** (category Games/Sports).

## 4. First start: the setup assistant

One window with pages (Adw.NavigationView or Kirigami page stack), with the step bar at the top:
*Check → Prepare → Zwift → Sign-in → Sensors → Done*. Every step is idempotent; if the user
cancels or the power fails, Tretlager picks up from there at the next start.

### 4.1 Welcome
- One sentence on what happens: “Tretlager sets up Zwift on this computer and connects your
  trainer and heart rate strap.”
- What you need: a Zwift account, about 11 GB of space, internet, a trainer/strap with Bluetooth.
- A note, small but present: Zwift does not officially support Linux; Tretlager uses Wine.
- Button **Let's go**.

### 4.2 Check the system (automatic, without root, a few seconds)
List with traffic lights, each row expandable with details:

| Check | Green | Yellow (works, with a note) | Red (blocking) |
|---|---|---|---|
| System | TUXEDO OS forky | other Debian testing | not amd64 |
| Graphics | NVIDIA driver loaded, GL test shows NVIDIA | Intel/AMD only (Mesa): runs, weaker | no OpenGL 3.1 |
| Hybrid graphics | detected → PRIME offload is set | – | – |
| Secure Boot + NVIDIA | module loaded | – | module not loaded: pointer to the TUXEDO guide, Tretlager changes nothing |
| Bluetooth | adapter on, BlueZ running | adapter off → button *Turn on* | no adapter: sensors later |
| Disk space | ≥ 15 GB free | 11–15 GB | < 11 GB |
| Network | cdn.zwift.com, dl.winehq.org reachable | – | offline |
| Existing Zwift | – | prefix found → *Adopt* or *New* | – |

The GL test is the one from T3 (`GLTest.exe`), but it only runs after Wine is installed. Until
then sysfs/`nvidia-smi` is enough; the result is filled in during 4.4.

### 4.3 Prepare the system (one confirmation, one password)
Page *I will make these changes to the system*:
- Add the **WineHQ** repository (dl.winehq.org, key D43F…672F)
- Install packages: `winehq-devel` *(tested version 11.20)* plus dependencies, download
  289 MB. The exact list comes from the APT simulation, before the confirmation.
- **No** i386 architecture, no system upgrade, no driver change

Button **Apply** → one Polkit prompt for `de.linuxundich.tretlager.setup`. The helper is a
fixed script without free parameters (check the key, write the source, `apt-get install` of the
fixed list, output line by line to the interface). On TUXEDO OS Snapper creates a snapshot
before and after APT anyway, and the page points this out.

Why not PackageKit: it cannot add a third-party repository with a key (FEASIBILITY §2). For the
package installation alone it would be possible; a single helper is simpler, though, and saves a
second prompt.

### 4.4 Set up Zwift (no interaction, approx. 10 min)
One page with a list of steps, the running step with progress and remaining time:

1. Download the Zwift installer (34 MB) and **verify the signature** (Zwift, Inc., SSL.com chain,
   `osslsigncode`): ✔ with the signer in the details
2. Create the Wine environment (`~/.local/share/tretlager/prefix`, without Mono/Gecko)
3. Components from Microsoft: fonts, .NET 4.8, d3dcompiler, WebView2 (winetricks with a
   pinned commit; note about Microsoft's licence)
4. Install the Zwift launcher
5. Download the game (4.9 GB, through the official launcher in the background)
6. Set up graphics: GL test → GLX + PRIME offload on hybrid systems, `UseEGL=N`, `UseXRandR=N`;
   result: “Zwift uses NVIDIA GeForce RTX 3050 Ti”

Pitfalls from the tests that the user should never see:
- `cabextract` missing → is a package dependency
- Dialogs from Wine (`rundll32 … could not be started`) → no prefix switch between Wine
  versions, set `WINEDLLOVERRIDES`, suppress dialogs by disabling `winedbg`
- After the download the version file is called `Zwift_ver_cur.<build>.xml`

### 4.5 Sign-in (the one delicate spot)
Worded honestly, two cards side by side:

| Card | Content |
|---|---|
| **Official sign-in** | “Currently does not work on Linux.” A short reason in the details (launcher 1.2 uses a Windows feature that Wine lacks). Tretlager checks with every launcher update whether it works again, and switches over then. |
| **Sign-in through the browser** | “You sign in on the Zwift page in your browser. Tretlager then takes over the session.” Below, clearly: “Zwift does not allow third-party programs in its sign-in (terms of service §5). You use this method at your own risk.” Checkbox *Understood* + button **Sign in in the browser** |

Browser sign-in flow, simpler than in the test:
- Instead of copying the address: for the duration of the sign-in, Tretlager registers its own
  handler or reads the redirect address through a small local window. *(To be checked: the
  redirect always goes to `launcher.zwift.com`; it can only be captured through the clipboard.
  The fallback remains: “Copy the address and paste it here” with an input field that recognises
  the code right away.)*
- Token only in the keyring (KWallet/Secret Service), never in files or logs.
- The token is valid for **6 h**, the refresh token for **8 days**. With refreshing, you only
  have to sign in if you have not ridden for more than a week. *(The refresh uses the same
  unofficial interface; that belongs in the same note.)*

This page depends on decision **E2**; without approval the assistant ends here with
“Zwift is installed; starting it is currently not possible”.

### 4.6 Sensors
- The bridge service is set up and started (user service, no root).
- Large note: “Pedal briefly and put on your heart rate strap.” The search starts right away.
- Devices found, with icon and role; trainer and strap are **preselected**, one button
  **Adopt**.
- Live values directly on the page (watts, rpm, bpm), so the user sees that it works.
- Diagnostics from the tests built in:
  - Implausible heart rate (RR intervals jump) → “Moisten the electrodes, wear only one strap”
  - Service discovery hangs (HRM-Pro Plus on AX201) → “Unclip the strap briefly; if it stays
    like this, your Bluetooth chip does not get along with this strap”
- *Skip* is possible (Zwift also runs without sensors in spectator mode).

### 4.7 Done
- Summary: Zwift version, graphics, sign-in, sensors.
- Switch **Start sensor bridge at login** (default: off; Tretlager starts it when Zwift starts
  anyway).
- Button **Start Zwift**. In addition, an application menu entry **Zwift** is added that takes
  the same start path.
- One-time note for Zwift: “Under *Paired Devices*, choose “Wahoo KICKR …” for power, cadence
  and resistance, and “Wahoo HRM …” for heart rate. The warnings about Bluetooth and ANT+ in
  Zwift are normal.”

## 5. Everyday use: the main window

```
┌───────────────────────────────────────────────┐
│ Tretlager                                  ☰  │
│                                               │
│          Ready to ride                        │
│     [        Start Zwift          ]           │
│                                               │
│  Sensors    KICKR ● 0 W   TICKR ● 62 bpm      │
│  Zwift      1.124.0 · up to date              │
│  Graphics   NVIDIA RTX 3050 Ti                │
│  Sign-in    valid, refresh in 7 days          │
└───────────────────────────────────────────────┘
```

**Start Zwift** does the following in this order, each with a status line:
1. Bridge running? Otherwise start it; devices connected? Otherwise a note “Wake up the trainer”
   (not blocking).
2. Token valid? Otherwise refresh it; if that has expired too → browser sign-in.
3. Update? `Zwift_ver_cur` local vs. CDN; if newer: prefix snapshot (Btrfs reflink,
   0.4 s), update through the launcher (`SilentLaunch`), then check the version.
4. Start Zwift (launcher in the background, game as a child process), GLX + PRIME offload.
5. Maximise the window (KWin rule or window size) so the Plasma panel does not cover anything.
6. After quitting: end leftover launcher processes, stop the bridge (unless in autostart),
   check the display mode.

The ☰ menu contains: *Sensors*, *Check setup*, *Help*, *Sign in again*.

Implemented in 0.2.0 for everyday use after setup:
- **Direct start:** the application menu entry *Zwift (Tretlager)* or the quick action *Start Zwift*
  (`tretlager --start`) opens the main window, starts right away and quits Tretlager after the
  ride. If setup is not complete, the assistant appears instead.
- **Warm up the bridge:** the sensor bridge already starts when the main window opens.
- **Update check in the background:** the main window shows a pending update before the click.
- **Out of the way:** during the ride Tretlager minimises itself and comes back afterwards.

## 6. Updates

| What | How | User sees |
|---|---|---|
| Zwift game | at start, through the official launcher | status line “Updating Zwift (1.125.0)” |
| Zwift launcher | likewise; then an automatic test whether the official sign-in works again | if so, a note “Official sign-in works again” |
| Wine | always the latest `winehq-devel` through system updates; Tretlager detects the new version at the next start and checks the GL path and Zwift start | on problems: “Zwift does not start since Wine 11.21” + diagnostics |
| Tretlager | Debian package through Discover | – |

After a failed update: **Back to the last working state** (reflink snapshot of the prefix),
instead of reinstalling Zwift.

## 7. When something goes wrong

- Every error message has three parts: what happened (one sentence), what the user can do
  (button), details to expand (log excerpt).
- **Repair** runs all steps again; finished steps are only checked.
- **Export diagnostic report** (text, without token and account data) for bug reports.
- Typical cases from the tests as fixed texts: graphics only Intel despite NVIDIA, distorted
  picture (resolution change), window under the panel, strap problems, network
  changes.

## 8. Interface on Plasma

TUXEDO OS forky runs Plasma. GTK4/libadwaita works there (see the bridge interface), but looks
like GNOME; custom icons are needed because Breeze uses different names. Recommendation: build
the assistant and the main window as a UI-free core (state machine, steps, progress over D-Bus
or a Python API) and implement the **Kirigami interface** for Plasma first, the GTK interface
afterwards. This matches E4 and the approach taken with Stafette.

## 9. Technical implementation of the flow

- **State:** `~/.local/state/tretlager/state.json` with the step, versions (Wine, launcher,
  game, WebView2), source and verification result of the installer, timestamps.
- **Locations:** prefix `~/.local/share/tretlager/prefix`, snapshots
  `~/.local/share/tretlager/snapshots/`, cache `~/.cache/tretlager/` (installer, winetricks).
- **Helper:** `/usr/libexec/tretlager/setup-system` + Polkit action; fixed steps, output
  line by line as JSON.
- **Version list:** shipped with the package, stating which combination of Wine, launcher and
  game is tested; Tretlager shows unknown combinations as “untested”.
- **Start logic:** move from `poc/token-login/start.sh` into the core (Python).

## 10. Decisions (mine, 2026-10-29)

- **E2 Sign-in:** browser sign-in is offered as an option with a warning.
- **Distribution:** a locally built Debian package for now; later a package repository on bender.
- **Interface first:** Kirigami.
- **Wine policy:** always the latest `winehq-devel`. Instead of pinning, Tretlager checks the GL
  path and start after a Wine update and reports breakage (section 6 accordingly: no pinning).
- **Name:** “Tretlager” remains the working title.
