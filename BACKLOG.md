# Backlog

## Entscheidungen

- [x] **E1 Wine-Quelle.** Freigegeben 2026-10-29 für tinytin (T2). Debian forky hat kein Wine. Empfehlung: WineHQ-Repo (`winehq-devel`,
  Suite forky) über einen pkexec-Helfer mit fester Aktion, festgenageltem Schlüssel und
  ausdrücklicher Zustimmung. Alternative: umu-launcher + Proton im Benutzerverzeichnis (kein
  root, aber Steam-Runtime-Container und weniger erprobt mit Zwift).
- [x] **E2 Anmeldung.** Christoph 2026-10-29: Browser-Anmeldung wird als ausdrückliche Option mit
  Hinweis auf AGB §5 angeboten (offizielle Anmeldung geht unter Wine nicht, siehe T2). Start per
  `RunFromProcess` (Spiel als Kind des Launchers) gehört dazu.
- [x] **E3 Sensoren.** Umgesetzt (tretlager/bridge, seit 0.8.0 per D-Bus-Aktivierung statt systemd). Eigene schlanke Bridge (Python, bleak, Benutzer-systemd-Dienst) BlueZ →
  DIRCON statt qdomyos-zwift. Projekt-Lizenz GPL-3, damit qdomyos-Protokollcode als Referenz
  übernommen werden darf.
- [x] **E4 Desktop.** Christoph 2026-10-29: GTK4/libadwaita oder Qt/Plasma, beides erlaubt.
  Umsetzung wie bei Stafette: Kern als UI-freie Python-Bibliothek (Diagnose, Installation,
  Updates, Bridge-Steuerung), darauf GTK/libadwaita und Qt/Kirigami. Welche Oberfläche zuerst
  kommt, entscheidet Phase C; der Zielrechner tinytin läuft mit Plasma.
- [x] **E5 Testhardware.** Rechner geklärt: `testt@tinytin` (forky, Plasma, Intel + RTX 3050 Ti
  mit PRIME-Offload, Treiber 580, AX201). Geräte: Wahoo KICKR V4, Garmin HRM-Pro Plus
  (BLE + ANT+), eingebauter Adapter; dazu Wahoo TICKR und USB-Stick TP-Link UB500 (30.10.).
- [x] **E6 Sprache.** Python (Kern, Bridge), Debian-Paket.
- [x] **E8 Bezug.** Christoph 2026-10-29: vorerst nur ein lokal gebautes Debian-Paket; später eine
  Paketquelle auf bender (dort läuft schon das Arch-Repo `pacman-repo`).
- [x] **E9 Oberfläche zuerst.** Christoph 2026-10-29: Kirigami (Ziel Plasma). Die GTK-Oberfläche der
  Bridge bleibt bestehen und wird später an den Kern angepasst.
- [x] **E10 Wine-Politik.** Christoph 2026-10-29: immer die neueste `winehq-devel`, kein Pinning.
  Folge: Tretlager prüft nach jedem Wine-Update selbst (GL-Test, Start-Test) und meldet Brüche.
  Im Flatpak (seit 0.8.0) kommt Wine mit der Tretlager-Version; „neueste Wine“ heißt dort: Wine im
  Manifest mit jeder Tretlager-Version anheben und vorher testen. Nach dem Wechsel gleicht Tretlager
  die Umgebung selbst ab (docs/updates.md).
- [ ] **E7 Name.** Arbeitstitel „Tretlager“.

## Phasen

- [x] A Machbarkeit (Recherche) – [FEASIBILITY.md](FEASIBILITY.md)
- [x] D' Machbarkeitstests T1–T7 (FEASIBILITY.md, Abschnitt 9): Zwift, Grafik, Anmeldung und Bridge laufen auf tinytin (29./30.10.)
- [x] B Systemdiagnose rein lesend (core/systemcheck.py; im Flatpak ohne Debian-Annahmen) (os-release, sysfs/DRM, nvidia-smi, EGL-Test, BlueZ per D-Bus,
  Wine-Version + Stub-Prüfung, Platz, vorhandene Prefixe)
- [x] ~~C GTK4-Prototyp~~ entfällt: Christoph 2026-10-30, es bleibt bei der Kirigami-Oberfläche
- [x] ~~D Installation: PackageKit~~ im Flatpak entfallen (Wine im Paket); umgesetzt sind (Simulation + Installation), pkexec-Helfer für WineHQ-Quelle,
  Download + Authenticode, Prefix, Launcher, Schritte mit Wiederaufnahme (core/setup.py)
- [x] E Bridge BLE → DIRCON mit echter Hardware (Leistung, Kadenz, ERG, Puls; Testfahrten 29./30.10.)
- [x] F Updates (SilentLaunch, `Zwift_ver_cur.xml`, Abgleich vor dem Start, Fortschritt; Plan docs/updates.md, 0.9.0)
- [ ] G Ende-zu-Ende auf frischem TUXEDO OS Forky → aufgegangen in F5 (Flatpak-Abnahme)
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
  gefunden wird, aber dauerhaft nicht verbindet.
  Live-Test 30.10. 12:3x (Flatpak): wieder hängend, BlueZ meldet am UB500 `Connected=true`,
  `ServicesResolved=false` → die GATT-Dienstsuche hängt wie am AX201, auch nach RemoveDevice und
  Stick-Neustecken. Nächster Schritt: btmon-Mitschnitt und LE-1M erzwingen (`btmgmt --index 1 phy`,
  root); Bridge könnte bei hängender Dienstsuche gezielt Disconnect + Cache leeren
- [ ] Nach dem Umschalten braucht der erste Verbindungsversuch des HRM-Pro manchmal eine Runde
  mehr (unvollständige Dienstsuche → Wartezeit wächst); ggf. Wartezeit nach Adapterwechsel zurücksetzen
- [x] Paket-Update startet die laufende Bridge nicht neu → im Flatpak gelöst: Tretlager startet eine
  ältere Bridge beim Öffnen neu (Versionsvergleich, seit 0.8.0; setzt eine neue Versionsnummer voraus)
- [x] Sensorseite: Schalter *Sensor-Bridge* sah unter Plasma ausgeschaltet aus, obwohl `checked` true war
  (30.10., noch FormCardPage); seit dem neuen Seitengerüst (0.6.4) richtig dargestellt, seitdem nicht wieder gesehen
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
- [x] Bridge-Neustart beim Einspielen trennt Sensoren kurz → Neustart nur, wenn Zwift nicht läuft (0.8.0)
- [x] Ende einer Zwift-Sitzung: Bridge stoppt, wenn nicht im Autostart (beim Direktstart geprüft)
- [x] M6a Debian-Paket `tretlager` (`build-aux/build-deb.sh`), 0.2.0 auf tinytin installiert, Bridge aus dem Paket läuft (2026-10-29)
- [x] ~~M6b Ende-zu-Ende Debian-Paket~~ entfällt (Debian-Paket eingestellt) → F5; frische Erstinstallation
  im Flatpak auf tinytin zweimal durchgelaufen (30.10., 15 min)
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
- [x] F3 Umstieg auf tinytin: Debian-Paket entfernt, alte Paketdaten (36 GB) gelöscht (30.10.)
- [ ] F4 Flatpak-Quelle auf bender mit GPG-Schlüssel
- [ ] F5 Abnahme: frisches TUXEDO OS, Fedora KDE + GNOME, Arch, lange Fahrt; Debian-Quelle auf bender abschalten
- [x] **Startabbruch auf nanhlanu (Arch, GNOME 51, 31.10.):** Bundle (master ce6b144, auf tinytin gebaut) installiert in 19 s, startet aber nicht: `QtCore.abi3.so: undefined symbol _ZN14QObjectPrivateC2E16QtPrivate_6_11_2, version Qt_6_PRIVATE_API`. nanhlanu hat `org.kde.Platform//6.11` vom 31.10. (Commit fb23e178), tinytin einen älteren (76fa01ac). PySide aus `io.qt.PySide.BaseApp` hängt an der privaten Qt-API der Patch-Version → jedes Laufzeit-Update kann Tretlager brechen. Lösung suchen: gegen aktuelle Laufzeit + BaseApp neu bauen, Laufzeit-Commit pinnen oder PySide selbst gegen die Laufzeit bauen; Startfehler sichtbar machen (kein Fenster, kein Log). Behoben: gegen BaseApp 6.11.3 (Testbau #47) gebaut, Hinweis beim Startabbruch
- [ ] BaseApp auf tinytin zurück auf Flathub stable, sobald flathub/io.qt.PySide.BaseApp#47 gemergt ist (`flatpak uninstall --user io.qt.PySide.BaseApp//6.11` + `flatpak install --user flathub io.qt.PySide.BaseApp//6.11`), dann neu bauen
- [x] Absturz bei der Anmeldung im Flatpak (nanhlanu 31.10.): `QtWebEngineProcess` nicht gefunden → Variablen im Manifest; eingebettete Zwift-Seite öffnet sich
- [x] GNOME: Symbole fehlten (Portal meldet Adwaita, nicht in der KDE-Laufzeit) → Plasma-Plattformthema außerhalb von Plasma (Breeze)
- [ ] GNOME: Hell/Dunkel von GNOME übernehmen (Portal `org.freedesktop.appearance color-scheme`); eigene kdeglobals über XDG_CONFIG_DIRS griff im Test nicht, `kdeglobals` in der Sandbox ist ein schreibgeschützter Platzhalter der Host-Datei
- [ ] GNOME: Schrift von GNOME (Adwaita Sans) statt Noto Sans aus dem Plasma-Thema prüfen
- [ ] Vor jeder Veröffentlichung (F4): Qt-Version von Laufzeit und BaseApp vergleichen; nach einem Qt-Patch-Update der Laufzeit zügig neu bauen und veröffentlichen, sonst startet Tretlager bei den Nutzern nicht

## Hinweise in der App

- [x] Haftungshinweis zur Sensor-Bridge ergänzen (Christoph 30.10.): Zwift ist womöglich nicht
  glücklich darüber, dass eine Software-Bridge Daten an Zwift übermittelt, die manipuliert werden
  könnten. Deshalb klar: Nutzung auf eigene Gefahr – nicht dass jemand seine mit viel Schweiß
  erstrampelten XP und Drops verliert (Kontosperre bzw. Zurücksetzen nicht ausgeschlossen).
  Ergänzt den Hinweis „Nicht für Rennen“ (Willkommen, Übersicht, Über Tretlager, Hilfe, README,
  Metainfo); Ton locker, aber eindeutig.
- [x] Beim ersten Start eine Warnung, die man bestätigen muss (Christoph 30.10.), mit allen
  Haftungshinweisen zusammen: Tretlager ist keine offizielle Zwift-App und wird von Zwift nicht
  unterstützt; Nutzung auf eigene Gefahr (XP und Drops); nicht für Rennen, keine Garantie für die
  Werte der Sensor-Bridge; Anmeldung über eigenes Fenster widerspricht den Zwift-Nutzungsbedingungen.
  Bestätigung im Zustand merken; erneut zeigen, wenn sich der Hinweistext ändert (Versionsmarke).

## Sicherheit

- [ ] Zwift bekommt das Token als Befehlszeilenargument (`ZwiftApp.exe --token={…}`); es steht damit in der
  Prozessliste und ist für jeden lokalen Benutzer lesbar (`ps`). Prüfen, ob RunFromProcess das Token
  anders übergeben kann (Datei/Pipe) oder ob Zwift es nur so annimmt; sonst in der Hilfe erwähnen.
  (Gesehen 30.10. beim Flatpak-Test; nie `pgrep -fa Zwift` o. Ä. ausgeben.)

## QA-Audit 2026-10-30 (docs/qa-audit-2026-10-30.md)

- [x] B-01 abwesender Sensor blockierte Bluetooth 40 s (gemessen, behoben)
- [x] Z-01/Z-02, L-01, L-02, B-02, B-03, U-01, U-02, S-01, I-01, I-02 behoben
- [x] B-04 Gerät bei kurzem BLE-Abbruch 45 s für Zwift halten (live mit getrenntem KICKR geprüft)
- [ ] B-05 Standby/Resume und Stick-Abziehen während der Fahrt testen
- [ ] F-01 `--talk-name=org.kde.KWin` ersetzen oder begründen (nur zum Maximieren)
- [ ] Bridge-Zustand per QtDBus-Signal `Changed` statt gdbus-Abfrage; `Backend` aufteilen
- [x] C-01 `setup.Context.run`: Timeout auch ohne Ausgabe durchsetzen
- [x] C-02 DIRCON: Sendepuffer begrenzen, wenn Zwift nicht liest
- [x] U-03 Startknopf größer, Live-Werte als Kennzahlen (im HIG-Rahmen); Hervorhebung unter echtem Plasma noch ansehen (Bildschirm war gesperrt)
- [ ] Metainfo: Screenshots (Release-Beschreibung seit 0.9.0)

## Updates (docs/updates.md)

- [x] Keine Schnappschüsse; Einrichtung vor jedem Start abgleichen (Wine-Wechsel → `wineboot -u` + Grafiktest)
- [ ] Neue Tretlager-Version im Programm melden (Flatpak-Portal) – bewusst offen, kein Flathub geplant (Christoph 30.10.)
- [x] Fortschritt beim Zwift-Update aus dem Zwift-Manifest
- [ ] Fortschritt bei einem echten Zwift-Update beobachten
- [x] Vorige Wine-Version aufbewahren (eine) und in der Übersicht wählbar
- [ ] Windows-Komponente gezielt erneuern (Revisionsmarke je Verb, `winetricks --force`)
- [ ] Echten Wine-Wechsel auf tinytin durchspielen (Tretlager mit anderer Wine-Version bauen)
