#!/bin/bash
# T2b (Opt-in-Test): Anmeldung im System-Browser, Code gegen Token tauschen, dann start.sh.
# Das Passwort sieht dieses Skript nie. Das Token bleibt für die Testsitzung in
# $XDG_RUNTIME_DIR (RAM, nur für den Benutzer lesbar, weg nach Abmelden/Neustart).
# Nutzt die nicht dokumentierte Launcher-Anmeldung (client_id Game_Launcher) – AGB-Risiko,
# nur als Test für das eigene Konto.
set -euo pipefail
cd "$(dirname "$0")"; . ./env.sh
REALM=https://secure.zwift.com/auth/realms/zwift
REDIR=https://launcher.zwift.com/launcher

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
curl -sS --proto '=https' -o "$TOK.new" -w 'token http=%{http_code}\n' \
  --data-urlencode client_id=Game_Launcher --data-urlencode redirect_uri="$REDIR" \
  --data-urlencode code="$CODE" --data-urlencode grant_type=authorization_code \
  --data-urlencode scope=openid "$REALM/protocol/openid-connect/token"
if python3 -I -c 'import json,sys; d=json.load(open(sys.argv[1])); assert "access_token" in d; print("Token ok, gültig", d.get("expires_in"), "s")' "$TOK.new"; then
  mv "$TOK.new" "$TOK"
else
  rm -f "$TOK.new"; echo "Token-Antwort ungültig"; exit 1
fi
echo "3) Starte Zwift ..."
exec ./start.sh
