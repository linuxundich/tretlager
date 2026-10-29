import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

Kirigami.ScrollablePage {
    title: "Fertig"

    Component.onCompleted: backend.markSetupComplete()

    PageContent {

        Kirigami.Icon {
            source: "data-success"
            Layout.preferredWidth: Kirigami.Units.iconSizes.enormous
            Layout.preferredHeight: Kirigami.Units.iconSizes.enormous
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: Kirigami.Units.gridUnit
        }
        Kirigami.Heading { text: "Zwift ist bereit"; level: 1; Layout.alignment: Qt.AlignHCenter }

        Controls.Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: "Einmalig in Zwift unter „Gekoppelte Geräte“: bei Leistungsquelle, Trittfrequenz und Widerstand „Wahoo KICKR …“ wählen, bei Herzfrequenz „Wahoo HRM …“. Die Warnungen zu Bluetooth und ANT+ in Zwift sind normal."
        }

        Controls.Button {
            text: "Zum Hauptfenster"
            icon.name: "go-home"
            highlighted: true
            Layout.alignment: Qt.AlignHCenter
            onClicked: {
                applicationWindow().pageStack.clear()
                applicationWindow().pageStack.push(Qt.resolvedUrl("MainPage.qml"))
            }
        }
    }
}
