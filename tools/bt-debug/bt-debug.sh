#!/bin/bash
# Record everything needed to understand sensor drops of the Tretlager bridge on this computer.
#
#   bt-debug.sh start [--observe auto|none|hciN]   start a recording (restarts the bridge in debug mode;
#                                                   TL_SRC=<dir> runs the bridge from a source tree)
#   bt-debug.sh mark "walked away"                  add a marker (pause, walk away, back, …)
#   bt-debug.sh marks                               interactive: every line typed becomes a marker
#   bt-debug.sh btmon                               HCI trace as root (asks for the sudo password)
#   bt-debug.sh status                              is everything running, last events
#   bt-debug.sh stop                                stop the recording, bridge back to normal
#   bt-debug.sh restart-probe                       reload probe.py into the running recording
#
# Recordings live in ~/bt-debug/runs/<time>/, ~/bt-debug/runs/current points to the newest.
set -euo pipefail

APP=de.linuxundich.Tretlager
BASE="$HOME/bt-debug"
BIN="$(cd "$(dirname "$0")" && pwd)"
RUNS="$BASE/runs"
CUR="$RUNS/current"
STATE="$HOME/.var/app/$APP/.local/state/tretlager"
CONFIG="$HOME/.var/app/$APP/config/tretlager"
UNITS=(btdbg-kernel btdbg-bluetoothd btdbg-bridge btdbg-bridgelog btdbg-probe)

stamp() { date +%Y-%m-%dT%H:%M:%S.%3N%:z; }

bridge_quit() {
    gdbus call --session --dest $APP.Bridge --object-path /de/linuxundich/Tretlager/Bridge \
        --method $APP.Bridge.Quit >/dev/null 2>&1 || true
    for _ in $(seq 20); do
        gdbus call --session --dest org.freedesktop.DBus --object-path /org/freedesktop/DBus \
            --method org.freedesktop.DBus.NameHasOwner $APP.Bridge 2>/dev/null | grep -q true || return 0
        sleep 0.5
    done
    echo "bridge did not quit" >&2
}

snapshot() {
    {
        echo "== $(stamp)"; uname -a; flatpak info $APP | grep -E "Version|Commit"
        echo "== lsusb"; lsusb
        echo "== btusb autosuspend: $(cat /sys/module/btusb/parameters/enable_autosuspend 2>/dev/null)"
        for d in /sys/bus/usb/devices/*; do
            [ -f "$d/idVendor" ] || continue
            [ -d "$d/$(basename "$d"):1.0/bluetooth" ] || ls "$d"/*/bluetooth >/dev/null 2>&1 || continue
            echo "$d $(cat "$d/idVendor"):$(cat "$d/idProduct") power=$(cat "$d/power/control") delay=$(cat "$d/power/autosuspend_delay_ms" 2>/dev/null)"
        done
        echo "== adapters"; bluetoothctl list
        for a in $(bluetoothctl list | awk '{print $2}'); do bluetoothctl show "$a" | grep -E "Controller|Name|Powered|Discovering|Roles" ; done
        echo "== connected"; bluetoothctl devices Connected
        echo "== power supply"; cat /sys/class/power_supply/A*/online 2>/dev/null
        echo "== bridge.json"; cat "$CONFIG/bridge.json"
    } > "$1" 2>&1
}

kill_instance() {  # $1 = probe or bridge
    local f="$CUR/$1.instance" id
    [ -s "$f" ] || return 0
    id=$(tr -dc 0-9 < "$f")
    [ -n "$id" ] && flatpak kill "$id" 2>/dev/null || true
}

unit_up() { systemctl --user is-active --quiet "$1"; }

case "${1:-}" in
start)
    shift
    OBSERVE=auto
    [ "${1:-}" = --observe ] && OBSERVE="$2"
    if [ -L "$CUR" ] && unit_up btdbg-probe; then echo "recording already running: $(readlink -f "$CUR")"; exit 1; fi
    RUN="$RUNS/$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$RUN"
    ln -sfn "$RUN" "$CUR"
    snapshot "$RUN/start.txt"
    for u in "${UNITS[@]}"; do systemctl --user reset-failed "$u" 2>/dev/null || true; done
    systemd-run --user -q --unit=btdbg-kernel -p StandardOutput="truncate:$RUN/kernel.log" \
        journalctl -k -f -n 0 -o short-iso-precise
    systemd-run --user -q --unit=btdbg-bluetoothd -p StandardOutput="truncate:$RUN/bluetoothd.log" \
        journalctl -u bluetooth -f -n 0 -o short-iso-precise
    # Bridge in debug mode (every notification in bridge.log); our instance owns the D-Bus name,
    # the Tretlager window and Zwift use it as usual.
    bridge_quit
    # flatpak run moves the app into its own scope: stopping the unit does not end it, so keep
    # the instance id and end it with `flatpak kill`.
    # TL_SRC=<source tree>: run the bridge from there (inside the Flatpak runtime) instead of /app
    if [ -n "${TL_SRC:-}" ]; then
        BRIDGE_CMD="--filesystem=$TL_SRC:ro --env=PYTHONPATH=$TL_SRC --command=python3"
        BRIDGE_ARGS="-m tretlager.bridge"
        echo "$(stamp) bridge from $TL_SRC" >> "$RUN/marks.log"
    else
        BRIDGE_CMD="--command=/app/bin/tretlager-bridge"; BRIDGE_ARGS=""
    fi
    systemd-run --user -q --unit=btdbg-bridge -p StandardOutput="truncate:$RUN/bridge-stderr.log" \
        /bin/sh -c "exec /usr/bin/flatpak run --instance-id-fd=3 --env=TRETLAGER_DEBUG=1 $BRIDGE_CMD \
        $APP $BRIDGE_ARGS 3>'$RUN/bridge.instance'"
    # The probe must only start once the debug bridge owns the name (it never activates one).
    for _ in $(seq 30); do
        gdbus call --session --dest org.freedesktop.DBus --object-path /org/freedesktop/DBus \
            --method org.freedesktop.DBus.NameHasOwner $APP.Bridge 2>/dev/null | grep -q true && break
        sleep 0.5
    done
    systemd-run --user -q --unit=btdbg-bridgelog -p StandardOutput="truncate:$RUN/bridge.log" \
        tail -F -n 0 "$STATE/bridge.log"
    systemd-run --user -q --unit=btdbg-probe -p StandardError="truncate:$RUN/probe-stderr.log" \
        /bin/sh -c "exec /usr/bin/flatpak run --instance-id-fd=3 --filesystem='$BASE' --command=python3 $APP \
        '$BIN/probe.py' --out '$RUN/events.jsonl' --observe '$OBSERVE' 3>'$RUN/probe.instance'"
    echo "$(stamp) start observe=$OBSERVE" >> "$RUN/marks.log"
    echo "recording: $RUN"
    ;;
mark)
    shift
    [ -L "$CUR" ] || { echo "no recording" >&2; exit 1; }
    echo "$(stamp) ${*:-mark}" >> "$CUR/marks.log"
    echo "marked: ${*:-mark}"
    ;;
marks)
    [ -L "$CUR" ] || { echo "no recording" >&2; exit 1; }
    echo "Type a note and press Enter for each event (p = pause, w = walked away, z = back). Ctrl+D ends."
    while IFS= read -r line; do
        case "$line" in p) line="pause";; w) line="walked away";; z) line="back";; esac
        echo "$(stamp) ${line:-mark}" >> "$CUR/marks.log"
        echo "  ✓ $(date +%H:%M:%S) ${line:-mark}"
    done
    ;;
btmon)
    [ -L "$CUR" ] || { echo "start a recording first" >&2; exit 1; }
    echo "HCI trace to $(readlink -f "$CUR")/hci.btsnoop – keep this window open, Ctrl+C ends."
    sudo btmon -w "$(readlink -f "$CUR")/hci.btsnoop"
    ;;
restart-probe)
    kill_instance probe
    systemctl --user stop btdbg-probe 2>/dev/null || true
    systemctl --user reset-failed btdbg-probe 2>/dev/null || true
    RUN="$(readlink -f "$CUR")"
    systemd-run --user -q --unit=btdbg-probe -p StandardError="append:$RUN/probe-stderr.log" \
        /bin/sh -c "exec /usr/bin/flatpak run --instance-id-fd=3 --filesystem='$BASE' --command=python3 $APP \
        '$BIN/probe.py' --out '$RUN/events.jsonl' --observe '${2:-auto}' 3>'$RUN/probe.instance'"
    echo "probe restarted"
    ;;
status)
    for u in "${UNITS[@]}"; do printf '%-18s %s\n' "$u" "$(systemctl --user is-active "$u" 2>/dev/null || true)"; done
    [ -L "$CUR" ] && { echo "run: $(readlink -f "$CUR")"; ls -la "$CUR/" | tail -n +2; echo "-- marks"; tail -5 "$CUR/marks.log"; }
    ;;
stop)
    [ -L "$CUR" ] && echo "$(stamp) stop" >> "$CUR/marks.log"
    kill_instance probe
    bridge_quit
    kill_instance bridge
    for u in "${UNITS[@]}"; do systemctl --user stop "$u" 2>/dev/null || true; done
    [ -L "$CUR" ] && snapshot "$CUR/stop.txt"
    echo "stopped; the Tretlager window starts the normal bridge again when needed"
    ;;
*)
    sed -n '2,13p' "$0"; exit 1
    ;;
esac
