import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

Kirigami.ScrollablePage {
    title: "Willkommen"

    PageContent {

        Kirigami.Icon {
            source: Qt.resolvedUrl("../../data/icons/de.linuxundich.Tretlager.svg")
            Layout.preferredWidth: Kirigami.Units.iconSizes.enormous
            Layout.preferredHeight: Kirigami.Units.iconSizes.enormous
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: Kirigami.Units.gridUnit
        }

        Kirigami.Heading {
            text: "Zwift unter Linux"
            level: 1
            Layout.alignment: Qt.AlignHCenter
        }

        Controls.Label {
            text: "Tretlager richtet Zwift auf diesem Rechner ein und verbindet deinen Trainer und Pulsgurt."
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
        }

        Kirigami.Separator { Layout.fillWidth: true }

        Kirigami.Heading { text: "Das brauchst du"; level: 3 }

        Repeater {
            model: [
                ["user-identity", "Ein Zwift-Konto"],
                ["drive-harddisk", "Etwa 11 GB freien Speicher"],
                ["network-wired", "Internet für etwa 5 GB Download"],
                ["network-bluetooth", "Smart-Trainer und Pulsgurt mit Bluetooth (später)"]
            ]
            delegate: RowLayout {
                required property var modelData
                spacing: Kirigami.Units.smallSpacing
                Kirigami.Icon {
                    source: modelData[0]
                    Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                    Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
                }
                Controls.Label { text: modelData[1]; Layout.fillWidth: true; wrapMode: Text.WordWrap }
            }
        }

        Hint {
            text: "Zwift unterstützt Linux offiziell nicht. Tretlager nutzt Wine und lädt Zwift von der offiziellen Quelle; an Zwift selbst wird nichts verändert."
        }

        Controls.Button {
            text: "Hilfe lesen"
            icon.name: "help-contents"
            flat: true
            Layout.alignment: Qt.AlignHCenter
            onClicked: applicationWindow().pageStack.push(Qt.resolvedUrl("HelpPage.qml"))
        }

        Controls.Button {
            text: "Los geht's"
            icon.name: "go-next"
            highlighted: true
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: Kirigami.Units.largeSpacing
            onClicked: {
                backend.runChecks()
                applicationWindow().pageStack.push(Qt.resolvedUrl("CheckPage.qml"))
            }
        }
    }
}
