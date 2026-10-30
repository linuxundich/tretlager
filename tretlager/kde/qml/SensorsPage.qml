import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

// Schritt 5 des Assistenten und zugleich die Sensorverwaltung aus der Seitenleiste.
ColumnsPage {
    id: page
    title: i18n("Sensoren")

    property bool wizard: applicationWindow().inWizard
    readonly property var se: backend.sensors
    readonly property var unstable: se.devices.filter(function (d) { return d.unstable && !d.compat })
    readonly property var roleText: ({ "trainer": i18n("Smart-Trainer"), "power": i18n("Leistungsmesser"),
        "cadence": i18n("Trittfrequenzsensor"), "heartrate": i18n("Pulsgurt"), "other": i18n("Sensor") })

    function signalText(rssi) {
        return i18n("%1 (%2 dBm)", rssi >= -65 ? i18n("stark") : rssi >= -80 ? i18n("mittel") : i18n("schwach"), rssi)
    }

    Component.onCompleted: backend.setSensorPolling(true)

    header: WizardHeader {
        visible: page.wizard
        stepId: "sensors"
        text: i18n("Kurz in die Pedale treten und den Pulsgurt anlegen.")
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
        text: i18n("Der gewählte Bluetooth-Adapter ist abgezogen oder ausgeschaltet. Bis dahin nutzt die Bridge den eingebauten Adapter und wechselt danach von selbst zurück.")
    }
    PageMessage {
        visible: page.unstable.length > 0
        type: Kirigami.MessageType.Warning
        text: i18n("Die Verbindung zu %1 bricht oft ab. Meist ist der Funkweg zu lang. Abhilfe: Rechner näher an den Trainer stellen oder einen USB-Bluetooth-Stick mit Verlängerung neben den Trainer legen.",
                   page.unstable.map(function (d) { return d.name }).join(", "))
    }

    // --- Suche oben, darunter die gekoppelten Sensoren ---
    leftCards: [
        FormCard.FormHeader {
            title: i18n("Sensoren in der Nähe")
            trailing: Kirigami.ContextualHelpButton {
                toolTipText: i18n("Die Suche dauert etwa zehn Sekunden und findet Smart-Trainer, Leistungsmesser, Trittfrequenzsensoren und Pulsgurte. Vorher kurz in die Pedale treten, damit der Trainer aufwacht; ein Pulsgurt sendet nur mit Hautkontakt.")
            }
        },
        FormCard.FormCard {
            FormCard.FormButtonDelegate {
                text: page.se.scanning ? i18n("Suche läuft …") : i18n("Nach Sensoren suchen")
                description: page.se.running ? "" : i18n("Dazu die Sensor-Bridge einschalten.")
                icon.name: "system-search"
                enabled: page.se.running && !page.se.scanning
                onClicked: backend.scanDevices()
            }
            FormCard.FormDelegateSeparator { visible: page.se.scanned && !page.se.scanning }
            FormCard.FormPlaceholderMessageDelegate {
                visible: page.se.scanned && !page.se.scanning && page.se.found.length === 0
                icon.name: "edit-none"
                text: i18n("Nichts gefunden")
                explanation: i18n("Trainer aufwecken, Gurt anlegen und erneut suchen.")
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
                        description: i18n("%1 · Signal %2", page.roleText[modelData.role] || i18n("Sensor"), page.signalText(modelData.rssi))
                            + (modelData.compat_short ? "\n" + modelData.compat_short : "")
                        icon.name: modelData.compat ? "data-warning" : "network-bluetooth"
                        trailing: Controls.Button {
                            text: modelData.configured ? i18n("Gekoppelt") : i18n("Hinzufügen")
                            icon.name: modelData.configured ? "dialog-ok" : "list-add"
                            enabled: !modelData.configured
                            onClicked: backend.addDevice(modelData.address, modelData.name, modelData.role)
                        }
                    }
                }
            }
        },

        FormCard.FormHeader { title: i18n("Gekoppelte Sensoren") },
        FormCard.FormCard {
            FormCard.FormPlaceholderMessageDelegate {
                visible: page.se.devices.length === 0
                icon.name: "network-bluetooth"
                text: page.se.running ? i18n("Noch keine Sensoren gekoppelt") : i18n("Sensor-Bridge ist aus")
                explanation: page.se.running ? i18n("Oben nach Sensoren suchen und hinzufügen.")
                                             : i18n("Zum Verwalten der Sensoren die Bridge einschalten.")
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
            title: i18n("Sensor-Bridge")
            trailing: Kirigami.ContextualHelpButton {
                toolTipText: i18n("Zwift kann unter Linux kein Bluetooth nutzen. Die Sensor-Bridge verbindet sich mit Trainer und Pulsgurt und bietet sie Zwift als Wahoo-Geräte mit „Direct Connect“ an; die Zwift Companion App ist dafür nicht nötig.")
            }
        },
        FormCard.FormCard {
            FormCard.FormSwitchDelegate {
                text: i18n("Sensor-Bridge")
                description: page.se.running ? i18n("Läuft und bietet die Sensoren Zwift an") : i18n("Aus – Zwift sieht keine Sensoren")
                checked: page.se.running
                enabled: page.se.installed
                onToggled: backend.setBridgeRunning(checked)
            }
            FormCard.FormDelegateSeparator { visible: page.se.adapters.length > 0 }
            FormCard.FormComboBoxDelegate {
                id: adapterBox
                visible: page.se.adapters.length > 1
                text: i18n("Bluetooth-Adapter")
                description: i18n("Über diesen Adapter verbindet die Bridge alle Sensoren.")
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
                text: i18n("Bluetooth-Adapter")
                description: page.se.adapters.length ? page.se.adapters[0].chip : ""
                trailing: Kirigami.ContextualHelpButton {
                    toolTipText: i18n("Ein USB-Bluetooth-Stick hilft, wenn der Rechner weit vom Trainer steht (mit Verlängerung neben den Trainer legen) oder der eingebaute Chip einen Sensor nicht verträgt. Angeschlossen lässt er sich hier auswählen.")
                }
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormSwitchDelegate {
                text: i18n("Beim Anmelden starten")
                description: i18n("Sonst startet sie mit Tretlager und vor jeder Fahrt.")
                checked: page.se.autostart
                enabled: page.se.installed
                onToggled: backend.setBridgeAutostart(checked)
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormSwitchDelegate {
                text: i18n("Im Netz anbieten")
                description: page.se.network
                    ? i18n("Im lokalen Netz sichtbar; jedes Gerät im Netz kann damit den Trainer steuern.")
                    : i18n("Nur nötig, wenn Zwift auf einem anderen Gerät läuft (Apple TV, iPad, zweiter Rechner).")
                checked: page.se.network
                enabled: page.se.installed && page.se.running
                onToggled: backend.setBridgeNetwork(checked)
            }
        }
    ]

    // --- Hilfe: über die volle Breite, die Fälle in zwei Spalten (gerade Anzahl) ---
    bottomCards: [
        FormCard.FormHeader { title: i18n("Bei Problemen") },
        FormCard.FormCard {
            GridLayout {
                Layout.fillWidth: true
                columns: page.wide ? 2 : 1
                columnSpacing: 0
                rowSpacing: 0
                Repeater {
                    model: [
                        [i18n("Sensor gerade nicht in Gebrauch"), "media-playback-pause",
                         i18n("Pausieren statt entfernen: Tretlager sucht dann nicht mehr danach, und die Kopplung bleibt erhalten.")],
                        [i18n("Zwift findet die Sensoren nicht"), "network-bluetooth",
                         i18n("Die Bridge muss laufen. In Zwift unter Gekoppelte Geräte „Wahoo KICKR …“ bzw. „Wahoo HRM …“ wählen.")],
                        [i18n("Puls viel zu hoch"), "emblem-important",
                         i18n("Elektroden anfeuchten, Gurt enger stellen und nur einen Gurt tragen. Hilft das nicht, die Batterie des Gurts wechseln.")],
                        [i18n("Gerät bleibt bei „Sucht das Gerät …“"), "view-refresh",
                         i18n("Kurz in die Pedale treten oder den Gurt kurz abklipsen; die Bridge sucht alle zehn Sekunden.")],
                        [i18n("Gerät verbindet sich nie"), "data-warning",
                         i18n("Manche Sensoren vertragen bestimmte Bluetooth-Chips nicht. Bekannte Fälle meldet Tretlager am Gerät; dann hilft ein USB-Bluetooth-Stick, gewählt als Bluetooth-Adapter.")],
                        [i18n("Verbindung bricht oft ab"), "network-wireless-disconnected",
                         i18n("Bluetooth reicht schlecht durch Wände. Rechner näher an den Trainer stellen oder einen USB-Bluetooth-Stick mit Verlängerung neben den Trainer legen.")]
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
        skipText: i18n("Überspringen")
        onSkip: applicationWindow().pageStack.push(Qt.resolvedUrl("FinishPage.qml"))
        nextEnabled: page.se.devices.length > 0
        onNext: applicationWindow().pageStack.push(Qt.resolvedUrl("FinishPage.qml"))
    }
}
