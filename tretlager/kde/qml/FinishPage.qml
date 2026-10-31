import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

ColumnsPage {
    title: i18n("Done")

    Component.onCompleted: backend.markSetupComplete()

    header: WizardHeader { stepId: "finish"; text: i18n("One more step in Zwift.") }

    PageHero {
        iconName: "data-success"
        title: i18n("Zwift is ready")
        text: i18n("From now on Zwift starts with one click, from the overview or from the application menu under Zwift (Tretlager).")
    }

    FormCard.FormHeader { title: i18n("Once in Zwift: Paired Devices") }
    FormCard.FormCard {
        FormCard.FormTextDelegate {
            text: i18n("Power, cadence and resistance")
            description: i18n("Select “Wahoo KICKR …”")
            icon.source: Qt.resolvedUrl("../../data/icons/tretlager-trainer-symbolic.svg")
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormTextDelegate {
            text: i18n("Heart rate")
            description: i18n("Select “Wahoo HRM …”")
            icon.source: Qt.resolvedUrl("../../data/icons/tretlager-heartrate-symbolic.svg")
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormTextDelegate {
            text: i18n("Notices about Bluetooth and ANT+")
            description: i18n("Zwift reports both as unavailable. That is normal; the devices come through the sensor bridge.")
            icon.name: "dialog-information"
        }
    }

    footer: WizardFooter {
        nextText: i18n("Go to overview")
        nextIcon: "go-home"
        onNext: applicationWindow().show("overview")
    }
}
