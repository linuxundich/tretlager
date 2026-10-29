# Changelog

Alle wichtigen Änderungen an Tretlager. Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

## [0.2.1] - 2026-10-29

### Behoben
- Sensor-Bridge: Geräte, die beim Verbinden wieder einschlafen (Trainer nach einer Pause), werden
  nach 10 s erneut versucht statt mit wachsender Pause bis 60 s.

## [0.2.0] - 2026-10-29

### Hinzugefügt
- Eigenes Programmsymbol im Breeze-Stil (Kurbelgarnitur mit Kettenblatt, zwei Kurbelarmen und
  Pedalen).
- Hilfe in der App (Menü → Hilfe, Willkommensseite): Einrichtung, Alltag, Koppeln in Zwift,
  Anmeldung, Problemlösungen, Datenschutz, Ablageorte.
- Startmenü-Eintrag „Zwift (Tretlager)“ und Schnellaktion „Zwift starten“: startet Zwift direkt
  (`tretlager --start`) und beendet Tretlager nach der Fahrt.

### Geändert
- Die Sensor-Bridge startet schon beim Öffnen des Hauptfensters, damit Trainer und Gurt beim
  Aufsteigen verbunden sind.
- Das Hauptfenster prüft im Hintergrund auf ein Zwift-Update und zeigt es vor dem Start an.
- Während der Fahrt minimiert sich Tretlager und kommt danach wieder nach vorn.

## [0.1.0] - 2026-10-29

Erste Version, auf TUXEDO OS forky (tinytin) mit Wahoo KICKR V4 und Wahoo TICKR getestet.

### Hinzugefügt
- Einrichtungsassistent für Plasma (PySide6 + Kirigami): Systemprüfung, Systemvorbereitung mit
  einer Polkit-Abfrage (WineHQ-Quelle, Wine), Zwift-Einrichtung mit Wiederaufnahme,
  Anmeldung, Sensoren, Abschluss.
- Hauptfenster mit „Zwift starten“: Bridge, Token-Erneuerung, Update mit Prefix-Schnappschuss,
  Start auf der NVIDIA-Karte (GLX + PRIME-Offload), Fenster maximieren (KWin), Aufräumen.
- Installer-Prüfung per Authenticode-Signatur (Zwift, Inc.).
- Sensor-Bridge `tretlager-bridge` (systemd-Benutzerdienst): BLE-Geräte über BlueZ als Wahoo
  Direct Connect (DIRCON) für Zwift, inklusive FTMS-Steuerung (Steigung, ERG); Ankündigung auf
  127.0.0.1; GTK-Oberfläche `tretlager-sensoren-gtk`.
- Optionale Anmeldung über den Browser (auf eigenes Risiko), Token im Schlüsselbund.

### Sicherheit
- Token nie in Befehlszeilen oder Protokollen; Abmelden beendet die Sitzung bei Zwift.
