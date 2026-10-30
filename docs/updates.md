# Updates – Zwift und alles, was Tretlager mitbringt

Stand 2026-10-30. Grundsatz: **keine Schnappschüsse** (nicht jeder Rechner hat Btrfs, und eine
volle Kopie der Zwift-Umgebung kostet 7–9 GB). Stattdessen hat jede Abhängigkeit genau einen
Update-Weg, und Tretlager gleicht vor jedem Start ab, ob die Zwift-Umgebung zum installierten
Tretlager passt. Zurück geht es über Flatpak, nicht über Kopien.

## Bausteine und ihr Update-Weg

| Baustein | Woher | Wie er aktuell wird | Was Tretlager danach tut |
|---|---|---|---|
| Tretlager (Python, QML, Bridge) | eigenes Flatpak | `flatpak update` bzw. Discover/GNOME Software aus der eigenen Quelle (F4, bender, GPG) | laufende Bridge älterer Version neu starten (`restart_if_outdated`, nicht während einer Fahrt) |
| Wine 11.x | im Flatpak, aus den Quellen gebaut | nur mit einer neuen Tretlager-Version (Version im Manifest) | Abgleich vor dem Start: `wineboot -u`, Grafiktest wiederholen |
| cabextract, osslsigncode, bleak, dbus-fast, SecretStorage | im Flatpak, feste Version + Prüfsumme | nur mit einer neuen Tretlager-Version | – |
| KDE-Laufzeit 6.11, PySide-BaseApp 6.11 | Flathub | `flatpak update` (Fehlerbehebungen innerhalb 6.11); Wechsel auf 6.12 nur mit neuer Tretlager-Version | – |
| NVIDIA-Treiber in der Sandbox (`GL.nvidia-…`) | Flathub | Flatpak installiert die zum Systemtreiber passende Erweiterung selbst | – |
| winetricks | GitHub, fester Commit + SHA-256 im Code | nur mit einer neuen Tretlager-Version | – |
| Windows-Komponenten (.NET 4.8, WebView2, Schriften, d3dcompiler_47) | Microsoft u. a. über winetricks | neue oder andere Komponenten nur mit einer neuen Tretlager-Version (`VERBS`) | Abgleich installiert fehlende Komponenten |
| Zwift-Launcher und Spiel | Zwift | Zwift selbst: Tretlager startet vor jeder Fahrt den Launcher unsichtbar (`SilentLaunch`), wenn `Zwift_ver_cur.xml` eine neuere Version meldet | zeigt den Fortschritt (siehe unten), wartet bis zu 15 min, bis die Version auf der Platte steht, startet dann |
| Zwift-Sitzung (Token) | Zwift | Tretlager erneuert sie selbst (6 h Zugriff, 8 Tage Erneuerung) | sonst Anmeldung |

Wine und alles andere im Flatpak wird also **nie** hinter Tretlagers Rücken aktualisiert. Eine neue
Wine-Version kommt nur mit einer Tretlager-Version, die damit getestet ist. Das ersetzt die frühere
Regel E10 („immer die neueste winehq-devel“), die für das Debian-Paket galt.

## Vor jedem Start: Einrichtung abgleichen

`Launcher.reconcile()` führt alle Einrichtungsschritte aus `core/setup.py` aus. Jeder prüft mit
`done()` am echten System, ob er erledigt ist; im Normalfall dauert der Abgleich unter einer
Sekunde (keine Programme, nur Dateien und `wine --version`).

| Schritt | gilt als erledigt, wenn … | sonst |
|---|---|---|
| Installer | der Zwift-Launcher schon installiert ist (oder der geprüfte Installer im Cache liegt) | laden, Signatur prüfen |
| Wine-Umgebung | sie existiert **und** mit dem jetzigen Wine angelegt/angepasst wurde (`state.json` → `prefix.wine`) | `wineboot -u` (neues Wine) bzw. anlegen |
| Komponenten | alle Verben aus `VERBS` in `winetricks.log` des Präfixes stehen | fehlende über winetricks |
| Launcher | `ZwiftLauncher.exe` vorhanden | Installer ausführen |
| Spiel | `ZwiftApp.exe` und Versionsdatei vorhanden | über den Launcher laden (Reparatur) |
| Grafik | der Grafiktest mit dem jetzigen Wine gelaufen ist | Grafiktest |

Schlägt ein Schritt fehl, startet Zwift nicht, und die Übersicht zeigt den Satz des Schritts.

`wineboot -u` läuft mit `WINEDLLOVERRIDES="mscoree,mshtml="` und höchstens 5 Minuten: Ohne die
Variable öffnet Wine einen unsichtbaren Dialog zur Mono-/Gecko-Installation und wartet (auf tinytin
hing es so über 10 Minuten). Die Variable gilt nur für diesen Aufruf; .NET bleibt an.

Gemessen auf tinytin (30.10., vorgetäuschter Wechsel 11.19 → 11.20): Abgleich mit Anpassung und
Grafiktest, dann Zwift nach 47 s; normaler Start ohne Änderung: Zwift nach 16 s.

## Zurück, wenn ein Update etwas kaputt macht

- **Wine (in Tretlager):** Tretlager hebt genau eine Wine-Version auf, die zuletzt bewährte
  (`~/.var/app/de.linuxundich.Tretlager/data/tretlager/wine-bewaehrt`, gut 500 MB, `core/wine.py`).
  - Nach der ersten Fahrt (≥ 5 min) wird das mitgelieferte Wine kopiert.
  - Bringt ein Tretlager-Update ein neues Wine, bleibt die Kopie der alten Version stehen. In der
    Übersicht erscheint unter *Zwift* der Schalter *Vorige Wine-Version nutzen*; der Abgleich passt
    die Zwift-Umgebung dann an die alte Version an (`wineboot -u`, Grafiktest).
  - Nach zwei Fahrten mit dem neuen Wine gilt es als bewährt und ersetzt die Kopie. Fahrten mit der
    alten Version zählen dafür nicht.
  - Kommt mit dem nächsten Tretlager-Update wieder ein anderes Wine, schaltet Tretlager zurück auf
    das mitgelieferte (es kann das Problem beheben).

- **Tretlager/Wine:** `flatpak remote-info --log tretlager-origin de.linuxundich.Tretlager` zeigt die
  Versionen, `flatpak update --commit=<ältere> de.linuxundich.Tretlager` holt die vorige zurück
  (mit ihrem Wine), `flatpak mask de.linuxundich.Tretlager` hält sie fest. Der Abgleich passt die
  Zwift-Umgebung dann wieder an die ältere Wine-Version an.
- **Zwift:** Ein Zurück gibt es nicht und braucht es nicht – Zwift lässt nur mit der aktuellen
  Version fahren. Ist die Zwift-Umgebung kaputt, legt *Einrichtung prüfen* sie neu an; nur das
  Spiel (≈ 5 GB) wird dann erneut geladen.

## Fortschritt beim Zwift-Update und bei der Erstinstallation

`Zwift_ver_cur.xml` nennt das Manifest der neuen Version (`Zwift_<Version>_<Hash>_manifest.xml`,
gleicher Ordner beim CDN, ≈ 5 MB, ≈ 20 000 Dateien mit Pfad und Größe). Tretlager vergleicht es
mit dem Zwift-Ordner: Fehlende oder anders große Dateien ergeben die Menge, die zu laden ist.
Der Launcher lädt zuerst in einen Zwischenordner (`drive_c/users/<Name>/AppData/Local/Temp/Zwift/Downloads`)
und verschiebt am Ende alles auf einmal in den Zwift-Ordner. Tretlager zählt deshalb alle 3 s
beides: was im Zwischenordner liegt (ohne Reste eines abgebrochenen Ladens) und was schon fertig
im Zwift-Ordner angekommen ist, und zeigt „… 1,2 von 3,4 GB“ mit Fortschrittsbalken (höchstens 99 %,
bis die Versionsdatei wechselt). Ohne Manifest (offline, anderes Format) bleibt es bei der Zeit: „seit 3 Minuten“.
Gleich große, geänderte Dateien zählt das nicht mit; die Anzeige ist ein Richtwert.

Dasselbe gilt für die Erstinstallation (Einrichtungsschritt *Zwift laden*, `setup.Game`): Statt
geschätzter 4,9 GB zeigt sie die Größe laut Manifest. Ohne Manifest schätzt sie wie bisher über
die Größe des Zwift-Ordners („etwa“). Gemeinsamer Code in `core/manifest.py`.

Auf tinytin geprüft (30.10.): mit der aktuellen Version 0 von 19 903 Dateien fehlend, Abgleich 1 s;
bei einer echten Erstinstallation 0 → 99 % gleichmäßig in 9 Minuten (5,1 GB, ≈ 10 MB/s). Ohne den
Zwischenordner stand die Anzeige 9 Minuten bei 0 % und sprang dann auf 99 %. Ein echtes
Zwift-Update ist noch nicht erschienen; es läuft über denselben Launcher und Zwischenordner.

## Ablauf für eine neue Tretlager-Version

1. Version in `tretlager/__init__.py` und CHANGELOG anheben (sonst startet die Bridge nach dem Update
   nicht neu), Metainfo-`<release>` ergänzen.
2. Wine anheben (optional): URL und SHA-256 im Manifest; auf tinytin bauen.
3. Auf tinytin: Abgleich mit bestehender Umgebung (Wine-Anpassung, Grafiktest), Zwift starten,
   kurze Fahrt mit Trainer und Puls, Zwift-Update falls gerade eins ansteht.
4. In die Flatpak-Quelle auf bender veröffentlichen (F4).

## Offen

- [ ] Tretlager meldet selbst, wenn eine neue Version bereitsteht (Flatpak-Portal
  `CreateUpdateMonitor` / `Update`) – bewusst offen, Verteilung über Flathub ist nicht geplant.
- [x] Fortschritt beim Zwift-Update aus dem Manifest (bei einem echten Update beobachten).
- [x] Vorige Wine-Version aufbewahren (eine) und wählbar.
- [ ] Eine Windows-Komponente gezielt erneuern (z. B. neuere WebView2), wenn Zwift sie verlangt:
  Revisionsmarke je Verb, dann `winetricks --force <verb>` im Abgleich.
- [ ] Flatpak-Quelle auf bender mit GPG (F4), erst dann gibt es `flatpak update` für Tretlager.
