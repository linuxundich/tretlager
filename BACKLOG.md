# Backlog

## Offene Entscheidungen (vor Phase D)

- [x] **E1 Wine-Quelle.** Freigegeben 2026-10-29 für tinytin (T2). Debian forky hat kein Wine. Empfehlung: WineHQ-Repo (`winehq-devel`,
  Suite forky) über einen pkexec-Helfer mit fester Aktion, festgenageltem Schlüssel und
  ausdrücklicher Zustimmung. Alternative: umu-launcher + Proton im Benutzerverzeichnis (kein
  root, aber Steam-Runtime-Container und weniger erprobt mit Zwift).
- [ ] **E2 Anmeldung.** Kein nachgebauter OAuth-Login (AGB §5, Grundsatz 7). Nur die offizielle
  WebView2-Anmeldung im Launcher. Offen: Ist der Start per `runfromprocess` (Spiel als Kind des
  Launchers) vertretbar, falls der Launcher das Spiel unter Wine nicht selbst startet?
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
- [ ] **E6 Sprache.** Empfehlung Python + PyGObject (Auftrag bevorzugt es; Bridge mit bleak in
  derselben Sprache), Meson, Debian-Paket.
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
