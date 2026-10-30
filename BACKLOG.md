# Backlog

## Offene Entscheidungen (vor Phase D)

- [x] **E1 Wine-Quelle.** Freigegeben 2026-10-29 für tinytin (T2). Debian forky hat kein Wine. Empfehlung: WineHQ-Repo (`winehq-devel`,
  Suite forky) über einen pkexec-Helfer mit fester Aktion, festgenageltem Schlüssel und
  ausdrücklicher Zustimmung. Alternative: umu-launcher + Proton im Benutzerverzeichnis (kein
  root, aber Steam-Runtime-Container und weniger erprobt mit Zwift).
- [x] **E2 Anmeldung.** Christoph 2026-10-29: Browser-Anmeldung wird als ausdrückliche Option mit
  Hinweis auf AGB §5 angeboten (offizielle Anmeldung geht unter Wine nicht, siehe T2). Start per
  `RunFromProcess` (Spiel als Kind des Launchers) gehört dazu.
- [ ] **E3 Sensoren.** Eigene schlanke Bridge (Python, bleak, Benutzer-systemd-Dienst) BlueZ →
  DIRCON statt qdomyos-zwift. Projekt-Lizenz GPL-3, damit qdomyos-Protokollcode als Referenz
  übernommen werden darf.
- [x] **E4 Desktop.** Christoph 2026-10-29: GTK4/libadwaita oder Qt/Plasma, beides erlaubt.
  Umsetzung wie bei Stafette: Kern als UI-freie Python-Bibliothek (Diagnose, Installation,
  Updates, Bridge-Steuerung), darauf GTK/libadwaita und Qt/Kirigami. Welche Oberfläche zuerst
  kommt, entscheidet Phase C; der Zielrechner tinytin läuft mit Plasma.
- [ ] **E5 Testhardware.** Rechner geklärt: `testt@tinytin` (forky, Plasma, Intel + RTX 3050 Ti
  mit PRIME-Offload, Treiber 580, AX201). Geräte: Wahoo KICKR V4, Garmin HRM-Pro Plus
  (BLE + ANT+), eingebauter Adapter. Keine weiteren Sensoren.
- [x] **E6 Sprache.** Python (Kern, Bridge), Debian-Paket.
- [x] **E8 Bezug.** Christoph 2026-10-29: vorerst nur ein lokal gebautes Debian-Paket; später eine
  Paketquelle auf bender (dort läuft schon das Arch-Repo `pacman-repo`).
- [x] **E9 Oberfläche zuerst.** Christoph 2026-10-29: Kirigami (Ziel Plasma). Die GTK-Oberfläche der
  Bridge bleibt bestehen und wird später an den Kern angepasst.
- [x] **E10 Wine-Politik.** Christoph 2026-10-29: immer die neueste `winehq-devel`, kein Pinning.
  Folge: Tretlager prüft nach jedem Wine-Update selbst (GL-Test, Start-Test) und meldet Brüche.
- [ ] **E7 Name.** Arbeitstitel „Tretlager“.

## Phasen

- [x] A Machbarkeit (Recherche) – [FEASIBILITY.md](FEASIBILITY.md)
- [ ] D' Machbarkeitstests T1–T7 (T1 Signatur weitgehend erledigt 2026-10-29) vor der Installationslogik (siehe FEASIBILITY.md, Abschnitt 9)
- [ ] B Systemdiagnose rein lesend (os-release, sysfs/DRM, nvidia-smi, EGL-Test, BlueZ per D-Bus,
  Wine-Version + Stub-Prüfung, Platz, vorhandene Prefixe)
- [x] ~~C GTK4-Prototyp~~ entfällt: Christoph 2026-10-30, es bleibt bei der Kirigami-Oberfläche
- [ ] D Installation: PackageKit (Simulation + Installation), pkexec-Helfer für WineHQ-Quelle,
  Download + Authenticode, Prefix, Launcher, Zustandsautomat mit Wiederaufnahme
- [ ] E Bridge BLE → DIRCON mit echter Hardware (Leistung, Kadenz, ERG, Puls)
- [ ] F Updates (SilentLaunch, `Zwift_ver_cur.xml`, Prefix-Schnappschuss, Versionsmatrix)
- [ ] G Ende-zu-Ende auf frischem TUXEDO OS Forky
- [ ] später: ANT+ nativ in der Bridge (openant/libusb)

## Bridge (T5/T6)

- [x] Bridge-Kern (DIRCON, GATT-Proxy, avahi, D-Bus, systemd-Benutzerdienst)
- [x] Oberfläche: Dienst an/aus, Autostart, Geräte suchen/hinzufügen/entfernen, Live-Werte
- [ ] HRM-Pro Plus auf tinytin: LE-1M-Gegenprobe (`btmgmt phy`), sonst USB-Bluetooth-Stick testen
  (Warnung seit 0.6.2 über `core/btcompat.py`; bei neuen Befunden dort ergänzen)
- [x] Bridge auf wählbaren Adapter umstellen (0.6.3; Umschalten, fehlender Adapter und Rückfall
  auf tinytin geprüft, mit echtem USB-Stick noch nicht)
- [x] Mit echtem USB-Bluetooth-Stick testen (30.10., TP-Link UB500): HRM-Pro Plus über den Stick ok,
  Umschalten, Aus- und Einschalten des Sticks ok
- [ ] Stick während einer Fahrt in Zwift abziehen (echtes Abziehen statt Ausschalten)
- [ ] HRM-Pro Plus über UB500 unzuverlässig: am 30.10. vormittags zweimal verbunden (nach 40–120 s),
  mittags trotz Signal (−74 dBm), ohne Handy-Bluetooth, allein getragen und nach Neustart des Sticks
  nur Zeitüberschreitungen; KICKR am selben Stick sofort verbunden. Ansätze: btmon-Mitschnitt (root),
  LE-1M erzwingen (`btmgmt phy`), Verbindungsparameter/Timeout der Bridge, zweiter Stick anderer Bauart.
  Nach Neustart von tinytin sofort wieder verbunden (30 s, 62 Schläge/min) → hängender Zustand in BlueZ
  oder im Controller (Stick-Neustart per Powered reichte nicht). Beim nächsten Mal zuerst
  `systemctl restart bluetooth` probieren; ggf. Tretlager-Hinweis „Bluetooth neu starten“ bei Gerät, das
  gefunden wird, aber dauerhaft nicht verbindet
- [ ] Nach dem Umschalten braucht der erste Verbindungsversuch des HRM-Pro manchmal eine Runde
  mehr (unvollständige Dienstsuche → Wartezeit wächst); ggf. Wartezeit nach Adapterwechsel zurücksetzen
- [ ] Paket-Update startet die laufende Bridge nicht neu (alte Version läuft weiter bis zum
  Neustart); postinst oder Hinweis in Tretlager
- [ ] Sensorseite: Schalter *Sensor-Bridge* sah unter Plasma ausgeschaltet aus, obwohl `checked` true war
  (30.10., noch FormCardPage); seit dem neuen Seitengerüst (0.6.4) richtig dargestellt, beobachten
- [x] TICKR mit sauberem Signal prüfen (Elektroden angefeuchtet: Werte wie Pulsuhr)
- [x] Zwift koppelt KICKR (Leistung, Trittfrequenz) und Pulsgurt über DIRCON, Werte realistisch (2026-10-29)
- [x] ERG und Steigungssimulation über FTMS-Control-Point (Antwort in der Schreib-Antwort, 2026-10-29)
- [ ] Oberfläche: Hinweis bei hängender Dienstsuche („Gurt kurz abklipsen“) statt endlos „Verbinde …“
- [ ] Oberfläche: Plasma-Feinschliff (Symbole geprüft, Entfernen-Knopf neu)
- [x] Netzwechsel: Verbindungen mit verschwundener lokaler Adresse schließen
- [ ] Ohne jede Netzverbindung testen (Ankündigung auf lo vorhanden)
- [ ] Längere Fahrt (≥ 30 min) auf Stabilität prüfen
- [x] Netzwechsel während der Fahrt: Ankündigung auf 127.0.0.1, Lauschen nur auf Loopback (2026-10-29)
- [ ] Netzwechsel-Test wiederholen: Kabel ab/an während der Fahrt

## Bedienung (Konzept: docs/bedienkonzept.md)

- [x] Entscheidungen: E2 ja, lokales .deb (später bender), Kirigami zuerst, neueste Wine (2026-10-29)
Umsetzung in Meilensteinen (Kern Python `tretlager/core`, Oberfläche PySide6 + Kirigami `tretlager/kde`):

- [x] M1 Systemprüfung im Kern (ohne root) + Kirigami-Gerüst: Willkommen, Prüfseite mit Ampel (auf tinytin geprüft 2026-10-29)
- [x] M2 Vorbereiten: Polkit-Helfer `setup-system` (WineHQ-Quelle, Paketliste per APT-Simulation), Seite mit Änderungsliste — auf tinytin mit Polkit-Dialog ausgeführt (2026-10-29, nach Fix des gpg-Arbeitsverzeichnisses)
- [x] M3 Zwift einrichten (Kern): Schritte mit Wiederaufnahme, Download + Signatur, Prefix, winetricks, Launcher, Spiel, GL-Test — auf tinytin Ende-zu-Ende in 459 s, zweiter Lauf 2 s (2026-10-29)
- [x] M3 Seite „Zwift einrichten“ in der Oberfläche durchgeklickt (alle Schritte „schon erledigt“)
- [x] M4 Anmeldung: Browser-Anmeldung mit Hinweis, Übernahme aus der Zwischenablage, Token im Schlüsselbund (ksecretd), Erneuerung — auf tinytin geprüft (2026-10-29)
- [ ] Breeze-Warnungen „ProgressBar.qml: Cannot read property 'top' of null“ beim Seitenaufbau klären
- [x] M5 Sensoren-Seite (Bridge über D-Bus) + Hauptfenster „Zwift starten“ — auf tinytin: Start mit Token aus dem Schlüsselbund, NVIDIA, Fenster per KWin maximiert, Auflösung bleibt, Launcher-Reste beendet (2026-10-29)
- [x] Sicherheit: Token nie in Befehlszeilen/Protokollen (Datei + `--token=@`), Abmelden beendet die Sitzung bei Zwift
- [ ] Bridge-Neustart beim Einspielen trennt Sensoren kurz – beim Paket-Update Zwift-Lauf beachten
- [x] Ende einer Zwift-Sitzung: Bridge stoppt, wenn nicht im Autostart (beim Direktstart geprüft)
- [x] M6a Debian-Paket `tretlager` (`build-aux/build-deb.sh`), 0.2.0 auf tinytin installiert, Bridge aus dem Paket läuft (2026-10-29)
- [ ] M6b Ende-zu-Ende auf frischem TUXEDO OS forky (VM `tuxedo-os-forky`: Ablauf ohne NVIDIA/Bluetooth; Polkit-Passwort und Zwift-Anmeldung durch Christoph)
- [x] Direktstart „Zwift (Tretlager)“ auf tinytin geprüft: Start nach 15 s, NVIDIA, Fenster/Auflösung ok, kein Token im Journal, nach der Fahrt Tretlager beendet, Bridge gestoppt (2026-10-29)
- [x] Nur eine Tretlager-Instanz (zweiter Aufruf nutzt das vorhandene Fenster; 0.3.0)
- [x] Paketquelle auf bender (Debian): `services/pacman-repo/publish-deb.sh`, `http://bender:8095/debian` (0.3.0)
- [x] Reichweite: Hinweis in der Oberfläche bei häufigen Abbrüchen (≥ 3 in 10 min) mit Abhilfe (0.3.0)
- [x] Oberfläche: Schalter „Im Netz anbieten“ (`local_only`), D-Bus `SetLocalOnly` (0.3.0)
- [x] ~~GTK-Oberfläche der Bridge nachziehen~~ entfällt: GTK-Oberfläche in 0.5.1 entfernt (Christoph 2026-10-30)

## Sprachen

- [x] Englische Oberfläche (0.7.0, gettext, `po/en.po`)
- [ ] Neue Texte: `po/update.sh` (auf dem Arch-Rechner mit gettext), Übersetzung in `po/en.po`
  ergänzen; `tests/test_i18n.py` meldet Lücken

## Flatpak (Plan: docs/flatpak.md)

- [x] F0 Machbarkeit auf tinytin (30.10.): alle Bausteine laufen (Wine aus Quellen, multiarch); offen: echte Fahrt, Kopie des bestehenden Präfixes
- [x] F1 Manifest und Bau (0.8.0): Wine aus Quellen, Python-Wheels fest, Metainfo, build.sh auf tinytin
- [x] F2 Code (0.8.0): Bridge per D-Bus-Aktivierung + Quit, Autostart-Portal, Bridge-Version, gdbus, Assistent ohne Vorbereiten
- [ ] Autostart der Bridge über das Background-Portal nach einem Neustart von tinytin prüfen
- [ ] F2b Distributionsunabhängig: Systemprüfung ohne Debian-Annahmen, Avahi-Prüfung, GNOME-Rückfälle (Maximieren, DPI)
- [ ] F3 Umstieg auf tinytin: Debian-Paket entfernt (30.10.); Zwift-Präfix (36 GB inkl. Sicherungen) unter ~/.local/share/tretlager übernehmen oder löschen
- [ ] F4 Flatpak-Quelle auf bender mit GPG-Schlüssel
- [ ] F5 Abnahme: frisches TUXEDO OS, Fedora KDE + GNOME, Arch, lange Fahrt; Debian-Quelle auf bender abschalten

## Sicherheit

- [ ] Zwift bekommt das Token als Befehlszeilenargument (`ZwiftApp.exe --token={…}`); es steht damit in der
  Prozessliste und ist für jeden lokalen Benutzer lesbar (`ps`). Prüfen, ob RunFromProcess das Token
  anders übergeben kann (Datei/Pipe) oder ob Zwift es nur so annimmt; sonst in der Hilfe erwähnen.
  (Gesehen 30.10. beim Flatpak-Test; nie `pgrep -fa Zwift` o. Ä. ausgeben.)
