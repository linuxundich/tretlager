import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

// Header of the wizard pages: "Step n of m" and a short sentence on what happens now.
// The number is derived from the step id (the Flatpak has no "Prepare" step).
Controls.Control {
    id: header
    property string stepId
    readonly property int step: applicationWindow().stepIds.indexOf(stepId) + 1
    property string text

    padding: Kirigami.Units.largeSpacing
    background: Rectangle { color: Kirigami.Theme.backgroundColor }

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.largeSpacing
        RowLayout {
            spacing: Kirigami.Units.largeSpacing
            Controls.Label {
                text: i18n("Step %1 of %2", header.step, applicationWindow().steps.length)
                font.bold: true
            }
            Controls.Label {
                Layout.fillWidth: true
                text: header.text
                color: Kirigami.Theme.disabledTextColor
                elide: Text.ElideRight
            }
        }
        Controls.ProgressBar {
            Layout.fillWidth: true
            from: 0
            to: applicationWindow().steps.length
            value: header.step
        }
    }
}
