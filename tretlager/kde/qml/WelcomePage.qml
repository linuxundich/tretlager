import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

FormCard.FormCardPage {
    id: page
    title: "Willkommen"

    ColumnLayout {
        Layout.alignment: Qt.AlignHCenter
        Layout.maximumWidth: Kirigami.Units.gridUnit * 30
        Layout.topMargin: Kirigami.Units.gridUnit * 2
        spacing: Kirigami.Units.smallSpacing

        Kirigami.Icon {
            source: "de.linuxundich.Tretlager"
            fallback: Qt.resolvedUrl("../../data/icons/de.linuxundich.Tretlager.svg")
            Layout.preferredWidth: Kirigami.Units.iconSizes.enormous
            Layout.preferredHeight: Kirigami.Units.iconSizes.enormous
            Layout.alignment: Qt.AlignHCenter
        }
        Kirigami.Heading {
            text: "Zwift unter Linux"
            level: 1
            Layout.alignment: Qt.AlignHCenter
        }
        Controls.Label {
            text: "Tretlager richtet Zwift auf diesem Rechner ein und verbindet Trainer und Pulsgurt."
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            color: Kirigami.Theme.disabledTextColor
            Layout.fillWidth: true
        }
    }

    FormCard.FormHeader { title: "Voraussetzungen" }
    FormCard.FormCard {
        FormCard.FormTextDelegate { text: "Zwift-Konto mit Abo"; icon.name: "user-identity" }
        FormCard.FormDelegateSeparator {}
        FormCard.FormTextDelegate { text: "Etwa 11 GB freier Speicher"; icon.name: "drive-harddisk" }
        FormCard.FormDelegateSeparator {}
        FormCard.FormTextDelegate { text: "Internetzugang für etwa 5 GB Download"; icon.name: "network-wired" }
        FormCard.FormDelegateSeparator {}
        FormCard.FormTextDelegate {
            text: "Smart-Trainer und Pulsgurt mit Bluetooth"
            description: "Erst im fünften Schritt nötig"
            icon.name: "network-bluetooth"
        }
    }

    FormCard.FormHeader { title: "Wichtig" }
    FormCard.FormCard {
        FormCard.FormTextDelegate {
            text: "Kein offizielles Zwift-Programm"
            description: "Zwift unterstützt Linux nicht. Tretlager nutzt Wine und lädt Zwift von der offiziellen "
                + "Quelle, ohne Zwift zu verändern. Die Anmeldung über den Browser widerspricht den "
                + "Zwift-Nutzungsbedingungen. Benutzung auf eigene Gefahr."
            icon.name: "dialog-warning"
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormButtonDelegate {
            text: "Über Tretlager und Lizenzen"
            icon.name: "help-about"
            onClicked: applicationWindow().pageStack.push(Qt.resolvedUrl("AboutPage.qml"))
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormButtonDelegate {
            text: "Hilfe lesen"
            icon.name: "help-contents"
            onClicked: applicationWindow().pageStack.push(Qt.resolvedUrl("HelpPage.qml"))
        }
    }

    Item { implicitHeight: Kirigami.Units.gridUnit }

    footer: WizardFooter {
        nextText: "Einrichtung beginnen"
        onNext: {
            backend.runChecks()
            applicationWindow().pageStack.push(Qt.resolvedUrl("CheckPage.qml"))
        }
    }
}
