#!/bin/bash
# Installs Tretlager for the current user into ~/.local (test installation, no root).
#   build-aux/install-user.sh            install or update
#   build-aux/install-user.sh --remove   uninstall
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
LIBDIR="$HOME/.local/lib/tretlager"
DOCDIR="$HOME/.local/share/doc/tretlager"
UNITDIR="$HOME/.config/systemd/user"
APPDIR="$HOME/.local/share/applications"

if [ "${1:-}" = "--remove" ]; then
  systemctl --user disable --now tretlager-bridge.service 2>/dev/null || true
  rm -rf "$LIBDIR" "$DOCDIR" "$UNITDIR/tretlager-bridge.service" "$APPDIR"/de.linuxundich.Tretlager*.desktop
  systemctl --user daemon-reload
  echo "Tretlager removed (settings in ~/.config/tretlager are kept)."
  exit 0
fi

mkdir -p "$LIBDIR" "$DOCDIR" "$UNITDIR" "$APPDIR"
rm -rf "$LIBDIR/tretlager"
cp -r "$SRC/tretlager" "$LIBDIR/"
find "$LIBDIR" -name __pycache__ -prune -exec rm -rf {} +
cp "$SRC"/*.md "$DOCDIR/" 2>/dev/null || true
for f in tretlager-bridge.service de.linuxundich.Tretlager.desktop de.linuxundich.Tretlager.Zwift.desktop; do
  case $f in *.service) dest="$UNITDIR/$f" ;; *) dest="$APPDIR/$f" ;; esac
  sed -e "s|@LIBDIR@|$LIBDIR|g" -e "s|@DOCDIR@|$DOCDIR|g" "$SRC/data/$f.in" > "$dest"
done
systemctl --user daemon-reload
if systemctl --user is-active -q tretlager-bridge.service; then
  systemctl --user restart tretlager-bridge.service
fi
echo "Tretlager installed to $LIBDIR"
