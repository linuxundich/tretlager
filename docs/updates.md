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
| Zwift-Launcher und Spiel | Zwift | Zwift selbst: Tretlager startet vor jeder Fahrt den Launcher unsichtbar (`SilentLaunch`), wenn `Zwift_ver_cur.xml` eine neuere Version meldet | wartet bis zu 15 min, bis die Version auf der Platte steht, startet dann |
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

- **Tretlager/Wine:** `flatpak remote-info --log tretlager-origin de.linuxundich.Tretlager` zeigt die
  Versionen, `flatpak update --commit=<ältere> de.linuxundich.Tretlager` holt die vorige zurück
  (mit ihrem Wine), `flatpak mask de.linuxundich.Tretlager` hält sie fest. Der Abgleich passt die
  Zwift-Umgebung dann wieder an die ältere Wine-Version an.
- **Zwift:** Ein Zurück gibt es nicht und braucht es nicht – Zwift lässt nur mit der aktuellen
  Version fahren. Ist die Zwift-Umgebung kaputt, legt *Einrichtung prüfen* sie neu an; nur das
  Spiel (≈ 5 GB) wird dann erneut geladen.

## Ablauf für eine neue Tretlager-Version

1. Version in `tretlager/__init__.py` und CHANGELOG anheben (sonst startet die Bridge nach dem Update
   nicht neu), Metainfo-`<release>` ergänzen.
2. Wine anheben (optional): URL und SHA-256 im Manifest; auf tinytin bauen.
3. Auf tinytin: Abgleich mit bestehender Umgebung (Wine-Anpassung, Grafiktest), Zwift starten,
   kurze Fahrt mit Trainer und Puls, Zwift-Update falls gerade eins ansteht.
4. In die Flatpak-Quelle auf bender veröffentlichen (F4).

## Offen

- [ ] Tretlager meldet selbst, wenn eine neue Version bereitsteht, und spielt sie auf Wunsch ein
  (Flatpak-Portal `org.freedesktop.portal.Flatpak`, `CreateUpdateMonitor` / `Update`).
- [ ] Fortschritt beim Zwift-Update (geladene GB wie bei der Einrichtung) statt nur Text.
- [ ] Eine Windows-Komponente gezielt erneuern (z. B. neuere WebView2), wenn Zwift sie verlangt:
  Revisionsmarke je Verb, dann `winetricks --force <verb>` im Abgleich.
- [ ] Flatpak-Quelle auf bender mit GPG (F4), erst dann gibt es `flatpak update` für Tretlager.
