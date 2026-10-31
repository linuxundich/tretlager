#!/bin/bash
# Build the Tretlager Flatpak and install it for the current user (on tinytin: 20 cores).
#   build-aux/flatpak/build.sh            build + install
#   build-aux/flatpak/build.sh --bundle   also create tretlager.flatpak (single file, takes a while)
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
cd "$here"
flatpak install --user --noninteractive --or-update flathub \
  org.kde.Platform//6.11 org.kde.Sdk//6.11 io.qt.PySide.BaseApp//6.11 org.freedesktop.Sdk.Extension.mingw-w64//25.08
flatpak-builder --user --install --force-clean --repo=repo build-dir de.linuxundich.Tretlager.yml
if [ "${1:-}" = "--bundle" ]; then
  flatpak build-bundle --runtime-repo=https://dl.flathub.org/repo/flathub.flatpakrepo repo tretlager.flatpak de.linuxundich.Tretlager
  ls -la tretlager.flatpak
fi
