#!/bin/bash
# Starts Zwift with an existing token from token-login.sh (opt-in test, terms-of-service risk).
# Same flow as netbrain/zwift: launcher with SilentLaunch, ZwiftApp.exe as its child.
set -euo pipefail
cd "$(dirname "$0")"; . ./env.sh
export WINEDEBUG=err+all,fixme-all
ZDIR="$WINEPREFIX/drive_c/Program Files (x86)/Zwift"
RFP="$PWD/RunFromProcess.exe"
LOG="$HOME/tretlager-t2/zwiftapp.log"
TOK="$XDG_RUNTIME_DIR/tretlager-token.json"
[ -f "$RFP" ] || { echo "RunFromProcess.exe is missing"; exit 1; }
[ -f "$TOK" ] || { echo "No token, run token-login.sh first"; exit 1; }
python3 -I -c '
import json, os, sys, time
d = json.load(open(sys.argv[1]))
left = os.path.getmtime(sys.argv[1]) + int(d.get("expires_in", 0)) - time.time()
print("Token valid for another %d min" % (left // 60))
sys.exit(0 if left > 60 else 1)' "$TOK" || { echo "Token expired, run token-login.sh first"; exit 1; }

cd "$ZDIR"
wineserver -k 2>/dev/null || true
# T3: On hybrid laptops under XWayland, Wine gets the NVIDIA GPU only via GLX.
wine reg add 'HKCU\Software\Wine\X11 Driver' /v UseEGL /t REG_SZ /d N /f >/dev/null 2>&1
# Zwift must not change the desktop resolution.
wine reg add 'HKCU\Software\Wine\X11 Driver' /v UseXRandR /t REG_SZ /d N /f >/dev/null 2>&1

echo "Starting the launcher in the background (SilentLaunch) ..."
wine start /d "C:\\Program Files (x86)\\Zwift" ZwiftLauncher.exe SilentLaunch >"$LOG" 2>&1
LPID=""
for i in $(seq 1 30); do
  LPID=$(wine tasklist 2>/dev/null | tr -d '\r' | awk '/^ZwiftLauncher.exe/{print $2; exit}')
  [ -n "$LPID" ] && break; sleep 1
done
[ -n "$LPID" ] || { echo "Launcher is not running"; exit 1; }
sleep 5

echo "Starting ZwiftApp.exe as a child of the launcher (PID $LPID, NVIDIA via GLX + PRIME offload) ..."
export __NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia
wine "$RFP" "$LPID" ZwiftApp.exe "--token=$(cat "$TOK")" >>"$LOG" 2>&1 \
  || { echo "RunFromProcess failed, see $LOG"; exit 1; }
sleep 15
wine taskkill /f /im ZwiftLauncher.exe >/dev/null 2>&1 || true
wine taskkill /f /im ZwiftWindowsCrashHandler.exe >/dev/null 2>&1 || true
echo "Zwift is running. Log: $LOG"
