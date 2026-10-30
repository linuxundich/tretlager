# Changelog

Alle wichtigen Änderungen an Tretlager. Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

## [0.6.10] - 2026-10-30

### Behoben
- *Einrichtung prüfen* in der Seitenleiste schaltete die Seitenleiste ab; aus dem Assistenten
  ging es nicht mehr heraus. Assistentenmodus und Seitenleiste sind jetzt getrennt
  (`inWizard` bzw. `navigation` in `Main.qml`): Nach abgeschlossener Einrichtung bleibt die
  Seitenleiste nutzbar, der Eintrag ist markiert, und die Fußleiste hat *Assistent schließen*.
  Ohne Seitenleiste läuft nur noch die erste Einrichtung.

### Geändert
- *Einrichtung prüfen* beginnt nach der Einrichtung gleich bei Schritt 1 (System prüfen) statt
  bei der Willkommensseite.

## [0.6.9] - 2026-10-30

### Geändert
- Hilfe ohne Fließtext: je Abschnitt eine Karte mit Einträgen aus fettem Stichwort und kurzem
  Satz, Problemfälle mit Symbol unten über die volle Breite in zwei Spalten, Pfade in
  Festbreitenschrift. Der Text ist neu gegliedert (Überblick, Fahren, Sensoren, Anmeldung,
  Datenschutz und Speicherorte, Einrichtung, Wenn etwas nicht klappt) und deutlich kürzer.
- `data/hilfe.md` hat ein einfaches Format (Abschnitt, optional Symbol und `wide`, Einleitung,
  Einträge `- [symbol] **Stichwort**: Text`); `core/helpdoc.py` zerlegt es und verteilt die
  Abschnitte nach geschätzter Höhe auf die beiden Spalten.

## [0.6.8] - 2026-10-30

### Hinzugefügt
- Sensoren pausieren (Knopf an jedem gekoppelten Sensor): Die Bridge sucht einen pausierten
  Sensor nicht, verbindet ihn nicht und bietet ihn Zwift nicht an; die Kopplung bleibt erhalten.
  Gedacht für Sensoren, die gerade nicht genutzt werden, als Vorstufe zum Entfernen. Pausierte
  Sensoren erscheinen gedimmt mit „Pausiert“, auch in der Übersicht. Nutzt die vorhandene
  D-Bus-Methode `SetDeviceEnabled`.
- *Bei Problemen*: Einträge „Sensor gerade nicht in Gebrauch“ und „Zwift findet die Sensoren
  nicht“; Hilfe ergänzt.

### Geändert
- Gerätezeile: dritte Zeile nur noch „In Zwift: …“ (die Rolle zeigt das Symbol), Wertespalte
  etwas schmaler. „Verbindet …“ heißt in Hilfe und Problemliste jetzt wie in der Zeile
  „Sucht das Gerät …“.

## [0.6.7] - 2026-10-30

### Geändert
- Sensoren: links oben die Suche (*Sensoren in der Nähe*), darunter *Gekoppelte Sensoren*.
- Gerätezeilen mit festen Maßen (Übersicht und Sensoren): Name, Zustand und Rolle mit Zwift-Name
  je einzeilig, lange Fehlermeldungen gekürzt (vollständig im Tooltip zusammen mit einer
  Erklärung des Zustands); Messwerte in einer Spalte fester Breite mit zwei reservierten Zeilen,
  Zahl fett mit Einheit daneben, ohne Wert ein Strich. Vorher änderte sich die Höhe, sobald Werte
  kamen oder gingen oder der Zustand wechselte.
- Suchergebnisse: Signal als „stark/mittel/schwach“ mit dBm; bekannte Chip-Probleme als eine Zeile
  (`compat_short`), die ausführliche Warnung erscheint am gekoppelten Gerät.
- Texte der Sensorseite gestrafft (Bridge, Bluetooth-Adapter, Netz, Meldungen, Bei Problemen);
  die Adapterauswahl zeigt nur noch den Chip, die Adresse nur bei zwei gleichen Sticks.

## [0.6.6] - 2026-10-30

### Geändert
- Sensoren: *Bei Problemen* steht unter beiden Spalten über die volle Breite, die vier Fälle in
  zwei Spalten. Vorher blieb links unter der Suche eine Lücke, während rechts gescrollt werden
  musste.
- Über Tretlager: *Unfreie Software* in die linke Spalte, damit beide Spalten ähnlich lang sind.

## [0.6.5] - 2026-10-30

### Geändert
- Ein ausgeschalteter Bluetooth-Adapter gilt wie ein abgezogener als fehlend: Die Bridge
  weicht auf den Standardadapter aus und kehrt zurück, sobald er wieder an ist. Ist ein Adapter
  gewählt, prüft sie das alle zehn Sekunden (bisher nur, solange er fehlte).
- Lesbare Namen für Realtek-RTL8761B-Sticks, darunter TP-Link UB500.

### Geprüft
- Auf tinytin mit TP-Link UB500 (RTL8761BU) als zweitem Adapter: Umschalten im laufenden
  Betrieb, Ausschalten des Sticks (Rückfall auf AX201 nach etwa zehn Sekunden) und
  Wiedereinschalten. Der Garmin HRM-Pro Plus verbindet sich über den Stick und liefert Puls,
  am eingebauten AX201 hängt er weiter.

## [0.6.4] - 2026-10-30

### Geändert
- Einheitliches Seitengerüst für alle Seiten (`ColumnsPage.qml`, Vorbild Übersicht): Meldungen
  und Seitenkopf über die volle Breite, darunter zwei Spalten, auf schmalen Fenstern
  untereinander; überall dieselbe Breite (Fenster bis `gridUnit * 62`, darüber mittig). Vorher
  waren alle Seiten außer der Übersicht schmale Listen mit viel Leerraum links und rechts.
  - Sensoren: links Geräte und Suche, rechts Bridge-Einstellungen und Hilfe bei Problemen.
  - Assistent: Willkommen und Fertig mit Seitenkopf wie die Übersicht; Vorbereiten mit Paketen
    in der rechten Spalte; Anmeldung mit dem eigenen Browser als zweite Spalte.
  - Hilfe: jeder Abschnitt als Karte, auf zwei Spalten verteilt, die Tabelle darunter.
  - Über Tretlager: eigene Seite statt der schmalen Standardseite, Lizenztext im Dialog.
- Gemeinsame Bausteine `PageHero.qml` und `PageMessage.qml`; `PageContent.qml` entfällt.

### Behoben
- *Einrichtung prüfen* aus der Seitenleiste zeigte eine leere Liste, bis man *Erneut prüfen* wählte.

## [0.6.3] - 2026-10-30

### Hinzugefügt
- Bluetooth-Adapter der Sensor-Bridge wählbar (Sensoren → *Bluetooth-Adapter*), etwa ein
  USB-Stick mit Verlängerung neben dem Trainer oder als Ausweg bei einem Chip, der einen Sensor
  nicht verträgt. Gespeichert wird die Adresse des Adapters (`adapter` in `bridge.json`), nicht
  hciN, weil sich die Nummer beim Umstecken ändern kann. Fehlt der gewählte Adapter, nutzt die
  Bridge den Standardadapter, zeigt eine Warnung und wechselt von selbst zurück, sobald er wieder
  da ist. Neue D-Bus-Methode `SetAdapter`.
- Die Chip-Warnung bezieht sich auf den gewählten Adapter und nennt den USB-Stick als Abhilfe.

### Behoben
- Die Bridge nutzte fest `hci0`; ein zusätzlicher USB-Stick blieb ungenutzt.

## [0.6.2] - 2026-10-30

### Hinzugefügt
- Warnung bei bekannten Problemkombinationen aus Bluetooth-Chip und Sensor
  (`tretlager/core/btcompat.py`). Tretlager erkennt den Chip des Adapters an der USB-Kennung und
  gleicht ihn mit einer Liste geprüfter Fälle ab. Erster Eintrag: Garmin HRM-Pro am Intel AX201
  (auf tinytin hängt die Dienstsuche, am AX200 läuft der Gurt).
  - Suche: Der Treffer trägt ein Warnsymbol und den Hinweis, bevor er hinzugefügt wird.
  - Sensorseite: Warnung direkt am Gerät statt endlosem „Verbindet …“.
  - Übersicht: Warnung für eingeschaltete Geräte mit bekanntem Problem.
- Systemprüfung nennt den Bluetooth-Chip.
- Hilfe und Sensorseite: Eintrag „Gerät verbindet sich nie“.

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
