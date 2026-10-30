# Changelog

Alle wichtigen Änderungen an Tretlager. Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

## [0.6.1] - 2026-10-30

### Hinzugefügt
- Hinweise zur Stromversorgung auf Notebooks (`tretlager/core/power.py`). Anlass: Auf tinytin hing
  Zwift, nachdem während des Starts das Netzteil gezogen bzw. gesteckt wurde; der NVIDIA-Treiber
  meldete dabei Dutzende „Xid 69“. Die Grafik wechselt nicht auf den Intel-Chip, das TCC-Profil
  bleibt gleich; vermutlich stellt nvidia-powerd das Leistungsbudget um.
  - Übersicht im Akkubetrieb: Empfehlung, mit Netzteil zu starten und es angeschlossen zu lassen.
  - Wechsel der Stromquelle während Start oder Fahrt: Desktop-Benachrichtigung und Warnung mit
    Abhilfe (Alt+F4, mit Netzteil neu starten).
  - Nach der Fahrt: Meldet der NVIDIA-Treiber Fehler im Kernel-Journal, zeigt die Übersicht sie mit
    wahrscheinlicher Ursache an.
- Hilfe: Abschnitt zum Netzteil und Tabelleneintrag „Zwift hängt nach dem Ab- oder Anstecken“.

## [0.6.0] - 2026-10-30

### Geändert
- Anmeldung bei Zwift ohne Fehlerseite: Die Anmeldeseite öffnet sich in einem eingebetteten,
  privaten Fenster (QtWebEngine, ohne Cookies auf der Platte), wie im offiziellen Launcher.
  Tretlager fängt den Rücksprung ab, bevor „Bad Request“ erscheint; Kopieren der Adresse
  entfällt. Andere Rücksprungadressen lässt Zwift nicht zu.
- Die Anmeldeseite erscheint in der Systemsprache (`ui_locales`).
- Fehlercodes von Zwift (z. B. `login_required`, `access_denied`) erscheinen als Klartext.
- Der eigene Browser bleibt als Ausweichweg, etwa für Passwortmanager oder die Anmeldung mit
  Google oder Apple.
- Neue Paketabhängigkeiten: `python3-pyside6.qtwebenginequick`, `qml6-module-qtwebengine`.

## [0.5.1] - 2026-10-30

### Entfernt
- GTK4-/libadwaita-Oberfläche der Bridge (`tretlager-sensoren-gtk`, Empfehlungen `python3-gi`,
  `gir1.2-gtk-4.0`, `gir1.2-adw-1`). Die Bridge wird nur noch über die Kirigami-Oberfläche
  gesteuert; deren Sensorsymbole liegen jetzt in `tretlager/data/icons`.

### Geändert
- Die Hilfe spricht nicht mehr mit „du“ an (KDE-HIG) und nennt die neuen Bezeichnungen
  (Übersicht, Seitenleiste, *Neu anmelden …*).
- Hilfe: Abschnitt zu abbrechenden Verbindungen ergänzt, UI-Namen kursiv.

## [0.5.0] - 2026-10-30

### Geändert
- Oberfläche nach den aktuellen KDE Human Interface Guidelines überarbeitet:
  - Seitenleiste (Kirigami-GlobalDrawer) mit Übersicht, Sensoren, Hilfe, Einrichtung prüfen
    und Über Tretlager; der Assistent bleibt ein linearer Ablauf mit einer Seite und
    Zurück-Knopf.
  - Einstellungen, Geräte und Listen als FormCards aus Kirigami Addons statt eigener Karten;
    Erklärungen hinter Hilfeknöpfen (ContextualHelpButton) statt langer Textblöcke.
  - Übersicht: Start rahmenlos oben, darunter Sensoren und Zwift in zwei Spalten.
  - Entfernen-Knöpfe bleiben sichtbar, Protokolle öffnen sich in einem Dialog.
  - Texte knapp und unpersönlich, Einheiten ausgeschrieben, Auslassungspunkte bei Aktionen,
    die weitere Eingaben verlangen.
  - Assistentenseiten mit Fortschrittsbalken „Schritt n von 6“ und einheitlicher Fußleiste.
- Über Tretlager nutzt die Standard-Infoseite von KDE (Kirigami Addons) mit Lizenztext.
- Neue Paketabhängigkeiten: `qml6-module-org-kde-kirigamiaddons-formcard` und
  `-components`; empfohlen `qml6-module-org-kde-desktop`.

### Hinzugefügt
- Ersatz für KLocalizedContext (`tretlager/kde/i18n.py`): Kirigami Addons zeigt seine eigenen
  Beschriftungen übersetzt, obwohl PySide keine KI18n-Bindung hat.
- `TRETLAGER_INSTANCE` startet zum Testen eine zweite Instanz neben der laufenden.

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
