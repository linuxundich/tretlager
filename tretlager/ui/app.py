"""Tretlager-Oberfläche: Sensor-Bridge steuern und Geräte verwalten."""

from __future__ import annotations

import sys
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from .. import APP_ID  # noqa: E402
from .bridge_client import BridgeClient  # noqa: E402

STATE_TEXT = {
    "verbunden": "Verbunden",
    "verbinde": "Verbinde …",
    "getrennt": "Getrennt",
    "fehler": "Fehler",
    "aus": "Ausgeschaltet",
}
ROLE_TEXT = {
    "trainer": "Smart-Trainer",
    "power": "Leistungsmesser",
    "cadence": "Geschwindigkeit/Trittfrequenz",
    "heartrate": "Pulsgurt",
    "other": "Sensor",
}
# Eigene Symbole in ui/icons, damit sie unter Adwaita und Breeze gleich aussehen.
ROLE_ICON = {
    "trainer": "tretlager-trainer-symbolic",
    "power": "tretlager-trainer-symbolic",
    "cadence": "tretlager-trainer-symbolic",
    "heartrate": "tretlager-heartrate-symbolic",
    "other": "bluetooth-symbolic",
}


def format_values(values: dict) -> str:
    parts = []
    if "power" in values:
        parts.append(f"{values['power']} W")
    if "cadence" in values:
        parts.append(f"{values['cadence']:.0f} U/min")
    if "heart_rate" in values:
        parts.append(f"{values['heart_rate']} bpm")
    return " · ".join(parts)


class DeviceRow(Adw.ExpanderRow):
    def __init__(self, window: "MainWindow", address: str):
        super().__init__()
        self.window = window
        self.address = address
        self.icon = Gtk.Image()
        self.add_prefix(self.icon)
        self.values = Gtk.Label(css_classes=["numeric", "dim-label"])
        self.add_suffix(self.values)

        self.zwift_row = Adw.ActionRow(title="In Zwift sichtbar als", subtitle_selectable=True)
        self.add_row(self.zwift_row)
        self.detail_row = Adw.ActionRow(title="Bluetooth-Adresse", subtitle_selectable=True)
        self.add_row(self.detail_row)
        self.enabled_row = Adw.SwitchRow(title="Weiterreichen",
                                         subtitle="Die Bridge hält die Verbindung und bietet das Gerät Zwift an")
        self._enabled_handler = self.enabled_row.connect("notify::active", self._on_enabled)
        self.add_row(self.enabled_row)
        # Normale Zeile mit eigenem Knopf statt Adw.ButtonRow: Die wirkt unter Breeze flach und
        # ohne rote Hervorhebung.
        remove_row = Adw.ActionRow(title="Gerät entfernen",
                                   subtitle="Die Bridge vergisst das Gerät; Zwift sieht es nicht mehr")
        remove = Gtk.Button(label="Entfernen", valign=Gtk.Align.CENTER, css_classes=["destructive-action"])
        remove.connect("clicked", lambda _b: window.confirm_remove(self.address, self.get_title()))
        remove_row.add_suffix(remove)
        self.add_row(remove_row)

    def update(self, d: dict) -> None:
        self.set_title(GLib.markup_escape_text(d["name"]))
        state = STATE_TEXT.get(d["state"], d["state"])
        sub = [ROLE_TEXT.get(d["role"], d["role"]), state]
        if d["state"] == "verbunden":
            n = d.get("zwift_clients", 0)
            sub.append("Zwift verbunden" if n else "wartet auf Zwift")
        if d.get("error"):
            sub.append(d["error"])
        self.set_subtitle(GLib.markup_escape_text(" · ".join(sub)))
        self.icon.set_from_icon_name(ROLE_ICON.get(d["role"], "bluetooth-symbolic"))
        self.values.set_label(format_values(d.get("values", {})))
        self.zwift_row.set_subtitle(f"{d.get('dircon_name', '–')} (Port {d['port']})")
        self.detail_row.set_subtitle(d["address"])
        with self.enabled_row.handler_block(self._enabled_handler):
            self.enabled_row.set_active(d["enabled"])

    def _on_enabled(self, row: Adw.SwitchRow, _pspec) -> None:
        self.window.client.set_device_enabled(self.address, row.get_active())


class AddDeviceDialog(Adw.Dialog):
    def __init__(self, window: "MainWindow"):
        super().__init__(title="Gerät hinzufügen", content_width=480, content_height=520)
        self.window = window
        header = Adw.HeaderBar()
        self.rescan = Gtk.Button(icon_name="view-refresh-symbolic", tooltip_text="Erneut suchen")
        self.rescan.connect("clicked", lambda _b: self.start_scan())
        header.pack_start(self.rescan)
        self.spinner = Adw.Spinner()
        header.pack_end(self.spinner)
        page = Adw.PreferencesPage()
        self.group = Adw.PreferencesGroup(
            title="Geräte in Reichweite",
            description="Gesucht wird nach Smart-Trainern, Leistungsmessern, Trittfrequenzsensoren "
                        "und Pulsgurten. Wecke den Trainer auf, indem du kurz trittst.")
        page.add(self.group)
        self.rows: list[Gtk.Widget] = []
        view = Adw.ToolbarView(content=page)
        view.add_top_bar(header)
        self.set_child(view)
        self.start_scan()

    def start_scan(self) -> None:
        for r in self.rows:
            self.group.remove(r)
        self.rows = []
        self.spinner.set_visible(True)
        self.rescan.set_sensitive(False)
        self._placeholder(Adw.ActionRow(title="Suche läuft …", subtitle="Etwa zehn Sekunden"))
        self.window.client.scan(10, self._scanned)

    def _placeholder(self, row: Gtk.Widget) -> None:
        self.group.add(row)
        self.rows.append(row)

    def _scanned(self, found: list | None) -> None:
        for r in self.rows:
            self.group.remove(r)
        self.rows = []
        self.spinner.set_visible(False)
        self.rescan.set_sensitive(True)
        if found is None:
            self._placeholder(Adw.ActionRow(title="Suche fehlgeschlagen",
                                            subtitle="Läuft die Bridge, und ist Bluetooth eingeschaltet?"))
            return
        if not found:
            self._placeholder(Adw.ActionRow(title="Nichts gefunden",
                                            subtitle="Gerät aufwecken und erneut suchen"))
            return
        for d in found:
            row = Adw.ActionRow(title=GLib.markup_escape_text(d["name"]),
                                subtitle=f"{ROLE_TEXT.get(d['role'], d['role'])} · {d['address']} · {d['rssi']} dBm")
            row.add_prefix(Gtk.Image(icon_name=ROLE_ICON.get(d["role"], "bluetooth-symbolic")))
            if d["configured"]:
                row.add_suffix(Gtk.Label(label="Schon hinzugefügt", css_classes=["dim-label"]))
            else:
                btn = Gtk.Button(label="Hinzufügen", valign=Gtk.Align.CENTER, css_classes=["suggested-action"])
                btn.connect("clicked", self._on_add, d)
                row.add_suffix(btn)
                row.set_activatable_widget(btn)
            self._placeholder(row)

    def _on_add(self, _btn: Gtk.Button, d: dict) -> None:
        self.window.client.add_device(d["address"], d["name"], d["role"])
        self.window.toast(f"„{d['name']}“ hinzugefügt")
        self.close()


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application):
        super().__init__(application=app, title="Tretlager", default_width=640, default_height=720)
        self.client = BridgeClient()
        self.client.connect("status", self._on_status)
        self.client.connect("error", lambda _c, msg: self.toast(msg))
        self.rows: dict[str, DeviceRow] = {}

        page = Adw.PreferencesPage()

        service = Adw.PreferencesGroup(
            title="Sensor-Bridge",
            description="Zwift kann unter Linux kein Bluetooth nutzen. Die Bridge hält deine Sensoren "
                        "und bietet sie Zwift als Wahoo-„Direct Connect“-Geräte im Netzwerk an.")
        self.running_row = Adw.SwitchRow(title="Bridge läuft")
        self._running_handler = self.running_row.connect("notify::active", self._on_running)
        service.add(self.running_row)
        self.autostart_row = Adw.SwitchRow(title="Beim Anmelden starten")
        self._autostart_handler = self.autostart_row.connect("notify::active", self._on_autostart)
        service.add(self.autostart_row)
        page.add(service)

        self.devices = Adw.PreferencesGroup(title="Geräte")
        add = Gtk.Button(icon_name="list-add-symbolic", tooltip_text="Gerät hinzufügen", valign=Gtk.Align.CENTER,
                         css_classes=["flat"])
        add.connect("clicked", lambda _b: AddDeviceDialog(self).present(self))
        self.add_button = add
        self.devices.set_header_suffix(add)
        self.empty_row = Adw.ActionRow(title="Noch keine Geräte",
                                       subtitle="Mit + suchst du Trainer und Pulsgurt in der Nähe")
        self.devices.add(self.empty_row)
        page.add(self.devices)

        hint = Adw.PreferencesGroup(
            title="In Zwift koppeln",
            description="In Zwift unter „Gekoppelte Geräte“ bei Leistungsquelle, Trittfrequenz, Steuerbarer "
                        "Trainer und Herzfrequenz das Gerät „Wahoo KICKR …“ bzw. „Wahoo HRM …“ wählen. "
                        "Die Warnung zu Bluetooth in Zwift ist dabei normal.")
        page.add(hint)

        self.toasts = Adw.ToastOverlay(child=page)
        view = Adw.ToolbarView(content=self.toasts)
        view.add_top_bar(Adw.HeaderBar())
        self.set_content(view)

        self.client.get_autostart(self._set_autostart)
        self._on_status(self.client, None)

    def toast(self, text: str) -> None:
        self.toasts.add_toast(Adw.Toast(title=GLib.markup_escape_text(text)))

    def confirm_remove(self, address: str, name: str) -> None:
        dialog = Adw.AlertDialog(heading="Gerät entfernen?",
                                 body=f"{name} wird nicht mehr an Zwift weitergereicht.")
        dialog.add_response("cancel", "Abbrechen")
        dialog.add_response("remove", "Entfernen")
        dialog.set_response_appearance("remove", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", lambda _d, r: r == "remove" and self.client.remove_device(address))
        dialog.present(self)

    def _set_autostart(self, enabled: bool) -> None:
        with self.autostart_row.handler_block(self._autostart_handler):
            self.autostart_row.set_active(enabled)

    def _on_running(self, row: Adw.SwitchRow, _pspec) -> None:
        self.client.set_running(row.get_active())

    def _on_autostart(self, row: Adw.SwitchRow, _pspec) -> None:
        self.client.set_autostart(row.get_active(), lambda _r: self.client.get_autostart(self._set_autostart))

    def _on_status(self, _client, status: dict | None) -> None:
        running = status is not None
        with self.running_row.handler_block(self._running_handler):
            self.running_row.set_active(running)
        self.running_row.set_subtitle("" if running else "Ohne laufende Bridge sieht Zwift keine Sensoren")
        self.devices.set_sensitive(running)
        self.add_button.set_sensitive(running)
        devices = status["devices"] if status else []
        seen = set()
        for d in devices:
            seen.add(d["address"])
            row = self.rows.get(d["address"])
            if row is None:
                row = DeviceRow(self, d["address"])
                self.rows[d["address"]] = row
                self.devices.add(row)
            row.update(d)
        for address in list(self.rows):
            if address not in seen:
                self.devices.remove(self.rows.pop(address))
        self.empty_row.set_visible(not self.rows)
        if not running:
            self.empty_row.set_title("Bridge ist ausgeschaltet")
            self.empty_row.set_subtitle("Schalte sie oben ein, um Geräte zu verwalten")
        else:
            self.empty_row.set_title("Noch keine Geräte")
            self.empty_row.set_subtitle("Mit + suchst du Trainer und Pulsgurt in der Nähe")


class App(Adw.Application):
    def __init__(self) -> None:
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)

    def do_startup(self) -> None:
        Adw.Application.do_startup(self)
        icons = Path(__file__).parent / "icons"
        Gtk.IconTheme.get_for_display(Gdk.Display.get_default()).add_search_path(str(icons))

    def do_activate(self) -> None:
        win = self.props.active_window or MainWindow(self)
        win.present()


def main() -> int:
    return App().run(sys.argv)
