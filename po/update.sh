#!/bin/bash
# Texte aus QML und Python sammeln (po/tretlager.pot), Kataloge abgleichen und übersetzen.
#   po/update.sh          .pot neu erzeugen, po/*.po per msgmerge abgleichen (braucht gettext)
#   po/update.sh --build  nur .po → data/locale/*.mo (reines Python, geht auch ohne gettext)
set -euo pipefail
cd "$(dirname "$0")/.."
if [ "${1:-}" != "--build" ]; then
  xgettext --from-code=UTF-8 --language=Python -k_ -kN_ -kngettext:1,2 -kpgettext:1c,2 \
      --add-comments=Translators: -o po/python.pot $(git ls-files "tretlager/*.py") tretlager/i18n.py helper/setup-system
  xgettext --from-code=UTF-8 --language=JavaScript -ki18n -ki18nc:1c,2 -ki18np:1,2 \
      --add-comments=Translators: -o po/qml.pot tretlager/kde/qml/*.qml
  msgcat --use-first po/python.pot po/qml.pot -o po/tretlager.pot
  sed -i "s/charset=CHARSET/charset=UTF-8/" po/tretlager.pot
  rm po/python.pot po/qml.pot
  for po in po/*.po; do msgmerge -q --update --backup=none --no-fuzzy-matching "$po" po/tretlager.pot; done
fi
for po in po/*.po; do
  lang="$(basename "$po" .po)"
  python3 build-aux/msgfmt.py "$po" "tretlager/data/locale/$lang/LC_MESSAGES/tretlager.mo"
done
