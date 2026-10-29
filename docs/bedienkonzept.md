# Bedienkonzept: vom leeren Rechner zum laufenden Zwift

Stand: 2026-10-29. Ziel ist TUXEDO OS auf Basis von Debian testing (forky) mit Plasma, so wie
auf tinytin. Grundlage sind die Tests in [FEASIBILITY.md](../FEASIBILITY.md); alle Zeiten und
Größen dort gemessen.

## 1. Leitlinien

1. **Ein Weg, keine Wahl, wo es keine braucht.** Tretlager entscheidet selbst, was sich messen
   lässt: GPU-Weg, Wine-Version, Fensterverhalten. Fragen gibt es nur bei echten Entscheidungen
   des Nutzers: Systemänderung, Anmeldeweg, Sensoren.
2. **Einmal Passwort, nicht fünfmal.** Alle Systemänderungen laufen gebündelt durch *einen*
   Helfer mit *einer* Polkit-Abfrage.
3. **Warten ist erlaubt, Rätseln nicht.** Lange Schritte (Download, Prefix) laufen ohne
   Zutun, mit echtem Fortschritt und Restzeit, nicht mit einem Balken, der bei 99 % hängt.
4. **Ehrlich sein.** Was unter Linux nicht geht (offizielle Anmeldung, ANT+), steht klar da, mit
   dem, was stattdessen möglich ist.
5. **Alltag = ein Knopf.** Nach der Einrichtung startet *ein* Klick Bridge, Updates, Anmeldung
   und Zwift in der richtigen Reihenfolge.

## 2. Was der Nutzer am Ende tut

| # | Handlung | Dauer |
|---|---|---|
| 1 | Tretlager installieren (Discover oder Doppelklick auf das .deb) | 1 min |
| 2 | Tretlager starten, *Einrichten* | – |
| 3 | Änderungen am System bestätigen, **einmal** Passwort | 1 min |
| 4 | warten: Wine, Komponenten, Zwift (ohne Zutun) | ca. 10 min |
| 5 | Anmeldeweg wählen, bei Zwift im Browser anmelden | 1 min |
| 6 | Trainer aufwecken, Gurt anlegen, Geräte übernehmen | 2 min |
| 7 | *Zwift starten*, in Zwift einmal koppeln | 2 min |

Gemessen auf tinytin: Wine-Pakete 289 MB, Prefix mit winetricks **297 s**, Zwift-Spiel 4,9 GB
in 1–2 min (Glasfaser), Gesamtbelegung etwa 10,5 GB (1,8 GB System, 8,6 GB Prefix).

## 3. Bezug von Tretlager

| Weg | Bewertung |
|---|---|
| **Debian-Paket `tretlager`** (Empfehlung) | passt zur Systemintegration: systemd-Benutzerdienst, Polkit-Aktion, BlueZ, avahi. Abhängigkeiten aus Debian: `python3-gi`, `gir1.2-adw-1`, `python3-bleak`, `avahi-daemon`, `bluez`, `osslsigncode`, `cabextract`. Wine kommt **nicht** als Abhängigkeit (nicht in forky), sondern im Assistenten |
| Eigene APT-Quelle (wie `pacman-repo` für Arch) | Updates automatisch über Discover; lohnt sich nach den ersten Nutzern |
| Aufnahme ins TUXEDO-Repo | bester Weg für TUXEDO-OS-Nutzer (eine Quelle, kein Fremdschlüssel); setzt Absprache voraus |
| Flatpak | ungeeignet: Polkit-Helfer, Systempakete, systemd-Benutzerdienst und Wine auf dem Host passen nicht in die Sandbox |

Nach der Installation: Startmenü-Eintrag **Tretlager** (Kategorie Spiele/Sport).

## 4. Erster Start: der Einrichtungsassistent

Ein Fenster mit Seiten (Adw.NavigationView bzw. Kirigami-Seitenstapel), oben die Schrittleiste:
*Prüfen → Vorbereiten → Zwift → Anmeldung → Sensoren → Fertig*. Jeder Schritt ist idempotent;
bricht der Nutzer ab oder fällt der Strom aus, setzt Tretlager beim nächsten Start dort fort.

### 4.1 Willkommen
- Ein Satz, was passiert: „Tretlager richtet Zwift auf diesem Rechner ein und verbindet deinen
  Trainer und Pulsgurt.“
- Was man braucht: Zwift-Konto, etwa 11 GB Platz, Internet, Trainer/Gurt mit Bluetooth.
- Hinweis klein, aber vorhanden: Zwift unterstützt Linux offiziell nicht; Tretlager nutzt Wine.
- Knopf **Los geht's**.

### 4.2 System prüfen (automatisch, ohne root, wenige Sekunden)
Liste mit Ampel, jede Zeile aufklappbar mit Details:

| Prüfung | Grün | Gelb (geht, mit Hinweis) | Rot (blockiert) |
|---|---|---|---|
| System | TUXEDO OS forky | anderes Debian testing | kein amd64 |
| Grafik | NVIDIA-Treiber geladen, GL-Test zeigt NVIDIA | nur Intel/AMD (Mesa): läuft, schwächer | kein OpenGL 3.1 |
| Hybrid-Grafik | erkannt → PRIME-Offload wird gesetzt | – | – |
| Secure Boot + NVIDIA | Modul geladen | – | Modul nicht geladen: Verweis auf TUXEDO-Anleitung, Tretlager ändert nichts |
| Bluetooth | Adapter an, BlueZ läuft | Adapter aus → Knopf *Einschalten* | kein Adapter: Sensoren später |
| Speicher | ≥ 15 GB frei | 11–15 GB | < 11 GB |
| Netzwerk | cdn.zwift.com, dl.winehq.org erreichbar | – | offline |
| Vorhandenes Zwift | – | Prefix gefunden → *Übernehmen* oder *Neu* | – |

Der GL-Test ist der aus T3 (`GLTest.exe`), läuft aber erst nach der Wine-Installation. Bis dahin
genügt sysfs/`nvidia-smi`; das Ergebnis wird in 4.4 nachgereicht.

### 4.3 System vorbereiten (eine Bestätigung, ein Passwort)
Seite *Diese Änderungen nehme ich am System vor*:
- Paketquelle **WineHQ** (dl.winehq.org, Schlüssel D43F…672F) hinzufügen
- Pakete installieren: `winehq-devel` *(getestete Version 11.20)* plus Abhängigkeiten, Download
  289 MB. Die genaue Liste kommt aus der APT-Simulation, vor der Bestätigung.
- **keine** i386-Architektur, kein Systemupgrade, keine Treiberänderung

Knopf **Ändern** → eine Polkit-Abfrage für `de.linuxundich.tretlager.setup`. Der Helfer ist ein
festes Skript ohne freie Parameter (Schlüssel prüfen, Quelle schreiben, `apt-get install` der
festen Liste, Ausgabe zeilenweise an die Oberfläche). Snapper legt auf TUXEDO OS ohnehin einen
Schnappschuss vor und nach APT an, darauf weist die Seite hin.

Warum nicht PackageKit: Es kann keine Fremdquelle mit Schlüssel anlegen (FEASIBILITY §2). Für
die reine Paketinstallation wäre es möglich; ein einziger Helfer ist aber einfacher und
erspart eine zweite Abfrage.

### 4.4 Zwift einrichten (ohne Zutun, ca. 10 min)
Eine Seite mit Schrittliste, der laufende Schritt mit Fortschritt und Restzeit:

1. Zwift-Installer laden (34 MB) und **Signatur prüfen** (Zwift, Inc., SSL.com-Kette,
   `osslsigncode`): ✔ mit Signierer in den Details
2. Wine-Umgebung anlegen (`~/.local/share/tretlager/prefix`, ohne Mono/Gecko)
3. Komponenten von Microsoft: Schriften, .NET 4.8, d3dcompiler, WebView2 (winetricks mit
   festgenageltem Commit; Hinweis auf Microsofts Lizenz)
4. Zwift-Launcher installieren
5. Spiel laden (4,9 GB, über den offiziellen Launcher im Hintergrund)
6. Grafik einrichten: GL-Test → GLX + PRIME-Offload bei Hybrid, `UseEGL=N`, `UseXRandR=N`;
   Ergebnis: „Zwift nutzt NVIDIA GeForce RTX 3050 Ti“

Fallen aus den Tests, die der Nutzer nie sehen soll:
- `cabextract` fehlt → ist Paketabhängigkeit
- Dialoge von Wine (`rundll32 … could not be started`) → kein Prefix-Wechsel zwischen
  Wine-Versionen, `WINEDLLOVERRIDES` setzen, Dialoge per `winedbg`-Abschaltung unterdrücken
- Versionsdatei heißt nach dem Laden `Zwift_ver_cur.<build>.xml`

### 4.5 Anmeldung (die eine heikle Stelle)
Ehrlich formuliert, zwei Karten nebeneinander:

| Karte | Inhalt |
|---|---|
| **Offizielle Anmeldung** | „Funktioniert unter Linux derzeit nicht.“ Kurzer Grund in den Details (Launcher 1.2 nutzt eine Windows-Funktion, die Wine fehlt). Tretlager prüft bei jedem Launcher-Update, ob sie wieder geht, und schaltet dann um. |
| **Anmeldung über den Browser** | „Du meldest dich auf der Zwift-Seite in deinem Browser an. Tretlager übernimmt danach die Sitzung.“ Darunter klar: „Zwift erlaubt keine fremden Programme an seiner Anmeldung (Nutzungsbedingungen §5). Du nutzt diesen Weg auf eigenes Risiko.“ Kontrollkästchen *Verstanden* + Knopf **Im Browser anmelden** |

Ablauf Browser-Anmeldung, einfacher als im Test:
- Statt Adresse kopieren: Tretlager registriert für die Dauer der Anmeldung einen eigenen
  Handler bzw. liest die Rücksprungadresse über ein kleines lokales Fenster aus. *(Zu prüfen:
  Der Rücksprung geht fest auf `launcher.zwift.com`; einfangen lässt er sich nur über die
  Zwischenablage. Fallback bleibt: „Adresse kopieren und hier einfügen“ mit Einfügefeld, das
  den Code sofort erkennt.)*
- Token nur im Schlüsselbund (KWallet/Secret Service), nie in Dateien oder Logs.
- Token gilt **6 h**, das Erneuerungs-Token **8 Tage**. Mit Erneuerung muss man sich nur
  anmelden, wenn man länger als eine Woche nicht fährt. *(Die Erneuerung nutzt dieselbe
  inoffizielle Schnittstelle; das gehört in denselben Hinweis.)*

Diese Seite hängt an Entscheidung **E2**; ohne Freigabe endet der Assistent hier mit
„Zwift ist installiert; Start derzeit nicht möglich“.

### 4.6 Sensoren
- Bridge-Dienst wird eingerichtet und gestartet (Benutzerdienst, kein root).
- Großer Hinweis: „Tritt kurz in die Pedale und leg den Pulsgurt an.“ Suche startet sofort.
- Gefundene Geräte mit Symbol und Rolle; Trainer und Gurt sind **vorausgewählt**, ein Knopf
  **Übernehmen**.
- Live-Werte direkt auf der Seite (Watt, U/min, bpm), damit der Nutzer sieht, dass es läuft.
- Diagnose aus den Tests eingebaut:
  - Puls unplausibel (RR-Intervalle springen) → „Elektroden anfeuchten, nur einen Gurt tragen“
  - Dienstsuche hängt (HRM-Pro Plus auf AX201) → „Gurt kurz abklipsen; bleibt es so, verträgt
    dein Bluetooth-Chip diesen Gurt nicht“
- *Überspringen* möglich (Zwift läuft auch ohne Sensoren im Zuschauermodus).

### 4.7 Fertig
- Zusammenfassung: Zwift-Version, Grafik, Anmeldung, Sensoren.
- Schalter **Sensor-Bridge beim Anmelden starten** (Standard: aus; Tretlager startet sie beim
  Zwift-Start ohnehin).
- Knopf **Zwift starten**. Zusätzlich landet ein Startmenü-Eintrag **Zwift** an, der denselben
  Startweg nimmt.
- Einmaliger Hinweis für Zwift: „Unter *Gekoppelte Geräte* „Wahoo KICKR …“ für Leistung,
  Trittfrequenz und Widerstand wählen, „Wahoo HRM …“ für Herzfrequenz. Die Warnungen zu
  Bluetooth und ANT+ in Zwift sind normal.“

## 5. Alltag: das Hauptfenster

```
┌───────────────────────────────────────────────┐
│ Tretlager                                  ☰  │
│                                               │
│          Bereit zum Fahren                    │
│     [        Zwift starten        ]           │
│                                               │
│  Sensoren   KICKR ● 0 W   TICKR ● 62 bpm      │
│  Zwift      1.124.0 · aktuell                 │
│  Grafik     NVIDIA RTX 3050 Ti                │
│  Anmeldung  gültig, Erneuerung in 7 Tagen     │
└───────────────────────────────────────────────┘
```

**Zwift starten** erledigt in dieser Reihenfolge, jeweils mit einer Statuszeile:
1. Bridge läuft? Sonst starten; Geräte verbunden? Sonst Hinweis „Trainer aufwecken“ (nicht
   blockierend).
2. Token gültig? Sonst erneuern; ist auch das abgelaufen → Browser-Anmeldung.
3. Update? `Zwift_ver_cur` lokal vs. CDN; wenn neu: Prefix-Schnappschuss (Btrfs-Reflink,
   0,4 s), Update über den Launcher (`SilentLaunch`), danach Version prüfen.
4. Zwift starten (Launcher im Hintergrund, Spiel als Kind), GLX + PRIME-Offload.
5. Fenster maximieren (KWin-Regel bzw. Fenstergröße), damit die Plasma-Leiste nichts verdeckt.
6. Nach dem Beenden: Launcher-Reste beenden, Bridge stoppen (falls nicht im Autostart),
   Bildschirmmodus prüfen.

Das Menü ☰ enthält: *Sensoren verwalten*, *Diagnose*, *Protokolle*, *Einstellungen*, *Über*.

## 6. Updates

| Was | Wie | Nutzer sieht |
|---|---|---|
| Zwift-Spiel | beim Start über den offiziellen Launcher | Statuszeile „Zwift wird aktualisiert (1.125.0)“ |
| Zwift-Launcher | ebenso; danach automatischer Test, ob die offizielle Anmeldung wieder geht | ggf. Hinweis „Offizielle Anmeldung funktioniert wieder“ |
| Wine | APT-Pinning auf die getestete Version; neue Versionen erst nach Freigabe in Tretlagers Versionsliste | „Wine 11.21 ist getestet, jetzt aktualisieren?“ |
| Tretlager | Debian-Paket über Discover | – |

Bei einem fehlgeschlagenen Update: **Zurück zum letzten funktionierenden Stand** (Reflink-
Schnappschuss des Prefix), statt Zwift neu zu installieren.

## 7. Wenn etwas schiefgeht

- Jede Fehlermeldung hat drei Teile: was passiert ist (ein Satz), was der Nutzer tun kann
  (Knopf), Details zum Aufklappen (Log-Auszug).
- **Reparieren** führt alle Schritte erneut aus; fertige Schritte werden nur geprüft.
- **Diagnosebericht exportieren** (Text, ohne Token und Konto-Daten) für Fehlermeldungen.
- Typische Fälle aus den Tests als feste Texte: Grafik nur Intel trotz NVIDIA, Bild verzerrt
  (Auflösungswechsel), Fenster unter der Leiste, Gurt-Probleme, Netzwechsel.

## 8. Oberfläche unter Plasma

TUXEDO OS forky läuft mit Plasma. GTK4/libadwaita funktioniert dort (siehe Bridge-Oberfläche),
sieht aber nach GNOME aus; eigene Symbole sind nötig, weil Breeze andere Namen hat. Empfehlung:
den Assistenten und das Hauptfenster als UI-freien Kern (Zustandsautomat, Schritte, Fortschritt
über D-Bus oder Python-API) bauen und zuerst die **Kirigami-Oberfläche** für Plasma umsetzen,
die GTK-Oberfläche danach. Das entspricht E4 und dem Vorgehen bei Stafette.

## 9. Technische Umsetzung des Ablaufs

- **Zustand:** `~/.local/state/tretlager/state.json` mit Schritt, Versionen (Wine, Launcher,
  Spiel, WebView2), Quelle und Prüfergebnis des Installers, Zeitstempeln.
- **Orte:** Prefix `~/.local/share/tretlager/prefix`, Schnappschüsse
  `~/.local/share/tretlager/snapshots/`, Cache `~/.cache/tretlager/` (Installer, winetricks).
- **Helfer:** `/usr/libexec/tretlager/setup-system` + Polkit-Aktion; feste Schritte, Rückgabe
  zeilenweise als JSON.
- **Versionsliste:** im Paket mitgeliefert, welche Kombination aus Wine, Launcher und Spiel
  getestet ist; unbekannte Kombinationen zeigt Tretlager als „ungetestet“ an.
- **Start-Logik:** aus `poc/token-login/start.sh` in den Kern (Python) übernehmen.

## 10. Offene Entscheidungen

- **E2 Anmeldung:** Browser-Anmeldung als ausdrückliche Option für Nutzer (mit Hinweis) – ja
  oder nein? Ohne sie endet die Einrichtung vor dem Start.
- **Bezug:** eigenes Debian-Paket mit eigener Quelle oder Anfrage bei TUXEDO?
- **Oberfläche zuerst:** Kirigami (Ziel Plasma) oder GTK (Auftrag)?
- **Wine-Politik:** feste getestete Version (Pinning) oder immer die aktuelle `winehq-devel`?
- **Name:** Arbeitstitel „Tretlager“.
