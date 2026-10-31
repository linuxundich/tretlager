# Feasibility analysis (Phase A)

As of: 2026-10-29. Research only: web, source code, package archives. Nothing has been tested on
real hardware yet.

Labels:
- **[Q]** backed by a primary source (source code, official page, package archive)
- **[F]** only a forum or community report
- **[S]** my own conclusion

Rating per area: **officially supported** · **works** (reported several times) ·
**experimental** · **does not work**.

## Summary

| Area | Rating | Gist |
|---|---|---|
| Zwift client on Linux | **experimental** (not officially supported) | The Windows client runs under Wine 11.x with WebView2 and dotnet48; any launcher version can break that |
| Wine on Forky | **works only via WineHQ** | Debian's `wine` has not been in testing since 2026-03-24; WineHQ has a `forky` suite with 11.0 and 11.20, pure WoW64 without i386 |
| Getting the installer | **works** | public URL `https://cdn.zwift.com/app/ZwiftSetup.exe`, no sign-in required; Authenticode verification possible, signer not yet checked |
| Sign-in | **biggest product risk** | The WebView2 sign-in of launcher 1.2.0 does not render under Wine; netbrain works around it with a re-implemented OAuth login, which conflicts with principle 7 and Zwift's terms of service |
| Graphics / NVIDIA | **works** | ZwiftApp uses **OpenGL 3.1**, not Direct3D, so DXVK is unnecessary; NVIDIA needs Wine's EGL/GLX switch |
| BLE directly from Zwift | **does not work** | Wine 11.20: GATT reads yes, notifications and writes are stubs, no power stream, no ERG |
| BLE via own bridge (DIRCON) | **works** (Zwift side), bridge **experimental** | Zwift detects Wahoo “Direct Connect” devices on the LAN even under Wine; a BlueZ → DIRCON bridge carries FTMS including ERG, power and cadence |
| ANT+ in Wine | **does not work** | `winusb.dll` in Wine is almost entirely stubs; ANT+ could at most work natively in the bridge |
| Updates | **works** with caveats | Launcher `SilentLaunch` updates; the version file `Zwift_ver_cur.xml` has checksums |
| Companion app needed? | **no**, with the bridge | The bridge replaces Companion as the path for sensors |

**Conclusion:** The project is feasible, but not in the way the brief assumes.
1. The sensors do not reach Zwift directly through Wine. Without the Companion app, the only
   path is an own bridge that presents itself as a Wahoo Direct Connect device.
2. Wine comes from the WineHQ repo, not from Debian.
3. Whether an ordinary person can sign in without tricks is open and must be tested first.

## 1. Zwift on Linux

### 1.1 Platforms
- [Q] Supported are Windows 10 64-bit or newer, macOS 10.14.4 or later, Android, iOS/iPadOS and
  Apple TV. Windows on ARM is explicitly excluded. Linux, VMs and Wine are not mentioned.
  https://support.zwift.com/es/supported-devices-to-run-zwift-H1Cj9QbeB.md
- [Q] On Linux there are only old forum replies saying that no Linux client is planned.
  https://forums.zwift.com/t/no-linux-support-yet/14041

### 1.2 How the client is built
- [Q] `ZwiftSetup.exe` only installs `ZwiftLauncher.exe`. The launcher then downloads the actual
  game `ZwiftApp.exe` (CI log: “Updating Zwift from version none to 1.124.0”).
  https://github.com/netbrain/zwift/issues/420
- [Q] Sign-in runs through WebView2 (Edge engine) in the launcher.
- [Q] According to a comment in netbrain's `src/run_zwift.sh`, there are three problems under Wine:
  1. The launcher does not show the sign-in page.
  2. It does not start `ZwiftApp.exe`.
  3. If you start `ZwiftApp.exe` on its own, the game calls the launcher again.

  https://github.com/netbrain/zwift/blob/master/src/run_zwift.sh

### 1.3 Reference project netbrain/zwift (Unlicense)
This is the most common approach and runs as a Podman or Docker container. [Q] from the Dockerfile:
- Base Debian trixie, **WineHQ wine-devel 11.20** (since PR #422 of 2026-10-24, previously 9.9)
- winetricks pinned to a commit because of the not yet released verb `webview2`
- Verbs `corefonts dotnet48 d3dcompiler_47 webview2`, Mono and Gecko off
- winbind (`ntlm_auth`), **no DXVK**

Start, [Q] from `run_zwift.sh`:
1. `wine start ZwiftLauncher.exe SilentLaunch`
2. determine the launcher's PID
3. start `ZwiftApp.exe --token=<json>` via `runfromprocess-rs.exe` as a child process of the launcher
4. terminate the launcher and the crash handler

The token comes from `zwift-auth.sh` (see section 3).

For comparison: [Q] umu-launcher (Proton outside of Steam) has an entry `umu-zwift` with the same
winetricks list. There is no evidence that Proton solves the launcher problem.
https://github.com/Open-Wine-Components/umu-protonfixes/blob/master/gamefixes-umu/umu-zwift.py

### 1.4 Recent breakages that show the maintenance burden
- [Q] **Launcher 1.2.0** (October 2026) crashed immediately under Wine (`RoGetActivationFactory`).
  Workaround in netbrain PR #421: `wineserver -k` after installation. According to the same PR,
  the WebView2 content still does not render. Zwift enforces the update to 1.2.0.
  https://github.com/netbrain/zwift/issues/420
- [Q] With Zwift 1.117–1.122, disk cache errors (4390, `ERROR_NOT_A_REPARSE_POINT`) made the game
  freeze: https://github.com/netbrain/zwift/issues/402
- [S] Wine lags behind every launcher release. The app has to keep a matrix “tested launcher and
  Zwift version × Wine version” and show unknown combinations as untested.

## 2. Wine and packages on TUXEDO OS Forky

- [Q] `wine`, `wine64`, `libwine` and `winetricks` have **not been in testing since 2026-03-24**.
  Several RC bugs block them. `dxvk` has been missing since 2026-10-15, `wine-development` no
  longer exists at all since 2025.
  https://tracker.debian.org/pkg/wine · https://tracker.debian.org/pkg/winetricks
- [Q] **WineHQ** has a `forky` suite: `winehq-stable 11.0.0.0~forky-1`, `winehq-devel` and
  `winehq-staging` 11.20. On amd64, Wine 11 is a single package without an i386 dependency
  (new WoW64 mode). `dpkg --add-architecture i386` is therefore not needed.
  **Confirmed on tinytin (2026-10-29):** source with `Architectures: amd64` only, then
  `apt-get install --install-recommends winehq-devel` → 6 new packages (wine-devel, winehq-devel,
  libasound2-plugins, libodbc2, libodbccr2, plus osslsigncode), 289 MB download, 1.8 GB used,
  **no i386 package**, `wine --version` = wine-11.20.
  https://dl.winehq.org/wine-builds/debian/dists/forky/
- [Q] TUXEDO repo `deb.tuxedocomputers.com/debian`:
  - suite `forky` with `tuxedo-drivers`, `tuxedo-control-center` and `nvidia-driver-assistant`
  - suite `forky-nvidia` with pinning to NVIDIA **580**

  Debian's own NVIDIA 550 packages are due to be removed from testing on 2026-11-08. Which source
  actually delivers the 580 drivers has to be clarified on the target machine
  (`/etc/apt/sources.list.d`).
- [Q] **TUXEDO OS Forky ships Plasma 6.7, not GNOME.**
  https://linuxiac.com/tuxedo-os-debian-based-open-beta-is-now-available-for-testing/
  The brief says GNOME. → Decision E4.
- [Q] PackageKit 1.4.0 with a built-in apt backend is in forky. Plasma Discover depends on it,
  so it is preinstalled. `gi.repository.PackageKitGlib` can:
  - resolve packages
  - determine the list of changes with `SIMULATE`
  - install with a Polkit prompt

  It can **not** set up third-party sources including keys (WineHQ) or run `--add-architecture`.
  That requires a small dedicated pkexec helper with a fixed action.

## 3. Getting the installer and signing in

### 3.1 Installer
- [Q] `https://cdn.zwift.com/app/ZwiftSetup.exe` is public and reachable without signing in.
  HEAD on 2026-10-29: 200, 34,028,992 bytes, Last-Modified 2026-10-19. netbrain and Lutris have
  used the same URL since at least 2022. The content changes with every launcher release.
  → Path 1 from the brief (official download URL) is satisfied.
- [Q] Zwift does not publish a hash for the installer.
- [S] Authenticity can therefore only be checked via the **Authenticode signature**:
  - tool: `osslsigncode verify` (package 2.14 in forky)
  - with a separate CA file of the Microsoft code signing roots, because Debian's CA bundle does
    not include them
  - additionally pin the signer (subject)
  - **Test T1 of 2026-10-29:** installer with 34,028,992 bytes, SHA-256 `dd10bb62…333f9d`
    - Signature: Authenticode (PKCS#7, revision 2.0) with an **EV code signing certificate**
    - Signer: `CN=Zwift, Inc.`, `O=Zwift, Inc.`, Delaware, registration number `5463328`,
      Long Beach CA. Valid 2024-03-16 to **2027-03-16**.
    - Chain: SSL.com EV Code Signing Intermediate CA RSA R3 → SSL.com EV Root Certification
      Authority RSA R2. The root **is in the regular system CA store** (Mozilla), so a separate
      Microsoft CA file is not needed.
    - The Authenticode hash I computed myself (SHA-256 over the file without checksum and
      signature table) matches the one in the signature, so the file is signed unmodified.
    - `osslsigncode 2.14 verify -CAfile /etc/ssl/certs/ca-certificates.crt -TSA-CAfile …` on
      tinytin: signature ok, CRL ok (crls.ssl.com), “Succeeded”. Signed and timestamped on
      2026-10-15 23:21 UTC by the TSA SSL.com Timestamping Unit 2025 E1 (chain up to SSL.com
      Root Certification Authority RSA, also in the system CA store).
    - Counter-check: 1 byte was changed in a copy, `verify` reports “Failed”.
    - **T1 done.** The app can use `osslsigncode` (Debian package); the CRL lookup goes over
      HTTP to SSL.com and must be listed in the privacy overview (can be turned off with
      `-ignore-crl`).
    - Consequence for the app: do **not** pin the leaf certificate by fingerprint, it expires in
      2027. Instead verify the chain against the system CA store and additionally require the
      subject fields (CN, O, registration number) and the code signing EKU.
- [Q] For game updates there is `https://cdn.zwift.com/gameassets/Zwift_Updates_Root/Zwift_ver_cur.xml`
  with `sversion` (currently 1.124.0), `manifest_checksum` and `ver_cur_checksum`. This makes it
  possible to compare the installed version with the vendor's current state.

### 3.2 Sign-in – the critical point
- [Q] netbrain's `zwift-auth.sh` signs in with username and password. It poses as the launcher
  (`client_id=Game_Launcher`) and plays through the OAuth code flow against
  `secure.zwift.com`:
  1. parse the HTML form
  2. submit the password
  3. exchange the code for a token
  4. call `ZwiftApp.exe --token=…`
- [Q] Zwift's terms of service (as of 2026-06-02, §5) prohibit, among other things,
  circumventing authentication or security measures, using scripts and automated programs, and
  letting programs interact with the platform without permission.
  https://support.zwift.com/en_us/terms-of-service-HJt7VBYyH.md
- [S] The re-implemented login does not circumvent authentication, because users sign in with
  their own credentials. It is, however, an **undocumented private interface** and automated, so
  it violates principle 7 and §5 xi/xiii. **I am not building this path in.**
- [S] Starting via `runfromprocess` (passing the game off as a child of the launcher) is a grey
  area as well. It does not circumvent any protection measure, but it fakes the process lineage.
  It is only used if it is necessary, and then documented. → Decision E2.
- **Permissible path:** The official launcher shows its WebView2 sign-in, users sign in there
  themselves, and the launcher starts the game. netbrain noted on 2026-01-25
  “webview2 in zwift launcher works”; with launcher 1.2.0 it no longer renders. **Whether this
  works with Wine 11.20 and launcher 1.2.x on Forky is the first test in Phase D.** If it does not,
  the app can honestly only “install, but not start” Zwift.

## 4. Graphics and NVIDIA

- [Q] ZwiftApp requires **OpenGL 3.1**. Zwift's own error message reads “OpenGL 3.1 is
  required”. https://support.zwift.com/en_us/opengl-error-on-windows-Skpfw62fB.md
- [S] This makes **DXVK unnecessary for the game**. Wine passes OpenGL through to the host
  driver. `d3dcompiler_47` is probably only needed by WebView2. The “DXVK/Vulkan” checkpoint in the
  brief shrinks: Vulkan is not needed for the game, but possibly for WebView2 (GPU acceleration of
  the launcher); that needs testing.
- [Q] Since 10.17, Wine uses EGL for OpenGL. With the proprietary NVIDIA driver, netbrain needs
  either `__EGL_VENDOR_LIBRARY_FILENAMES=""` or the fallback to GLX (registry `UseEGL=N`, switch
  `WINE_DISABLE_EGL`). Native Wayland does not work on NVIDIA, XWayland does.
  https://github.com/netbrain/zwift/issues/404
- [S] The diagnostics therefore have to distinguish:
  1. card present: sysfs `/sys/class/drm/*/device/vendor` = `0x10de`
  2. driver loaded: `/sys/module/nvidia/version`
  3. OpenGL actually accelerated: renderer string via EGL/GLX, not llvmpipe
  4. 32-bit: not applicable with WoW64 (to be confirmed)
- [Q] Machine-readable sources:
  - `nvidia-smi --query-gpu=… --format=csv,noheader`
  - `vulkaninfo --json` or `vkEnumeratePhysicalDevices` directly
  - for OpenGL, preferably a small dedicated EGL test instead of parsing `eglinfo`
- Secure Boot and DKMS: the app does not change anything there. It only reports when the module
  is not loaded and Secure Boot is active (`mokutil --sb-state`), and points to TUXEDO's procedure.

## 5. Sensors: BLE and ANT+

### 5.1 Direct BLE access from Wine – does not work
- [Q] Wine 11.0 (January 2026): `winebth.sys` via the BlueZ D-Bus. Scanning, pairing and first
  GATT services are visible through the Win32 BLE API.
  https://raw.githubusercontent.com/wine-mirror/wine/wine-11.0/ANNOUNCE.md
- [Q] State of Wine 11.20 (master):
  - Win32 present: `BluetoothGATTGetServices`, `GetCharacteristics`, `GetCharacteristicValue`
  - Win32 still stubs: `BluetoothGATTRegisterEvent` (notifications),
    `BluetoothGATTSetCharacteristicValue` (writes) and `BluetoothGATTSetDescriptorValue`
    (CCCD)
  - WinRT: `GetCharacteristics` and the advertisement watcher return `E_NOTIMPL`

  https://github.com/wine-mirror/wine/blob/master/dlls/bluetoothapis/bluetoothapis.spec
- [S] Without notifications, no power or heart rate values flow; without writes, there is no
  ERG. Which API Zwift uses (probably WinRT) is not proven, but it makes no difference: both paths
  are incomplete.
- [F] No report of Zwift seeing BLE sensors directly under Wine. A Debian 13 user in
  February 2026: “not properly identifying BLE Equipment”.
  https://forums.zwift.com/t/how-to-zwift-on-debian-linux/591025
- Consequence according to the brief (section 8): direct access is demonstrably impossible, so a
  bridge has to be evaluated. The app's diagnostics show this with a test of their own (Wine
  version plus stub list) instead of just claiming it.

### 5.2 Bridge via Wahoo Direct Connect (DIRCON) – the viable path
- [Q/F] Zwift officially supports trainers with “Direct Connect” (Wahoo DIRCON). This is GATT
  over TCP on the LAN, announced via mDNS `_wahoo-fitness-tnp._tcp`.
- [F] This also works under Wine:
  - Kickr V5/V6 on Debian 11 with Wine 7.18 (2022)
  - in February 2026 on Debian 13 in the netbrain container
  - in July 2025 with host networking

  https://forums.zwift.com/t/how-to-zwift-on-debian-linux/591025
- [Q] Wine's `dnsapi` mDNS functions are stubs. [S] So Zwift discovers with its own multicast
  code; multicast must reach the game. With native Wine without a container, that is the case.
- [Q] Wahoo does not publish a protocol specification. The best reference is qdomyos-zwift
  (GPL-3.0, active), `src/devices/dircon/`:
  - 6-byte header
  - messages for discovering services and characteristics, reading, writing, enabling
    notifications, and unsolicited notifications
  - qdomyos provides FTMS (0x1826) with control point 0x2AD9, i.e. **ERG**, plus Cycling
    Power (0x1818), CSC (0x1816) and heart rate (0x180D) as a separate mDNS instance.

  https://github.com/cagnulein/qdomyos-zwift/tree/master/src/devices/dircon
- Legal assessment [S]:
  - DIRCON is a connection type offered by Zwift. The bridge behaves like a Wahoo device.
  - It does not touch any Zwift binary, any sign-in or any server interface.
  - The protocol is known through interoperability analysis, not documented.
  - It therefore meets the conditions from section 8 except for “documented interface”, which it
    meets only partially.
  - Code from qdomyos (GPL-3) may be reused if the project becomes GPL-3.
- Open questions that can only be answered with hardware:
  1. **Does Zwift accept heart rate via a DIRCON instance?** Real Kickrs do not provide heart
     rate, which is why previous users needed Companion for it.
  2. Does Zwift find a DIRCON instance on **the same machine** (mDNS loopback)?
  3. Stability and latency of ERG over the chain BLE → bridge → TCP → Wine.
  4. Concurrent access: the bridge holds the BLE connection exclusively; Zwift sees the trainer
     only through the bridge.

### 5.3 ANT+
- [Q] Apart from `WinUsb_Free`, Wine's `winusb.dll` has only stubs (unchanged since 2022). The
  Windows drivers of the ANT sticks (libusb-win32, SiLabs, WHQL) do not load in Wine.
  https://github.com/wine-mirror/wine/blob/master/dlls/winusb/winusb.spec
- [F] There is not a single success report. Users fall back to a VM with USB passthrough.
- [S] **ANT+ in Wine: does not work.** A possible later option: the bridge reads ANT+ natively on
  Linux (libusb, e.g. the Python library `openant`) and passes the values on via DIRCON.
  Only after BLE.

## 6. Updates

- [Q] netbrain compares the local `Zwift_ver_cur.xml` with the one from the CDN. If it differs, it
  starts the launcher with `SilentLaunch` and waits up to 5 minutes for the new version.
- [S] This uses the official update path and is permissible. The app adopts the principle:
  - record the version before and after
  - check free space
  - before the update, offer a Btrfs or copy snapshot of the Wine prefix. TUXEDO OS creates
    snapshots via Snapper anyway, but only of the system, not of `~`.
- Runtime updates (Wine from WineHQ) go through APT and thus through the system updates. The app
  only shows whether the installed Wine version is in the tested matrix and warns about an
  untested jump.

## 7. What changes compared to the brief

| Assumption in the brief | Finding | Consequence |
|---|---|---|
| Prefer Debian packages | Wine is missing in forky | WineHQ source with explicit consent (E1) |
| Check DXVK, 32-bit libraries | OpenGL game, WoW64 | largely not applicable; focus diagnostics on OpenGL/EGL |
| Direct BLE connection from Zwift | Wine GATT incomplete | DIRCON bridge as a separate user service (E3) |
| ANT+ optional | impossible in Wine | “not supported”; later natively in the bridge |
| GNOME/Wayland | Forky default is Plasma | clarify target machine (E4) |
| Sign-in via the official path | WebView2 may not render | first test; no re-implemented login (E2) |

## 8. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Launcher sign-in does not render under Wine | high | Start impossible without a grey-area trick | Test T2 first; try WebView2 variants and Wine versions; report honestly |
| R2 | Zwift update breaks Wine compatibility | high (regularly) | Start fails | Version matrix, prefix snapshot before update, restore |
| R3 | Zwift does not accept heart rate via DIRCON | medium | No heart rate strap | Test T6; otherwise mark heart rate as “not supported” |
| R4 | DIRCON on the same host is not found | medium | Bridge useless | Test T5; fallback: bridge on its own IP (network namespace, Raspberry Pi) |
| R5 | WineHQ source changes keys or packages | low | Installation fails | Pin the key fingerprint, explain errors |
| R6 | NVIDIA EGL problems | medium | Black screen/crash | Test the EGL/GLX switch automatically |
| R7 | Zwift changes its terms or blocks Wine | low | Project ends | Build in no circumvention, so there is nothing to block |

## 9. Feasibility tests for Phase D (before the installation logic)

| Test | Where | Question |
|---|---|---|
| T1 ✔ | any | Authenticode of `ZwiftSetup.exe`: signer, chain, timestamp |
| T2 ◐ | Forky + NVIDIA | WineHQ 11.20 + winetricks webview2: does the sign-in render in launcher 1.2.x? Does it start the game itself? |
| T3 ✔ | Forky + NVIDIA | OpenGL renderer in Wine = NVIDIA? EGL or GLX needed? fps in Watopia |
| T4 | Forky VM | Prefix setup idempotent, abort/resume |
| T5 | Forky + BLE | Bridge prototype (FTMS) on the same host: does Zwift find the device? |
| T6 | Forky + trainer + strap | Power, cadence, ERG, gradient simulation, heart rate via DIRCON |
| T7 | Forky | Update via `SilentLaunch`, then version from `Zwift_ver_cur.xml` |

T2, T3, T5 and T6 need the target machine with NVIDIA, a BLE adapter and real devices.
smokki only has Intel graphics; the VM `tuxedo-os-forky` has no NVIDIA card.

### Target machine tinytin (`testt@tinytin`, checked read-only on 2026-10-29)

| Item | Finding |
|---|---|
| System | TUXEDO OS (Debian base), `VERSION_CODENAME=forky`, kernel 7.2.7.1-tuxedo |
| Desktop | **KDE Plasma 6.7.4, Wayland**; libadwaita 1.10 is installed, GNOME is not |
| Graphics | **Hybrid:** Intel Iris Xe (Alder Lake-P) + NVIDIA GeForce RTX 3050 Ti Laptop, 4 GB |
| NVIDIA driver | 580.178.04 loaded; `nvidia-driver-libs 580.178.04-1tux1` from `txos.tuxedocomputers.com/debian` (595 and 610 there as well), runtime D3 on |
| GL/Vulkan | EGL vendors nvidia + mesa, Vulkan ICDs nvidia + intel |
| Secure Boot | off |
| Bluetooth | Intel AX201, adapter `tinytin` with BlueZ 5.87 |
| ANT+ | no stick |
| Wine | not installed; i386 is already active as a foreign architecture |
| PackageKit | 1.4.0 installed |
| Space/RAM | 920 GB free, 31 GB RAM |

Devices: **Wahoo KICKR V4** (smart trainer) and **Garmin HRM-Pro Plus** (heart rate strap, BLE and
ANT+), connected via the built-in AX201.

Consequences for the devices [S], to be checked on the hardware before T5:
- A KICKR V4 has no built-in Direct Connect (that came with later models). The bridge is
  therefore the way to go anyway; there is no real DIRCON device for comparison.
- The V4 offers FTMS with a control point (checked, see T5 preparation below).
- The HRM-Pro Plus allows several BLE connections at the same time. So the bridge can hold it
  while a watch is also connected.

Consequences for the machine:
- On the hybrid notebook, the Plasma session runs on the Intel GPU. Zwift has to use
  **PRIME offload** to the NVIDIA card: `__NV_PRIME_RENDER_OFFLOAD=1` and
  `__GLX_VENDOR_LIBRARY_NAME=nvidia` for GLX, or `__EGL_VENDOR_LIBRARY_FILENAMES` with
  `10_nvidia.json` for EGL.
- The graphics diagnostics must therefore report *which* GPU actually gets Wine's OpenGL context.
  “NVIDIA driver loaded” is not enough. This is part of T3.
- The UI runs under Plasma; libadwaita works there but looks like GNOME (E4).

## 10. Licenses of third-party components

| Component | License | Use |
|---|---|---|
| Wine (WineHQ) | LGPL-2.1+ | runtime, system package |
| winetricks | LGPL-2.1+ | once, for setup (WebView2, dotnet48, corefonts) |
| WebView2, .NET 4.8, Core Fonts | Microsoft EULA | downloaded by winetricks from the vendor, not bundled |
| netbrain/zwift | Unlicense | reference only |
| qdomyos-zwift | GPL-3.0 | protocol reference; reuse only under GPL-3 |
| bleak | MIT | BLE in the bridge (python3-bleak 3.0.2 in forky) |
| Zwift | proprietary | only downloaded via the official path and never modified |

## 11. Results of the feasibility tests

### T2 (part 1), tinytin, 2026-10-29

Setup:
- WineHQ `wine-devel 11.20~forky-1`, amd64 only (WoW64)
- Prefix `~/.local/share/tretlager/prefix-t2`, without Mono and Gecko
- winetricks `20260125-next` (commit f3890f6) with `corefonts dotnet48 d3dcompiler_47 webview2`.
  The package **`cabextract`**, which winetricks requires, was also needed.
- Scripts in `~/tretlager-t2/` on tinytin, each as its own `systemd-run --user` unit

| Step | Result |
|---|---|
| Prefix + winetricks | ok, **297 s** |
| `ZwiftSetup.exe /SP- /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /NOCANCEL` | ok, rc 0 |
| `ZwiftLauncher.exe SilentLaunch` (without sign-in) | downloads the game: **Zwift 1.124.0 (167761)**, 4.9 GB, in about 1–2 min; the launcher then stays idle in the background |
| Version file | `Zwift_ver_cur.xml` is renamed to `Zwift_ver_cur.<build>.xml`, the name is stored in `Zwift_ver_cur_filename.txt` (UTF-16/NUL) |
| WebView2 runtime | **109.0.1518.140**, the last Win7 version; winetricks sets `msedgewebview2.exe` to Win7 (Wine bug 58921) |
| Starting the launcher normally (sign-in) | **fails.** Log: “EnsureCoreWebView2Async” → “Main Window Visible: True” → process exits after about 20 s with rc 0. No window and no WebView2 data folder appear. Same with `--no-sandbox --disable-gpu` |

Confirmed in the binary:
- `BleWin10Lib.dll` uses **WinRT BLE** (`BluetoothLEAdvertisementWatcher`,
  `GattDeviceServicesResult`, `GattReadClientCharacteristicConfigurationDescriptorResult`).
  These are exactly the parts that return `E_NOTIMPL` in Wine.
- `ZwiftApp.exe` contains `_wahoo-fitness-tnp._tcp.local.` (DIRCON) and
  `_zwift-protocol._tcp.local.`.
- Next to it are `ANT_DLL.dll` and a “Windows ANT Dongle Driver”.

Interim status: installing and updating work without signing in via the official path. **The
official sign-in in the launcher does not work with this combination.** This matches netbrain
(#420/#421).

Next variants for T2:
1. newer WebView2 runtime (Fixed Version) in Win10 mode
2. `wine-staging` 11.20
3. umu-launcher + Proton/GE-Proton, which ships its own WebView2 fixes
4. Wine trace (`+loaddll,+combase`) to find the cause

### T2 (part 2): newer WebView2, tinytin, 2026-10-29

Wine bug 58921: from Windows 8.1 on, WebView2 uses DirectComposition. Vanilla Wine returns
`DCompositionCreateDevice` → `E_NOTIMPL` (as of 11.18), hence the forced Win7 mode in winetricks.
wine-staging has a DComp patch set with which similar WebView2 apps render again.
https://bugs.winehq.org/show_bug.cgi?id=58921

| Attempt (clone `prefix-t2b`, via Btrfs reflink in 0.4 s) | Result |
|---|---|
| Win7 override removed, bootstrapper again | installs 109 again |
| 109 removed, Evergreen standalone x64 (215 MB, signed “Microsoft Corporation”) | EdgeUpdate aborts with `0x80040902`, 109 stays |
| Fixed Version CAB **156.0.4314.50 x64** (official CDN, cabextract), `WEBVIEW2_BROWSER_EXECUTABLE_FOLDER`, Win10, wine-devel 11.20 | Launcher exits silently after ~20 s as before, rc 0 |

Trace (`+seh,+loaddll,+process`):
- `WebView2Loader.dll` and `EmbeddedBrowserWebView.dll` from 156 are loaded.
- **No `msedgewebview2.exe` is ever started.**
- There are several .NET exceptions (`e0434352`), after which the launcher exits without a log
  line of its own.

Consequence: the age of the runtime is not the cause. Under vanilla Wine 11.20, WebView2 never
even gets to the browser process.

Side finding: Microsoft's code signing roots are not in the system CA store. If the app verifies
WebView2 downloads itself, it needs its own Microsoft CA file; for Zwift the system store is
sufficient.

Next step: the same test with `wine-staging` 11.20 (`/opt/wine-staging`, installable alongside
wine-devel).

### T2 (part 3): wine-staging, tinytin, 2026-10-29

- `wine-staging 11.20` from WineHQ, into `/opt/wine-staging`, alongside wine-devel.
- First start in the clone: Staging updates the prefix (`wine.inf`). In the process a dialog
  “rundll32 … This application could not be started” hangs until someone at the screen clicks
  *No*. The app must therefore always run the prefix with the same Wine version or trigger the
  update itself unattended.
- Launcher with WebView2 156 (Fixed Version, Win10): **same picture as with vanilla.**
  “EnsureCoreWebView2Async”, then no `msedgewebview2.exe`, exit after ~20 s with rc 0.

Status at netbrain (#420/#421, 2026-10-23): the crash of launcher 1.2 is worked around, “the
webview2 content in the launcher still does not render”. Nobody reports a working launcher
sign-in with 1.2 under Wine.

**Interim result T2:** the official sign-in is currently not possible with launcher 1.2 under
Wine 11.20: vanilla and Staging, WebView2 109 and 156 tested. Installing and updating work.

Possible next steps:
1. Proton via umu-launcher in the home directory (no root, Valve's/GE's own WebView2 fixes)
2. test WebView2 separately from the launcher (Microsoft sample app) to separate the launcher
   problem from the Wine problem; possibly a bug report to Wine
3. re-implemented token login (netbrain): technically proven, but a terms-of-service risk → only
   on an explicit decision (E2)
4. wait: the app installs and updates, and honestly reports starting as “currently not possible”

### T2 (part 4): Proton via umu-launcher, tinytin, 2026-10-29

- umu-launcher **1.4.4** as a zipapp (SHA-256 from the release verified) and **GE-Proton11-11**
  (SHA-512 verified, based on Wine 11.0 Staging). Both live in
  `~/.local/share/tretlager/runtimes/`, without root.
- `GAMEID=umu-zwift`: the protonfix installs `corefonts dotnet48 d3dcompiler_47 webview2` itself,
  with winetricks 20260125-next. Prefix plus setup take **250 s**, plus the download of the Steam
  Runtime the first time.
- The game was taken over from `prefix-t2` via reflink; nothing was downloaded again.
- Launcher under Proton with WebView2 109/Win7: **exits silently after ~20 s, rc 0**, no
  WebView2 data folder.
- With WebView2 156 Fixed Version and Win10: the same.

**Overall result T2 (six combinations):**

| Runtime | WebView2 109 (Win7) | WebView2 156 (Win10) |
|---|---|---|
| WineHQ wine-devel 11.20 | ✗ | ✗ |
| WineHQ wine-staging 11.20 | – | ✗ |
| GE-Proton11-11 (umu) | ✗ | ✗ |

In none of the combinations does launcher 1.2 start a WebView2 browser process; it exits without
an error message. **The official sign-in is currently not possible under Wine.**
Installing and updating work in all runtimes.

### T2 (part 5): WebView2 separately from the launcher, tinytin, 2026-10-29

Test apps in `poc/wv2test/` (C#, compiled with `csc.exe` from .NET 4.8 in the prefix, NuGet
`Microsoft.Web.WebView2` 1.0.4314.35), wine-devel 11.20, WebView2 109:

| Test | Result |
|---|---|
| WinForms `WebView2` | init OK, browser process running, `example.com` loaded and **visibly rendered** |
| WPF `WebView2` (HWND-based) | init OK, navigation OK |
| WPF **`WebView2CompositionControl`** | crash: `TypeLoadException: Could not find Windows Runtime type 'Windows.UI.Composition.ContainerVisual'` in `TryInitializeD3DImage()` |

`ZwiftLauncher.exe` is a WPF app (.NET Framework 4.7.2) and contains
`WebView2CompositionControl`. There is no switch in `ZwiftLauncher.exe.config`; the launcher
tries twice (“deleting user data and retrying”) and then gives up.

**Cause of T2:** from launcher 1.2 on, Zwift draws the sign-in page with the
`WebView2CompositionControl`. That needs the WinRT API `Windows.UI.Composition`, which Wine
(vanilla, Staging, Proton) does not have. WebView2 itself runs under Wine. This fits the earlier
reports “webview2 in zwift launcher works” (January 2026, older launcher).

Consequences:
- A solution via the official sign-in would need either `Windows.UI.Composition` in Wine (large;
  a bug report with this minimal example is worthwhile) or Zwift returning to, or falling back
  on, the classic control (feedback to Zwift possible).
- Tretlager does not build a launcher patch (principle: Zwift files stay unmodified).

### T2b: opt-in token login, T3: graphics, tinytin, 2026-10-29

**Zwift runs on tinytin.** Path (`poc/token-login/`):
1. Sign-in in the system browser on `secure.zwift.com` with `client_id=Game_Launcher`. I sign
   in myself; the script never sees the password.
2. The browser lands on `launcher.zwift.com/launcher?state=…&code=…` and shows “Bad Request”.
   The address is copied into the terminal; the code is only valid briefly.
3. Exchange the code for a token (`/openid-connect/token`). The token is stored in
   `$XDG_RUNTIME_DIR` and deleted after the start.
4. `ZwiftLauncher.exe SilentLaunch`, then `ZwiftApp.exe --token=…` as a **child of the launcher**
   via a custom `RunFromProcess.exe` (C#, `PROC_THREAD_ATTRIBUTE_PARENT_PROCESS`, built with
   csc.exe in the prefix). Then terminate the launcher and the crash handler.

Without the right parent process, `ZwiftApp.exe` restarts the launcher. That then crashes
(`AccessViolationException` in `ZwiftPatcher.patcher_CheckExperimentation`).

Assessment: this path uses the undocumented launcher sign-in and fakes the parent process
(terms of service §5, principle 7). It is a **test for my own account on my explicit
decision**, not an agreed part of the app (E2 remains open).

**T3 graphics** (`poc/gltest/GLTest.cs`, same WGL path as GLFW in Zwift):

| Variant | Result |
|---|---|
| Wine default (EGL) | Intel Iris Xe, OpenGL 4.6 Mesa 26.1.6 |
| EGL + `__EGL_VENDOR_LIBRARY_FILENAMES=10_nvidia.json` + offload | **no pixel format** → Zwift “OpenGL 3.1 required” |
| EGL, vendor empty (netbrain) | Intel |
| GLX (`HKCU\Software\Wine\X11 Driver\UseEGL=N`) | Intel |
| **GLX + `__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia`** | **NVIDIA RTX 3050 Ti, OpenGL 4.6.0, 580.178.04** |

In the game: `ZwiftApp.exe` with 3.3 GB VRAM and 58 % SM load on the NVIDIA card; the log says
“GPU … NVIDIA GeForce RTX 3050 Ti Laptop GPU”. So on hybrid machines the app has to set GLX and
PRIME offload and prove it with this GL test.

**Sensors in the game:** `BLE_LOAD_FAIL; library="BleWin10Lib_fallback.dll", windowsBuild=19045`
→ “Native BLE unavailable, deferring scan” → “Starting ANT+ scan”. As expected, Zwift finds no
Bluetooth. Next up is T5 (bridge).

Side findings:
- Zwift writes Sentry crash reports (`AppData/Local/Zwift/.sentry`). This belongs in the privacy
  overview; it comes from Zwift, not from Tretlager.
- On the first start, world data is missing (“Watopia not found”). The game ran anyway; whether
  it downloads the data later still needs checking.

### Window and resolution, tinytin, 2026-10-29

- In fullscreen, Zwift **switched the panel's mode** via Wine/XRandR (2880×1800 →
  2560×1600). Together with Plasma's X11 scaling (1.6), the picture was distorted. Fix in the
  prefix: `HKCU\Software\Wine\X11 Driver\UseXRandR=N`. The mode can be reset with
  `kscreen-doctor output.eDP-1.mode.1`.
- After that the picture was fine, but the window (2872×1766 at y=44) was under the Plasma
  panel, and the lower buttons were hidden. Double-clicking the title bar (KWin maximizes) fixes
  this. The app has to start Zwift maximized or in fullscreen.
- A sharp picture under Plasma with scaling requires *Legacy Applications (X11) → Apply scaling
  themselves*. That is a desktop setting; the app only points it out.

### T5 preparation: GATT inventory of the test devices, tinytin, 2026-10-29

BlueZ 5.87 without root (`bluetoothctl`, `busctl`). Connected briefly, read out, disconnected.

**Wahoo KICKR V4** (`Wahoo KICKR C058`, advertises 0x1818 and 0x1826):

| Service | Characteristic | Properties |
|---|---|---|
| FTMS 0x1826 | 0x2ACC Fitness Machine Feature | read |
| | 0x2AD2 Indoor Bike Data | notify |
| | 0x2AD3 Training Status | read, notify |
| | 0x2AD6 Supported Resistance Level Range | read |
| | 0x2AD8 Supported Power Range | read |
| | **0x2AD9 Fitness Machine Control Point** | write, indicate |
| | 0x2ADA Fitness Machine Status | notify |
| Cycling Power 0x1818 | 0x2A63 Measurement | notify |
| | 0x2A65 Feature, 0x2A5D Sensor Location | read |
| | 0x2A66 Control Point | write, indicate |
| | `A026E005` Wahoo ERG extension | write, indicate |
| User Data 0x181C | 0x2A98 Weight | read, write |
| Wahoo proprietary `EE01/EE03/EE06/EE0B` | `A026E002/04/0A/23/37` | notify, write-without-response |

So the V4 supports **FTMS with a control point**. ERG and gradient simulation work via the
standard and do not need Wahoo's proprietary extension.

**Garmin HRM-Pro Plus** (`HRMPro+:462237`): Heart Rate 0x180D (0x2A37 notify, 0x2A38 read),
Battery 0x180F, Running Speed and Cadence 0x1814, Garmin proprietary `2401`. It accepts several
connections (connected after a fresh scan).

Consequence for the bridge: it must pass through the characteristics for FTMS, Cycling Power and
Heart Rate 1:1 via DIRCON, including the control point's indications. Zwift does not need Wahoo's
proprietary services via FTMS (to be checked whether Zwift prefers them when they are visible).

### T5/T6: bridge with real devices, tinytin, 2026-10-29

Bridge (`tretlager/bridge`) and UI (`tretlager/ui`) as a user installation
(`build-aux/install-user.sh`), service `tretlager-bridge.service`.

| Device | Result |
|---|---|
| Wahoo KICKR V4 | stable connection, FTMS and Cycling Power mirrored, mDNS “Wahoo KICKR FE2E” on 36866, live values in the UI |
| Wahoo TICKR (`DC:1E:D3:39:2C:8D`) | connects, occasional drops with reconnection; **values too high** (88–133 instead of 54–66 according to the watch) |
| Garmin HRM-Pro Plus | on tinytin **no service discovery** (connected, `ServicesResolved` never comes), afterwards the strap stops advertising until it is put on again |

Findings:
- **TICKR:** the raw data (0x2A37) shows that the strap itself counts wrong. Besides plausible
  RR intervals of 0.7–1.0 s, values of 0.17–0.31 s keep appearing; often one beat is split in two
  (0.48 + 0.21 s). This points to a disturbed signal (electrode contact, fit, a second strap). The
  bridge passes the bytes through unchanged; its decoder is correct.
- **HRM-Pro Plus:** from smokki (AX200, firmware 193-33.24, Arch kernel 7.2.11) it is connected
  and resolved in 3 s (31 GATT objects). On tinytin (AX201 `ibt-0040-4150`, firmware 202-5.26
  from May 2026, kernel 7.2.7.1-tuxedo) service discovery hangs, also without the bridge, after a
  reset of the adapter and with the BlueZ cache cleared. The kernel log repeatedly shows
  `Bluetooth: hci0: ACL packet for unknown connection handle`. Assumption: the strap cannot cope
  with negotiating LE 2M or larger data packets after connecting. Counter-check: limit
  `btmgmt phy` to LE 1M (needs root).
- **Bridge bugs fixed along the way:** BlueZ only connects or scans one thing at a time per
  adapter (“Operation already in progress”) → shared lock. An aborted connection has to be
  disconnected, otherwise the device stops advertising. Failing devices are retried with a
  growing pause (up to 60 s).

### T5/T6: Zwift via the bridge, tinytin, 2026-10-29 evening — works

- Zwift finds the bridge devices via mDNS (`[WFTNP] CreateWFTNPDevice for "Wahoo HRM 2C8D"`,
  `found service UUID 0x180D`) and connects via TCP to the bridge **on the same machine**. This
  rules out risks R4 (same host) and R3 (heart rate via DIRCON).
- Paired and confirmed: **power source = Wahoo KICKR FE2E**, **heart rate = Wahoo HRM 2C8D**
  (TICKR), cadence via the KICKR. Me on the trainer: watts and cadence realistic.
- Bridge recording (5 s grid): while pedalling 40–51 W, 39–44 rpm, 10–13 km/h, 0 during the
  pauses; heart rate 73–96 bpm; both devices connected throughout, one Zwift client each.
- Network change (cable → Wi-Fi): Zwift's TCP connections were stuck on the address that had
  disappeared and piled up; Zwift lost the devices. Fixed: the bridge closes connections whose
  local address is gone (checked every 3 s); Zwift then reconnects via the new address.
- Still open: controllable trainer (gradient, ERG via FTMS control point 0x2AD9), longer ride,
  behaviour without any network connection.

### T6: gradient and ERG via the bridge, tinytin, 2026-10-29 21:05–21:15 — works

- Bug before: Zwift waited for the FTMS control point's response and kept resetting the trainer
  (`[FTMS] Request took too long, resetting trainer`). Cause: in the DIRCON write response, the
  bridge only sent an echo of the command. Zwift expects the device's response there
  (`0x80, opcode, result`), as qdomyos-zwift provides it. Fixed: the bridge waits up to 3 s for
  the KICKR's indication and returns it in the write response; notifications go to all DIRCON
  clients (qdomyos default).
- Ride (me): rides, gradient and ERG mode felt right.
- Control point in 15 min: `80 11 01` (gradient simulation) 75×, `80 05 01` (ERG target power)
  3×, plus `80 00 01` (request control), `80 01 01` (reset), `80 07 01` (start); no missing
  response, no more “took too long” after the fix.
- Heart rate dropped out once: when the network cable was replugged, Zwift's connection to the
  cable address broke off (`Error connecting … 192.168.0.55:36867 [995]`); Zwift reconnected
  after a few seconds. The TICKR itself stayed connected via Bluetooth. With two addresses, Zwift
  binds devices to different addresses (trainer via Wi-Fi, strap via cable).
- **Fixed (21:25):** by default the bridge now advertises its devices under 127.0.0.1 (avahi
  `AddAddress` for `tretlager-<port>.local` with `NO_REVERSE`, service with this host) and only
  listens on loopback. Zwift under Wine connects through it (`127.0.0.1:36866/36867`).
  Cable/Wi-Fi changes no longer affect the Zwift–bridge connection, and the trainer cannot be
  controlled from the LAN. For Zwift on other devices there is `"local_only": false` in
  `~/.config/tretlager/bridge.json` (no switch in the UI yet).

### M3: setup by the core, tinytin, 2026-10-29 late — works

`tretlager/core/setup.py` with a fresh prefix `~/.local/share/tretlager/prefix`, unattended:

| Step | Duration |
|---|---|
| Download installer, verify signature (osslsigncode, signer Zwift, Inc. / 5463328) | ~1 s |
| Wine environment (`wineboot -u`, Mono/Gecko off) | 15 s |
| winetricks (commit f3890f6, SHA-256 verified): corefonts, dotnet48, d3dcompiler_47, webview2 | 281 s |
| Launcher (`/VERYSILENT`, then `wineserver -k`) | 15 s |
| Game via `SilentLaunch` (Zwift 1.124.0) | 127 s |
| Graphics: `UseEGL=N`, `UseXRandR=N`, GL test → NVIDIA RTX 3050 Ti, OpenGL 4.6.0 | 20 s |
| **total** | **459 s** |

Second run: all steps recognised as done, 2 s. Bug found while writing it:
`WINEDLLOVERRIDES=mscoree,mshtml=` may only apply to `wineboot`, otherwise .NET (winetricks,
`csc.exe`) is disabled.

### M4: sign-in in the assistant, tinytin, 2026-10-29 late — works

- Page *Sign-in*: the official sign-in is explained as “currently not possible”; browser sign-in
  only after ticking “at your own risk” (terms of service §5). Tretlager opens the Zwift page in
  the default browser; after the redirect address is copied, it picks up the code from the
  clipboard by itself (my verdict: “worked”).
- Token in the Secret Service (Plasma: ksecretd via `python3-secretstorage`), not in files.
- Renewal via `grant_type=refresh_token` verified: afterwards 359 min of access, 7 days of
  renewal.

### M5: start from the main window, tinytin, 2026-10-29 night — works

- First attempt: Zwift started, but the start call ran into a timeout (Zwift inherited the output
  pipe). Python's error message with the token in the command line ended up in the UI's log.
  Log deleted, session at Zwift ended (renewal rejected afterwards), cause fixed: token via a
  0600 file on tmpfs, `RunFromProcess` reads `--token=@file`, no pipes, no tracebacks with
  command lines.
- In addition, Zwift switched the resolution to 2560×1600 despite `UseXRandR=N`; additionally
  setting `UseXVidMode=N` fixes this (set on every start).
- Second attempt after signing in again: only `ZwiftApp.exe` running, resolution 2880×1800,
  window 2880×1686 from y=44 (KWin script), `nvidia-smi pmon`: ZwiftApp.exe type G, 66 % SM,
  3.4 GB; no token in the log, hand-over file deleted; in Zwift all four sensor tiles connected.
