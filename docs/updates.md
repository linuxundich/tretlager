# Updates – Zwift and everything Tretlager brings along

As of 2026-10-30. Principle: **no snapshots** (not every computer has Btrfs, and a full copy of the
Zwift environment costs 7–9 GB). Instead, every dependency has exactly one update path, and before
every start Tretlager checks whether the Zwift environment matches the installed Tretlager. Rolling
back happens via Flatpak, not via copies.

## Components and their update path

| Component | Source | How it gets updated | What Tretlager does afterwards |
|---|---|---|---|
| Tretlager (Python, QML, bridge) | own Flatpak | `flatpak update` or Discover/GNOME Software from my own repository (F4, bender, GPG) | restarts a running bridge of an older version (`restart_if_outdated`, not during a ride) |
| Wine 11.x | in the Flatpak, built from source | only with a new Tretlager version (version in the manifest) | reconciliation before the start: `wineboot -u`, repeat the graphics test |
| cabextract, osslsigncode, bleak, dbus-fast, SecretStorage | in the Flatpak, pinned version + checksum | only with a new Tretlager version | – |
| KDE runtime 6.11, PySide BaseApp 6.11 | Flathub | `flatpak update` (bug fixes within 6.11); switch to 6.12 only with a new Tretlager version | – |
| NVIDIA driver in the sandbox (`GL.nvidia-…`) | Flathub | Flatpak installs the extension matching the system driver by itself | – |
| winetricks | GitHub, pinned commit + SHA-256 in the code | only with a new Tretlager version | – |
| Windows components (.NET 4.8, WebView2, fonts, d3dcompiler_47) | Microsoft and others via winetricks | new or different components only with a new Tretlager version (`VERBS`) | reconciliation installs missing components |
| Zwift launcher and game | Zwift | Zwift itself: before every ride, Tretlager starts the launcher invisibly (`SilentLaunch`) if `Zwift_ver_cur.xml` reports a newer version | shows the progress (see below), waits up to 15 min until the version is on disk, then starts |
| Zwift session (token) | Zwift | Tretlager renews it by itself (6 h access, 8 days refresh) | otherwise sign-in |

So Wine and everything else in the Flatpak is **never** updated behind Tretlager's back. A new Wine
version only comes with a Tretlager version that has been tested with it. This replaces the earlier
rule E10 (“always the latest winehq-devel”), which applied to the Debian package.

## Before every start: reconcile the setup

`Launcher.reconcile()` runs all setup steps from `core/setup.py`. Each one uses `done()` to check
against the real system whether it is complete; normally the reconciliation takes less than a
second (no programs, only files and `wine --version`).

| Step | counts as done if … | otherwise |
|---|---|---|
| Installer | the Zwift launcher is already installed (or the verified installer is in the cache) | download, verify signature |
| Wine environment | it exists **and** was created/updated with the current Wine (`state.json` → `prefix.wine`) | `wineboot -u` (new Wine) or create it |
| Components | all verbs from `VERBS` are listed in the prefix's `winetricks.log` | missing ones via winetricks |
| Launcher | `ZwiftLauncher.exe` present | run the installer |
| Game | `ZwiftApp.exe` and version file present | download via the launcher (repair) |
| Graphics | the graphics test ran with the current Wine | graphics test |

If a step fails, Zwift does not start, and the overview shows that step's message.

`wineboot -u` runs with `WINEDLLOVERRIDES="mscoree,mshtml="` and for at most 5 minutes: without
the variable, Wine opens an invisible dialog for the Mono/Gecko installation and waits (on tinytin
it hung like this for over 10 minutes). The variable applies only to this call; .NET stays on.

Measured on tinytin (Oct 30, simulated switch 11.19 → 11.20): reconciliation with update and
graphics test, then Zwift after 47 s; normal start without changes: Zwift after 16 s.

## Rolling back when an update breaks something

- **Wine (in Tretlager):** Tretlager keeps exactly one Wine version, the last proven one
  (`~/.var/app/de.linuxundich.Tretlager/data/tretlager/wine-bewaehrt`, a good 500 MB,
  `core/wine.py`).
  - After the first ride (≥ 5 min), the bundled Wine is copied.
  - If a Tretlager update brings a new Wine, the copy of the old version stays. In the overview,
    the switch *Use previous Wine version* appears under *Zwift*; the reconciliation then adapts
    the Zwift environment to the old version (`wineboot -u`, graphics test).
  - After two rides with the new Wine, it counts as proven and replaces the copy. Rides with the
    old version do not count for this.
  - If the next Tretlager update brings yet another Wine, Tretlager switches back to the bundled
    one (it may fix the problem).

- **Tretlager/Wine:** `flatpak remote-info --log tretlager-origin de.linuxundich.Tretlager` shows
  the versions, `flatpak update --commit=<older> de.linuxundich.Tretlager` brings back the previous
  one (with its Wine), `flatpak mask de.linuxundich.Tretlager` pins it. The reconciliation then
  adapts the Zwift environment back to the older Wine version.
- **Zwift:** there is no rollback and none is needed – Zwift only lets you ride with the current
  version. If the Zwift environment is broken, *Check setup* recreates it; only the game
  (≈ 5 GB) is downloaded again.

## Progress during a Zwift update and the first installation

`Zwift_ver_cur.xml` names the manifest of the new version (`Zwift_<Version>_<Hash>_manifest.xml`,
same folder on the CDN, ≈ 5 MB, ≈ 20,000 files with path and size). Tretlager compares it with the
Zwift folder: missing files or files of a different size make up the amount to download.
The launcher first downloads into a staging folder (`drive_c/users/<Name>/AppData/Local/Temp/Zwift/Downloads`)
and at the end moves everything into the Zwift folder at once. Tretlager therefore counts both
every 3 s: what is in the staging folder (without leftovers of an aborted download) and what has
already arrived in the Zwift folder, and shows “… 1.2 of 3.4 GB” with a progress bar (at most 99 %,
until the version file changes). Without a manifest (offline, different format) it falls back to
the elapsed time: “for 3 minutes”.
Changed files of the same size are not counted; the display is an estimate.

The same applies to the first installation (setup step *Download Zwift*, `setup.Game`): instead of
an estimated 4.9 GB it shows the size according to the manifest. Without a manifest it estimates as
before from the size of the Zwift folder (“about”). Shared code in `core/manifest.py`.

Verified on tinytin (Oct 30): with the current version, 0 of 19,903 files missing, reconciliation
1 s; during a real first installation 0 → 99 % evenly in 9 minutes (5.1 GB, ≈ 10 MB/s). Without
the staging folder, the display stayed at 0 % for 9 minutes and then jumped to 99 %. A real Zwift
update has not been released yet; it goes through the same launcher and staging folder.

## Procedure for a new Tretlager version

1. Bump the version in `tretlager/__init__.py` and the CHANGELOG (otherwise the bridge does not
   restart after the update), add the metainfo `<release>`.
2. Bump Wine (optional): URL and SHA-256 in the manifest; build on tinytin.
3. On tinytin: reconciliation with the existing environment (Wine update, graphics test), start
   Zwift, short ride with trainer and heart rate, Zwift update if one happens to be pending.
4. Publish to the Flatpak repository on bender (F4).

## Open

- [ ] Tretlager reports by itself when a new version is available (Flatpak portal
  `CreateUpdateMonitor` / `Update`) – deliberately left open, distribution via Flathub is not
  planned.
- [x] Progress during a Zwift update from the manifest (observe during a real update).
- [x] Keep the previous Wine version (one) and make it selectable.
- [ ] Renew a specific Windows component (e.g. a newer WebView2) when Zwift requires it: revision
  marker per verb, then `winetricks --force <verb>` in the reconciliation.
- [ ] Flatpak repository on bender with GPG (F4); only then is there `flatpak update` for
  Tretlager.
