# Tretlager als Flatpak – Phasenplan

Stand 2026-10-30. **Primärziel:** Tretlager als Flatpak, das distributionsunabhängig auf modernen
Distributionen läuft (nicht zwingend überall) und alles mitbringt, was Zwift braucht (Wine,
winetricks, Werkzeuge, Python-Pakete). Ein Systemupdate kann die getestete Wine-Version nicht mehr
ändern, der Schritt *Vorbereiten* (WineHQ-Quelle, Passwort, APT) entfällt. Das Debian-Paket ist
eingestellt (auf tinytin am 30.10. entfernt) und wird nicht mehr weiterentwickelt.

### Was „moderne Distribution“ heißt

- Flatpak ≥ 1.14 (Background-Portal, `--allow=multiarch`), xdg-desktop-portal mit KDE- oder
  GNOME-Backend, BlueZ ≥ 5.6x, Avahi (für die Ankündigung an Zwift), PipeWire oder PulseAudio.
- Wayland-Sitzung mit XWayland oder X11; NVIDIA mit proprietärem Treiber, für den es die
  passende Flathub-Erweiterung gibt, oder Mesa (Intel/AMD).
- Ziel-Tests: TUXEDO OS (Plasma), Fedora (KDE und GNOME), Arch, Ubuntu 26.04 LTS.
- Was nur unter Plasma geht (KWin-Skript zum Maximieren, XWayland-Skalierung aus `kwinrc`),
  bekommt unter GNOME einen sinnvollen Rückfall statt eines Fehlers.

## Was schon geklärt ist (Flathub, 30.10.)

| Baustein | Stand | Quelle |
|---|---|---|
| Laufzeit | `org.kde.Platform//6.11` mit Kirigami (KF6) | `flatpak remote-ls flathub` |
| PySide6 + QtWebEngine | `io.qt.PySide.BaseApp//6.11` (PySide 6.11.2, wie auf tinytin), baut auf `io.qt.qtwebengine.BaseApp//6.11` und KDE 6.11 auf → PySide6, Kirigami und WebEngine in einer Umgebung | `flatpak remote-info --show-metadata` |
| NVIDIA | `org.freedesktop.Platform.GL.nvidia-580-178-04` passt zum Treiber von tinytin; Flatpak installiert die passende Erweiterung selbst | `flatpak remote-ls` |
| tinytin | Flatpak 1.18.4, Flathub als Systemquelle eingerichtet | `flatpak --version` |
| Verteilung | Nicht über Flathub (Flathub verbietet KI-erstellte Manifeste und Einreichungen), sondern eigene Quelle auf bender wie bei den anderen Apps | Arbeitsregel |

## Offene Kernfragen (entscheiden über das Vorhaben)

1. ~~Kirigami Addons~~ – geklärt: in `org.kde.Platform//6.11` enthalten (1.13.1).
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

Wegwerf-Manifest (`build-aux/flatpak/spike/`, nach F0 durch das echte Manifest ersetzt), installiert
auf tinytin aus einer Einzeldatei. Der laufende Tretlager (Debian-Paket) bleibt unangetastet;
die Bridge des Pakets während der Tests stoppen.

- [x] a) Oberfläche: PySide-BaseApp + Tretlager-Quellen → Fenster, FormCards, Plasma-Stil;
      Anmeldefenster (WebEngine) zeigt die Zwift-Seite.
- [x] b) Wine: fertige Kron4ek-WoW64-Builds stürzen in **jeder** Flatpak-Laufzeit ab
      (`virtual_init`, Code 139), das offizielle `org.winehq.Wine//wow64` läuft → Wine 11.20 aus den
      Quellen gebaut (mingw-w64-Erweiterung 25.08, `--enable-archs=i386,x86_64`). Braucht
      `--allow=multiarch` (sonst bleibt `syswow64` leer). corefonts, .NET 4.8, WebView2 ok.
- [x] c) Zwift: Launcher und Spiel im neuen Präfix, Grafiktest „NVIDIA GeForce RTX 3050 Ti“
      (OpenGL 4.6, 580.178.04) über die GL-Erweiterung; Start mit Token aus dem Schlüsselbund.
      Offen: Kopie des bestehenden Präfixes gegen das Flatpak-Wine.
- [x] d) Bridge im Flatpak: BlueZ (UB500), Avahi, D-Bus-Name; Zwift im Flatpak koppelt KICKR
      (automatisch) und HRM-Pro.
- [x] e) sysfs (Netzteil, Bluetooth-Chip), Schlüsselbund, Benachrichtigungen (gdbus), KWin-Skript
      (nach Korrektur, Skript in `$XDG_RUNTIME_DIR/app/<ID>`).

**Ergebnis F0 (30.10.): machbar.** Eine echte Fahrt fehlt noch, alle Bausteine laufen. Erkenntnisse für
F1/F2:

- In der Sandbox fehlen `busctl`, `systemctl`, `journalctl`, `bluetoothctl`: `bridgectl`,
  Systemprüfung (Bluetooth) und Adapterliste auf `gdbus` bzw. dbus-fast umstellen.
- Systemprüfung: Betriebssystem aus `/run/host/os-release`; NVIDIA über `/proc/driver/nvidia/version`
  (`/sys/module/nvidia` fehlt); Wine „im Paket“.
- `--socket=x11` statt `fallback-x11` (Wine nähme sonst den Wayland-Treiber).
- Kirigami Addons 1.13.1 ist in `org.kde.Platform//6.11`, kein eigenes Modul nötig.
- Bauen auf tinytin (20 Kerne): Wine-Modul dauert dort einige Minuten.

**Ausstiegskriterium:** eine echte Fahrt mit dem Spike-Flatpak. Scheitert b) oder c), Wine im
Manifest selbst bauen (F0 wiederholen) oder das Vorhaben zurückstellen.

### F1 Manifest und Bau – erledigt (0.8.0, 30.10.)

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

### F2 Anpassungen im Code (Erkennung über `/.flatpak-info`) – erledigt (0.8.0)

Umgesetzt: Bridge per D-Bus-Aktivierung (statt Portal-Spawn: der Sitzungsbus startet die
exportierte Dienstdatei als eigene Instanz) und `Quit`, Autostart über das Background-Portal,
Bridge-Version mit Neustart nach Update, gdbus statt busctl/systemctl, Assistent ohne
*Vorbereiten*, Systemprüfung mit Host-os-release und Avahi. Auf tinytin geprüft: Aktivierung,
`Quit`, Start aus der Oberfläche, Systemprüfung alles grün. Offen: NVIDIA-Fehler nach der Fahrt
(kein Journal in der Sandbox) entfallen; Autostart über das Portal noch nicht nach einem Neustart
geprüft.

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

### F2b Distributionsunabhängigkeit

- Systemprüfung ohne Debian-Annahmen: Betriebssystem nur noch anzeigen (aus
  `/run/host/os-release`), nicht mehr als „Zielsystem“ werten; Prüfungen auf Flatpak-Fähigkeiten
  (Portal, Avahi, BlueZ, GPU) statt auf Pakete.
- Hilfe und Texte ohne TUXEDO-/APT-Bezug, wo es nicht ums Debian-Paket geht.
- Avahi fehlt auf manchen Distributionen standardmäßig: Prüfung mit verständlicher Abhilfe, ggf.
  Ankündigung ohne Avahi (eigenes mDNS) als Ausweg.
- GNOME: Fenster maximieren ohne KWin (Wine-Registry bzw. Vollbild), DPI aus der Fensterskalierung.

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
