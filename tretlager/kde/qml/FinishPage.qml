import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

FormCard.FormCardPage {
    title: "Fertig"

    Component.onCompleted: backend.markSetupComplete()

    header: WizardHeader { step: 6; text: "Noch ein Handgriff in Zwift." }

    ColumnLayout {
        Layout.alignment: Qt.AlignHCenter
        Layout.topMargin: Kirigami.Units.gridUnit * 2
        spacing: Kirigami.Units.smallSpacing
        Kirigami.Icon {
            source: "data-success"
            Layout.preferredWidth: Kirigami.Units.iconSizes.enormous
            Layout.preferredHeight: Kirigami.Units.iconSizes.enormous
            Layout.alignment: Qt.AlignHCenter
        }
        Kirigami.Heading { text: "Zwift ist bereit"; level: 1; Layout.alignment: Qt.AlignHCenter }
    }

    FormCard.FormHeader { title: "Einmalig in Zwift: Gekoppelte Geräte" }
    FormCard.FormCard {
        FormCard.FormTextDelegate {
            text: "Leistung, Trittfrequenz und Widerstand"
            description: "„Wahoo KICKR …“ auswählen"
            icon.source: Qt.resolvedUrl("../../ui/icons/hicolor/scalable/actions/tretlager-trainer-symbolic.svg")
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormTextDelegate {
            text: "Herzfrequenz"
            description: "„Wahoo HRM …“ auswählen"
            icon.source: Qt.resolvedUrl("../../ui/icons/hicolor/scalable/actions/tretlager-heartrate-symbolic.svg")
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormTextDelegate {
            text: "Hinweise zu Bluetooth und ANT+"
            description: "Zwift meldet beides als nicht verfügbar. Das ist normal, die Geräte kommen über die Sensor-Bridge."
            icon.name: "dialog-information"
        }
    }

    Item { implicitHeight: Kirigami.Units.gridUnit }

    footer: WizardFooter {
        nextText: "Zur Übersicht"
        nextIcon: "go-home"
        onNext: applicationWindow().show("overview")
    }
}
