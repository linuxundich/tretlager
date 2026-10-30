# Tretlager als Flatpak – Phasenplan

Stand 2026-10-30. Ziel: Tretlager mit allem, was Zwift braucht (Wine, winetricks, Werkzeuge,
Python-Pakete), als ein Flatpak ausliefern. Damit kann ein Systemupdate die getestete
Wine-Version nicht mehr ändern, der Schritt *Vorbereiten* (WineHQ-Quelle, Passwort, APT)
entfällt, und Tretlager läuft auch außerhalb von TUXEDO OS. Das Debian-Paket bleibt, bis das
Flatpak Phase F5 bestanden hat.

## Was schon geklärt ist (Flathub, 30.10.)

| Baustein | Stand | Quelle |
|---|---|---|
| Laufzeit | `org.kde.Platform//6.11` mit Kirigami (KF6) | `flatpak remote-ls flathub` |
| PySide6 + QtWebEngine | `io.qt.PySide.BaseApp//6.11` (PySide 6.11.2, wie auf tinytin), baut auf `io.qt.qtwebengine.BaseApp//6.11` und KDE 6.11 auf → PySide6, Kirigami und WebEngine in einer Umgebung | `flatpak remote-info --show-metadata` |
| NVIDIA | `org.freedesktop.Platform.GL.nvidia-580-178-04` passt zum Treiber von tinytin; Flatpak installiert die passende Erweiterung selbst | `flatpak remote-ls` |
| tinytin | Flatpak 1.18.4, Flathub als Systemquelle eingerichtet | `flatpak --version` |
| Verteilung | Nicht über Flathub (Flathub verbietet KI-erstellte Manifeste und Einreichungen), sondern eigene Quelle auf bender wie bei den anderen Apps | Arbeitsregel |

## Offene Kernfragen (entscheiden über das Vorhaben)

1. **Kirigami Addons** (FormCard, Components) ist vermutlich nicht in `org.kde.Platform`; KDE-Apps
   auf Flathub bauen es als eigenes Modul mit (CMake, wenige Minuten). Prüfen und ggf. als Modul
   aufnehmen.
2. **Wine in der KDE-Laufzeit.** `org.winehq.Wine` ist eine eigenständige App auf der
   Freedesktop-Laufzeit und lässt sich nicht einbinden. Plan: Wine als WoW64-Build ins Paket
   (Kron4ek `wine-11.20-amd64-wow64.tar.xz`, Prüfsumme fest im Manifest). WoW64 braucht keine
   32-Bit-Bibliotheken, also keine `Compat.i386`-/`GL32`-Erweiterungen. **Risiko:** Laufen
   .NET 4.8, WebView2 und der Zwift-Launcher unter WoW64 genauso wie unter dem bisherigen
   `winehq-devel` 11.20 (klassisch mit 32-Bit-Teil)? Ausweichweg: Wine selbst im Manifest bauen
   bzw. ein klassischer Build mit `Compat.i386` (prüfen, ob es diese Erweiterung zur KDE-Laufzeit
   gibt).
3. **NVIDIA in der Sandbox.** Mit `--device=dri` und der GL-Erweiterung sollte Zwift per
   PRIME-Offload (`__NV_PRIME_RENDER_OFFLOAD`, `__GLX_VENDOR_LIBRARY_NAME=nvidia`) auf der RTX
   laufen; Gegenprobe mit dem vorhandenen Grafiktest (`gltest`).
4. **Bridge in der Sandbox.** bleak über `org.bluez` (System-Bus), mDNS über Avahi, DIRCON auf
   127.0.0.1. Findet Zwift (im selben Flatpak) die Geräte wie bisher?

## Phasen

### F0 Machbarkeit auf tinytin (vor jeder Umbauarbeit)

Wegwerf-Manifest unter `build-aux/flatpak/spike/`, gebaut auf dem Arch-Rechner, installiert auf
tinytin aus einer lokalen Quelle. Der laufende Tretlager (Debian-Paket) bleibt unangetastet;
die Bridge des Pakets während der Tests stoppen.

- [ ] a) Oberfläche: PySide-BaseApp + Kirigami Addons + Tretlager-Quellen → Fenster startet,
      FormCards, Hilfe, Anmeldefenster (WebEngine) zeigt die Zwift-Seite.
- [ ] b) Wine: WoW64-Build im Flatpak → `wineboot`, Grafiktest auf NVIDIA, winetricks
      (`corefonts`, `dotnet48`, `webview2`, `d3dcompiler_47`) in einem neuen Präfix.
- [ ] c) Zwift: Launcher und Spiel im neuen Präfix starten (Token-Start wie bisher); danach eine
      Kopie des bestehenden Präfixes (8,6 GB) gegen das Flatpak-Wine testen.
- [ ] d) Bridge: Scan, KICKR + HRM-Pro über den UB500, Ankündigung per Avahi, Zwift koppelt.
- [ ] e) Kleinkram: `/sys/class/bluetooth` und `/sys/class/power_supply` lesbar, Schlüsselbund
      (`org.freedesktop.secrets`), Benachrichtigungen, KWin-Skript zum Maximieren.

**Ausstiegskriterium:** eine echte Fahrt mit dem Spike-Flatpak. Scheitert b) oder c), Wine im
Manifest selbst bauen (F0 wiederholen) oder das Vorhaben zurückstellen.

### F1 Manifest und Bau

- `build-aux/flatpak/de.linuxundich.Tretlager.yml`, Basis `io.qt.PySide.BaseApp//6.11`,
  Laufzeit `org.kde.Platform//6.11`.
- Module: Kirigami Addons; Python-Pakete (bleak, dbus-fast, SecretStorage samt
  Abhängigkeiten, per `flatpak-pip-generator`); Wine (Tarball, Prüfsumme); winetricks (fest wie
  bisher, Prüfsumme); cabextract; osslsigncode; Tretlager selbst (inkl. `po/update.sh --build`).
- `finish-args` (Entwurf):
  - `--share=network`, `--share=ipc`, `--socket=wayland`, `--socket=fallback-x11`,
    `--socket=pulseaudio`, `--device=dri`
  - `--system-talk-name=org.bluez`, `--system-talk-name=org.freedesktop.Avahi`
  - `--talk-name=org.freedesktop.secrets`, `--talk-name=org.freedesktop.Notifications`,
    `--talk-name=org.kde.KWin`
  - Bus-Name der Bridge `de.linuxundich.Tretlager.Bridge` beginnt mit der App-ID und ist damit
    ohne eigene Freigabe erlaubt.
- `build-aux/flatpak/build.sh` wie bei Freisteller/Kulisse (lokale Quelle `repo/`).

### F2 Anpassungen im Code (Erkennung über `/.flatpak-info`)

- **Assistent ohne *Vorbereiten*:** Polkit-Helfer, APT-Plan und WineHQ-Prüfung nur im
  Debian-Paket; im Flatpak fünf Schritte. Systemprüfung: Wine „im Paket enthalten“.
- **Wine-Pfade:** `/app/wine/bin` statt `/opt/wine-devel`; Umgebung in `setup`/`launch` zentral.
- **Bridge ohne systemd:** `bridgectl` startet die Bridge als eigene Flatpak-Instanz über das
  Portal (`org.freedesktop.portal.Flatpak.Spawn`), damit sie unabhängig vom Fenster läuft.
  *Beim Anmelden starten* über das Background-Portal (`RequestBackground`, autostart) statt
  `systemctl --user enable`.
- **Bridge-Version:** Die Bridge meldet ihre Version; startet Tretlager nach einem Update mit
  einer älteren laufenden Bridge, startet es sie neu, solange Zwift nicht läuft (löst auch das
  Problem des Debian-Pakets).
- **NVIDIA-Fehler nach der Fahrt:** Das Kernel-Journal ist in der Sandbox nicht lesbar. Meldung
  im Flatpak weglassen; Warnung beim Wechsel der Stromquelle bleibt (sysfs).
- **Speicherorte:** Vorschlag `--filesystem=xdg-data/tretlager`, `xdg-config/tretlager`,
  `xdg-cache/tretlager`, `xdg-state/tretlager` → dieselben Pfade wie das Debian-Paket, keine
  Umzüge, Präfix und Einstellungen bleiben. Alternative (sauberer, aber mit Umzug von 8,6 GB):
  Sandbox-Pfade unter `~/.var/app/de.linuxundich.Tretlager/`.

### F3 Umstieg vom Debian-Paket

- Anleitung bzw. kleines Skript: Bridge-Dienst stoppen und abschalten, `apt remove tretlager`
  (Daten bleiben), Flatpak installieren. Optional WineHQ-Quelle und `winehq-devel` entfernen.
- Auf tinytin durchspielen: Zwift, Anmeldung (Schlüsselbund), Bridge-Einstellungen inkl.
  UB500 und pausiertem TICKR müssen ohne Neueinrichtung weiterlaufen.

### F4 Verteilung über bender

- Flatpak-Quelle neben pacman-repo und Debian-Quelle (nginx Port 8095, Pfad `/flatpak`),
  `services/pacman-repo/publish-flatpak.sh`, `.flatpakrepo`-Datei.
- Eigener GPG-Schlüssel für die Quelle (über HTTP ohne Signatur wäre jede Änderung unterwegs
  unbemerkt).
- README: Installation per `flatpak remote-add` + `flatpak install`.

### F5 Abnahme

- [ ] Frisches TUXEDO OS forky (VM `tuxedo-os-forky`, Ablauf ohne NVIDIA/Bluetooth; Polkit
      entfällt, Zwift-Anmeldung durch Christoph) – ersetzt BACKLOG M6b.
- [ ] Eine zweite Distribution mit Plasma (z. B. Fedora KDE in einer VM).
- [ ] Fahrt ≥ 30 min auf tinytin, Netzteil ab/an, ohne Netz.
- [ ] Danach: Debian-Paket einfrieren (nur noch Fehlerbehebungen) oder einstellen.

## Was sich für den Nutzer ändert

- Kein Passwort, keine Paketquelle von WineHQ, keine APT-Änderungen am System.
- Download einmalig größer: KDE-Laufzeit und PySide-Basis (zusammen gut 1 GB, teilen sich andere
  KDE-Flatpaks) plus Wine (~ 200 MB). Zwift selbst (~ 5 GB) wie bisher.
- Updates über `flatpak update` bzw. Discover statt APT.
- Entfällt: Meldung von NVIDIA-Treiberfehlern nach der Fahrt.

## Quellen

- Flathub: `flatpak remote-ls/remote-info flathub` (30.10.2026)
- Kron4ek Wine-Builds, Release 11.20 mit WoW64-Tarballs: https://github.com/Kron4ek/Wine-Builds/releases/tag/11.20
- KDE-Doku Flatpak-Manifeste: https://develop.kde.org/docs/packaging/flatpak/manifest/
- Kirigami Addons als eigenes Flatpak-Modul (Beispiel Angelfish): https://lxr.kde.org/source/network/angelfish/flatpak/kirigami-addons.json
