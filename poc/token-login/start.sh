#!/bin/bash
# Startet Zwift mit einem vorhandenen Token aus token-login.sh (Opt-in-Test, AGB-Risiko).
# Ablauf wie netbrain/zwift: Launcher mit SilentLaunch, ZwiftApp.exe als dessen Kind.
set -euo pipefail
cd "$(dirname "$0")"; . ./env.sh
export WINEDEBUG=err+all,fixme-all
ZDIR="$WINEPREFIX/drive_c/Program Files (x86)/Zwift"
RFP="$PWD/RunFromProcess.exe"
LOG="$HOME/tretlager-t2/zwiftapp.log"
TOK="$XDG_RUNTIME_DIR/tretlager-token.json"
[ -f "$RFP" ] || { echo "RunFromProcess.exe fehlt"; exit 1; }
[ -f "$TOK" ] || { echo "Kein Token, erst token-login.sh"; exit 1; }
python3 -I -c '
import json, os, sys, time
d = json.load(open(sys.argv[1]))
left = os.path.getmtime(sys.argv[1]) + int(d.get("expires_in", 0)) - time.time()
print("Token noch %d min gültig" % (left // 60))
sys.exit(0 if left > 60 else 1)' "$TOK" || { echo "Token abgelaufen, erst token-login.sh"; exit 1; }

cd "$ZDIR"
wineserver -k 2>/dev/null || true
# T3: Auf Hybrid-Notebooks unter XWayland bekommt Wine die NVIDIA-Karte nur über GLX.
wine reg add 'HKCU\Software\Wine\X11 Driver' /v UseEGL /t REG_SZ /d N /f >/dev/null 2>&1
# Zwift soll die Auflösung des Desktops nicht umstellen.
wine reg add 'HKCU\Software\Wine\X11 Driver' /v UseXRandR /t REG_SZ /d N /f >/dev/null 2>&1

echo "Starte Launcher im Hintergrund (SilentLaunch) ..."
wine start /d "C:\\Program Files (x86)\\Zwift" ZwiftLauncher.exe SilentLaunch >"$LOG" 2>&1
LPID=""
for i in $(seq 1 30); do
  LPID=$(wine tasklist 2>/dev/null | tr -d '\r' | awk '/^ZwiftLauncher.exe/{print $2; exit}')
  [ -n "$LPID" ] && break; sleep 1
done
[ -n "$LPID" ] || { echo "Launcher läuft nicht"; exit 1; }
sleep 5

echo "Starte ZwiftApp.exe als Kind des Launchers (PID $LPID, NVIDIA per GLX + PRIME-Offload) ..."
export __NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia
wine "$RFP" "$LPID" ZwiftApp.exe "--token=$(cat "$TOK")" >>"$LOG" 2>&1 \
  || { echo "RunFromProcess fehlgeschlagen, siehe $LOG"; exit 1; }
sleep 15
wine taskkill /f /im ZwiftLauncher.exe >/dev/null 2>&1 || true
wine taskkill /f /im ZwiftWindowsCrashHandler.exe >/dev/null 2>&1 || true
echo "Zwift läuft. Log: $LOG"
