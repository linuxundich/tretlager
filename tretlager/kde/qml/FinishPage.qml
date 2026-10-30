import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

ColumnsPage {
    title: "Fertig"

    Component.onCompleted: backend.markSetupComplete()

    header: WizardHeader { step: 6; text: "Noch ein Handgriff in Zwift." }

    PageHero {
        iconName: "data-success"
        title: "Zwift ist bereit"
        text: "Ab jetzt startet Zwift mit einem Klick, in der Übersicht oder im Startmenü unter Zwift (Tretlager)."
    }

    FormCard.FormHeader { title: "Einmalig in Zwift: Gekoppelte Geräte" }
    FormCard.FormCard {
        FormCard.FormTextDelegate {
            text: "Leistung, Trittfrequenz und Widerstand"
            description: "„Wahoo KICKR …“ auswählen"
            icon.source: Qt.resolvedUrl("../../data/icons/tretlager-trainer-symbolic.svg")
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormTextDelegate {
            text: "Herzfrequenz"
            description: "„Wahoo HRM …“ auswählen"
            icon.source: Qt.resolvedUrl("../../data/icons/tretlager-heartrate-symbolic.svg")
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormTextDelegate {
            text: "Hinweise zu Bluetooth und ANT+"
            description: "Zwift meldet beides als nicht verfügbar. Das ist normal, die Geräte kommen über die Sensor-Bridge."
            icon.name: "dialog-information"
        }
    }

    footer: WizardFooter {
        nextText: "Zur Übersicht"
        nextIcon: "go-home"
        onNext: applicationWindow().show("overview")
    }
}
