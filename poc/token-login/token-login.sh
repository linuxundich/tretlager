#!/bin/bash
# T2b (opt-in test): sign in in the system browser, exchange the code for a token, then start.sh.
# This script never sees the password. The token stays in $XDG_RUNTIME_DIR for the test
# session (RAM, readable only by the user, gone after logout/reboot).
# Uses the undocumented launcher sign-in (client_id Game_Launcher) - terms-of-service risk,
# only as a test for your own account.
set -euo pipefail
cd "$(dirname "$0")"; . ./env.sh
REALM=https://secure.zwift.com/auth/realms/zwift
REDIR=https://launcher.zwift.com/launcher

STATE=$(head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n')
URL="$REALM/protocol/openid-connect/auth?response_type=code&client_id=Game_Launcher&redirect_uri=https%3A%2F%2Flauncher.zwift.com%2Flauncher&scope=openid&login=true&state=$STATE"
echo "1) The Zwift sign-in opens in the browser. Please sign in there."
setsid -f xdg-open "$URL" >/dev/null 2>&1 </dev/null || echo "   Please open manually: $URL"
echo "2) Afterwards the address bar shows launcher.zwift.com/launcher?state=...&code=..."
read -r -p "   Paste this complete address here and press Enter (quickly, the code expires soon): " BACK
CODE=$(printf %s "$BACK" | grep -oE '[?&]code=[^&]+' | head -1 | cut -d= -f2- || true)
GOT_STATE=$(printf %s "$BACK" | grep -oE '[?&]state=[^&]+' | head -1 | cut -d= -f2- || true)
[ -n "$CODE" ] || { echo "No code= found."; exit 1; }
[ "$GOT_STATE" = "$STATE" ] || echo "Note: state does not match, trying anyway."

TOK="$XDG_RUNTIME_DIR/tretlager-token.json"
umask 077
curl -sS --proto '=https' -o "$TOK.new" -w 'token http=%{http_code}\n' \
  --data-urlencode client_id=Game_Launcher --data-urlencode redirect_uri="$REDIR" \
  --data-urlencode code="$CODE" --data-urlencode grant_type=authorization_code \
  --data-urlencode scope=openid "$REALM/protocol/openid-connect/token"
if python3 -I -c 'import json,sys; d=json.load(open(sys.argv[1])); assert "access_token" in d; print("Token ok, valid for", d.get("expires_in"), "s")' "$TOK.new"; then
  mv "$TOK.new" "$TOK"
else
  rm -f "$TOK.new"; echo "Invalid token response"; exit 1
fi
echo "3) Starting Zwift ..."
exec ./start.sh
