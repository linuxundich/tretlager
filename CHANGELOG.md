# Changelog

Alle wichtigen Änderungen an Tretlager. Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

### Hinzugefügt
- Dezente Silhouette einer Radgruppe hinter dem Seitenkopf von Übersicht und Willkommensseite:
  drei Tonstufen aus einem Foto (`build-aux/make-backdrop.py`), in der Textfarbe des Farbschemas
  mit 7–9 % Deckkraft, passt zu Hell und Dunkel.

## [0.9.0] - 2026-10-30

QA-Audit (`docs/qa-audit-2026-10-30.md`), Update-Plan ohne Schnappschüsse (`docs/updates.md`),
überarbeitete Übersicht und Hinweis „Nicht für Rennen“.

### Geändert
- Programmsymbol mit silbernen Kettenblättern und dunkler Kante: Das frühere, ganz dunkle Symbol war
  auf einem dunklen Plasma-Panel kaum zu erkennen.
- Updates ohne Schnappschüsse (Plan in `docs/updates.md`): Vor jedem Start gleicht Tretlager die
  Einrichtung ab. Nach einem Tretlager-Update mit neuem Wine passt `wineboot -u` die
  Zwift-Umgebung an, und der Grafiktest läuft erneut; fehlende Windows-Komponenten oder Teile von
  Zwift werden nachinstalliert. Der Schnappschuss vor Zwift-Updates entfällt (kostete ohne Btrfs
  eine volle Kopie von 7–9 GB), alte Schnappschüsse werden gelöscht. Den Installer lädt Tretlager
  nicht mehr erneut, wenn der Zwift-Launcher schon installiert ist; installierte Komponenten liest
  es direkt aus `winetricks.log` (2 s schneller).
- Hilfe „Puls viel zu hoch“: zusätzlich der Tipp, die Batterie des Gurts zu wechseln.
- Hinweis „Nicht für Rennen“: Es gibt keine Garantie, dass die Sensor-Bridge Leistung, Trittfrequenz
  und Puls korrekt an Zwift weitergibt; an Rennen und Wettbewerben mit Wertung nicht mit Tretlager
  teilnehmen. Steht in der Übersicht unter *Zwift starten*, auf der Willkommensseite, unter
  *Über Tretlager*, in der Hilfe, im README und in den Metadaten.
- Übersicht sportlicher gewichtet: *Zwift starten* als großer, einziger hervorgehobener Knopf (hat
  den Tastaturfokus), Messwerte der Sensoren als Kennzahlen (große Ziffer, Einheit darunter).
- Übersicht: „Bereit zum Fahren“ nur, wenn alle eingeschalteten Sensoren verbunden sind, sonst
  „Fast bereit“ mit den noch gesuchten Sensoren.
- Verständliche Fehlertexte statt BlueZ-/D-Bus-Meldungen an Sensoren und Bridge; Rohtext ins
  Protokoll.
- Während der Fahrt und bei minimiertem Fenster fragt die Oberfläche die Bridge nur alle 15 s ab
  (Oberfläche während der Fahrt 0,4 % CPU).
- Übrige Texte der Einrichtung übersetzt; Debian-Hinweis auf der Sensorseite entfernt.
- README: Voraussetzungen, Aktualisieren, Deinstallieren, Datenorte, Netzverbindungen,
  Fehlerbehebung, bekannte Grenzen.

### Hinzugefügt
- Fortschritt beim Zwift-Update und bei der Erstinstallation: Tretlager liest das Manifest der
  Zwift-Version, vergleicht es mit dem Zwift-Ordner und zeigt „… 1,2 von 3,4 GB“ mit
  Fortschrittsbalken (`core/manifest.py`); ohne Manifest die Dauer bzw. wie bisher eine Schätzung.
- Vorige Wine-Version: Tretlager hebt die zuletzt bewährte Wine-Version auf (genau eine, ≈ 500 MB).
  Nach einem Tretlager-Update mit neuem Wine startet *Vorige Wine-Version nutzen* in der Übersicht
  Zwift wieder mit der alten; nach zwei Fahrten mit dem neuen Wine ersetzt es die Kopie.
- Kurzes Protokoll der Oberfläche (`core/applog.py`, `$XDG_STATE_HOME/tretlager/tretlager.log`):
  Start, zweite Aufrufe, Zwift läuft/beendet, Schließen, Beenden – für die Fehlersuche, ohne Token.
- Schließen während einer Fahrt nur nach Rückfrage: Im Flatpak läuft Zwift in derselben Instanz und
  endet mit dem Fenster.

### Behoben
- Kurze Bluetooth-Abbrüche: Die Bridge hält das Gerät 45 s lang für Zwift angekündigt und die
  Verbindung zu Zwift offen; nach dem Wiederverbinden fließen die Daten weiter, ohne dass Zwift das
  Gerät neu suchen muss (auf tinytin mit künstlich getrenntem KICKR geprüft: 17 s Pause, Verbindung
  blieb). Vorher verschwand das Gerät bei jedem Abbruch aus Zwift.
- Einrichtung: Abbrechen und Zeitlimit greifen auch, wenn ein Programm stumm hängt.
- Bridge: Liest Zwift nicht mehr, verwirft sie Messwerte, statt den Sendepuffer wachsen zu lassen.
- Ein abwesender Sensor (Gurt nicht angelegt) blockierte Bluetooth bis zu 40 s pro Versuch: Die
  Suche in der Oberfläche dauerte 40–63 s statt 3 s, und ein anderer Sensor, der neu verbinden
  wollte, fiel bis zu einer Minute aus. Die Bridge sucht die Adresse jetzt höchstens 8 s, getrennt
  vom Verbindungsaufbau (QA-Audit B-01, `docs/qa-audit-2026-10-30.md`).
- Ende der Fahrt: Tretlager erkennt Zwift über `/proc` (argv[0]) statt alle 5 s `wine tasklist`
  zu starten; ein Fehler beim Nachsehen beendet die Überwachung nicht mehr (sonst hing die
  Oberfläche bei „Zwift läuft“). Auch bei unerwarteten Startfehlern wird aufgeräumt.
- Ohne Internet und mit abgelaufenem Zugriffstoken verlangte Tretlager eine neue Anmeldung; jetzt
  heißt es, dass die Zwift-Anmeldung nicht erreichbar ist.
- Ohne laufenden Schlüsselbund blieb die Anmeldeseite beim Laden stehen; jetzt eine Meldung.
- Eine beschädigte `bridge.json` verhinderte den Start der Bridge; sie wird als `bridge.defekt`
  beiseitegelegt.
- Einzelinstanz nimmt Befehle nur noch vom eigenen Benutzer an (`SO_PEERCRED`).
- Bridge lief nach dem Schließen weiter, wenn das Fenster vor dem Aufräumen nach der Fahrt zuging:
  Tretlager stoppt sie jetzt auch beim Beenden (außer im Autostart oder während Zwift läuft).
- Systemprüfung im Flatpak meldete zu wenig freien Speicher (17 statt 900 GB auf tinytin): Sie maß
  `~`, das in der Sandbox ohne Freigabe nur ein kleines tmpfs ist. Gemessen wird jetzt der
  Datenordner (`XDG_DATA_HOME`), in dem die Zwift-Umgebung liegt.

## [0.8.0] - 2026-10-30

Erste Version als Flatpak (`build-aux/flatpak/de.linuxundich.Tretlager.yml`); das Debian-Paket ist
eingestellt. Plan und Testergebnisse in `docs/flatpak.md`.

### Hinzugefügt
- Flatpak mit eigenem Wine 11.20 (aus den Quellen als WoW64 gebaut, mingw-w64), cabextract,
  osslsigncode und den Python-Paketen als feste Wheels (`gen-python-deps.py`); Laufzeit KDE 6.11
  mit PySide-BaseApp 6.11. Bauen auf tinytin: `build-aux/flatpak/build.sh`.
- Sensor-Bridge per D-Bus-Aktivierung (`de.linuxundich.Tretlager.Bridge.service`): eigene Instanz,
  läuft unabhängig vom Fenster; neue D-Bus-Methode `Quit`; die Bridge meldet ihre Version, und
  Tretlager startet eine ältere laufende Bridge nach einem Update neu (solange Zwift nicht läuft).
- *Beim Anmelden starten* über das Background-Portal.
- Systemprüfung „Geräte-Ankündigung“: ohne Avahi findet Zwift die Sensoren nicht.

### Geändert
- Bridge-Steuerung, Adapterliste und Bluetooth-Prüfung über `gdbus` statt `busctl`/`systemctl`
  (beides fehlt in der Sandbox).
- Assistent im Flatpak ohne *Vorbereiten* (Wine ist im Paket): fünf Schritte, die Nummern ergeben
  sich aus der Schrittkennung.
- Systemprüfung: Betriebssystem aus `/run/host/os-release` und nur angezeigt, nicht mehr als
  „Zielsystem“ bewertet; NVIDIA-Treiber auch aus `/proc/driver/nvidia/version`; Wine „im Flatpak
  enthalten“.
- Wine-DPI liest `~/.config/kwinrc` auch aus dem Flatpak (Freigabe nur lesend).
- Hilfe: Speicherorte unter `~/.var/app/de.linuxundich.Tretlager/`, Einrichtung in fünf Schritten.

### Behoben
- Zwift-Fenster im Flatpak nicht maximiert (unten abgeschnitten): Das KWin-Skript lag im privaten
  `/tmp` der Sandbox, das KWin nicht sieht. Es liegt nun in `$XDG_RUNTIME_DIR/app/<App-ID>`.

### Entfernt
- Flatpak-Spike aus F0 (`build-aux/flatpak/spike/`), ersetzt durch das echte Manifest.

## [0.7.1] - 2026-10-30

### Hinzugefügt
- Wine-Fenster in Bildschirmgröße auf HiDPI (`core/display.py`): Tretlager setzt
  `HKCU\Control Panel\Desktop\LogPixels` auf 96 × Skalierung, nach dem Anlegen der
  Wine-Umgebung, beim Fortsetzen der Einrichtung und vor jedem Start (nur bei Abweichung).
  Die Skalierung kommt aus KWins XWayland-Einstellung (`kwinrc`, `[Xwayland] Scale`), sonst aus
  der Fensterskalierung der Oberfläche; `TRETLAGER_DPI` erzwingt einen Wert. Auf tinytin (1,6×)
  nun 154 statt 96; Zwift startet damit unverändert.

## [0.7.0] - 2026-10-30

### Hinzugefügt
- Englische Oberfläche. Übersetzung per gettext (Domain `tretlager`, `tretlager/i18n.py`):
  Deutsch bleibt Quellsprache, ohne deutsche Systemsprache erscheint Englisch;
  `TRETLAGER_LANG` erzwingt eine Sprache. Alle 382 Texte aus QML (`i18n()`, verkettete Texte als
  Platzhalter `%1`) und Python (`_()`, Statusmeldungen, Fehler, Systemprüfung, Einrichtung,
  Anmeldung, Bridge-Zustände) sind übersetzt, dazu die Hilfe (`hilfe.en.md`) und die
  Desktop-Dateien. Die Zwift-Anmeldeseite erscheint in der Sprache der Oberfläche.
- `build-aux/msgfmt.py`: übersetzt Kataloge ohne gettext (fehlt auf tinytin); `po/update.sh`
  sammelt Texte und gleicht Kataloge ab; Test auf Vollständigkeit und Platzhalter.

### Geändert
- Anmeldeseite: Der Satz, Tretlager prüfe nach jedem Launcher-Update die offizielle Anmeldung,
  ist gestrichen – diese Prüfung gibt es nicht. Der Hilfetext zur Anmeldung in der Übersicht
  nennt das eigene Anmeldefenster statt des Browsers.

### Geprüft
- Eingebettete Anmeldung mit echten Zugangsdaten (Christoph, 30.10.).

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
