## Was Tretlager macht

Tretlager richtet den offiziellen Windows-Client von **Zwift** auf diesem Rechner ein und startet
ihn mit einem Klick. Zwift läuft dabei unter **Wine**. Weil Zwift unter Wine kein Bluetooth
nutzen kann, verbindet die **Sensor-Bridge** deinen Smart-Trainer und Pulsgurt und bietet sie
Zwift als Wahoo-„Direct Connect“-Geräte an. Die Zwift Companion App brauchst du dafür nicht.

Zwift unterstützt Linux offiziell nicht. Tretlager lädt Zwift nur von der offiziellen Quelle,
prüft die Signatur des Installers und verändert an Zwift selbst nichts.

## Einrichtung

Der Assistent führt in sechs Schritten durch alles:

1. **Prüfen** – Grafik, Bluetooth, Speicher und Internet; ändert nichts.
2. **Vorbereiten** – richtet die WineHQ-Paketquelle ein und installiert Wine. Vorher siehst
   du jede Änderung; du gibst einmal dein Passwort ein.
3. **Zwift** – lädt und installiert Zwift samt den nötigen Microsoft-Komponenten, etwa
   10 Minuten ohne dein Zutun. Abbrechen ist jederzeit möglich; beim nächsten Start geht es
   dort weiter.
4. **Anmeldung** – siehe unten.
5. **Sensoren** – Trainer aufwecken (kurz treten), Pulsgurt anlegen, Geräte übernehmen.
6. **Fertig**.

## Alltag

- Im Startmenü startet **Zwift (Tretlager)** Zwift direkt, ohne Umweg über das Hauptfenster.
- Im Hauptfenster startet **Zwift starten** dasselbe. Die Sensor-Bridge läuft schon an, sobald
  Tretlager geöffnet ist, damit Trainer und Gurt bereit sind, wenn du aufs Rad steigst.
- Vor dem Start prüft Tretlager auf ein Zwift-Update und legt vorher eine Sicherung der
  Zwift-Umgebung an.
- Während Zwift läuft, legt sich Tretlager in die Taskleiste; nach dem Beenden räumt es auf.

## Sensoren in Zwift koppeln

Einmalig in Zwift unter **Gekoppelte Geräte**:

- **Leistungsquelle**, **Trittfrequenz** und **Widerstand**: „Wahoo KICKR …“
- **Herzfrequenz**: „Wahoo HRM …“

Die Warnsymbole für Bluetooth und ANT+ oben rechts in Zwift sind normal.

## Anmeldung

Die Anmeldung im Zwift-Launcher funktioniert unter Linux derzeit nicht. Ersatzweise meldest du
dich im Browser bei Zwift an; Tretlager übernimmt danach die Sitzung. **Zwift erlaubt keine
fremden Programme an seiner Anmeldung (Nutzungsbedingungen, Abschnitt 5). Du nutzt diesen Weg
auf eigenes Risiko.**

- Dein Passwort gibst du nur auf der Zwift-Seite ein, nie in Tretlager.
- Die Sitzung liegt im Schlüsselbund deines Benutzerkontos und wird selbst erneuert. Nach einer
  Woche ohne Fahrt meldest du dich neu an.
- **Abmelden** (Hauptfenster → Menü → Neu anmelden) beendet die Sitzung auch bei Zwift.

## Wenn etwas nicht klappt

| Problem | Abhilfe |
|---|---|
| Pulswerte viel zu hoch | Elektroden des Gurts anfeuchten, Gurt enger, nur einen Gurt tragen |
| Gerät bleibt bei „verbinde …“ | Trainer kurz treten, Gurt kurz abklipsen; Tretlager sucht alle 10 s |
| Zwift findet die Sensoren nicht | Hauptfenster → Sensoren: läuft die Bridge, sind die Geräte „verbunden“? |
| Bild unscharf unter Plasma | Systemeinstellungen → Anzeige → Legacy-Anwendungen (X11): *Skalierung selbst anwenden* |
| „Sitzung abgelaufen“ | Im Hauptfenster *Anmelden* wählen und im Browser neu anmelden |
| Zwift startet nach einem Update nicht | Menü → Einrichtung prüfen; die Sicherung vor dem Update bleibt erhalten |

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
