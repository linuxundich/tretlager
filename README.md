# Tretlager (Arbeitstitel)

Native Qt-/Kirigami-Anwendung, die den offiziellen Windows-Client von **Zwift** unter Linux
einrichtet, startet und aktuell hält: Wine, Laufzeit, Grafikdiagnose (NVIDIA), Sensoren über
Bluetooth LE ohne Zwift Companion App.

**Ziel (seit 2026-10-30): ein Flatpak**, das auf modernen Distributionen läuft und alles mitbringt,
was Zwift braucht (eigenes Wine, winetricks, Werkzeuge). Plan und Stand in
[docs/flatpak.md](docs/flatpak.md). Entwickelt und getestet auf TUXEDO OS Forky (Plasma) auf
tinytin; Plasma ist das Hauptziel, GNOME soll funktionieren.

**Stand (2026-10-30):** 0.9.0 als Flatpak auf tinytin; Zwift läuft (Opt-in-Token-Login, NVIDIA
per GLX + PRIME-Offload), die **Sensor-Bridge** koppelt Trainer und Pulsgurt über Wahoo Direct
Connect, ohne Companion App. Machbarkeit in [FEASIBILITY.md](FEASIBILITY.md), Bedienkonzept in
[docs/bedienkonzept.md](docs/bedienkonzept.md), QA-Audit in
[docs/qa-audit-2026-10-30.md](docs/qa-audit-2026-10-30.md), offene Punkte in [BACKLOG.md](BACKLOG.md).

**Nicht für Rennen:** Es gibt keine Garantie, dass die Sensor-Bridge Leistung, Trittfrequenz und
Puls korrekt an Zwift weitergibt. An Rennen und Wettbewerben mit Wertung sollte man mit Tretlager
nicht teilnehmen. Der Hinweis steht in der App auf der Willkommensseite, in der Übersicht unter
*Zwift starten*, unter *Über Tretlager* und in der Hilfe.

Kernbefunde:
- Zwift läuft nur experimentell unter Wine (11.x, im Flatpak aus den Quellen gebaut).
- Das Spiel nutzt OpenGL 3.1, DXVK ist überflüssig.
- Direktes BLE aus Wine geht nicht (GATT-Benachrichtigungen und Schreiben fehlen). Sensoren
  kommen über eine eigene Bridge, die sich als Wahoo-„Direct Connect“-Gerät ausgibt.
- Die offizielle Anmeldung im Launcher (WebView2) geht unter Wine nicht; Tretlager meldet über ein
  eigenes Anmeldefenster an (nur nach Zustimmung, widerspricht §5 der Zwift-AGB).

## Voraussetzungen auf dem Rechner

Tretlager bringt Wine, winetricks, Python-Pakete und Werkzeuge mit. Vom System kommen nur:

- Flatpak ≥ 1.14 mit Flathub (für `org.kde.Platform//6.11`, `io.qt.PySide.BaseApp//6.11` und bei
  NVIDIA die passende `GL.nvidia-…`-Erweiterung) und xdg-desktop-portal.
- **BlueZ** (Bluetooth-Dienst) und ein Bluetooth-LE-Adapter, eingebaut oder als USB-Stick.
- **Avahi** (`avahi-daemon`): Darüber findet Zwift die Sensoren. Die Systemprüfung warnt, wenn es fehlt.
- Ein **Schlüsselbund** nach Secret-Service-Standard (KWallet/ksecretd unter Plasma, GNOME
  Schlüsselbund) für die Zwift-Sitzung.
- x86-64, eine Wayland-Sitzung mit XWayland oder X11; NVIDIA mit proprietärem Treiber oder Mesa.

Getestet ist bisher nur TUXEDO OS Forky mit Plasma 6.7 (tinytin). Fedora, Ubuntu, openSUSE, Arch
und GNOME sind Ziel, aber ungeprüft (Phase F5 in [docs/flatpak.md](docs/flatpak.md)).

## Alltag mit dem Flatpak

- **Aktualisieren:** `flatpak update de.linuxundich.Tretlager`; Wine und alle übrigen Bausteine
  kommen mit Tretlager. Vor jedem Start gleicht Tretlager die Zwift-Umgebung ab (neues Wine →
  `wineboot -u` und Grafiktest) und spielt Zwift-Updates über den Zwift-Launcher ein. Keine
  Schnappschüsse. Die zuletzt bewährte Wine-Version hebt Tretlager auf (eine, ≈ 500 MB); macht ein
  neues Wine Probleme, startet der Schalter *Vorige Wine-Version nutzen* in der Übersicht Zwift
  wieder damit. Plan: [docs/updates.md](docs/updates.md).
- **Deinstallieren:** `flatpak uninstall de.linuxundich.Tretlager`; Zwift-Umgebung (gut 10 GB),
  Einstellungen und Protokolle löscht `flatpak uninstall --delete-data de.linuxundich.Tretlager`.
  Die Zwift-Sitzung im Schlüsselbund entfernt *Abmelden* in Tretlager vorher.
- **Daten:** alles unter `~/.var/app/de.linuxundich.Tretlager/` – `data/tretlager/prefix`
  (Zwift), `config/tretlager/bridge.json` (Sensoren), `.local/state/tretlager/` (Zustand,
  Protokoll `tretlager.log`). Das Bridge-Protokoll steht im Journal:
  `journalctl --user -t de.linuxundich.Tretlager.Bridge`.
- **Netz:** Tretlager meldet nichts nach Hause. Verbindungen gehen nur zu Zwift (Versionsprüfung
  `cdn.zwift.com`, Anmeldung `secure.zwift.com`, Spiel-Updates über den Zwift-Launcher), zu GitHub
  (winetricks, einmalig) und zu den Download-Quellen von winetricks (Microsoft u. a. für Schriften,
  .NET und WebView2, einmalig bei der Einrichtung).

## Fehlerbehebung

| Problem | Abhilfe |
|---|---|
| Sensor bleibt bei „Sucht das Gerät …“ | Trainer kurz antreten, Gurt anfeuchten und anlegen. Nicht genutzte Sensoren *pausieren*. |
| Sensor verbindet sich nie (Garmin HRM-Pro an Intel AX201) | Bekannte Chip-Unverträglichkeit; USB-Bluetooth-Stick einstecken und unter *Sensoren* als Adapter wählen. Hängt es danach weiter: `systemctl restart bluetooth` (root) oder Neustart. |
| Zwift findet keine Sensoren | Bridge muss laufen (*Sensoren*), Avahi muss laufen; in Zwift „Wahoo KICKR …“ bzw. „Wahoo HRM …“ koppeln. |
| „Kein Schlüsselbund erreichbar“ | KWallet bzw. GNOME Schlüsselbund starten und entsperren. |
| Zwift hängt nach Wechsel Netz/Akku | NVIDIA-Treiber (Xid); Zwift mit Alt+F4 beenden, mit Netzteil neu starten. |

## Bekannte Einschränkungen

- Nur Bluetooth LE (FTMS, Cycling Power, CSC, Herzfrequenz); ANT+ nicht.
- Tatsächlich getestet: Wahoo KICKR V4 (FTMS, ERG, Steigung), Wahoo TICKR, Garmin HRM-Pro Plus
  (nur über USB-Stick zuverlässig). Andere Geräte mit diesen Standarddiensten sollten gehen,
  sind aber ungeprüft.
- Fenster maximieren und Wine-DPI aus der XWayland-Skalierung gibt es nur unter Plasma.
- Zwift bekommt die Sitzung als Befehlszeilenargument (sichtbar in der Prozessliste, BACKLOG).

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
(`build-aux/make-icon.py`). Die Hintergrundgrafik `tretlager/data/backdrop.png` erzeugt
`build-aux/make-backdrop.py` aus einem Foto, das nicht im Repository liegt
(`build-aux/make-backdrop.py foto.jpg`).
Tretlager ist kein Produkt von Zwift Inc. und wird von Zwift nicht
unterstützt; die Benutzung erfolgt auf eigene Gefahr. Zwift, .NET Framework, WebView2 und die
übrigen Windows-Komponenten sind unfreie Software. Tretlager liefert sie nicht mit, die
Einrichtung lädt sie beim Hersteller. Die Übersicht aller Komponenten und Lizenzen steht in der
App unter *Über Tretlager*.
