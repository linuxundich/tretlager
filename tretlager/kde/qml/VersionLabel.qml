import QtQuick
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

// „Version 0.9.0 · Build 9ea5ca9“: Die Build-Kennung (wie bei `flatpak info`) unterscheidet zwei
// Bauten derselben Version.
Controls.Label {
    text: backend.build !== "" ? i18n("Version %1 · Build %2", backend.version, backend.build)
                               : i18n("Version %1", backend.version)
    color: Kirigami.Theme.disabledTextColor
    font: Kirigami.Theme.smallFont
}
