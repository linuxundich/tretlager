#!/bin/bash
# Extract strings from QML and Python (po/tretlager.pot), merge the catalogs and compile them.
#   po/update.sh          regenerate the .pot, merge po/*.po with msgmerge (needs gettext)
#   po/update.sh --build  only .po -> data/locale/*.mo (pure Python, works without gettext)
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
