import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

ColumnsPage {
    id: page
    title: i18n("Welcome")
    backdrop: true

    PageHero {
        title: i18n("Zwift on Linux")
        text: i18n("Tretlager sets up Zwift on this computer and connects your trainer and heart rate strap. The setup guides you through everything in %1 steps.", applicationWindow().stepIds.length)
        VersionLabel {}
    }

    leftCards: [
        FormCard.FormHeader { title: i18n("Requirements") },
        FormCard.FormCard {
            FormCard.FormTextDelegate { text: i18n("Zwift account with subscription"); icon.name: "user-identity" }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate { text: i18n("About 11 GB of free disk space"); icon.name: "drive-harddisk" }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate { text: i18n("Internet access for a download of about 5 GB"); icon.name: "network-wired" }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: i18n("Smart trainer and heart rate strap with Bluetooth")
                description: i18n("Only needed at step %1", applicationWindow().stepIds.indexOf("sensors") + 1)
                icon.name: "network-bluetooth"
            }
        }
    ]

    rightCards: [
        FormCard.FormHeader { title: i18n("Important") },
        FormCard.FormCard {
            FormCard.FormTextDelegate {
                text: i18n("Not an official Zwift program")
                description: i18n("Zwift does not support Linux. Tretlager uses Wine and downloads Zwift from the official source without modifying it. Signing in outside the launcher contradicts Zwift's terms of service. Use at your own risk.")
                icon.name: "dialog-warning"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: i18n("At your own risk")
                description: i18n("Zwift may not be happy that a software bridge sends data to Zwift that could be manipulated. Restrictions up to a suspended account cannot be ruled out – including the XP and drops earned with so much sweat.")
                icon.name: "emblem-warning"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: i18n("Not for races")
                description: i18n("Tretlager does not guarantee that the sensor bridge passes power, cadence and heart rate to Zwift correctly. Do not use Tretlager for races or competitions with results.")
                icon.name: "flag"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormButtonDelegate {
                text: i18n("About Tretlager and licenses")
                icon.name: "help-about"
                onClicked: applicationWindow().pageStack.push(Qt.resolvedUrl("AboutPage.qml"))
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormButtonDelegate {
                text: i18n("Read the help")
                icon.name: "help-contents"
                onClicked: applicationWindow().pageStack.push(Qt.resolvedUrl("HelpPage.qml"))
            }
        }
    ]

    footer: WizardFooter {
        nextText: i18n("Start setup")
        onNext: {
            backend.runChecks()
            applicationWindow().pageStack.push(Qt.resolvedUrl("CheckPage.qml"))
        }
    }
}
