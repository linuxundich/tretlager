#!/bin/bash
# Builds dist/tretlager_<version>_all.deb from the source tree (needs only dpkg-deb).
#   build-aux/build-deb.sh
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="$(sed -n 's/^## \[\([0-9][^]]*\)\].*/\1/p' "$SRC/CHANGELOG.md" | head -1)"
[ -n "$VERSION" ] || { echo "No version in CHANGELOG.md"; exit 1; }
grep -q "^__version__ = \"$VERSION\"" "$SRC/tretlager/__init__.py" \
  || { echo "tretlager/__init__.py: __version__ does not match CHANGELOG ($VERSION)"; exit 1; }
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
R="$STAGE/root"

# Translations: po/*.po -> tretlager/data/locale (pure Python, tinytin lacks gettext)
"$SRC/po/update.sh" --build

# Python package (without tests and bytecode)
install -d "$R/usr/lib/python3/dist-packages"
cp -r "$SRC/tretlager" "$R/usr/lib/python3/dist-packages/"
find "$R/usr/lib/python3/dist-packages/tretlager" -name __pycache__ -prune -exec rm -rf {} +

# Launch commands
install -d "$R/usr/bin"
printf '#!/bin/sh\nexec python3 -m tretlager.kde "$@"\n' > "$R/usr/bin/tretlager"
printf '#!/bin/sh\nexec python3 -m tretlager.bridge "$@"\n' > "$R/usr/bin/tretlager-bridge"
chmod 0755 "$R"/usr/bin/*

# Helper, key, polkit
install -D -m 0755 "$SRC/helper/setup-system" "$R/usr/libexec/tretlager/setup-system"
install -D -m 0644 "$SRC/tretlager/data/winehq.key" "$R/usr/share/tretlager/winehq.key"
install -D -m 0644 "$SRC/data/de.linuxundich.tretlager.policy" "$R/usr/share/polkit-1/actions/de.linuxundich.tretlager.policy"

# systemd user service and desktop files (without the PYTHONPATH of the user installation)
install -d "$R/usr/lib/systemd/user" "$R/usr/share/applications"
sed -e '/^Environment=PYTHONPATH/d' -e 's|^ExecStart=.*|ExecStart=/usr/bin/tretlager-bridge|' \
    -e 's|@DOCDIR@|/usr/share/doc/tretlager|' "$SRC/data/tretlager-bridge.service.in" \
    > "$R/usr/lib/systemd/user/tretlager-bridge.service"
for d in de.linuxundich.Tretlager de.linuxundich.Tretlager.Zwift; do
  sed -e 's|^Exec=env PYTHONPATH=@LIBDIR@ /usr/bin/python3 -m tretlager.kde|Exec=tretlager|' \
      "$SRC/data/$d.desktop.in" > "$R/usr/share/applications/$d.desktop"
done
install -D -m 0644 "$SRC/tretlager/data/icons/de.linuxundich.Tretlager.svg" \
    "$R/usr/share/icons/hicolor/scalable/apps/de.linuxundich.Tretlager.svg"

# Documentation
install -d "$R/usr/share/doc/tretlager"
cp "$SRC"/README.md "$SRC"/FEASIBILITY.md "$SRC"/BACKLOG.md "$SRC"/docs/*.md "$R/usr/share/doc/tretlager/"
gzip -9n -c "$SRC/CHANGELOG.md" > "$R/usr/share/doc/tretlager/changelog.gz"
install -m 0644 "$SRC/build-aux/deb/copyright" "$R/usr/share/doc/tretlager/copyright"

# Control files
install -d "$R/DEBIAN"
SIZE="$(du -sk --exclude=DEBIAN "$R" | cut -f1)"
sed -e "s/@VERSION@/$VERSION/" -e "s/@SIZE@/$SIZE/" "$SRC/build-aux/deb/control.in" > "$R/DEBIAN/control"
install -m 0755 "$SRC/build-aux/deb/postinst" "$R/DEBIAN/postinst"

mkdir -p "$SRC/dist"
OUT="$SRC/dist/tretlager_${VERSION}_all.deb"
dpkg-deb --root-owner-group -Zxz --build "$R" "$OUT" >/dev/null
echo "$OUT"
