## Overview
<!-- icon: help-about -->

Tretlager sets up Zwift on Linux, starts it with one click and connects your trainer and heart
rate strap.

- **Zwift under Wine**: The official Zwift Windows client runs under Wine, which Tretlager brings
  along. Tretlager downloads Zwift from Zwift, verifies the signature and does not modify it.
- **Sensor bridge**: Zwift cannot use Bluetooth under Wine. The bridge connects the trainer and
  heart rate strap and offers them to Zwift as Wahoo devices; the Companion app is not needed.
- **Not a Zwift program**: Zwift does not support Linux. Use at your own risk.
- **XP and drops**: Zwift may not be happy that a software bridge sends data that could be
  manipulated. Restrictions up to a suspended account cannot be ruled out. The warnings from the
  first start are under *About Tretlager*.

## Riding
<!-- icon: media-playback-start -->

- **Starting Zwift**: From the overview or from the application menu under *Zwift (Tretlager)*.
- **Before the start**: Tretlager checks the Zwift environment against the installed version (after
  a Tretlager update, for example, against a new Wine) and installs Zwift updates through the Zwift
  launcher.
- **Tretlager updates**: Wine and everything else come with Tretlager itself, through the software
  centre or `flatpak update`. Tretlager keeps the last proven Wine version; if Zwift runs worse after
  an update, switch on *Use previous Wine version* in the overview.
- **During the ride**: Tretlager waits minimised and tidies up after Zwift closes.
- **Not for races**: Tretlager does not guarantee that the sensor bridge passes power, cadence
  and heart rate to Zwift correctly. Do not use Tretlager for races or competitions with results.
- **On a laptop**: Connect the power adapter before starting and keep it connected. Switching
  between AC and battery can crash the NVIDIA driver.

## Sensors
<!-- icon: network-bluetooth -->

- **Pairing in Tretlager**: Search and add under *Sensors*. Pedal briefly beforehand; a heart
  rate strap only transmits with skin contact.
- **Pairing in Zwift**: Once under *Paired Devices*, select “Wahoo KICKR …” for power, cadence
  and resistance and “Wahoo HRM …” for heart rate. The warning icons for Bluetooth and ANT+ are
  normal.
- **Pausing**: Pause sensors that are not in use instead of removing them. Tretlager then stops
  searching for them, and the pairing is kept.
- **Bluetooth adapter**: A USB dongle on an extension cable next to the trainer helps with dead
  spots and with chips that do not get along with a sensor.

## Heart rate straps
<!-- icon: network-bluetooth -->

- **Long connection intervals**: The Wahoo TICKR and the Garmin HRM-Pro Plus switch their Bluetooth
  connection to a long interval by themselves, the TICKR to about 1 second, the HRM-Pro Plus to
  about 2 seconds. Heart rate still arrives in time, but Linux remembers the interval and starts the
  next connection with it. Reconnecting therefore takes up to two minutes (*Found, reading the
  sensor…*), and for about half a minute heart rate comes only every few seconds until the strap
  shortens the interval.
- **Garmin HRM-Pro Plus**: It ends the Bluetooth connection by itself every 7 to 15 minutes,
  also right next to the computer, and then stays silent for two to five minutes. Tretlager
  reconnects on its own, but heart rate is missing for that time. For Zwift the Wahoo TICKR is
  the better choice.
- **Not paired in the system settings**: Tretlager connects to the straps without pairing. A
  strap that is connected without anyone reading the heart rate, for example while pairing it in
  the Bluetooth settings, immediately asks for the slow interval, and when paired, Linux keeps it
  even after a restart. Remove straps paired by mistake in the Bluetooth settings.

## Sign-in
<!-- icon: user-identity -->

The Zwift launcher cannot sign in on Linux at the moment. Tretlager therefore opens Zwift's
sign-in page in a window of its own. **Zwift does not allow this (terms of service, section 5);
using it is at your own risk.**

- **Password**: Only enter it on Zwift's page. Tretlager neither reads nor stores it.
- **Your own browser**: For password managers or signing in with Google or Apple. The browser
  then shows “Bad Request”; copy the address and Tretlager picks it up.
- **Session**: Stored in the keyring and renewed automatically. After a week without riding,
  signing in again is required.
- **Signing out**: Overview → *Sign in again…* → *Sign out*. This also ends the session at Zwift.

## Privacy and storage locations
<!-- icon: security-high -->

- **No usage data**: Tretlager only connects to Zwift, GitHub (winetricks) and Microsoft
  (components via winetricks). Zwift itself sends crash reports to Sentry.
- **Everything in one place**: `~/.var/app/de.linuxundich.Tretlager/` – Zwift environment and backups
  under `data/tretlager`, bridge settings under `config/tretlager`, cache under `cache/tretlager`.
- **Removing**: Uninstalling removes the program; the Zwift environment (about 9 GB) stays until the
  folder is deleted (`flatpak uninstall --delete-data de.linuxundich.Tretlager`).

## Setup
<!-- icon: configure -->

- **1. Check**: Graphics, Bluetooth, device announcement, disk space and internet. Nothing on the
  system changes, no password is needed.
- **2. Zwift**: Download and installation, about ten minutes. You can cancel at any time; the
  next start continues where it left off.
- **3.–5. Sign-in, sensors, done**: See the sections above.
- **Zwift on the NVIDIA card**: On laptops with two graphics chips Tretlager puts
  Zwift on the NVIDIA card itself (PRIME offload). If the card is switched off (envycontrol
  "integrated"), first run `sudo envycontrol -s hybrid`, reboot and run `flatpak update` (fetches the
  matching NVIDIA part for the Flatpak). Tretlager sets up graphics again on the next start.

## Troubleshooting
<!-- icon: help-hint; wide -->

- [emblem-important] **Heart rate far too high**: Moisten the electrodes, tighten the strap and
  wear only one strap. If that does not help, replace the strap's battery: a weak battery often
  gives erratic or too high readings.
- [view-refresh] **Sensor stays at “Searching for the device…”**: Pedal briefly or unclip the
  strap for a moment; the bridge searches every ten seconds. Bluetooth headphones on the same
  adapter crowd out the sensors while they play: disconnect them or connect them through a second
  adapter; Tretlager points this out.
- [data-warning] **Sensor is found but never connects**: It does not get along with the
  Bluetooth chip; Tretlager reports known cases on the sensor. Remedy: USB Bluetooth dongle.
- [network-bluetooth] **Sensor does not come back after a break**: Allow up to three minutes
  (see *Heart rate straps*). If the sensor then shows *unplug and plug in the Bluetooth adapter,
  or restart the computer*, Linux keeps a slow connection setting for it that only this clears;
  switching Bluetooth off and on does not help. If no connection comes up at all, the Bluetooth
  chip is stuck: Tretlager switches Bluetooth off and on once by itself, unless headphones or
  other devices are connected.
- [system-suspend-inhibited] **Screen dims or locks during the ride**: Switch on *Keep screen on
  during the ride* in the main window. It only applies while Zwift runs.
- [network-wireless-disconnected] **Connection drops often**: Move the computer closer to the
  trainer or place a USB Bluetooth dongle on an extension cable next to the trainer.
- [network-bluetooth] **Zwift does not find the sensors**: Check under *Sensors* that the bridge
  is running and the sensors are connected; without a running Avahi (`avahi-daemon`) Zwift will not
  find them.
- [battery-low] **Zwift hangs after plugging or unplugging the power adapter**: Close it with
  Alt+F4 and restart it with the power adapter connected; if that does not help, restart the
  computer.
- [video-display] **Blurry picture on Plasma**: *System Settings* → *Display* → *Legacy
  Applications (X11)* → *Apply scaling themselves*.
- [update-none] **Zwift does not start after an update**: Sidebar → *Check setup*. The backup
  taken before the update is kept.
- [view-fullscreen] **Zwift's picture sticks out over the edge of the screen**: Double-click
  Zwift's title bar twice (restore, maximise). Tretlager remembers the monitor Zwift was on and
  opens it there next time.
- [debug-run] **Reporting a problem**: *About Tretlager* → *Error reports*: switch on *Detailed
  logging*, reproduce the problem, then *Save error report…* and send the ZIP file to the
  developer. It contains system information and the logs of Tretlager, the sensor bridge, Wine and
  Zwift (Zwift's log also lists the names of nearby riders); sign-in data, passwords and e-mail
  addresses are removed. Alternatively start with *Start with detailed logging* from the
  application menu (right-click on Tretlager) or `flatpak run de.linuxundich.Tretlager --debug`.
