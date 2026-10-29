# Tretlager (Arbeitstitel)

Native GTK4-/libadwaita-Anwendung, die den offiziellen Windows-Client von **Zwift** unter
**TUXEDO OS Forky** (Debian testing) einrichtet, startet und aktuell hält: Wine, Laufzeit,
Grafikdiagnose (NVIDIA), Sensoren über Bluetooth LE ohne Zwift Companion App.

**Stand (2026-10-29):** Machbarkeit geprüft, Zwift läuft auf dem Testrechner tinytin (Opt-in-
Token-Login, NVIDIA per GLX + PRIME-Offload). Die **Sensor-Bridge** mit Oberfläche funktioniert:
Zwift koppelt Trainer und Pulsgurt über Wahoo Direct Connect, ohne Companion App.
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

## Bridge ausprobieren (Benutzerinstallation)

    build-aux/install-user.sh          # nach ~/.local, systemd-Benutzerdienst tretlager-bridge
    systemctl --user start tretlager-bridge
    PYTHONPATH=~/.local/lib/tretlager python3 -m tretlager.ui

Abhängigkeiten (Debian forky): `python3-bleak`, `python3-gi`, `gir1.2-gtk-4.0`, `gir1.2-adw-1`,
laufender `avahi-daemon` und BlueZ. Tests: `python -m pytest tests`.
