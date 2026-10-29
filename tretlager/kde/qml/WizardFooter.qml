import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

// Fußleiste der Assistentenseiten: links Abbrechen bzw. Überspringen, rechts der nächste Schritt.
Controls.ToolBar {
    id: footer
    property string skipText: ""
    property string nextText: "Weiter"
    property string nextIcon: "go-next"
    property bool nextEnabled: true
    property bool nextVisible: true
    signal skip()
    signal next()

    position: Controls.ToolBar.Footer

    contentItem: RowLayout {
        spacing: Kirigami.Units.mediumSpacing
        Controls.Button {
            visible: footer.skipText !== ""
            text: footer.skipText
            flat: true
            onClicked: footer.skip()
        }
        Item { Layout.fillWidth: true }
        Controls.Button {
            visible: footer.nextVisible
            text: footer.nextText
            icon.name: footer.nextIcon
            highlighted: true
            enabled: footer.nextEnabled
            onClicked: footer.next()
        }
    }
}
