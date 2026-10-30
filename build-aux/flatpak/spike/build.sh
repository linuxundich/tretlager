#!/bin/bash
# F0-Spike bauen und als Einzeldatei (tretlager-spike.flatpak) für tinytin ablegen.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
cd "$here"
flatpak-builder --user --force-clean --repo=repo build-dir de.linuxundich.Tretlager.yml
flatpak build-bundle --runtime-repo=https://dl.flathub.org/repo/flathub.flatpakrepo repo tretlager-spike.flatpak de.linuxundich.Tretlager
ls -la tretlager-spike.flatpak
