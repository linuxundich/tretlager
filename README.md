# Tretlager (Arbeitstitel)

Native GTK4-/libadwaita-Anwendung, die den offiziellen Windows-Client von **Zwift** unter
**TUXEDO OS Forky** (Debian testing) einrichtet, startet und aktuell hält: Wine, Laufzeit,
Grafikdiagnose (NVIDIA), Sensoren über Bluetooth LE ohne Zwift Companion App.

**Stand:** Phase A (Machbarkeit) liegt als Entwurf vor, noch kein Code.
Ergebnis in [FEASIBILITY.md](FEASIBILITY.md), offene Entscheidungen und Phasen in
[BACKLOG.md](BACKLOG.md).

Kernbefunde:
- Zwift läuft nur experimentell unter Wine (WineHQ 11.x; Debian forky hat derzeit kein Wine).
- Das Spiel nutzt OpenGL 3.1, DXVK ist überflüssig.
- Direktes BLE aus Wine geht nicht (GATT-Benachrichtigungen und Schreiben fehlen). Sensoren
  kommen über eine eigene Bridge, die sich als Wahoo-„Direct Connect“-Gerät ausgibt.
- Die Anmeldung im Launcher (WebView2) ist das größte offene Risiko.

## Grundsätze

Keine Umgehung von Anmeldung, DRM oder Lizenzprüfung, keine veränderten Zwift-Dateien, keine
Telemetrie, keine stillen Systemänderungen. Nicht Funktionierendes wird als solches angezeigt.
