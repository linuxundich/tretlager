# Tretlager (Arbeitstitel)

Native Qt-/Kirigami-Anwendung, die den offiziellen Windows-Client von **Zwift** unter Linux
einrichtet, startet und aktuell hält: Wine, Laufzeit, Grafikdiagnose (NVIDIA), Sensoren über
Bluetooth LE ohne Zwift Companion App.

**Ziel (seit 2026-10-30): ein Flatpak**, das auf modernen Distributionen läuft und alles mitbringt,
was Zwift braucht (eigenes Wine, winetricks, Werkzeuge). Plan und Stand in
[docs/flatpak.md](docs/flatpak.md). Entwickelt und getestet auf TUXEDO OS Forky (Plasma) auf
tinytin; Plasma ist das Hauptziel, GNOME soll funktionieren.

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

Abhängigkeiten (Debian forky): `python3-bleak`, `python3-dbus-fast`, laufender `avahi-daemon`
und BlueZ. Gesteuert wird die Bridge über die Sensoren-Seite der Kirigami-Oberfläche.
Tests: `python -m pytest tests`.

## Oberfläche (Kirigami)

    PYTHONPATH=. python3 -m tretlager.kde

Braucht zusätzlich `python3-pyside6.qtqml`, `python3-pyside6.qtquick`,
`python3-pyside6.qtquickcontrols2`, `python3-pyside6.qtgui`, `qml6-module-org-kde-kirigami` und
`qml6-module-org-kde-kirigamiaddons-formcard` (plus `-components`). Die Oberfläche folgt den
KDE Human Interface Guidelines: Seitenleiste nach der Einrichtung, FormCards, Hilfeknöpfe,
Assistent als linearer Ablauf. `TRETLAGER_INSTANCE=test` startet eine zweite Instanz neben der
laufenden, etwa zum Testen aus dem Quellbaum.

### Sprachen

Quellsprache ist Deutsch, dazu gibt es Englisch (`po/en.po`, Hilfe in
`tretlager/data/hilfe.en.md`). Ohne deutsche Systemsprache zeigt Tretlager Englisch;
`TRETLAGER_LANG=en` bzw. `de` erzwingt eine Sprache. QML-Texte stehen in `i18n()`, Python-Texte
in `_()` (Texte der Bridge in `N_()`, übersetzt erst in der Oberfläche).

    po/update.sh          # Texte sammeln (po/tretlager.pot), Kataloge abgleichen; braucht gettext
    po/update.sh --build  # po/*.po → tretlager/data/locale/*.mo, reines Python (auch auf tinytin)

`build-deb.sh` übersetzt die Kataloge selbst. `tests/test_i18n.py` schlägt fehl, wenn ein Text
keine englische Übersetzung hat oder Platzhalter nicht übereinstimmen.

## Flatpak

    build-aux/flatpak/build.sh            # auf tinytin: bauen und für den Benutzer installieren
    build-aux/flatpak/build.sh --bundle   # zusätzlich tretlager.flatpak (Einzeldatei)
    flatpak run de.linuxundich.Tretlager

Braucht `flatpak-builder` sowie (lädt `build.sh` selbst) `org.kde.Sdk//6.11`,
`io.qt.PySide.BaseApp//6.11` und `org.freedesktop.Sdk.Extension.mingw-w64//25.08`. Wine wird aus
den Quellen gebaut (auf tinytin einige Minuten). Neue Python-Abhängigkeiten:
`build-aux/flatpak/gen-python-deps.py` schreibt `python-deps.json` neu.

Die Sensor-Bridge startet per D-Bus-Aktivierung als eigene Instanz:
`flatpak run --command=tretlager-bridge de.linuxundich.Tretlager` startet sie von Hand.

## Debian-Paket (eingestellt)

Das Debian-Paket (bis 0.7.1) war der erste Auslieferungsweg und wird nicht weiterentwickelt; es
bleibt nur, bis das Flatpak die Abnahme (F5) bestanden hat. Auf tinytin ist es seit 2026-10-30
entfernt.

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
