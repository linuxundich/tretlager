#!/bin/bash
# Installs the helper, the key and the polkit action system-wide - only for testing before the Debian package.
# Run as root:  sudo build-aux/install-system-test.sh   (--remove to uninstall)
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
if [ "${1:-}" = "--remove" ]; then
  rm -f /usr/libexec/tretlager/setup-system /usr/share/tretlager/winehq.key \
        /usr/share/polkit-1/actions/de.linuxundich.tretlager.policy
  rmdir /usr/libexec/tretlager /usr/share/tretlager 2>/dev/null || true
  echo "System parts removed."; exit 0
fi
install -D -m 0755 "$SRC/helper/setup-system" /usr/libexec/tretlager/setup-system
install -D -m 0644 "$SRC/tretlager/data/winehq.key" /usr/share/tretlager/winehq.key
install -D -m 0644 "$SRC/data/de.linuxundich.tretlager.policy" /usr/share/polkit-1/actions/de.linuxundich.tretlager.policy
echo "Helper, key and polkit action installed."
