# Machbarkeitsanalyse (Phase A)

Stand: 2026-10-29. Reine Recherche: Web, Quelltexte, Paketarchive. Noch nichts ist auf echter
Hardware getestet.

Kennzeichnung:
- **[Q]** belegt durch eine Primärquelle (Quelltext, offizielle Seite, Paketarchiv)
- **[F]** nur ein Forums- oder Community-Bericht
- **[S]** eigener Schluss

Bewertung je Teilbereich: **offiziell unterstützt** · **funktioniert** (mehrfach berichtet) ·
**experimentell** · **geht nicht**.

## Kurzfassung

| Teilbereich | Bewertung | Kern |
|---|---|---|
| Zwift-Client unter Linux | **experimentell** (offiziell nicht unterstützt) | Windows-Client läuft unter Wine 11.x mit WebView2 und dotnet48; jede Launcher-Version kann das brechen |
| Wine auf Forky | **funktioniert nur über WineHQ** | Debians `wine` ist seit 2026-03-24 nicht mehr in testing; WineHQ hat eine `forky`-Suite mit 11.0 und 11.20, reines WoW64 ohne i386 |
| Bezug des Installers | **funktioniert** | öffentliche URL `https://cdn.zwift.com/app/ZwiftSetup.exe`, ohne Anmeldung; Authenticode-Prüfung möglich, Signierer noch nicht geprüft |
| Anmeldung | **größtes Produktrisiko** | Die WebView2-Anmeldung des Launchers 1.2.0 rendert unter Wine nicht; netbrain umgeht das mit einem nachgebauten OAuth-Login, das kollidiert mit Grundsatz 7 und den Zwift-AGB |
| Grafik / NVIDIA | **funktioniert** | ZwiftApp nutzt **OpenGL 3.1**, nicht Direct3D, also ist DXVK überflüssig; NVIDIA braucht den EGL/GLX-Schalter von Wine |
| BLE direkt aus Zwift | **geht nicht** | Wine 11.20: GATT lesen ja, Benachrichtigungen und Schreiben sind Stubs, kein Leistungsstrom, kein ERG |
| BLE über eigene Bridge (DIRCON) | **funktioniert** (Zwift-Seite), Bridge **experimentell** | Zwift erkennt Wahoo-„Direct Connect“-Geräte im LAN auch unter Wine; eine Bridge BlueZ → DIRCON überträgt FTMS samt ERG, Leistung und Kadenz |
| ANT+ in Wine | **geht nicht** | `winusb.dll` ist in Wine fast nur Stubs; ANT+ ginge höchstens nativ in der Bridge |
| Updates | **funktioniert** mit Vorbehalt | Launcher `SilentLaunch` aktualisiert; Versionsdatei `Zwift_ver_cur.xml` hat Prüfsummen |
| Companion App nötig? | **nein**, mit Bridge | Die Bridge ersetzt Companion als Weg für Sensoren |

**Fazit:** Das Vorhaben ist machbar, aber nicht so, wie der Auftrag es annimmt.
1. Die Sensoren erreichen Zwift nicht direkt über Wine. Ohne Companion App führt der einzige
   Weg über eine eigene Bridge, die sich als Wahoo-Direct-Connect-Gerät ausgibt.
2. Wine kommt aus dem WineHQ-Repo, nicht aus Debian.
3. Ob sich ein normaler Mensch ohne Tricks anmelden kann, ist offen und muss als Erstes
   getestet werden.

## 1. Zwift unter Linux

### 1.1 Plattformen
- [Q] Unterstützt sind Windows 10 64 Bit oder neuer, macOS ab 10.14.4, Android, iOS/iPadOS und
  Apple TV. Windows on ARM ist ausdrücklich ausgeschlossen. Linux, VMs und Wine kommen nicht vor.
  https://support.zwift.com/es/supported-devices-to-run-zwift-H1Cj9QbeB.md
- [Q] Zu Linux gibt es nur alte Forumsantworten, nach denen kein Linux-Client geplant ist.
  https://forums.zwift.com/t/no-linux-support-yet/14041

### 1.2 Aufbau des Clients
- [Q] `ZwiftSetup.exe` installiert nur `ZwiftLauncher.exe`. Der Launcher lädt das eigentliche
  Spiel `ZwiftApp.exe` nach (CI-Log: „Updating Zwift from version none to 1.124.0“).
  https://github.com/netbrain/zwift/issues/420
- [Q] Die Anmeldung läuft über WebView2 (Edge-Engine) im Launcher.
- [Q] Laut Kommentar in netbrains `src/run_zwift.sh` gibt es unter Wine drei Probleme:
  1. Der Launcher zeigt die Anmeldeseite nicht.
  2. Er startet `ZwiftApp.exe` nicht.
  3. Startet man `ZwiftApp.exe` allein, ruft das Spiel wieder den Launcher auf.

  https://github.com/netbrain/zwift/blob/master/src/run_zwift.sh

### 1.3 Referenzprojekt netbrain/zwift (Unlicense)
Das ist der verbreitetste Weg und läuft als Podman- oder Docker-Container. [Q] aus dem Dockerfile:
- Basis Debian trixie, **WineHQ wine-devel 11.20** (seit PR #422 vom 2026-10-24, vorher 9.9)
- winetricks auf einen Commit gepinnt, wegen des noch unveröffentlichten Verbs `webview2`
- Verben `corefonts dotnet48 d3dcompiler_47 webview2`, Mono und Gecko aus
- winbind (`ntlm_auth`), **kein DXVK**

Start, [Q] aus `run_zwift.sh`:
1. `wine start ZwiftLauncher.exe SilentLaunch`
2. die PID des Launchers ermitteln
3. `ZwiftApp.exe --token=<json>` per `runfromprocess-rs.exe` als Kindprozess des Launchers starten
4. Launcher und Crash-Handler beenden

Das Token kommt aus `zwift-auth.sh` (siehe Abschnitt 3).

Zum Vergleich: [Q] umu-launcher (Proton außerhalb von Steam) führt einen Eintrag `umu-zwift` mit
derselben winetricks-Liste. Es gibt keinen Beleg, dass Proton das Problem mit dem Launcher löst.
https://github.com/Open-Wine-Components/umu-protonfixes/blob/master/gamefixes-umu/umu-zwift.py

### 1.4 Aktuelle Brüche, die Wartungslast zeigen
- [Q] **Launcher 1.2.0** (Oktober 2026) stürzte unter Wine sofort ab (`RoGetActivationFactory`).
  Workaround in netbrain-PR #421: `wineserver -k` nach der Installation. Laut demselben PR
  rendert der WebView2-Inhalt weiterhin nicht. Zwift erzwingt das Update auf 1.2.0.
  https://github.com/netbrain/zwift/issues/420
- [Q] Bei Zwift 1.117–1.122 ließen Festplatten-Cache-Fehler (4390, `ERROR_NOT_A_REPARSE_POINT`)
  das Spiel einfrieren: https://github.com/netbrain/zwift/issues/402
- [S] Wine hinkt jedem Launcher-Release hinterher. Die App muss eine Matrix „getestete
  Launcher- und Zwift-Version × Wine-Version“ mitführen und unbekannte Kombinationen als
  ungetestet anzeigen.

## 2. Wine und Pakete auf TUXEDO OS Forky

- [Q] `wine`, `wine64`, `libwine` und `winetricks` sind **seit 2026-03-24 nicht in testing**.
  Mehrere RC-Bugs blockieren sie. `dxvk` fehlt seit 2026-10-15, `wine-development` gibt es seit
  2025 gar nicht mehr.
  https://tracker.debian.org/pkg/wine · https://tracker.debian.org/pkg/winetricks
- [Q] **WineHQ** hat eine Suite `forky`: `winehq-stable 11.0.0.0~forky-1`, `winehq-devel` und
  `winehq-staging` 11.20. Für amd64 ist Wine 11 ein einzelnes Paket ohne i386-Abhängigkeit
  (neuer WoW64-Modus). `dpkg --add-architecture i386` entfällt damit.
  https://dl.winehq.org/wine-builds/debian/dists/forky/
- [Q] TUXEDO-Repo `deb.tuxedocomputers.com/debian`:
  - Suite `forky` mit `tuxedo-drivers`, `tuxedo-control-center` und `nvidia-driver-assistant`
  - Suite `forky-nvidia` mit Pinning auf NVIDIA **580**

  Debians eigene NVIDIA-550-Pakete sollen am 2026-11-08 aus testing fliegen. Welche Quelle die
  580er tatsächlich liefert, muss am Zielrechner geklärt werden (`/etc/apt/sources.list.d`).
- [Q] **TUXEDO OS Forky bringt Plasma 6.7 mit, nicht GNOME.**
  https://linuxiac.com/tuxedo-os-debian-based-open-beta-is-now-available-for-testing/
  Der Auftrag nennt GNOME. → Entscheidung E4.
- [Q] PackageKit 1.4.0 mit eingebautem apt-Backend ist in forky. Plasma Discover hängt davon ab,
  also ist es vorinstalliert. `gi.repository.PackageKitGlib` kann:
  - Pakete auflösen
  - mit `SIMULATE` die Änderungsliste ermitteln
  - mit Polkit-Nachfrage installieren

  **Nicht** möglich sind Fremdquellen samt Schlüssel einrichten (WineHQ) und
  `--add-architecture`. Dafür braucht es einen eigenen kleinen pkexec-Helfer mit fester Aktion.

## 3. Bezug des Installers und Anmeldung

### 3.1 Installer
- [Q] `https://cdn.zwift.com/app/ZwiftSetup.exe` ist öffentlich und ohne Anmeldung erreichbar.
  HEAD am 2026-10-29: 200, 34 028 992 Byte, Last-Modified 2026-10-19. Dieselbe URL nutzen
  netbrain und Lutris seit mindestens 2022. Der Inhalt wechselt mit jedem Launcher-Release.
  → Weg 1 aus dem Auftrag (offizielle Download-URL) ist erfüllt.
- [Q] Zwift veröffentlicht keinen Hashwert für den Installer.
- [S] Die Echtheit lässt sich deshalb nur über die **Authenticode-Signatur** prüfen:
  - Werkzeug: `osslsigncode verify` (Paket 2.14 in forky)
  - mit eigener CA-Datei der Microsoft-Code-Signing-Wurzeln, denn Debians CA-Bündel enthält sie
    nicht
  - zusätzlich den Signierer (Subject) festnageln
  - **Test T1 vom 2026-10-29:** Installer mit 34 028 992 Byte, SHA-256 `dd10bb62…333f9d`
    - Signatur: Authenticode (PKCS#7, Revision 2.0) mit **EV-Code-Signing-Zertifikat**
    - Signierer: `CN=Zwift, Inc.`, `O=Zwift, Inc.`, Delaware, Registriernummer `5463328`,
      Long Beach CA. Gültig 2024-03-16 bis **2027-03-16**.
    - Kette: SSL.com EV Code Signing Intermediate CA RSA R3 → SSL.com EV Root Certification
      Authority RSA R2. Die Wurzel **steht im normalen System-CA-Speicher** (Mozilla); eine eigene
      Microsoft-CA-Datei ist also nicht nötig.
    - Der selbst berechnete Authenticode-Hash (SHA-256 über die Datei ohne Prüfsumme und
      Signaturtabelle) steht in der Signatur, die Datei ist also unverändert signiert.
    - Noch nicht geprüft: kryptografische Prüfung der Signatur über die signierten Attribute
      und den Zeitstempel. Das folgt mit `osslsigncode verify` auf tinytin.
    - Folge für die App: Das Blatt-Zertifikat **nicht** per Fingerprint festnageln, es läuft
      2027 ab. Stattdessen Kette gegen den System-CA-Speicher prüfen und dazu Subject-Felder
      (CN, O, Registriernummer) sowie Code-Signing-EKU verlangen.
- [Q] Für Spiel-Updates gibt es `https://cdn.zwift.com/gameassets/Zwift_Updates_Root/Zwift_ver_cur.xml`
  mit `sversion` (derzeit 1.124.0), `manifest_checksum` und `ver_cur_checksum`. Damit lässt sich
  die installierte Version gegen den Stand des Anbieters vergleichen.

### 3.2 Anmeldung – der kritische Punkt
- [Q] netbrains `zwift-auth.sh` meldet sich mit Benutzername und Passwort an. Es gibt sich dabei
  als Launcher aus (`client_id=Game_Launcher`) und spielt den OAuth-Code-Flow gegen
  `secure.zwift.com` durch:
  1. das HTML-Formular auslesen
  2. das Passwort absenden
  3. den Code gegen ein Token tauschen
  4. `ZwiftApp.exe --token=…` aufrufen
- [Q] Die Zwift-AGB (Stand 2026-06-02, §5) verbieten unter anderem, Authentifizierungs- oder
  Sicherheitsmaßnahmen zu umgehen, Skripte und automatisierte Programme zu nutzen und Programme
  ohne Erlaubnis mit der Plattform interagieren zu lassen.
  https://support.zwift.com/en_us/terms-of-service-HJt7VBYyH.md
- [S] Der nachgebaute Login ist keine Umgehung der Authentifizierung, denn der Nutzer meldet sich
  mit eigenen Daten an. Er ist aber eine **nicht dokumentierte private Schnittstelle** und
  automatisiert, verstößt also gegen Grundsatz 7 und §5 xi/xiii. **Diesen Weg baue ich nicht
  ein.**
- [S] Auch der Start per `runfromprocess` (Spiel als Kind des Launchers ausgeben) ist eine
  Grauzone. Er umgeht keine Schutzmaßnahme, täuscht aber die Prozess-Abstammung vor. Er wird
  nur eingesetzt, wenn er nötig ist, und dann dokumentiert. → Entscheidung E2.
- **Zulässiger Weg:** Der offizielle Launcher zeigt seine WebView2-Anmeldung, der Nutzer meldet
  sich dort selbst an, und der Launcher startet das Spiel. netbrain notierte am 2026-01-25
  „webview2 in zwift launcher works“, beim Launcher 1.2.0 rendert sie nicht mehr. **Ob das mit
  Wine 11.20 und Launcher 1.2.x auf Forky geht, ist der erste Test in Phase D.** Geht es nicht,
  kann die App Zwift ehrlicherweise nur „installieren, aber nicht starten“.

## 4. Grafik und NVIDIA

- [Q] ZwiftApp verlangt **OpenGL 3.1**. Zwifts eigene Fehlermeldung lautet „OpenGL 3.1 is
  required“. https://support.zwift.com/en_us/opengl-error-on-windows-Skpfw62fB.md
- [S] Damit ist **DXVK für das Spiel überflüssig**. Wine reicht OpenGL an den Host-Treiber durch.
  `d3dcompiler_47` braucht vermutlich nur WebView2. Der Prüfpunkt „DXVK/Vulkan“ im Auftrag
  schrumpft: Vulkan ist für das Spiel nicht nötig, eventuell aber für WebView2 (GPU-Beschleunigung
  des Launchers), das ist zu testen.
- [Q] Wine nutzt seit 10.17 EGL für OpenGL. Mit dem proprietären NVIDIA-Treiber braucht netbrain
  entweder `__EGL_VENDOR_LIBRARY_FILENAMES=""` oder den Rückweg auf GLX (Registry
  `UseEGL=N`, Schalter `WINE_DISABLE_EGL`). Natives Wayland geht auf NVIDIA nicht, XWayland ja.
  https://github.com/netbrain/zwift/issues/404
- [S] Die Diagnose muss deshalb unterscheiden:
  1. Karte vorhanden: sysfs `/sys/class/drm/*/device/vendor` = `0x10de`
  2. Treiber geladen: `/sys/module/nvidia/version`
  3. OpenGL tatsächlich beschleunigt: Renderer-String über EGL/GLX, nicht llvmpipe
  4. 32 Bit: entfällt bei WoW64 (zu bestätigen)
- [Q] Maschinenlesbare Quellen:
  - `nvidia-smi --query-gpu=… --format=csv,noheader`
  - `vulkaninfo --json` oder direkt `vkEnumeratePhysicalDevices`
  - für OpenGL am besten ein eigener kleiner EGL-Test statt `eglinfo` parsen
- Secure Boot und DKMS: Die App ändert daran nichts. Sie meldet nur, wenn das Modul nicht geladen
  ist und Secure Boot aktiv ist (`mokutil --sb-state`), und verweist auf TUXEDOs Weg.

## 5. Sensoren: BLE und ANT+

### 5.1 Direkter BLE-Zugriff aus Wine – geht nicht
- [Q] Wine 11.0 (Januar 2026): `winebth.sys` über BlueZ-D-Bus. Scannen, Koppeln und erste
  GATT-Dienste sind über die Win32-BLE-API sichtbar.
  https://raw.githubusercontent.com/wine-mirror/wine/wine-11.0/ANNOUNCE.md
- [Q] Stand Wine 11.20 (master):
  - Win32 vorhanden: `BluetoothGATTGetServices`, `GetCharacteristics`, `GetCharacteristicValue`
  - Win32 noch Stubs: `BluetoothGATTRegisterEvent` (Benachrichtigungen),
    `BluetoothGATTSetCharacteristicValue` (Schreiben) und `BluetoothGATTSetDescriptorValue`
    (CCCD)
  - WinRT: `GetCharacteristics` und der Advertisement-Watcher liefern `E_NOTIMPL`

  https://github.com/wine-mirror/wine/blob/master/dlls/bluetoothapis/bluetoothapis.spec
- [S] Ohne Benachrichtigungen fließen keine Leistungs- und Pulswerte, ohne Schreiben gibt es kein
  ERG. Welche API Zwift nutzt (vermutlich WinRT), ist nicht belegt, ändert aber nichts: Beide Wege
  sind unvollständig.
- [F] Kein Bericht, dass Zwift unter Wine BLE-Sensoren direkt sieht. Debian-13-Nutzer im
  Februar 2026: „not properly identifying BLE Equipment“.
  https://forums.zwift.com/t/how-to-zwift-on-debian-linux/591025
- Folge laut Auftrag (Abschnitt 8): Der direkte Zugriff ist nachweislich nicht möglich, also ist
  eine Bridge zu prüfen. Die Diagnose der App weist das mit einem eigenen Test aus (Wine-Version
  plus Stub-Liste), statt es zu behaupten.

### 5.2 Bridge über Wahoo Direct Connect (DIRCON) – der tragfähige Weg
- [Q/F] Zwift unterstützt offiziell Trainer mit „Direct Connect“ (Wahoo DIRCON). Das ist GATT
  über TCP im LAN, angekündigt per mDNS `_wahoo-fitness-tnp._tcp`.
- [F] Das funktioniert auch unter Wine:
  - Kickr V5/V6 unter Debian 11 mit Wine 7.18 (2022)
  - im Februar 2026 unter Debian 13 im netbrain-Container
  - im Juli 2025 mit Host-Netz

  https://forums.zwift.com/t/how-to-zwift-on-debian-linux/591025
- [Q] Wines `dnsapi`-mDNS sind Stubs. [S] Zwift sucht also mit eigenem Multicast-Code; Multicast
  muss das Spiel erreichen. Bei nativem Wine ohne Container ist das gegeben.
- [Q] Wahoo veröffentlicht keine Protokollspezifikation. Die beste Referenz ist qdomyos-zwift
  (GPL-3.0, aktiv), `src/devices/dircon/`:
  - 6-Byte-Kopf
  - Nachrichten für Dienste und Charakteristika suchen, lesen, schreiben, Benachrichtigung
    einschalten und unaufgeforderte Benachrichtigung
  - qdomyos stellt FTMS (0x1826) mit Control Point 0x2AD9 bereit, also **ERG**, dazu Cycling
    Power (0x1818), CSC (0x1816) und Puls (0x180D) als eigene mDNS-Instanz.

  https://github.com/cagnulein/qdomyos-zwift/tree/master/src/devices/dircon
- Rechtliche Einordnung [S]:
  - DIRCON ist eine von Zwift angebotene Verbindungsart. Die Bridge verhält sich wie ein
    Wahoo-Gerät.
  - Sie berührt keine Zwift-Binärdatei, keine Anmeldung und keine Server-Schnittstelle.
  - Das Protokoll ist durch Interoperabilitäts-Analyse bekannt, nicht dokumentiert.
  - Damit erfüllt sie die Bedingungen aus Abschnitt 8 bis auf „dokumentierte Schnittstelle“, dort
    nur teilweise.
  - Code aus qdomyos (GPL-3) darf übernommen werden, wenn das Projekt GPL-3 wird.
- Offene Fragen, nur mit Hardware zu klären:
  1. **Nimmt Zwift Puls über eine DIRCON-Instanz an?** Echte Kickr liefern keinen Puls, deshalb
     brauchten bisherige Nutzer dafür Companion.
  2. Findet Zwift eine DIRCON-Instanz auf **demselben Rechner** (mDNS-Loopback)?
  3. Stabilität und Latenz von ERG über die Kette BLE → Bridge → TCP → Wine.
  4. Gleichzeitiger Zugriff: Die Bridge hält die BLE-Verbindung exklusiv; Zwift sieht den
     Trainer nur über die Bridge.

### 5.3 ANT+
- [Q] Wines `winusb.dll` hat außer `WinUsb_Free` nur Stubs (unverändert seit 2022). Die
  Windows-Treiber der ANT-Sticks (libusb-win32, SiLabs, WHQL) laden in Wine nicht.
  https://github.com/wine-mirror/wine/blob/master/dlls/winusb/winusb.spec
- [F] Es gibt keinen einzigen Erfolgsbericht. Nutzer weichen auf eine VM mit USB-Durchreichung aus.
- [S] **ANT+ in Wine: geht nicht.** Möglich wäre später: Die Bridge liest ANT+ nativ unter Linux
  (libusb, z. B. die Python-Bibliothek `openant`) und reicht die Werte über DIRCON weiter.
  Erst nach BLE.

## 6. Updates

- [Q] netbrain vergleicht die lokale `Zwift_ver_cur.xml` mit der vom CDN. Ist sie anders, startet
  es den Launcher mit `SilentLaunch` und wartet bis zu 5 Minuten auf die neue Version.
- [S] Das nutzt den offiziellen Updateweg und ist zulässig. Die App übernimmt das Prinzip:
  - Version vorher und nachher festhalten
  - freien Platz prüfen
  - vor dem Update einen Btrfs- oder Kopie-Schnappschuss des Wine-Prefix anbieten. TUXEDO OS
    legt per Snapper ohnehin Schnappschüsse an, aber nur vom System, nicht von `~`.
- Laufzeit-Updates (Wine aus WineHQ) laufen über APT und damit über die Systemupdates. Die App
  zeigt nur, ob die installierte Wine-Version in der getesteten Matrix steht, und warnt vor einem
  ungetesteten Sprung.

## 7. Was der Auftrag ändert

| Annahme im Auftrag | Befund | Folge |
|---|---|---|
| Debian-Pakete bevorzugen | Wine fehlt in forky | WineHQ-Quelle mit ausdrücklicher Zustimmung (E1) |
| DXVK, 32-Bit-Bibliotheken prüfen | OpenGL-Spiel, WoW64 | entfällt weitgehend; Diagnose auf OpenGL/EGL ausrichten |
| direkte BLE-Verbindung aus Zwift | Wine-GATT unvollständig | DIRCON-Bridge als eigener Benutzerdienst (E3) |
| ANT+ optional | in Wine unmöglich | „nicht unterstützt“; später nativ in der Bridge |
| GNOME/Wayland | Forky-Standard ist Plasma | Zielrechner klären (E4) |
| Login über offiziellen Weg | WebView2 rendert evtl. nicht | erster Test; kein nachgebauter Login (E2) |

## 8. Risiken

| # | Risiko | Wahrscheinlichkeit | Wirkung | Gegenmaßnahme |
|---|---|---|---|---|
| R1 | Launcher-Anmeldung rendert unter Wine nicht | hoch | Start unmöglich ohne Grauzonen-Trick | Test T2 zuerst; WebView2-Varianten und Wine-Versionen durchprobieren; ehrlich melden |
| R2 | Zwift-Update bricht Wine-Kompatibilität | hoch (regelmäßig) | Start bricht ab | Versionsmatrix, Prefix-Schnappschuss vor Update, Wiederherstellen |
| R3 | Zwift nimmt Puls über DIRCON nicht an | mittel | Pulsgurt fehlt | Test T6; sonst Puls als „nicht unterstützt“ kennzeichnen |
| R4 | DIRCON auf demselben Host wird nicht gefunden | mittel | Bridge nutzlos | Test T5; Ausweich: Bridge auf eigener IP (Netz-Namespace, Raspberry Pi) |
| R5 | WineHQ-Quelle ändert Schlüssel oder Pakete | gering | Installation scheitert | Schlüssel-Fingerprint festnageln, Fehler erklären |
| R6 | NVIDIA-EGL-Probleme | mittel | schwarzes Bild/Absturz | EGL/GLX-Schalter automatisch testen |
| R7 | Zwift ändert AGB oder sperrt Wine | gering | Projekt endet | keine Umgehung einbauen, damit nichts zu sperren ist |

## 9. Machbarkeitstests für Phase D (vor der Installationslogik)

| Test | Wo | Frage |
|---|---|---|
| T1 | beliebig | Authenticode von `ZwiftSetup.exe`: Signierer, Kette, Zeitstempel |
| T2 | Forky + NVIDIA | WineHQ 11.20 + winetricks webview2: rendert die Anmeldung im Launcher 1.2.x? startet er das Spiel selbst? |
| T3 | Forky + NVIDIA | OpenGL-Renderer in Wine = NVIDIA? EGL oder GLX nötig? fps auf Watopia |
| T4 | Forky-VM | Prefix-Einrichtung idempotent, Abbruch/Wiederaufnahme |
| T5 | Forky + BLE | Bridge-Prototyp (FTMS) auf demselben Host: findet Zwift das Gerät? |
| T6 | Forky + Trainer + Gurt | Leistung, Kadenz, ERG, Steigungssimulation, Puls über DIRCON |
| T7 | Forky | Update per `SilentLaunch`, danach Version aus `Zwift_ver_cur.xml` |

T2, T3, T5 und T6 brauchen den Zielrechner mit NVIDIA, einen BLE-Adapter und echte Geräte.
smokki hat nur Intel-Grafik; die VM `tuxedo-os-forky` hat keine NVIDIA-Karte.

### Zielrechner tinytin (`testt@tinytin`, lesend geprüft am 2026-10-29)

| Punkt | Befund |
|---|---|
| System | TUXEDO OS (Debian base), `VERSION_CODENAME=forky`, Kernel 7.2.7.1-tuxedo |
| Desktop | **KDE Plasma 6.7.4, Wayland**; libadwaita 1.10 ist installiert, GNOME nicht |
| Grafik | **Hybrid:** Intel Iris Xe (Alder Lake-P) + NVIDIA GeForce RTX 3050 Ti Laptop, 4 GB |
| NVIDIA-Treiber | 580.178.04 geladen; `nvidia-driver-libs 580.178.04-1tux1` aus `txos.tuxedocomputers.com/debian` (dort auch 595 und 610), Runtime-D3 an |
| GL/Vulkan | EGL-Hersteller nvidia + mesa, Vulkan-ICD nvidia + intel |
| Secure Boot | aus |
| Bluetooth | Intel AX201, Adapter `tinytin` bei BlueZ 5.87 |
| ANT+ | kein Stick |
| Wine | nicht installiert; i386 ist als Fremdarchitektur schon aktiv |
| PackageKit | 1.4.0 installiert |
| Platz/RAM | 920 GB frei, 31 GB RAM |

Geräte: **Wahoo KICKR V4** (Smart-Trainer) und **Garmin HRM-Pro Plus** (Pulsgurt, BLE und ANT+),
verbunden über den eingebauten AX201.

Folgen für die Geräte [S], vor T5 auf der Hardware zu prüfen:
- Ein KICKR V4 hat kein eingebautes Direct Connect (das kam mit späteren Modellen). Die Bridge
  ist also ohnehin der Weg, ein echtes DIRCON-Gerät gibt es nicht als Vergleich.
- Welche GATT-Dienste der V4 mit seiner Firmware anbietet, ist offen: FTMS (0x1826) oder nur
  Cycling Power (0x1818) mit Wahoos eigener Erweiterung für ERG. Das entscheidet, was die
  Bridge weiterreicht. Erster Schritt von T5: Dienste per BlueZ auslesen.
- Der HRM-Pro Plus erlaubt mehrere BLE-Verbindungen gleichzeitig. Die Bridge kann ihn also
  halten, während eine Uhr mitläuft.

Folgen für den Rechner:
- Auf dem Hybrid-Notebook läuft die Plasma-Sitzung auf der Intel-GPU. Zwift muss mit
  **PRIME-Offload** auf die NVIDIA-Karte: `__NV_PRIME_RENDER_OFFLOAD=1` und
  `__GLX_VENDOR_LIBRARY_NAME=nvidia` für GLX bzw. `__EGL_VENDOR_LIBRARY_FILENAMES` mit
  `10_nvidia.json` für EGL.
- Die Grafikdiagnose muss deshalb melden, *welche* GPU den OpenGL-Kontext von Wine tatsächlich
  bekommt. „NVIDIA-Treiber geladen“ reicht nicht. Das gehört zu T3.
- Die Oberfläche läuft unter Plasma; libadwaita funktioniert dort, sieht aber nach GNOME aus (E4).

## 10. Lizenzen der Fremdkomponenten

| Komponente | Lizenz | Nutzung |
|---|---|---|
| Wine (WineHQ) | LGPL-2.1+ | Laufzeit, Systempaket |
| winetricks | LGPL-2.1+ | einmalig zum Einrichten (WebView2, dotnet48, corefonts) |
| WebView2, .NET 4.8, Core Fonts | Microsoft-EULA | lädt winetricks vom Hersteller, nicht mitgeliefert |
| netbrain/zwift | Unlicense | nur Referenz |
| qdomyos-zwift | GPL-3.0 | Protokollreferenz; Übernahme nur bei GPL-3 |
| bleak | MIT | BLE in der Bridge (python3-bleak 3.0.2 in forky) |
| Zwift | proprietär | wird nur über den offiziellen Weg geladen und nie verändert |
