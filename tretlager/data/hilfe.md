## Überblick
<!-- icon: help-about -->

Tretlager richtet Zwift unter Linux ein, startet es mit einem Klick und verbindet Trainer und
Pulsgurt.

- **Zwift unter Wine**: Der offizielle Windows-Client von Zwift läuft unter Wine, das Tretlager
  mitbringt. Tretlager lädt Zwift von Zwift, prüft die Signatur und verändert nichts daran.
- **Sensor-Bridge**: Zwift kann unter Wine kein Bluetooth. Die Bridge verbindet Trainer und
  Pulsgurt und bietet sie Zwift als Wahoo-Geräte an; die Companion App ist nicht nötig.
- **Kein Programm von Zwift**: Zwift unterstützt Linux nicht. Die Benutzung erfolgt auf eigene
  Gefahr.

## Fahren
<!-- icon: media-playback-start -->

- **Zwift starten**: In der Übersicht oder im Startmenü unter *Zwift (Tretlager)*.
- **Vor dem Start**: Tretlager sucht nach Zwift-Updates und sichert vorher die Zwift-Umgebung.
- **Während der Fahrt**: Tretlager wartet minimiert und räumt nach dem Beenden auf.
- **Auf dem Notebook**: Netzteil vor dem Start anschließen und angeschlossen lassen. Ein Wechsel
  zwischen Netz und Akku kann den NVIDIA-Treiber zum Absturz bringen.

## Sensoren
<!-- icon: network-bluetooth -->

- **In Tretlager koppeln**: Unter *Sensoren* suchen und hinzufügen. Vorher kurz in die Pedale
  treten; ein Pulsgurt sendet nur mit Hautkontakt.
- **In Zwift koppeln**: Einmalig unter *Gekoppelte Geräte* „Wahoo KICKR …“ für Leistung,
  Trittfrequenz und Widerstand wählen, „Wahoo HRM …“ für den Puls. Die Warnsymbole für Bluetooth
  und ANT+ sind normal.
- **Pausieren**: Sensoren, die gerade nicht genutzt werden, pausieren statt entfernen. Tretlager
  sucht dann nicht mehr danach, die Kopplung bleibt erhalten.
- **Bluetooth-Adapter**: Ein USB-Stick mit Verlängerung neben dem Trainer hilft bei Funklöchern
  und bei Chips, die einen Sensor nicht vertragen.

## Anmeldung
<!-- icon: user-identity -->

Der Zwift Launcher kann sich unter Linux derzeit nicht anmelden. Tretlager öffnet die
Anmeldeseite von Zwift deshalb in einem eigenen Fenster. **Zwift erlaubt das nicht
(Nutzungsbedingungen, Abschnitt 5); die Nutzung erfolgt auf eigenes Risiko.**

- **Passwort**: Nur auf der Seite von Zwift eingeben. Tretlager liest und speichert es nicht.
- **Eigener Browser**: Für Passwortmanager oder die Anmeldung über Google oder Apple. Der Browser
  zeigt danach „Bad Request“; die Adresse kopieren, Tretlager übernimmt sie.
- **Sitzung**: Liegt im Schlüsselbund und erneuert sich selbst. Nach einer Woche ohne Fahrt ist
  eine neue Anmeldung nötig.
- **Abmelden**: Übersicht → *Neu anmelden …* → *Abmelden*. Das beendet die Sitzung auch bei Zwift.

## Datenschutz und Speicherorte
<!-- icon: security-high -->

- **Keine Nutzungsdaten**: Tretlager verbindet sich nur mit Zwift, GitHub (winetricks) und Microsoft
  (Komponenten über winetricks). Zwift selbst sendet Absturzberichte an Sentry.
- **Alles an einem Ort**: `~/.var/app/de.linuxundich.Tretlager/` – Zwift-Umgebung und Sicherungen
  unter `data/tretlager`, Einstellungen der Bridge unter `config/tretlager`, Zwischenspeicher unter
  `cache/tretlager`.
- **Entfernen**: Mit Tretlager verschwindet das Programm; die Zwift-Umgebung (etwa 9 GB) bleibt, bis
  der Ordner gelöscht wird (`flatpak uninstall --delete-data de.linuxundich.Tretlager`).

## Einrichtung
<!-- icon: configure -->

- **1. Prüfen**: Grafik, Bluetooth, Geräte-Ankündigung, Speicher und Internet. Am System ändert
  sich nichts, ein Passwort ist nicht nötig.
- **2. Zwift**: Download und Installation, etwa zehn Minuten. Abbrechen geht jederzeit, beim
  nächsten Start geht es an derselben Stelle weiter.
- **3.–5. Anmeldung, Sensoren, Fertig**: Siehe die Abschnitte oben.

## Wenn etwas nicht klappt
<!-- icon: help-hint; wide -->

- [emblem-important] **Puls viel zu hoch**: Elektroden anfeuchten, Gurt enger stellen und nur
  einen Gurt tragen.
- [view-refresh] **Sensor bleibt bei „Sucht das Gerät …“**: Kurz in die Pedale treten oder den
  Gurt kurz abklipsen; die Bridge sucht alle zehn Sekunden.
- [data-warning] **Sensor wird gefunden, verbindet sich aber nie**: Er verträgt den
  Bluetooth-Chip nicht; bekannte Fälle meldet Tretlager am Sensor. Abhilfe: USB-Bluetooth-Stick.
- [network-wireless-disconnected] **Verbindung bricht oft ab**: Rechner näher an den Trainer
  stellen oder einen USB-Bluetooth-Stick mit Verlängerung neben den Trainer legen.
- [network-bluetooth] **Zwift findet die Sensoren nicht**: Unter *Sensoren* prüfen, ob die Bridge
  läuft und die Sensoren verbunden sind; ohne laufendes Avahi (`avahi-daemon`) findet Zwift sie nicht.
- [battery-low] **Zwift hängt nach dem Ab- oder Anstecken des Netzteils**: Mit Alt+F4 beenden und
  mit Netzteil neu starten; hilft das nicht, den Rechner neu starten.
- [video-display] **Bild unscharf unter Plasma**: *Systemeinstellungen* → *Anzeige* →
  *Legacy-Anwendungen (X11)* → *Skalierung selbst anwenden*.
- [update-none] **Zwift startet nach einem Update nicht**: Seitenleiste → *Einrichtung prüfen*.
  Die Sicherung vor dem Update bleibt erhalten.
