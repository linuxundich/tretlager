import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

// Kopfzeile der Assistentenseiten: „Schritt n von 6“ und ein kurzer Satz, was jetzt passiert.
Controls.Control {
    id: header
    property int step
    property string text

    padding: Kirigami.Units.largeSpacing
    background: Rectangle { color: Kirigami.Theme.backgroundColor }

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.largeSpacing
        RowLayout {
            spacing: Kirigami.Units.largeSpacing
            Controls.Label {
                text: i18n("Schritt %1 von %2", header.step, applicationWindow().steps.length)
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
