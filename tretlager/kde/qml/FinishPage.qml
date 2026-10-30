import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

ColumnsPage {
    title: i18n("Fertig")

    Component.onCompleted: backend.markSetupComplete()

    header: WizardHeader { step: 6; text: i18n("Noch ein Handgriff in Zwift.") }

    PageHero {
        iconName: "data-success"
        title: i18n("Zwift ist bereit")
        text: i18n("Ab jetzt startet Zwift mit einem Klick, in der Übersicht oder im Startmenü unter Zwift (Tretlager).")
    }

    FormCard.FormHeader { title: i18n("Einmalig in Zwift: Gekoppelte Geräte") }
    FormCard.FormCard {
        FormCard.FormTextDelegate {
            text: i18n("Leistung, Trittfrequenz und Widerstand")
            description: i18n("„Wahoo KICKR …“ auswählen")
            icon.source: Qt.resolvedUrl("../../data/icons/tretlager-trainer-symbolic.svg")
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormTextDelegate {
            text: i18n("Herzfrequenz")
            description: i18n("„Wahoo HRM …“ auswählen")
            icon.source: Qt.resolvedUrl("../../data/icons/tretlager-heartrate-symbolic.svg")
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormTextDelegate {
            text: i18n("Hinweise zu Bluetooth und ANT+")
            description: i18n("Zwift meldet beides als nicht verfügbar. Das ist normal, die Geräte kommen über die Sensor-Bridge.")
            icon.name: "dialog-information"
        }
    }

    footer: WizardFooter {
        nextText: i18n("Zur Übersicht")
        nextIcon: "go-home"
        onNext: applicationWindow().show("overview")
    }
}
