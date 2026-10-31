import QtQuick
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

// "Version 0.9.0 · Build 9ea5ca9": the build id (as in `flatpak info`) distinguishes two
// builds of the same version.
Controls.Label {
    text: backend.build !== "" ? i18n("Version %1 · build %2", backend.version, backend.build)
                               : i18n("Version %1", backend.version)
    color: Kirigami.Theme.disabledTextColor
    font: Kirigami.Theme.smallFont
}
