#!/bin/bash
# Installiert Helfer, Schlüssel und Polkit-Aktion systemweit – nur für Tests vor dem Debian-Paket.
# Als root ausführen:  sudo build-aux/install-system-test.sh   (--remove zum Entfernen)
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
if [ "${1:-}" = "--remove" ]; then
  rm -f /usr/libexec/tretlager/setup-system /usr/share/tretlager/winehq.key \
        /usr/share/polkit-1/actions/de.linuxundich.tretlager.policy
  rmdir /usr/libexec/tretlager /usr/share/tretlager 2>/dev/null || true
  echo "Systemteile entfernt."; exit 0
fi
install -D -m 0755 "$SRC/helper/setup-system" /usr/libexec/tretlager/setup-system
install -D -m 0644 "$SRC/tretlager/data/winehq.key" /usr/share/tretlager/winehq.key
install -D -m 0644 "$SRC/data/de.linuxundich.tretlager.policy" /usr/share/polkit-1/actions/de.linuxundich.tretlager.policy
echo "Helfer, Schlüssel und Polkit-Aktion installiert."
