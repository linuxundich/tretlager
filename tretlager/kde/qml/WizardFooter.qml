import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

// Fußleiste der Assistentenseiten: links Abbrechen bzw. Überspringen (nach der Einrichtung
// sonst „Assistent schließen“), rechts der nächste Schritt.
Controls.ToolBar {
    id: footer
    property string skipText: ""
    property string nextText: i18n("Next")
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
        // Nach abgeschlossener Einrichtung lässt sich der Assistent jederzeit verlassen.
        Controls.Button {
            visible: footer.skipText === "" && backend.setupComplete
            text: i18n("Close assistant")
            icon.name: "window-close"
            flat: true
            onClicked: applicationWindow().show("overview")
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
