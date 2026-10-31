import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

// Infoseite im selben Gerüst wie die übrigen Seiten: oben Name, Version und Haftungshinweis,
// darunter links, was der Hinweis auf Zwift bedeutet, rechts die Lizenzen.
ColumnsPage {
    id: page
    title: i18n("About Tretlager")

    LogDialog {
        id: licenseDialog
        title: i18n("GNU General Public License v3")
        text: backend.licenseText
    }

    PageHero {
        title: i18n("Tretlager %1", backend.version)
        text: i18n("Set up Zwift on Linux, keep it up to date and connect it to your trainer and heart rate strap.\nTretlager is a private project and not a program by Zwift Inc. Zwift does not support running on Linux. Use at your own risk.")
        VersionLabel {}
        Controls.Label {
            text: i18n("© 2026 Christoph Langner · GPL-3.0-or-later")
            color: Kirigami.Theme.disabledTextColor
            font: Kirigami.Theme.smallFont
        }
        RowLayout {
            Layout.topMargin: Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.smallSpacing
            Controls.Button {
                text: i18n("License")
                icon.name: "license"
                onClicked: licenseDialog.open()
            }
            Controls.Button {
                text: "linuxundich.de"
                icon.name: "internet-web-browser"
                onClicked: Qt.openUrlExternally("https://linuxundich.de/")
            }
        }
    }

    // Name, Lizenz, wofür, Link
    readonly property var freeParts: [
        [i18n("Qt and PySide6"), "LGPL-3.0", i18n("User interface"), "https://www.qt.io/licensing/open-source-lgpl-obligations"],
        [i18n("KDE Kirigami and Kirigami Addons"), "LGPL-2.0-or-later", i18n("Plasma-style user interface"), "https://develop.kde.org/frameworks/kirigami/"],
        [i18n("Bleak"), i18n("MIT"), i18n("Bluetooth Low Energy via BlueZ"), "https://github.com/hbldh/bleak"],
        ["dbus-fast", i18n("MIT"), i18n("D-Bus for the bridge and Avahi"), "https://github.com/Bluetooth-Devices/dbus-fast"],
        [i18n("SecretStorage"), i18n("BSD-3-Clause"), i18n("Zwift session in the keyring"), "https://github.com/mitya57/secretstorage"],
        [i18n("Wine (WineHQ)"), "LGPL-2.1-or-later", i18n("runs the Zwift Windows client"), "https://www.winehq.org/license"],
        ["winetricks", "LGPL-2.1-or-later", i18n("installs Windows components in the Wine prefix"), "https://github.com/Winetricks/winetricks"]
    ]

    leftCards: [
        FormCard.FormHeader { title: i18n("What this means") },
        FormCard.FormCard {
            FormCard.FormTextDelegate {
                text: i18n("No support from Zwift")
                description: i18n("Zwift does not support Linux or Wine. Report problems to Tretlager, not to Zwift.")
                icon.name: "help-about"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: i18n("Sign-in through the browser")
                description: i18n("Bypasses the official launcher and contradicts Zwift's terms of service. Restrictions up to a suspended account cannot be ruled out.")
                icon.name: "dialog-warning"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: i18n("Zwift stays unmodified")
                description: i18n("Tretlager does not modify any Zwift files and bypasses neither copy protection nor the subscription check. Riding requires a valid Zwift subscription.")
                icon.name: "security-high"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: i18n("Sensor bridge")
                description: i18n("Presents itself to Zwift as a Wahoo device with “Direct Connect” and passes on the device's values without changing them.")
                icon.name: "network-bluetooth"
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
                description: i18n("There is no guarantee that the sensor bridge passes power, cadence and heart rate to Zwift completely and correctly; transmission errors and dropouts are possible. Do not use Tretlager for races or competitions with results.")
                icon.name: "flag"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormButtonDelegate {
                text: i18n("Show warnings")
                description: i18n("The notes from the first start")
                icon.source: Qt.resolvedUrl("../../data/icons/tretlager-warning.svg")
                onClicked: applicationWindow().showWarnings()
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: i18n("No warranty")
                description: i18n("To the extent permitted by law (GPL, sections 15 and 16). Zwift, Wahoo, KICKR, TICKR and Garmin are trademarks of their owners; Tretlager is not affiliated with any of these companies.")
                icon.name: "emblem-important"
            }
        },

        FormCard.FormHeader { title: i18n("Non-free software that Tretlager downloads") },
        FormCard.FormCard {
            FormCard.FormTextDelegate {
                text: i18n("Not included in the package")
                description: i18n("The setup downloads these parts directly from the vendor; the vendor's license terms apply.")
                icon.name: "download"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormLinkDelegate {
                text: i18n("Zwift")
                description: i18n("Zwift terms of service · the game itself, downloaded by Tretlager from Zwift")
                url: "https://www.zwift.com/terms"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: i18n(".NET Framework 4.8, WebView2, Core Fonts, d3dcompiler_47")
                description: i18n("Microsoft license terms · required by the Zwift launcher, downloaded by winetricks from Microsoft")
            }
        }
    ]

    rightCards: [
        FormCard.FormHeader { title: i18n("Free software Tretlager builds on") },
        FormCard.FormCard {
            Repeater {
                model: page.freeParts
                delegate: FormCard.FormLinkDelegate {
                    required property var modelData
                    text: modelData[0]
                    description: modelData[1] + " · " + modelData[2]
                    url: modelData[3]
                }
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormLinkDelegate {
                text: "qdomyos-zwift"
                description: i18n("Description of the Wahoo “Direct Connect” protocol (DIRCON) the bridge is based on")
                url: "https://github.com/cagnulein/qdomyos-zwift"
            }
        }
    ]
}
