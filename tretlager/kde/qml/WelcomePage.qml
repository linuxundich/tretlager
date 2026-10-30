import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

ColumnsPage {
    id: page
    title: i18n("Willkommen")

    PageHero {
        title: i18n("Zwift unter Linux")
        text: i18n("Tretlager richtet Zwift auf diesem Rechner ein und verbindet Trainer und Pulsgurt. Die Einrichtung führt in %1 Schritten durch alles.", applicationWindow().stepIds.length)
    }

    leftCards: [
        FormCard.FormHeader { title: i18n("Voraussetzungen") },
        FormCard.FormCard {
            FormCard.FormTextDelegate { text: i18n("Zwift-Konto mit Abo"); icon.name: "user-identity" }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate { text: i18n("Etwa 11 GB freier Speicher"); icon.name: "drive-harddisk" }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate { text: i18n("Internetzugang für etwa 5 GB Download"); icon.name: "network-wired" }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: i18n("Smart-Trainer und Pulsgurt mit Bluetooth")
                description: i18n("Erst bei Schritt %1 nötig", applicationWindow().stepIds.indexOf("sensors") + 1)
                icon.name: "network-bluetooth"
            }
        }
    ]

    rightCards: [
        FormCard.FormHeader { title: i18n("Wichtig") },
        FormCard.FormCard {
            FormCard.FormTextDelegate {
                text: i18n("Kein offizielles Zwift-Programm")
                description: i18n("Zwift unterstützt Linux nicht. Tretlager nutzt Wine und lädt Zwift von der offiziellen Quelle, ohne Zwift zu verändern. Die Anmeldung über den Browser widerspricht den Zwift-Nutzungsbedingungen. Benutzung auf eigene Gefahr.")
                icon.name: "dialog-warning"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: i18n("Nicht für Rennen")
                description: i18n("Tretlager garantiert nicht, dass die Sensor-Bridge Leistung, Trittfrequenz und Puls korrekt an Zwift weitergibt. An Rennen und Wettbewerben mit Wertung daher nicht mit Tretlager teilnehmen.")
                icon.name: "flag"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormButtonDelegate {
                text: i18n("Über Tretlager und Lizenzen")
                icon.name: "help-about"
                onClicked: applicationWindow().pageStack.push(Qt.resolvedUrl("AboutPage.qml"))
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormButtonDelegate {
                text: i18n("Hilfe lesen")
                icon.name: "help-contents"
                onClicked: applicationWindow().pageStack.push(Qt.resolvedUrl("HelpPage.qml"))
            }
        }
    ]

    footer: WizardFooter {
        nextText: i18n("Einrichtung beginnen")
        onNext: {
            backend.runChecks()
            applicationWindow().pageStack.push(Qt.resolvedUrl("CheckPage.qml"))
        }
    }
}
