## Was Tretlager macht

Tretlager richtet den offiziellen Windows-Client von **Zwift** auf diesem Rechner ein und startet
ihn mit einem Klick. Zwift läuft dabei unter **Wine**. Weil Zwift unter Wine kein Bluetooth
nutzen kann, verbindet die **Sensor-Bridge** Smart-Trainer und Pulsgurt und bietet sie Zwift als
Wahoo-Geräte mit „Direct Connect“ an. Die Zwift Companion App ist dafür nicht nötig.

Zwift unterstützt Linux offiziell nicht. Tretlager lädt Zwift nur von der offiziellen Quelle,
prüft die Signatur des Installers und verändert an Zwift selbst nichts.

## Einrichtung

Der Assistent führt in sechs Schritten durch alles:

1. **Prüfen**: Grafik, Bluetooth, Speicher und Internet. Am System ändert sich nichts.
2. **Vorbereiten**: richtet die WineHQ-Paketquelle ein und installiert Wine. Alle Änderungen
   stehen vorher in einer Liste; das Passwort ist nur einmal nötig.
3. **Zwift**: lädt und installiert Zwift samt den nötigen Microsoft-Komponenten. Das dauert etwa
   zehn Minuten und läuft von selbst. Abbrechen ist jederzeit möglich, beim nächsten Start geht
   es an derselben Stelle weiter.
4. **Anmeldung**: siehe unten.
5. **Sensoren**: Trainer aufwecken (kurz in die Pedale treten), Pulsgurt anlegen, Geräte
   hinzufügen.
6. **Fertig**.

## Alltag

- Im Startmenü startet *Zwift (Tretlager)* Zwift direkt, ohne Umweg über die Übersicht.
- In der Übersicht startet *Zwift starten* dasselbe. Die Sensor-Bridge läuft schon an, sobald
  Tretlager geöffnet ist, damit Trainer und Gurt beim Aufsteigen bereit sind.
- Vor dem Start sucht Tretlager nach einem Zwift-Update und sichert vorher die Zwift-Umgebung.
- Während Zwift läuft, ist Tretlager minimiert; nach dem Beenden räumt es auf.

## Sensoren in Zwift koppeln

Einmalig in Zwift unter *Gekoppelte Geräte*:

- *Leistungsquelle*, *Trittfrequenz* und *Widerstand*: „Wahoo KICKR …“
- *Herzfrequenz*: „Wahoo HRM …“

Die Warnsymbole für Bluetooth und ANT+ oben rechts in Zwift sind normal.

## Anmeldung

Die Anmeldung im Zwift Launcher funktioniert unter Linux derzeit nicht. Ersatzweise öffnet
Tretlager die Anmeldeseite von Zwift in einem eigenen, privaten Fenster und übernimmt danach die
Sitzung. **Zwift erlaubt keine fremden Programme an seiner Anmeldung (Nutzungsbedingungen,
Abschnitt 5). Die Nutzung dieses Wegs erfolgt auf eigenes Risiko.**

- E-Mail und Passwort werden nur auf der Anmeldeseite von Zwift eingegeben. Tretlager liest
  und speichert sie nicht; das Fenster vergisst alles beim Schließen.
- Liegt das Passwort im Passwortmanager des Browsers oder läuft die Anmeldung über Google oder
  Apple, gibt es *Im eigenen Browser anmelden*. Der Browser zeigt danach „Bad Request“; die
  Adresse aus der Adresszeile kopieren, Tretlager übernimmt sie aus der Zwischenablage.
- Die Sitzung liegt im Schlüsselbund des Benutzerkontos und erneuert sich selbst. Nach einer
  Woche ohne Fahrt ist eine neue Anmeldung nötig.
- *Abmelden* (Übersicht → *Neu anmelden …*) beendet die Sitzung auch bei Zwift.

## Wenn etwas nicht klappt

| Problem | Abhilfe |
|---|---|
| Pulswerte viel zu hoch | Elektroden des Gurts anfeuchten, Gurt enger stellen, nur einen Gurt tragen |
| Gerät bleibt bei „Verbindet …“ | Kurz in die Pedale treten, Gurt kurz abklipsen; die Bridge sucht alle zehn Sekunden |
| Verbindung bricht oft ab | Rechner näher an den Trainer stellen oder USB-Bluetooth-Stick mit Verlängerung nutzen |
| Zwift findet die Sensoren nicht | Seitenleiste → *Sensoren*: Läuft die Bridge, sind die Geräte verbunden? |
| Bild unscharf unter Plasma | *Systemeinstellungen* → *Anzeige* → *Legacy-Anwendungen (X11)*: *Skalierung selbst anwenden* |
| Sitzung abgelaufen | In der Übersicht *Anmelden …* wählen und im Browser neu anmelden |
| Zwift startet nach einem Update nicht | Seitenleiste → *Einrichtung prüfen*; die Sicherung vor dem Update bleibt erhalten |

## Datenschutz

Tretlager sendet keine Nutzungsdaten. Verbindungen gehen nur zu Zwift (Download, Anmeldung,
Updates), zu WineHQ und zu Microsoft (Komponenten über winetricks). Zwift selbst schreibt
Absturzberichte (Sentry); das liegt außerhalb von Tretlager.

## Wo Tretlager Daten ablegt

- Zwift-Umgebung: `~/.local/share/tretlager/prefix`
- Sicherungen vor Updates: `~/.local/share/tretlager/snapshots`
- Zwischenspeicher (Installer, winetricks): `~/.cache/tretlager`
- Einstellungen der Bridge: `~/.config/tretlager/bridge.json`
- Zustand der Einrichtung: `~/.local/state/tretlager/state.json`
