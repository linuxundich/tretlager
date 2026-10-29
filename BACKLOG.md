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
- [ ] C GTK4-Prototyp: Hauptfenster, Assistent, Diagnose; Platzhalter klar erkennbar
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
- [x] TICKR mit sauberem Signal prüfen (Elektroden angefeuchtet: Werte wie Pulsuhr)
- [x] Zwift koppelt KICKR (Leistung, Trittfrequenz) und Pulsgurt über DIRCON, Werte realistisch (2026-10-29)
- [x] ERG und Steigungssimulation über FTMS-Control-Point (Antwort in der Schreib-Antwort, 2026-10-29)
- [ ] Oberfläche: Hinweis bei hängender Dienstsuche („Gurt kurz abklipsen“) statt endlos „Verbinde …“
- [ ] Oberfläche: Plasma-Feinschliff (Symbole geprüft, Entfernen-Knopf neu)
- [x] Netzwechsel: Verbindungen mit verschwundener lokaler Adresse schließen
- [ ] Ohne jede Netzverbindung testen (Ankündigung auf lo vorhanden)
- [ ] Längere Fahrt (≥ 30 min) auf Stabilität prüfen
- [x] Netzwechsel während der Fahrt: Ankündigung auf 127.0.0.1, Lauschen nur auf Loopback (2026-10-29)
- [ ] Oberfläche: Schalter „Auch für Zwift auf anderen Geräten im Netz anbieten“ (local_only)
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
- [ ] Nur eine Tretlager-Instanz (zweiter Aufruf soll das vorhandene Fenster nutzen)
- [ ] Paketquelle auf bender (Debian), analog pacman-repo
- [ ] Reichweite: Notebook im Nebenraum → KICKR verbindet nur wackelig (AX201). Hinweis in der Oberfläche bei häufigen Abbrüchen; Empfehlung USB-Bluetooth-Stick mit Verlängerung oder Bridge auf einem Rechner neben dem Trainer
- [ ] Oberfläche: Schalter „Auch für Zwift auf anderen Geräten im Netz anbieten“ (`local_only`), z. B. Bridge auf Raspberry Pi neben dem Trainer
