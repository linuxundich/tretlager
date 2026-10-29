# Changelog

Alle wichtigen Änderungen an Tretlager. Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

## [0.4.1] - 2026-10-30

### Hinzugefügt
- Seite „Über Tretlager“ (Menü und Willkommensseite): Version, Hinweis, dass Tretlager kein
  offizielles Zwift-Programm ist und die Benutzung auf eigene Gefahr erfolgt, Lizenz sowie die
  freien und unfreien Komponenten mit ihren Lizenzen.
- Lizenz GPL-3.0-or-later (`LICENSE`), im Debian-Paket als `copyright`.
- Die Willkommensseite nennt den Hinweis zu Zwift und Haftung gleich vor der Einrichtung.

### Geändert
- Neues Symbol im Stil heutiger Rennrad-Kurbeln: Vierarm-Spinne, zwei Kettenblätter,
  verjüngte Kurbelarme, waagrechte Klickpedale mittig am Kurbelauge. Erzeugt von
  `build-aux/make-icon.py`.

## [0.4.0] - 2026-10-30

### Geändert
- Neue Übersicht für den Desktop: oben „Zwift starten“ mit Erklärung, darunter Karten in zwei
  Spalten für Sensoren, Zwift-Version, Grafik, Anmeldung sowie Hilfe und Wartung; jede Karte
  erklärt kurz, was dahintersteckt.
- Sensoren-Seite neu gegliedert: Bridge mit ihren Schaltern, deine Geräte als große Karten mit
  Zustand, Werten und Zwift-Namen, Suche nach neuen Geräten, „Wenn etwas hakt“.
- Beim Start stehen Übersicht und Sensoren nebeneinander, das Fenster öffnet größer.
- Einrichtungsseiten mit begrenzter Lesebreite; Erklärungen als ruhige Hinweise statt blauer
  Meldungskästen.
- Symbol: Die Pedale stehen waagrecht, das hintere liegt hinter Kurbelarm und Kettenblatt.

## [0.3.2] - 2026-10-30

### Geändert
- Im breiten Fenster zeigt das Hauptfenster die Sensoren gleich rechts daneben.

## [0.3.1] - 2026-10-30

### Geändert
- Tretlager öffnet sich so breit, dass Hauptfenster und Sensoren bzw. Hilfe nebeneinander
  passen, sofern der Bildschirm Platz hat.

## [0.3.0] - 2026-10-30

### Hinzugefügt
- Nur eine Tretlager-Instanz: Ein zweiter Aufruf holt das offene Fenster nach vorn;
  „Zwift (Tretlager)“ startet Zwift dann im vorhandenen Fenster.
- Schalter „Im Netz anbieten“ in der Sensoren-Seite: Die Bridge kündigt ihre Geräte auch im LAN
  an (z. B. Bridge auf einem Rechner neben dem Trainer, Zwift auf einem anderen Gerät).
- Hinweis bei schwachem Funk: Bricht eine Sensorverbindung in 10 Minuten dreimal oder öfter ab,
  zeigen Sensoren-Seite und Hauptfenster einen Hinweis mit Abhilfe.
- Debian-Paketquelle im Heimnetz: `deb [trusted=yes] http://bender:8095/debian ./`.

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
