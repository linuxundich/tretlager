#!/bin/bash
# T2b (Opt-in-Test): Anmeldung im System-Browser, Code gegen Token tauschen, Zwift starten.
# Das Passwort sieht dieses Skript nie. Das Token liegt nur in $XDG_RUNTIME_DIR (RAM) und wird
# nach dem Start gelöscht. Nutzt die nicht dokumentierte Launcher-Anmeldung (client_id
# Game_Launcher) – AGB-Risiko, nur als Test für das eigene Konto.
# Ablauf wie netbrain/zwift: Launcher mit SilentLaunch starten, ZwiftApp.exe als dessen Kind.
set -euo pipefail
cd "$(dirname "$0")"; . ./env.sh
export WINEDEBUG=err+all,fixme-all
REALM=https://secure.zwift.com/auth/realms/zwift
REDIR=https://launcher.zwift.com/launcher
ZDIR="$WINEPREFIX/drive_c/Program Files (x86)/Zwift"
RFP="$PWD/RunFromProcess.exe"
LOG="$HOME/tretlager-t2/zwiftapp.log"
[ -f "$RFP" ] || { echo "RunFromProcess.exe fehlt"; exit 1; }

STATE=$(head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n')
URL="$REALM/protocol/openid-connect/auth?response_type=code&client_id=Game_Launcher&redirect_uri=https%3A%2F%2Flauncher.zwift.com%2Flauncher&scope=openid&login=true&state=$STATE"
echo "1) Im Browser öffnet sich die Zwift-Anmeldung. Bitte dort anmelden."
setsid -f xdg-open "$URL" >/dev/null 2>&1 </dev/null || echo "   Bitte von Hand öffnen: $URL"
echo "2) Danach steht in der Adresszeile launcher.zwift.com/launcher?state=...&code=..."
read -r -p "   Diese komplette Adresse hier einfügen und Enter (zügig, der Code gilt kurz): " BACK
CODE=$(printf %s "$BACK" | grep -oE '[?&]code=[^&]+' | head -1 | cut -d= -f2- || true)
GOT_STATE=$(printf %s "$BACK" | grep -oE '[?&]state=[^&]+' | head -1 | cut -d= -f2- || true)
[ -n "$CODE" ] || { echo "Kein code= gefunden."; exit 1; }
[ "$GOT_STATE" = "$STATE" ] || echo "Hinweis: state passt nicht, versuche trotzdem."

TOK="$XDG_RUNTIME_DIR/tretlager-token.json"
umask 077
trap 'rm -f "$TOK"' EXIT
curl -sS --proto '=https' -o "$TOK" -w 'token http=%{http_code}\n' \
  --data-urlencode client_id=Game_Launcher --data-urlencode redirect_uri="$REDIR" \
  --data-urlencode code="$CODE" --data-urlencode grant_type=authorization_code \
  --data-urlencode scope=openid "$REALM/protocol/openid-connect/token"
python3 -I -c 'import json,sys; d=json.load(open(sys.argv[1])); assert "access_token" in d; print("Token ok, gültig", d.get("expires_in"), "s")' "$TOK" \
  || { echo "Token-Antwort ungültig"; exit 1; }

cd "$ZDIR"
echo "3) Starte Launcher im Hintergrund (SilentLaunch) ..."
wineserver -k 2>/dev/null || true
wine start /d "C:\\Program Files (x86)\\Zwift" ZwiftLauncher.exe SilentLaunch >"$LOG" 2>&1
LPID=""
for i in $(seq 1 30); do
  LPID=$(wine tasklist 2>/dev/null | tr -d '\r' | awk '/^ZwiftLauncher.exe/{print $2; exit}')
  [ -n "$LPID" ] && break; sleep 1
done
[ -n "$LPID" ] || { echo "Launcher läuft nicht"; exit 1; }
echo "   Launcher-PID $LPID"
sleep 5

echo "4) Starte ZwiftApp.exe als Kind des Launchers (NVIDIA per GLX + PRIME-Offload) ..."
# T3: Auf Hybrid-Notebooks unter XWayland bekommt Wine die NVIDIA-Karte nur über GLX.
wine reg add 'HKCU\Software\Wine\X11 Driver' /v UseEGL /t REG_SZ /d N /f >/dev/null 2>&1
export __NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia
wine "$RFP" "$LPID" ZwiftApp.exe "--token=$(cat "$TOK")" >>"$LOG" 2>&1 \
  && echo "   gestartet" || { echo "   RunFromProcess fehlgeschlagen, siehe $LOG"; exit 1; }
sleep 15
rm -f "$TOK"
echo "   Token-Datei gelöscht. Launcher und Crash-Handler werden beendet."
wine taskkill /f /im ZwiftLauncher.exe >/dev/null 2>&1 || true
wine taskkill /f /im ZwiftWindowsCrashHandler.exe >/dev/null 2>&1 || true
echo "Fertig. Zwift sollte laufen. Log: $LOG"
