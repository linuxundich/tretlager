"""Ein BLE-Gerät halten und als DIRCON-Gerät anbieten."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Callable

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakDeviceNotFoundError, BleakError
from dbus_fast import BusType, Message, MessageType
from dbus_fast.aio import MessageBus

from . import dircon, gatt
from .config import DeviceConfig
from .mdns import Announcer
from ..i18n import N_

log = logging.getLogger(__name__)

RECONNECT_DELAY = 5.0
# Wie lange auf die Indication eines Control Points gewartet wird.
CONTROL_POINT_TIMEOUT = 3.0
MAX_RECONNECT_DELAY = 60.0
NOT_FOUND_DELAY = 10.0
# Hinweis „Verbindung instabil“: so viele Abbrüche oder Fehlversuche in diesem Zeitraum.
UNSTABLE_EVENTS = 3
UNSTABLE_WINDOW = 600.0
# Verbinden plus Dienstsuche. Die Versuche laufen nacheinander (connect_lock): Ein hängender
# Versuch hält alle anderen Geräte so lange auf (nanhlanu 31.10.: TICKR 40 s, KICKR wartete mit).
# Nur der Garmin HRM-Pro Plus braucht für die Dienstsuche mehr als 20 s.
CONNECT_TIMEOUT = 20.0
SLOW_CONNECT_TIMEOUT = 40.0
SLOW_CONNECT_NAMES = ("HRM-Pro",)
# So lange bleibt ein Gerät nach einem Abbruch für Zwift angekündigt und der DIRCON-Server offen.
# Zwift behält die Kopplung und bekommt nach dem Wiederverbinden einfach wieder Daten; sonst
# verschwindet das Gerät aus Zwift und muss neu gefunden werden (QA-Audit B-04).
GRACE = 45.0
# Suche nach der Adresse vor dem Verbinden. Getrennt vom Verbindungs-Timeout: bleak sucht sonst
# 40 s nach einem abwesenden Gerät und hält so lange die Sperre; ein Trainer, der neu verbinden
# will, und die Suche in der Oberfläche warteten dann bis zu einer Minute (gemessen 30.10.).
# Werbende Sensoren senden mehrmals pro Sekunde, 8 s reichen.
FIND_TIMEOUT = 8.0
def connect_timeout(name: str) -> float:
    """Zeitlimit für Verbinden und Dienstsuche; lang nur für bekannt langsame Sensoren."""
    return SLOW_CONNECT_TIMEOUT if any(n.lower() in (name or "").lower() for n in SLOW_CONNECT_NAMES) else CONNECT_TIMEOUT


# BlueZ baut pro Adapter nur eine Verbindung gleichzeitig auf („Operation already in progress“).
connect_lock = asyncio.Lock()

_PROPS = {"read": dircon.PROP_READ, "write": dircon.PROP_WRITE, "write-without-response": dircon.PROP_WRITE,
          "notify": dircon.PROP_NOTIFY, "indicate": dircon.PROP_INDICATE}


async def bluez_disconnect(address: str, adapter: str = "") -> None:
    """Gerät in BlueZ trennen, falls es noch verbunden ist (Fehler werden ignoriert)."""
    path = f"/org/bluez/{adapter or 'hci0'}/dev_" + address.upper().replace(":", "_")
    try:
        bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    except Exception:
        return
    try:
        reply = await bus.call(Message(destination="org.bluez", path=path,
                                       interface="org.freedesktop.DBus.Properties", member="Get",
                                       signature="ss", body=["org.bluez.Device1", "Connected"]))
        if reply.message_type != MessageType.ERROR and reply.body[0].value:
            log.info("%s: verwaiste Verbindung wird getrennt", address)
            await bus.call(Message(destination="org.bluez", path=path, interface="org.bluez.Device1",
                                   member="Disconnect"))
    finally:
        bus.disconnect()


def describe_error(e: BaseException) -> tuple[str, bool]:
    """Verständlicher Satz zu einem Verbindungsfehler und ob das Gerät nur nicht gefunden wurde.

    BlueZ- und bleak-Meldungen wie „org.bluez.Error.NotReady“ sagen Nutzern nichts; die Rohmeldung
    steht weiter im Protokoll der Bridge.
    """
    raw = str(e)
    if isinstance(e, BleakDeviceNotFoundError) or "was not found" in raw:
        return N_("Out of range or asleep"), True
    if "failed to discover services" in raw:
        # Gerät ist beim Verbinden wieder eingeschlafen (KICKR nach Pause): bald erneut.
        return N_("Device is asleep – pedal briefly or put on the strap"), True
    if isinstance(e, (asyncio.TimeoutError, TimeoutError)):
        return N_("Connection timed out, trying again"), False
    if "NotReady" in raw or "not powered" in raw.lower() or ("adapter" in raw.lower() and "not found" in raw):
        return N_("Bluetooth is off or the adapter is missing"), False
    if "InProgress" in raw or "in progress" in raw:
        return N_("Bluetooth is busy, retrying"), False
    if "le-connection-abort" in raw or "ConnectionAttemptFailed" in raw or "Software caused connection abort" in raw:
        return N_("Connection attempt aborted, retrying"), False
    if "NotPermitted" in raw or "NotAuthorized" in raw or "AccessDenied" in raw:
        return N_("Bluetooth denies access to the device"), False
    if isinstance(e, RuntimeError) and raw:
        return raw, False  # eigene, schon verständliche Texte (N_)
    return N_("Connection failed, retrying"), False


def dircon_name(cfg: DeviceConfig) -> str:
    """Name, unter dem Zwift das Gerät sieht. Zwift erwartet Wahoo-Namen."""
    suffix = cfg.address.replace(":", "")[-4:]
    if cfg.role == "heartrate":
        return f"Wahoo HRM {suffix}"
    return f"Wahoo KICKR {suffix}"


class BridgedDevice:
    """Verbindet ein BLE-Gerät und spiegelt dessen Standarddienste über DIRCON."""

    def __init__(self, cfg: DeviceConfig, announcer: Announcer, on_change: Callable[[], None],
                 local_only: bool = True, adapter: str = ""):
        self.cfg = cfg
        self.local_only = local_only
        self.adapter = adapter  # hciN, leer = Standardadapter
        self.announcer = announcer
        self.on_change = on_change
        self.state = "getrennt"  # getrennt, verbinde, verbunden, fehler
        self.error = ""
        self.values: dict = {}
        self.values_at = 0.0
        self._services: list[dircon.Service] = []
        self._client: BleakClient | None = None
        self._notifying: set[str] = set()
        # Nur für Zwift auf diesem Rechner: nur auf Loopback lauschen, damit niemand im Netz den
        # Trainer steuern kann.
        self._server = dircon.Server(self, host="127.0.0.1" if local_only else "0.0.0.0", port=cfg.port)
        self._task: asyncio.Task | None = None
        self._disconnected = asyncio.Event()
        self._was_connected = False
        self._pending: dict[str, asyncio.Future] = {}
        self._trouble: list[float] = []  # Zeitpunkte von Abbrüchen und Fehlversuchen
        self._grace: asyncio.Task | None = None  # Schonfrist nach einem Abbruch
        self._announced: list[str] = []  # bei Zwift angekündigte Dienste

    # --- GattBackend für den DIRCON-Server ---

    def services(self) -> list[dircon.Service]:
        return self._services

    async def read(self, char_uuid: str) -> bytes:
        client = self._require_client()
        return bytes(await client.read_gatt_char(char_uuid))

    async def write(self, char_uuid: str, data: bytes) -> bytes | None:
        client = self._require_client()
        props = self._char_props(char_uuid)
        if "indicate" not in props:
            await client.write_gatt_char(char_uuid, data, response="write" in props)
            return None
        # Control Point: Die Antwort kommt als Indication; Zwift will sie in der Schreib-Antwort.
        await self.set_notify(char_uuid, True)
        answer = asyncio.get_running_loop().create_future()
        self._pending[char_uuid] = answer
        try:
            await client.write_gatt_char(char_uuid, data, response=True)
            return await asyncio.wait_for(answer, CONTROL_POINT_TIMEOUT)
        except asyncio.TimeoutError:
            log.warning("%s: keine Antwort des Control Points %s auf %s", self.cfg.address, char_uuid[4:8],
                        data.hex(" "))
            return None
        finally:
            self._pending.pop(char_uuid, None)

    async def set_notify(self, char_uuid: str, enabled: bool) -> None:
        # BLE-Benachrichtigungen bleiben an, sobald sie einmal laufen; die DIRCON-Sitzungen
        # filtern selbst. So stört ein Client, der abbestellt, keinen anderen.
        if not enabled or char_uuid in self._notifying:
            return
        client = self._require_client()
        await client.start_notify(char_uuid, lambda _c, data, u=char_uuid: self._notified(u, data))
        self._notifying.add(char_uuid)

    # --- Lebenszyklus ---

    def start(self) -> None:
        self._task = asyncio.create_task(self._run(), name=f"device {self.cfg.address}")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._teardown()
        await self._withdraw()

    def _note_trouble(self) -> None:
        now = time.monotonic()
        self._trouble = [t for t in self._trouble if now - t < UNSTABLE_WINDOW] + [now]

    @property
    def unstable(self) -> bool:
        now = time.monotonic()
        return sum(1 for t in self._trouble if now - t < UNSTABLE_WINDOW) >= UNSTABLE_EVENTS

    def status(self) -> dict:
        fresh = time.monotonic() - self.values_at < 5
        return {
            "address": self.cfg.address,
            "name": self.cfg.name,
            "role": self.cfg.role,
            "enabled": self.cfg.enabled,
            "port": self.cfg.port,
            "dircon_name": dircon_name(self.cfg),
            "state": self.state,
            "error": self.error,
            "services": [s.uuid for s in self._services],
            "zwift_clients": self._server.client_count,
            "unstable": self.unstable,
            "values": self.values if fresh else {},
        }

    async def _run(self) -> None:
        failures = 0
        while True:
            not_found = False
            try:
                await self._connect_and_serve()
            except asyncio.CancelledError:
                raise
            except (BleakError, OSError, asyncio.TimeoutError, RuntimeError) as e:
                text, not_found = describe_error(e)
                if not not_found or "failed to discover" in str(e):
                    self._note_trouble()
                self._set_state("fehler", text)
                log.warning("%s: %s (%s: %s)", self.cfg.address, text, type(e).__name__, e)
            # Nach einer stehenden Verbindung gleich wieder versuchen; ein Gerät, das immer wieder
            # scheitert, seltener probieren, damit es die BlueZ-Sperre nicht dauernd belegt.
            failures = 0 if self._was_connected else failures + 1
            self._was_connected = False
            await self._teardown()
            self._start_grace()
            if not_found:
                # Schlafende Geräte (Gurt ohne Hautkontakt) schnell wiederfinden: Die Suche belegt
                # BlueZ nur kurz, anders als ein hängender Verbindungsaufbau.
                await asyncio.sleep(NOT_FOUND_DELAY)
                continue
            await asyncio.sleep(min(RECONNECT_DELAY * 2 ** max(failures - 1, 0), MAX_RECONNECT_DELAY))

    async def _connect_and_serve(self) -> None:
        self._set_state("verbinde")
        self._disconnected.clear()
        # Eine verwaiste BlueZ-Verbindung (z. B. nach einem abgebrochenen Versuch) verhindert,
        # dass das Gerät wieder wirbt; dann findet bleak es nicht mehr.
        async with connect_lock:
            await bluez_disconnect(self.cfg.address, self.adapter)
            bluez = {"adapter": self.adapter} if self.adapter else {}
            device = await BleakScanner.find_device_by_address(self.cfg.address, timeout=FIND_TIMEOUT, bluez=bluez)
            if device is None:
                raise BleakDeviceNotFoundError(self.cfg.address, f"Device with address {self.cfg.address} was not found.")
            client = BleakClient(device, disconnected_callback=lambda _c: self._disconnected.set(),
                                 timeout=connect_timeout(self.cfg.name), bluez=bluez)
            self._client = client  # auch bei Fehlschlag in _teardown trennen
            await client.connect()
        services = self._collect_services(client)
        if not services:
            raise RuntimeError(N_("Device offers no supported service (FTMS, Cycling Power, CSC, heart rate)"))
        self._cancel_grace()
        if self._server.running and [s.uuid for s in services] != self._announced:
            await self._withdraw()  # anderes Dienstangebot als vor dem Abbruch: neu ankündigen
        self._services = services
        if not self._server.running:
            await self._server.start()
            self._announced = [s.uuid for s in services]
            await self.announcer.publish(dircon_name(self.cfg), self.cfg.port, self._announced,
                                         mac=self.cfg.address, serial=self.cfg.address.replace(":", ""),
                                         local_only=self.local_only)
        else:
            log.info("%s: wieder verbunden, Zwift-Verbindung blieb bestehen", self.cfg.address)
        # Für die Live-Anzeige schon vor Zwift die Messwerte abonnieren, dazu alles, was Zwift
        # vor einem Abbruch abonniert hatte.
        wanted = [u for u in gatt.DECODERS if self._char_props(u) & {"notify", "indicate"}]
        wanted += [u for u in self._server.subscribed() if u not in wanted]
        for uuid in wanted:
            await self.set_notify(uuid, True)
        self._was_connected = True
        self._set_state("verbunden")
        await self._disconnected.wait()
        raise RuntimeError(N_("Connection to the device lost"))

    def _start_grace(self) -> None:
        if self._server.running and (self._grace is None or self._grace.done()):
            self._grace = asyncio.create_task(self._grace_expiry(), name=f"grace {self.cfg.address}")

    def _cancel_grace(self) -> None:
        if self._grace and not self._grace.done():
            self._grace.cancel()
        self._grace = None

    async def _grace_expiry(self) -> None:
        await asyncio.sleep(GRACE)
        log.info("%s: Schonfrist abgelaufen, Gerät wird für Zwift zurückgezogen", self.cfg.address)
        self._grace = None
        await self._withdraw()

    async def _withdraw(self) -> None:
        """Ankündigung zurückziehen und DIRCON-Server schließen (Zwift verliert das Gerät)."""
        self._cancel_grace()
        await self.announcer.withdraw(self.cfg.port)
        await self._server.stop()
        self._announced = []
        self.on_change()

    async def _teardown(self) -> None:
        """Nur die BLE-Seite abbauen; Ankündigung und DIRCON-Server bleiben (Schonfrist)."""
        self._notifying.clear()
        if self._client:
            try:
                await self._client.disconnect()
            except Exception:
                pass
            self._client = None
        if self.state == "verbunden":
            self._set_state("getrennt")

    # --- Hilfen ---

    def _collect_services(self, client: BleakClient) -> list[dircon.Service]:
        out = []
        for s in client.services:
            if s.uuid not in gatt.BRIDGED_SERVICES:
                continue
            chars = []
            for c in s.characteristics:
                props = 0
                for p in c.properties:
                    props |= _PROPS.get(p, 0)
                chars.append(dircon.Characteristic(c.uuid, props))
            out.append(dircon.Service(s.uuid, chars))
        return out

    def _char_props(self, char_uuid: str) -> set[str]:
        if self._client:
            c = self._client.services.get_characteristic(char_uuid)
            if c:
                return set(c.properties)
        return set()

    def _require_client(self) -> BleakClient:
        if not self._client or not self._client.is_connected:
            raise RuntimeError(N_("Device not connected"))
        return self._client

    def _notified(self, char_uuid: str, data: bytearray) -> None:
        value = bytes(data)
        pending = self._pending.get(char_uuid)
        if pending and not pending.done():
            pending.set_result(value)
            log.info("%s: Control Point %s antwortet %s", self.cfg.address, char_uuid[4:8], value.hex(" "))
        self._server.notify(char_uuid, value)
        decoder = gatt.DECODERS.get(char_uuid)
        if decoder:
            log.debug("%s %s: %s", self.cfg.address, char_uuid[4:8], value.hex(" "))
            try:
                self.values.update(decoder(value))
                self.values_at = time.monotonic()
            except Exception:
                pass

    def _set_state(self, state: str, error: str = "") -> None:
        self.state = state
        self.error = error
        self.on_change()
