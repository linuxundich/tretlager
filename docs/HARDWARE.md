# Tested hardware and software

Tretlager is developed and tested on the hardware below, all of it my own. If you run it on
something else, an [issue](https://github.com/linuxundich/tretlager/issues) with your results is
very welcome, whether it works or not.

Status: October 31, 2026, Tretlager 0.9.0 and the current `master`.

## Computers

### TUXEDO InfinityBook Pro Gen7 (main system)

All development, the long test rides and the demo video happened on this laptop.

| | |
|---|---|
| CPU | Intel Core i7-12700H (14 cores, 20 threads) |
| RAM | 32 GB |
| Graphics | Intel Iris Xe (Alder Lake-P) + NVIDIA GeForce RTX 3050 Ti Laptop GPU, 4 GB |
| NVIDIA driver | 580.178.04 from the TUXEDO repositories, Flatpak extension `org.freedesktop.Platform.GL.nvidia-580-178-04` |
| Bluetooth | Intel Wi-Fi 6 AX201 (built in, USB ID 8087:0026); TP-Link UB500 USB adapter (Realtek RTL8761BU, 2357:0604) |
| System | TUXEDO OS (Debian forky base), kernel 7.2.7 (TUXEDO), BlueZ 5.87 |
| Desktop | KDE Plasma 6.7.4 on Wayland, display scaling 160 % |

Zwift runs on the RTX 3050 Ti through PRIME render offload and uses about 3.3 GB of video
memory. With the laptop on its power supply the game runs smoothly; switching between power
supply and battery during a ride can hang the NVIDIA driver (Xid 69), so Tretlager warns about it.

### Dell XPS 15 9560 (second system)

Used to check that Tretlager also works outside Plasma and on another distribution.

| | |
|---|---|
| CPU | Intel Core i7-7700HQ (4 cores, 8 threads) |
| RAM | 16 GB |
| Graphics | Intel HD Graphics 630 + NVIDIA GeForce GTX 1050 Mobile, 4 GB |
| NVIDIA driver | 580.196.07 (`nvidia-580xx-dkms`), hybrid mode, Flatpak extension `org.freedesktop.Platform.GL.nvidia-580-196-07` |
| Bluetooth | Qualcomm Atheros QCA61x4 (built in) |
| System | Arch Linux, kernel 7.2.11, Avahi 0.9-rc5 |
| Desktop | GNOME 51.1 on Wayland |

Installation, setup of Wine and Zwift, the sign-in and starting Zwift on the GTX 1050 (OpenGL
4.6) work. Under GNOME Tretlager uses the Breeze style but follows GNOME's light or dark mode and
interface font. With the NVIDIA card switched off (integrated mode), Tretlager falls back to the
Intel graphics and redoes its graphics check when the card comes back.

## Sensors

| Sensor | Bluetooth services | Result |
|---|---|---|
| Wahoo KICKR V4 (smart trainer) | FTMS with control point, Cycling Power, Wahoo's own services | Power, cadence, ERG mode and simulated climbs work. The V4 has no built-in Direct Connect; the bridge provides it. |
| Wahoo TICKR (heart rate strap) | Heart Rate | Works. Implausibly high values usually mean a weak battery or dry electrodes. |
| Garmin HRM-Pro Plus (heart rate strap) | Heart Rate | Works through the Intel AX201 and the TP-Link UB500. Switches its connection to a 2 s interval, which Linux keeps for the next connection; reconnecting then takes up to two minutes (0.11.2 waits for it). Ends the connection by itself every 7–15 minutes and is silent for a few minutes. The earlier finding "hangs with the AX201" (2026-10-29) was this slow interval. |

ANT+ is not supported; Wine cannot reach ANT+ sticks, and the bridge only speaks Bluetooth LE.

### Headphones and the number of connections

No chip maker states a usable connection limit: TP-Link advertises "7 devices" for the UB500,
Intel gives no figure for the AX201. The real limit is airtime. On tinytin (2026-11-03) the KICKR
and Bluetooth headphones were connected through the built-in AX201; the TICKR then got nothing
but connection timeouts for ten minutes and connected only once the headphones were removed.
KICKR plus TICKR alone connect reliably. The bridge therefore lists other devices connected
through its adapter, and the interface warns while a sensor is waiting and headphones share the
adapter.

### Range

The built-in Bluetooth of a laptop in the next room is not enough for a reliable trainer
connection. A USB Bluetooth adapter on an extension cable near the bike helps, as does running the
bridge on a computer next to the trainer ("Offer on the network").

## Software

| Component | Version |
|---|---|
| Tretlager | 0.9.0 and `master` (Flatpak `de.linuxundich.Tretlager`) |
| Flatpak | 1.18.4 |
| Runtime | `org.kde.Platform//6.11` (Qt 6.11.3, Kirigami, Kirigami Addons) |
| Python UI | PySide6 6.11.3 from `io.qt.PySide.BaseApp//6.11` (with QtWebEngine for the sign-in window) |
| Wine | 11.20, built from source inside the Flatpak (WoW64, no 32-bit host libraries needed) |
| Windows components | Fonts, .NET Framework 4.8 and WebView2 via winetricks |
| Zwift | 1.124.0 (game) with Zwift launcher 1.2 |
| Sensor bridge | Python with Bleak 3, BlueZ on the host, Avahi for the mDNS announcement |

### What did not work

- Zwift's own sign-in in the launcher: it needs `Windows.UI.Composition`, which Wine, Wine
  Staging and Proton do not implement. Tretlager signs in through Zwift's web page instead.
- Bluetooth directly from Wine: GATT notifications and writes are stubs in Wine 11, so Zwift sees
  no Bluetooth sensors. The bridge solves this over the network protocol.
- DXVK is not needed: Zwift renders with OpenGL.

## Demo video

The [demo video](tretlager-demo.mp4) was recorded on the InfinityBook in a Plasma session at
2880 × 1620 with GPU Screen Recorder through the screencast portal, mouse and keyboard driven by a
script. For the recording the bridge used a simulated rider instead of the real trainer and strap
(marked "Rider data simulated" in the video); Tretlager, the bridge, Wine and Zwift are the real
thing.
