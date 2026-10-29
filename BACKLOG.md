# Backlog

## Offene Entscheidungen (vor Phase D)

- [ ] **E1 Wine-Quelle.** Debian forky hat kein Wine. Empfehlung: WineHQ-Repo (`winehq-devel`,
  Suite forky) über einen pkexec-Helfer mit fester Aktion, festgenageltem Schlüssel und
  ausdrücklicher Zustimmung. Alternative: umu-launcher + Proton im Benutzerverzeichnis (kein
  root, aber Steam-Runtime-Container und weniger erprobt mit Zwift).
- [ ] **E2 Anmeldung.** Kein nachgebauter OAuth-Login (AGB §5, Grundsatz 7). Nur die offizielle
  WebView2-Anmeldung im Launcher. Offen: Ist der Start per `runfromprocess` (Spiel als Kind des
  Launchers) vertretbar, falls der Launcher das Spiel unter Wine nicht selbst startet?
- [ ] **E3 Sensoren.** Eigene schlanke Bridge (Python, bleak, Benutzer-systemd-Dienst) BlueZ →
  DIRCON statt qdomyos-zwift. Projekt-Lizenz GPL-3, damit qdomyos-Protokollcode als Referenz
  übernommen werden darf.
- [ ] **E4 Desktop des Zielrechners.** TUXEDO OS Forky bringt Plasma mit; der Auftrag nennt GNOME.
  Läuft auf dem Zielrechner GNOME, oder soll libadwaita auch unter Plasma gut aussehen?
- [ ] **E5 Testhardware.** Welcher Rechner mit NVIDIA-Karte, welcher Trainer, welcher Pulsgurt,
  welcher BLE-Adapter? (smokki: Intel-Grafik, AX200.)
- [ ] **E6 Sprache.** Empfehlung Python + PyGObject (Auftrag bevorzugt es; Bridge mit bleak in
  derselben Sprache), Meson, Debian-Paket.
- [ ] **E7 Name.** Arbeitstitel „Tretlager“.

## Phasen

- [x] A Machbarkeit (Recherche) – [FEASIBILITY.md](FEASIBILITY.md)
- [ ] D' Machbarkeitstests T1–T7 vor der Installationslogik (siehe FEASIBILITY.md, Abschnitt 9)
- [ ] B Systemdiagnose rein lesend (os-release, sysfs/DRM, nvidia-smi, EGL-Test, BlueZ per D-Bus,
  Wine-Version + Stub-Prüfung, Platz, vorhandene Prefixe)
- [ ] C GTK4-Prototyp: Hauptfenster, Assistent, Diagnose; Platzhalter klar erkennbar
- [ ] D Installation: PackageKit (Simulation + Installation), pkexec-Helfer für WineHQ-Quelle,
  Download + Authenticode, Prefix, Launcher, Zustandsautomat mit Wiederaufnahme
- [ ] E Bridge BLE → DIRCON mit echter Hardware (Leistung, Kadenz, ERG, Puls)
- [ ] F Updates (SilentLaunch, `Zwift_ver_cur.xml`, Prefix-Schnappschuss, Versionsmatrix)
- [ ] G Ende-zu-Ende auf frischem TUXEDO OS Forky
- [ ] später: ANT+ nativ in der Bridge (openant/libusb)
