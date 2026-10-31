import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

// Schritt 5 des Assistenten und zugleich die Sensorverwaltung aus der Seitenleiste.
ColumnsPage {
    id: page
    title: i18n("Sensors")

    property bool wizard: applicationWindow().inWizard
    readonly property var se: backend.sensors
    readonly property var unstable: se.devices.filter(function (d) { return d.unstable && !d.compat })
    readonly property var roleText: ({ "trainer": i18n("Smart trainer"), "power": i18n("Power meter"),
        "cadence": i18n("Cadence sensor"), "heartrate": i18n("Heart rate strap"), "other": i18n("Sensor") })

    function signalText(rssi) {
        return i18n("%1 (%2 dBm)", rssi >= -65 ? i18n("strong") : rssi >= -80 ? i18n("medium") : i18n("weak"), rssi)
    }

    Component.onCompleted: backend.setSensorPolling(true)

    header: WizardHeader {
        visible: page.wizard
        stepId: "sensors"
        text: i18n("Pedal briefly and put on the heart rate strap.")
    }

    // --- Meldungen ---
    PageMessage {
        visible: page.se.error !== ""
        type: Kirigami.MessageType.Error
        text: page.se.error
    }
    PageMessage {
        visible: page.se.running && page.se.adapterMissing
        type: Kirigami.MessageType.Warning
        text: i18n("The selected Bluetooth adapter is unplugged or turned off. Until it is back, the bridge uses the built-in adapter and then switches back by itself.")
    }
    PageMessage {
        visible: page.unstable.length > 0
        type: Kirigami.MessageType.Warning
        text: i18n("The connection to %1 drops often. Usually the radio path is too long. Remedy: move the computer closer to the trainer or place a USB Bluetooth dongle on an extension cable next to the trainer.",
                   page.unstable.map(function (d) { return d.name }).join(", "))
    }

    // --- Suche oben, darunter die gekoppelten Sensoren ---
    leftCards: [
        FormCard.FormHeader {
            title: i18n("Sensors nearby")
            trailing: Kirigami.ContextualHelpButton {
                toolTipText: i18n("The search takes about ten seconds and finds smart trainers, power meters, cadence sensors and heart rate straps. Pedal briefly beforehand so the trainer wakes up; a heart rate strap only transmits with skin contact.")
            }
        },
        FormCard.FormCard {
            FormCard.FormButtonDelegate {
                text: page.se.scanning ? i18n("Searching…") : i18n("Search for sensors")
                description: page.se.running ? "" : i18n("Turn on the sensor bridge for this.")
                icon.name: "system-search"
                enabled: page.se.running && !page.se.scanning
                onClicked: backend.scanDevices()
            }
            FormCard.FormDelegateSeparator { visible: page.se.scanned && !page.se.scanning }
            FormCard.FormPlaceholderMessageDelegate {
                visible: page.se.scanned && !page.se.scanning && page.se.found.length === 0
                icon.name: "edit-none"
                text: i18n("Nothing found")
                explanation: i18n("Wake up the trainer, put on the strap and search again.")
            }
            Repeater {
                model: page.se.scanning ? [] : page.se.found
                delegate: ColumnLayout {
                    required property var modelData
                    required property int index
                    Layout.fillWidth: true
                    spacing: 0
                    FormCard.FormDelegateSeparator { visible: index > 0 }
                    FormCard.FormTextDelegate {
                        Layout.fillWidth: true
                        text: modelData.name
                        description: i18n("%1 · signal %2", page.roleText[modelData.role] || i18n("Sensor"), page.signalText(modelData.rssi))
                            + (modelData.compat_short ? "\n" + modelData.compat_short : "")
                        icon.name: modelData.compat ? "data-warning" : "network-bluetooth"
                        trailing: Controls.Button {
                            text: modelData.configured ? i18n("Paired") : i18n("Add")
                            icon.name: modelData.configured ? "dialog-ok" : "list-add"
                            enabled: !modelData.configured
                            onClicked: backend.addDevice(modelData.address, modelData.name, modelData.role)
                        }
                    }
                }
            }
        },

        FormCard.FormHeader { title: i18n("Paired sensors") },
        FormCard.FormCard {
            FormCard.FormPlaceholderMessageDelegate {
                visible: page.se.devices.length === 0
                icon.name: "network-bluetooth"
                text: page.se.running ? i18n("No sensors paired yet") : i18n("Sensor bridge is off")
                explanation: page.se.running ? i18n("Search for sensors above and add them.")
                                             : i18n("Turn on the bridge to manage sensors.")
            }
            Repeater {
                model: page.se.devices
                delegate: ColumnLayout {
                    required property var modelData
                    required property int index
                    Layout.fillWidth: true
                    spacing: 0
                    FormCard.FormDelegateSeparator { visible: index > 0 }
                    DeviceDelegate {
                        device: modelData
                        detailed: true
                        Layout.fillWidth: true
                        onRemoveRequested: backend.removeDevice(modelData.address)
                        onPauseRequested: function (pause) { backend.setDeviceEnabled(modelData.address, !pause) }
                    }
                }
            }
        }
    ]

    // --- Bridge ---
    rightCards: [
        FormCard.FormHeader {
            title: i18n("Sensor bridge")
            trailing: Kirigami.ContextualHelpButton {
                toolTipText: i18n("Zwift cannot use Bluetooth on Linux. The sensor bridge connects to the trainer and heart rate strap and offers them to Zwift as Wahoo devices with “Direct Connect”; the Zwift Companion app is not needed.")
            }
        },
        FormCard.FormCard {
            FormCard.FormSwitchDelegate {
                text: i18n("Sensor bridge")
                description: page.se.running ? i18n("Running and offering the sensors to Zwift") : i18n("Off – Zwift sees no sensors")
                checked: page.se.running
                enabled: page.se.installed
                onToggled: backend.setBridgeRunning(checked)
            }
            FormCard.FormDelegateSeparator { visible: page.se.adapters.length > 0 }
            FormCard.FormComboBoxDelegate {
                id: adapterBox
                visible: page.se.adapters.length > 1
                text: i18n("Bluetooth adapter")
                description: i18n("The bridge connects all sensors through this adapter.")
                enabled: page.se.running
                // Gleiche Chips (zwei gleiche Sticks) anhand der Adresse unterscheiden
                model: page.se.adapters.map(function (a) {
                    const twins = page.se.adapters.filter(function (b) { return b.chip === a.chip }).length > 1
                    return twins ? a.chip + " (" + a.address + ")" : a.chip
                })
                currentIndex: page.se.adapters.findIndex(function (a) { return a.hci === page.se.adapterHci })
                onActivated: function (index) { backend.setBridgeAdapter(page.se.adapters[index].address) }
            }
            FormCard.FormTextDelegate {
                visible: page.se.adapters.length === 1
                text: i18n("Bluetooth adapter")
                description: page.se.adapters.length ? page.se.adapters[0].chip : ""
                trailing: Kirigami.ContextualHelpButton {
                    toolTipText: i18n("A USB Bluetooth dongle helps if the computer is far from the trainer (place it next to the trainer on an extension cable) or if the built-in chip does not get along with a sensor. Once plugged in, it can be selected here.")
                }
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormSwitchDelegate {
                text: i18n("Start at login")
                description: i18n("Otherwise it starts with Tretlager and before every ride.")
                checked: page.se.autostart
                enabled: page.se.installed
                onToggled: backend.setBridgeAutostart(checked)
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormSwitchDelegate {
                text: i18n("Offer on the network")
                description: page.se.network
                    ? i18n("Visible on the local network; any device on the network can then control the trainer.")
                    : i18n("Only needed if Zwift runs on another device (Apple TV, iPad, second computer).")
                checked: page.se.network
                enabled: page.se.installed && page.se.running
                onToggled: backend.setBridgeNetwork(checked)
            }
        }
    ]

    // --- Hilfe: über die volle Breite, die Fälle in zwei Spalten (gerade Anzahl) ---
    bottomCards: [
        FormCard.FormHeader { title: i18n("Troubleshooting") },
        FormCard.FormCard {
            GridLayout {
                Layout.fillWidth: true
                columns: page.wide ? 2 : 1
                columnSpacing: 0
                rowSpacing: 0
                Repeater {
                    model: [
                        [i18n("Sensor not in use right now"), "media-playback-pause",
                         i18n("Pause instead of removing: Tretlager then stops searching for it, and the pairing is kept.")],
                        [i18n("Zwift does not find the sensors"), "network-bluetooth",
                         i18n("The bridge must be running. In Zwift, select “Wahoo KICKR …” or “Wahoo HRM …” under Paired Devices.")],
                        [i18n("Heart rate far too high"), "emblem-important",
                         i18n("Moisten the electrodes, tighten the strap and wear only one strap. If that does not help, replace the strap's battery.")],
                        [i18n("Device stays at “Searching for the device…”"), "view-refresh",
                         i18n("Pedal briefly or unclip the strap for a moment; the bridge searches every ten seconds.")],
                        [i18n("Device never connects"), "data-warning",
                         i18n("Some sensors do not get along with certain Bluetooth chips. Tretlager reports known cases on the device; a USB Bluetooth dongle selected as the Bluetooth adapter helps then.")],
                        [i18n("Connection drops often"), "network-wireless-disconnected",
                         i18n("Bluetooth does not travel well through walls. Move the computer closer to the trainer or place a USB Bluetooth dongle on an extension cable next to the trainer.")]
                    ]
                    delegate: FormCard.FormTextDelegate {
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.preferredWidth: 1
                        Layout.alignment: Qt.AlignTop
                        text: modelData[0]
                        icon.name: modelData[1]
                        description: modelData[2]
                    }
                }
            }
        }
    ]

    footer: WizardFooter {
        visible: page.wizard
        skipText: i18n("Skip")
        onSkip: applicationWindow().pageStack.push(Qt.resolvedUrl("FinishPage.qml"))
        nextEnabled: page.se.devices.length > 0
        onNext: applicationWindow().pageStack.push(Qt.resolvedUrl("FinishPage.qml"))
    }
}
