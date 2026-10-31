"""Hold a BLE device and offer it as a DIRCON device."""

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
# How long to wait for the indication of a control point.
CONTROL_POINT_TIMEOUT = 3.0
MAX_RECONNECT_DELAY = 60.0
NOT_FOUND_DELAY = 10.0
# "Connection unstable" hint: this many drops or failed attempts within this period.
UNSTABLE_EVENTS = 3
UNSTABLE_WINDOW = 600.0
# Connecting plus service discovery. Attempts run one after another (connect_lock): a hanging
# attempt holds up all other devices for that long (measured 2026-10-31: TICKR took 40 s, the
# KICKR had to wait). Only the Garmin HRM-Pro Plus needs more than 20 s for service discovery.
CONNECT_TIMEOUT = 20.0
SLOW_CONNECT_TIMEOUT = 40.0
SLOW_CONNECT_NAMES = ("HRM-Pro",)
# How long a device stays announced to Zwift, with its DIRCON server open, after a drop.
# Zwift keeps the pairing and simply receives data again after reconnecting; otherwise the
# device disappears from Zwift and has to be found again (QA audit B-04).
GRACE = 45.0
# Scan for the address before connecting. Separate from the connect timeout: otherwise bleak
# searches 40 s for an absent device and holds the lock all that time; a trainer that wants to
# reconnect and the scan in the user interface then waited up to a minute (measured 2026-10-30).
# Advertising sensors send several times per second, 8 s is enough.
FIND_TIMEOUT = 8.0
def connect_timeout(name: str) -> float:
    """Time limit for connecting and service discovery; long only for sensors known to be slow."""
    return SLOW_CONNECT_TIMEOUT if any(n.lower() in (name or "").lower() for n in SLOW_CONNECT_NAMES) else CONNECT_TIMEOUT


# BlueZ sets up only one connection at a time per adapter ("Operation already in progress").
connect_lock = asyncio.Lock()

_PROPS = {"read": dircon.PROP_READ, "write": dircon.PROP_WRITE, "write-without-response": dircon.PROP_WRITE,
          "notify": dircon.PROP_NOTIFY, "indicate": dircon.PROP_INDICATE}


async def bluez_disconnect(address: str, adapter: str = "") -> None:
    """Disconnect the device in BlueZ if it is still connected (errors are ignored)."""
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
            log.info("%s: disconnecting orphaned connection", address)
            await bus.call(Message(destination="org.bluez", path=path, interface="org.bluez.Device1",
                                   member="Disconnect"))
    finally:
        bus.disconnect()


def describe_error(e: BaseException) -> tuple[str, bool]:
    """Plain-language sentence for a connection error, and whether the device was merely not found.

    BlueZ and bleak messages like "org.bluez.Error.NotReady" mean nothing to users; the raw message
    still goes to the bridge log.
    """
    raw = str(e)
    if isinstance(e, BleakDeviceNotFoundError) or "was not found" in raw:
        return N_("Out of range or asleep"), True
    if "failed to discover services" in raw:
        # Device fell asleep again while connecting (KICKR after a break): retry soon.
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
        return raw, False  # our own, already readable texts (N_)
    return N_("Connection failed, retrying"), False


def dircon_name(cfg: DeviceConfig) -> str:
    """Name under which Zwift sees the device. Zwift expects Wahoo names."""
    suffix = cfg.address.replace(":", "")[-4:]
    if cfg.role == "heartrate":
        return f"Wahoo HRM {suffix}"
    return f"Wahoo KICKR {suffix}"


class BridgedDevice:
    """Connects a BLE device and mirrors its standard services over DIRCON."""

    def __init__(self, cfg: DeviceConfig, announcer: Announcer, on_change: Callable[[], None],
                 local_only: bool = True, adapter: str = ""):
        self.cfg = cfg
        self.local_only = local_only
        self.adapter = adapter  # hciN, empty = default adapter
        self.announcer = announcer
        self.on_change = on_change
        self.state = "disconnected"  # state values sent over D-Bus: disconnected, connecting, connected, error
        self.error = ""
        self.values: dict = {}
        self.values_at = 0.0
        self._services: list[dircon.Service] = []
        self._client: BleakClient | None = None
        self._notifying: set[str] = set()
        # Only for Zwift on this computer: listen on loopback only, so nobody in the network can
        # control the trainer.
        self._server = dircon.Server(self, host="127.0.0.1" if local_only else "0.0.0.0", port=cfg.port)
        self._task: asyncio.Task | None = None
        self._disconnected = asyncio.Event()
        self._was_connected = False
        self._pending: dict[str, asyncio.Future] = {}
        self._trouble: list[float] = []  # times of drops and failed attempts
        self._grace: asyncio.Task | None = None  # grace period after a drop
        self._announced: list[str] = []  # services announced to Zwift

    # --- GattBackend for the DIRCON server ---

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
        # Control point: the answer arrives as an indication; Zwift wants it in the write response.
        await self.set_notify(char_uuid, True)
        answer = asyncio.get_running_loop().create_future()
        self._pending[char_uuid] = answer
        try:
            await client.write_gatt_char(char_uuid, data, response=True)
            return await asyncio.wait_for(answer, CONTROL_POINT_TIMEOUT)
        except asyncio.TimeoutError:
            log.warning("%s: no answer from control point %s to %s", self.cfg.address, char_uuid[4:8],
                        data.hex(" "))
            return None
        finally:
            self._pending.pop(char_uuid, None)

    async def set_notify(self, char_uuid: str, enabled: bool) -> None:
        # BLE notifications stay on once they are running; the DIRCON sessions filter on their
        # own. That way a client that unsubscribes does not disturb any other.
        if not enabled or char_uuid in self._notifying:
            return
        client = self._require_client()
        await client.start_notify(char_uuid, lambda _c, data, u=char_uuid: self._notified(u, data))
        self._notifying.add(char_uuid)

    # --- Lifecycle ---

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
                self._set_state("error", text)
                log.warning("%s: %s (%s: %s)", self.cfg.address, text, type(e).__name__, e)
            # After an established connection retry right away; try a device that keeps failing
            # less often, so it does not hold the BlueZ lock all the time.
            failures = 0 if self._was_connected else failures + 1
            self._was_connected = False
            await self._teardown()
            self._start_grace()
            if not_found:
                # Find sleeping devices (strap without skin contact) again quickly: the scan only
                # occupies BlueZ briefly, unlike a hanging connection attempt.
                await asyncio.sleep(NOT_FOUND_DELAY)
                continue
            await asyncio.sleep(min(RECONNECT_DELAY * 2 ** max(failures - 1, 0), MAX_RECONNECT_DELAY))

    async def _connect_and_serve(self) -> None:
        self._set_state("connecting")
        self._disconnected.clear()
        # An orphaned BlueZ connection (e.g. after an aborted attempt) keeps the device from
        # advertising again; bleak then no longer finds it.
        async with connect_lock:
            await bluez_disconnect(self.cfg.address, self.adapter)
            bluez = {"adapter": self.adapter} if self.adapter else {}
            device = await BleakScanner.find_device_by_address(self.cfg.address, timeout=FIND_TIMEOUT, bluez=bluez)
            if device is None:
                raise BleakDeviceNotFoundError(self.cfg.address, f"Device with address {self.cfg.address} was not found.")
            client = BleakClient(device, disconnected_callback=lambda _c: self._disconnected.set(),
                                 timeout=connect_timeout(self.cfg.name), bluez=bluez)
            self._client = client  # disconnect in _teardown even on failure
            await client.connect()
        services = self._collect_services(client)
        if not services:
            raise RuntimeError(N_("Device offers no supported service (FTMS, Cycling Power, CSC, heart rate)"))
        self._cancel_grace()
        if self._server.running and [s.uuid for s in services] != self._announced:
            await self._withdraw()  # different services than before the drop: announce again
        self._services = services
        if not self._server.running:
            await self._server.start()
            self._announced = [s.uuid for s in services]
            await self.announcer.publish(dircon_name(self.cfg), self.cfg.port, self._announced,
                                         mac=self.cfg.address, serial=self.cfg.address.replace(":", ""),
                                         local_only=self.local_only)
        else:
            log.info("%s: reconnected, Zwift connection was kept", self.cfg.address)
        # Subscribe to the measurements for the live display even before Zwift does, plus
        # everything Zwift had subscribed to before a drop.
        wanted = [u for u in gatt.DECODERS if self._char_props(u) & {"notify", "indicate"}]
        wanted += [u for u in self._server.subscribed() if u not in wanted]
        for uuid in wanted:
            await self.set_notify(uuid, True)
        self._was_connected = True
        self._set_state("connected")
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
        log.info("%s: grace period expired, withdrawing device from Zwift", self.cfg.address)
        self._grace = None
        await self._withdraw()

    async def _withdraw(self) -> None:
        """Withdraw the announcement and close the DIRCON server (Zwift loses the device)."""
        self._cancel_grace()
        await self.announcer.withdraw(self.cfg.port)
        await self._server.stop()
        self._announced = []
        self.on_change()

    async def _teardown(self) -> None:
        """Tear down the BLE side only; announcement and DIRCON server stay (grace period)."""
        self._notifying.clear()
        if self._client:
            try:
                await self._client.disconnect()
            except Exception:
                pass
            self._client = None
        if self.state == "connected":
            self._set_state("disconnected")

    # --- Helpers ---

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
            log.info("%s: control point %s answers %s", self.cfg.address, char_uuid[4:8], value.hex(" "))
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
