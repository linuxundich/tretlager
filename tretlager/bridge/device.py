"""Hold a BLE device and offer it as a DIRCON device."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Callable

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakDBusError, BleakDeviceNotFoundError, BleakError
from dbus_fast import BusType, Message, MessageType, Variant
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
# Setting up the link (BlueZ Device1.Connect). Attempts run one after another (connect_lock): a
# hanging attempt holds up all other devices for that long, so this stays short.
CONNECT_TIMEOUT = 20.0
# Service discovery once the link is up, outside connect_lock. Sensors switch their own connection
# to long intervals (TICKR about 1 s, Garmin HRM-Pro Plus about 2 s), and Linux starts every new
# connection with the interval the sensor asked for last: the kernel keeps it per adapter, only
# unplugging the adapter or a restart clears it (bt-debug and btmon on tinytin, 2026-11-06). At 1 s
# discovery took 23 s (TICKR), the old limit of 20 s gave up just before and the bridge looped
# forever. Once subscribed, the sensors pick their interval themselves, so patience is enough.
DISCOVERY_TIMEOUT = 150.0  # HRM-Pro Plus at 2 s: 38 s and 80 s measured on 2026-11-06
# Discovery failures in a row with the link up before the bridge asks for a replug.
SLOW_FAILURES = 2
# How long a device stays announced to Zwift, with its DIRCON server open, after a drop.
# Zwift keeps the pairing and simply receives data again after reconnecting; otherwise the
# device disappears from Zwift and has to be found again (QA audit B-04).
GRACE = 45.0
# Scan for the address before connecting. Separate from the connect timeout: otherwise bleak
# searches 40 s for an absent device and holds the lock all that time; a trainer that wants to
# reconnect and the scan in the user interface then waited up to a minute (measured 2026-10-30).
# Advertising sensors send several times per second, 8 s is enough.
FIND_TIMEOUT = 8.0
# Stuck controller (tinytin 2026-11-03, Intel AX201, kernel 7.2): after a strap came back in range,
# every connection attempt ran into the kernel's 20 s LE timeout for half an hour, although the
# strap was advertising. At each timeout the kernel logged "ACL packet for unknown connection
# handle": the controller held a link to the strap that the kernel had already given up on, and
# that link blocks every new attempt. Removing the sensor in Tretlager does not reach it; only a
# controller reset does. So after this many timeouts in a row of a device that was found, the
# bridge switches the adapter off and on (all devices reconnect, Zwift keeps them: grace period),
# at most once per RESET_INTERVAL and only if no other Bluetooth device (headphones) is connected.
STUCK_TIMEOUTS = 3
RESET_INTERVAL = 600.0
_last_reset: dict[str, float] = {}
resetting: set[str] = set()  # adapters being switched off and on; the service skips its adapter check


# BlueZ sets up only one connection at a time per adapter ("Operation already in progress").
connect_lock = asyncio.Lock()

_PROPS = {"read": dircon.PROP_READ, "write": dircon.PROP_WRITE, "write-without-response": dircon.PROP_WRITE,
          "notify": dircon.PROP_NOTIFY, "indicate": dircon.PROP_INDICATE}


def device_path(address: str, adapter: str = "") -> str:
    return f"/org/bluez/{adapter or 'hci0'}/dev_" + address.upper().replace(":", "_")


async def bluez_connect(address: str, adapter: str, timeout: float) -> None:
    """Set up the link only (Device1.Connect returns before service discovery is done).

    Raises asyncio.TimeoutError when no link comes up, BleakDBusError for BlueZ errors.
    """
    path = device_path(address, adapter)
    bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    try:
        try:
            reply = await asyncio.wait_for(bus.call(Message(destination="org.bluez", path=path,
                                                            interface="org.bluez.Device1", member="Connect")),
                                           timeout)
        except asyncio.TimeoutError:
            # cancel the pending request, otherwise BlueZ keeps trying
            await bus.call(Message(destination="org.bluez", path=path, interface="org.bluez.Device1",
                                   member="Disconnect"))
            raise
        if reply.message_type == MessageType.ERROR and reply.error_name != "org.bluez.Error.AlreadyConnected":
            raise BleakDBusError(reply.error_name, reply.body)
    finally:
        bus.disconnect()


async def bluez_disconnect(address: str, adapter: str = "") -> None:
    """Disconnect the device in BlueZ if it is still connected (errors are ignored)."""
    path = device_path(address, adapter)
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


# Audio profiles (A2DP sink, headset, hands-free): a playing headphone takes most of the airtime.
AUDIO_UUIDS = {"0000110b-0000-1000-8000-00805f9b34fb", "00001108-0000-1000-8000-00805f9b34fb",
               "0000111e-0000-1000-8000-00805f9b34fb"}


def foreign_devices(objects: dict, adapter: str, bridged) -> list[dict]:
    """Devices connected through the adapter that the bridge does not handle, e.g. headphones.

    Finding on tinytin (2026-11-03): with headphones and the KICKR on the AX201, the TICKR got
    nothing but connection timeouts for ten minutes, until the headphones were removed. No chip
    maker states a usable limit (TP-Link: "7 devices" for the UB500, Intel: none); in practice
    audio is what crowds out the sensors.
    """
    path = f"/org/bluez/{adapter or 'hci0'}/"
    ours = {a.upper() for a in bridged}
    out = []
    for obj, ifaces in sorted(objects.items()):
        dev = ifaces.get("org.bluez.Device1")
        if not dev or not obj.startswith(path) or not (dev.get("Connected") and dev["Connected"].value):
            continue
        address = dev["Address"].value.upper() if "Address" in dev else ""
        if address in ours:
            continue
        icon = dev["Icon"].value if "Icon" in dev else ""
        uuids = set(dev["UUIDs"].value) if "UUIDs" in dev else set()
        name = (dev["Alias"].value if "Alias" in dev else "") or address
        out.append({"name": name, "address": address, "audio": icon.startswith("audio-") or bool(uuids & AUDIO_UUIDS)})
    return out


async def bluez_objects(bus) -> dict:
    reply = await bus.call(Message(destination="org.bluez", path="/",
                                   interface="org.freedesktop.DBus.ObjectManager", member="GetManagedObjects"))
    return {} if reply.message_type == MessageType.ERROR else reply.body[0]


async def other_devices(adapter: str, bridged) -> list[dict]:
    """foreign_devices() from BlueZ; empty if BlueZ does not answer."""
    try:
        bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    except Exception:
        return []
    try:
        return foreign_devices(await bluez_objects(bus), adapter, bridged)
    finally:
        bus.disconnect()


async def reset_adapter(adapter: str, bridged) -> str:
    """Switch the adapter off and on again; returns "" when done, otherwise the reason (N_ text)."""
    hci = adapter or "hci0"
    if time.monotonic() - _last_reset.get(hci, -RESET_INTERVAL) < RESET_INTERVAL:
        return N_("Bluetooth is stuck – switch Bluetooth off and on again")
    path = f"/org/bluez/{hci}"
    try:
        bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
    except Exception:
        return N_("Bluetooth is stuck – switch Bluetooth off and on again")

    async def powered(on: bool) -> bool:
        reply = await bus.call(Message(destination="org.bluez", path=path,
                                       interface="org.freedesktop.DBus.Properties", member="Set",
                                       signature="ssv", body=["org.bluez.Adapter1", "Powered", Variant("b", on)]))
        return reply.message_type != MessageType.ERROR

    try:
        others = foreign_devices(await bluez_objects(bus), hci, bridged)
        if others:
            log.warning("%s stuck, but %s is connected: not resetting", hci, others[0]["address"])
            return N_("Another Bluetooth device such as headphones is using the adapter – disconnect it or "
                      "connect it through another adapter")
        _last_reset[hci] = time.monotonic()
        resetting.add(hci)
        log.warning("%s seems stuck, switching it off and on", hci)
        try:
            if not await powered(False):
                return N_("Bluetooth is stuck – switch Bluetooth off and on again")
            await asyncio.sleep(1.0)
        finally:
            # Also when cancelled: never leave the adapter switched off.
            await powered(True)
            await asyncio.sleep(2.0)
            resetting.discard(hci)
        return ""
    finally:
        bus.disconnect()


def describe_error(e: BaseException) -> tuple[str, bool]:
    """Plain-language sentence for a connection error, and whether the device was merely not found.

    BlueZ and bleak messages like "org.bluez.Error.NotReady" mean nothing to users; the raw message
    still goes to the bridge log.
    """
    raw = str(e)
    if isinstance(e, BleakDeviceNotFoundError) or "was not found" in raw or "UnknownObject" in raw:
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
                 local_only: bool = True, adapter: str = "", bridged: Callable[[], list[str]] = lambda: []):
        self.cfg = cfg
        self.bridged = bridged  # addresses of all bridged devices (they may drop during a reset)
        self.local_only = local_only
        self.adapter = adapter  # hciN, empty = default adapter
        self.announcer = announcer
        self.on_change = on_change
        self.state = "disconnected"  # state values sent over D-Bus: disconnected, connecting, reading, connected, error
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
        self._link_up = False  # the current attempt got past Device1.Connect

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
        timeouts = 0  # link timeouts in a row of a device that was found (stuck controller)
        slow = 0  # discovery failures in a row with the link up (slow interval kept by the kernel)
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
                link_up, self._link_up = self._link_up, False
                # find_device_by_address returns None instead of timing out: a timeout before the
                # link is up comes from Device1.Connect, the device was advertising.
                timeouts = timeouts + 1 if isinstance(e, (asyncio.TimeoutError, TimeoutError)) and not link_up else 0
                slow = slow + 1 if link_up else 0
                if slow >= SLOW_FAILURES:
                    # The adapter reset does not clear the remembered interval and drops the other
                    # devices, so ask for what helps.
                    text = N_("Bluetooth keeps a slow setting for this sensor – unplug and plug in the "
                              "Bluetooth adapter, or restart the computer")
                self._set_state("error", text)
                log.warning("%s: %s (%s: %s)%s", self.cfg.address, text, type(e).__name__, e,
                            " [link was up]" if link_up else "")
                if timeouts >= STUCK_TIMEOUTS:
                    async with connect_lock:
                        await self._teardown()
                        reason = await reset_adapter(self.adapter, self.bridged())
                    if reason:
                        self._set_state("error", reason)
                    else:
                        timeouts = 0
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
            started = time.monotonic()
            await bluez_connect(self.cfg.address, self.adapter, CONNECT_TIMEOUT)
            self._link_up = True
        # Found and linked; with a remembered slow interval reading the services takes minutes, and
        # "Searching for the device…" looked as if the strap was not found (Christoph, 2026-11-06).
        self._set_state("reading")
        # Service discovery without the lock: bleak sees the link and only waits for the services.
        client = BleakClient(device, disconnected_callback=lambda _c: self._disconnected.set(),
                             timeout=DISCOVERY_TIMEOUT, bluez=bluez)
        self._client = client  # disconnect in _teardown even on failure
        await client.connect()
        self._link_up = False
        log.info("%s: connected, services after %.0f s", self.cfg.address, time.monotonic() - started)
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
            log.debug("%s: control point %s answers %s", self.cfg.address, char_uuid[4:8], value.hex(" "))
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
