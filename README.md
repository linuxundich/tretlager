# Tretlager (Arbeitstitel)

Native GTK4-/libadwaita-Anwendung, die den offiziellen Windows-Client von **Zwift** unter
**TUXEDO OS Forky** (Debian testing) einrichtet, startet und aktuell hält: Wine, Laufzeit,
Grafikdiagnose (NVIDIA), Sensoren über Bluetooth LE ohne Zwift Companion App.

**Stand (2026-10-29):** Machbarkeit geprüft, Zwift läuft auf dem Testrechner tinytin (Opt-in-
Token-Login, NVIDIA per GLX + PRIME-Offload). Die **Sensor-Bridge** mit Oberfläche funktioniert:
Zwift koppelt Trainer und Pulsgurt über Wahoo Direct Connect, ohne Companion App.
Ergebnis in [FEASIBILITY.md](FEASIBILITY.md), Bedienkonzept in
[docs/bedienkonzept.md](docs/bedienkonzept.md), offene Entscheidungen und Phasen in
[BACKLOG.md](BACKLOG.md).

Kernbefunde:
- Zwift läuft nur experimentell unter Wine (WineHQ 11.x; Debian forky hat derzeit kein Wine).
- Das Spiel nutzt OpenGL 3.1, DXVK ist überflüssig.
- Direktes BLE aus Wine geht nicht (GATT-Benachrichtigungen und Schreiben fehlen). Sensoren
  kommen über eine eigene Bridge, die sich als Wahoo-„Direct Connect“-Gerät ausgibt.
- Die Anmeldung im Launcher (WebView2) ist das größte offene Risiko.

## Grundsätze

Keine Umgehung von Anmeldung, DRM oder Lizenzprüfung, keine veränderten Zwift-Dateien, keine
Telemetrie, keine stillen Systemänderungen. Nicht Funktionierendes wird als solches angezeigt.

## Bridge ausprobieren (Benutzerinstallation)

    build-aux/install-user.sh          # nach ~/.local, systemd-Benutzerdienst tretlager-bridge
    systemctl --user start tretlager-bridge
    PYTHONPATH=~/.local/lib/tretlager python3 -m tretlager.ui

Abhängigkeiten (Debian forky): `python3-bleak`, `python3-gi`, `gir1.2-gtk-4.0`, `gir1.2-adw-1`,
laufender `avahi-daemon` und BlueZ. Tests: `python -m pytest tests`.

## Oberfläche (Kirigami)

    PYTHONPATH=. python3 -m tretlager.kde

Braucht zusätzlich `python3-pyside6.qtqml`, `python3-pyside6.qtquick`,
`python3-pyside6.qtquickcontrols2`, `python3-pyside6.qtgui`, `qml6-module-org-kde-kirigami` und
`qml6-module-org-kde-kirigamiaddons-formcard` (plus `-components`). Die Oberfläche folgt den
KDE Human Interface Guidelines: Seitenleiste nach der Einrichtung, FormCards, Hilfeknöpfe,
Assistent als linearer Ablauf. `TRETLAGER_INSTANCE=test` startet eine zweite Instanz neben der
laufenden, etwa zum Testen aus dem Quellbaum.

## Debian-Paket

    build-aux/build-deb.sh            # → dist/tretlager_<Version>_all.deb (braucht dpkg-deb)
    sudo apt install ./dist/tretlager_<Version>_all.deb

Im Heimnetz einfacher über die eigene Paketquelle auf bender (unsigniert, nur LAN):

    echo 'deb [trusted=yes] http://bender:8095/debian ./' | sudo tee /etc/apt/sources.list.d/linuxundich.list
    sudo apt update && sudo apt install tretlager

Neue Version veröffentlichen: Paket bauen, dann `services/pacman-repo/publish-deb.sh`.

Danach im Startmenü: **Tretlager** (Assistent/Hauptfenster) und **Zwift (Tretlager)** (Direktstart).
Version steht in `CHANGELOG.md`.

## Lizenz und Hinweis

Tretlager steht unter der GPL-3.0-or-later (`LICENSE`), das gilt auch für das Symbol
(`build-aux/make-icon.py`). Tretlager ist kein Produkt von Zwift Inc. und wird von Zwift nicht
unterstützt; die Benutzung erfolgt auf eigene Gefahr. Zwift, .NET Framework, WebView2 und die
übrigen Windows-Komponenten sind unfreie Software. Tretlager liefert sie nicht mit, die
Einrichtung lädt sie beim Hersteller. Die Übersicht aller Komponenten und Lizenzen steht in der
App unter *Über Tretlager*.
