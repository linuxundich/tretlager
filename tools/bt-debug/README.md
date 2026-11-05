# bt-debug

Records everything needed to understand why a sensor drops or does not come back:
the bridge in debug mode (every notification), BlueZ events of the sensors including the
disconnect reason, the bridge state per device, kernel and bluetoothd messages, and, with a
second Bluetooth adapter, whether the sensor is advertising while the bridge fails to connect.
The probe only listens; it never connects to a device itself.

Copy the folder to the test computer as `~/bt-debug/bin/` (the Flatpak must be installed):

    bt-debug.sh start            # restarts the bridge in debug mode, recording to ~/bt-debug/runs/<time>/
    bt-debug.sh btmon            # optional, as root: full HCI trace (hci.btsnoop, open with Wireshark)
    bt-debug.sh mark "walked away"
    bt-debug.sh marks            # interactive: p = pause, w = walked away, z = back, anything else as typed
    bt-debug.sh stop
    analyze.py ~/bt-debug/runs/current [--since 10m]

`--observe auto` (default) watches advertising through the adapter the bridge does not use.
