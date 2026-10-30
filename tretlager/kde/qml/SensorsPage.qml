import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

// Schritt 5 des Assistenten und zugleich die Sensorverwaltung aus der Seitenleiste.
ColumnsPage {
    id: page
    title: "Sensoren"

    property bool wizard: applicationWindow().inWizard
    readonly property var se: backend.sensors
    readonly property var unstable: se.devices.filter(function (d) { return d.unstable && !d.compat })
    readonly property var roleText: ({ "trainer": "Smart-Trainer", "power": "Leistungsmesser",
        "cadence": "Trittfrequenzsensor", "heartrate": "Pulsgurt", "other": "Sensor" })

    function signalText(rssi) {
        return (rssi >= -65 ? "stark" : rssi >= -80 ? "mittel" : "schwach") + " (" + rssi + " dBm)"
    }

    Component.onCompleted: backend.setSensorPolling(true)

    header: WizardHeader {
        visible: page.wizard
        step: 5
        text: "Kurz in die Pedale treten und den Pulsgurt anlegen."
    }

    // --- Meldungen ---
    PageMessage {
        visible: !page.se.installed
        type: Kirigami.MessageType.Error
        text: "Die Sensor-Bridge fehlt (Dienst tretlager-bridge). Abhilfe: das Paket tretlager neu installieren."
    }
    PageMessage {
        visible: page.se.error !== ""
        type: Kirigami.MessageType.Error
        text: page.se.error
    }
    PageMessage {
        visible: page.se.running && page.se.adapterMissing
        type: Kirigami.MessageType.Warning
        text: "Der gewählte Bluetooth-Adapter ist abgezogen oder ausgeschaltet. Bis dahin nutzt die Bridge "
              + "den eingebauten Adapter und wechselt danach von selbst zurück."
    }
    PageMessage {
        visible: page.unstable.length > 0
        type: Kirigami.MessageType.Warning
        text: "Die Verbindung zu " + page.unstable.map(function (d) { return d.name }).join(", ")
              + " bricht oft ab. Meist ist der Funkweg zu lang. Abhilfe: Rechner näher an den Trainer "
              + "stellen oder einen USB-Bluetooth-Stick mit Verlängerung neben den Trainer legen."
    }

    // --- Suche oben, darunter die gekoppelten Sensoren ---
    leftCards: [
        FormCard.FormHeader {
            title: "Sensoren in der Nähe"
            trailing: Kirigami.ContextualHelpButton {
                toolTipText: "Die Suche dauert etwa zehn Sekunden und findet Smart-Trainer, Leistungsmesser, "
                    + "Trittfrequenzsensoren und Pulsgurte. Vorher kurz in die Pedale treten, damit der "
                    + "Trainer aufwacht; ein Pulsgurt sendet nur mit Hautkontakt."
            }
        },
        FormCard.FormCard {
            FormCard.FormButtonDelegate {
                text: page.se.scanning ? "Suche läuft …" : "Nach Sensoren suchen"
                description: page.se.running ? "" : "Dazu die Sensor-Bridge einschalten."
                icon.name: "system-search"
                enabled: page.se.running && !page.se.scanning
                onClicked: backend.scanDevices()
            }
            FormCard.FormDelegateSeparator { visible: page.se.scanned && !page.se.scanning }
            FormCard.FormPlaceholderMessageDelegate {
                visible: page.se.scanned && !page.se.scanning && page.se.found.length === 0
                icon.name: "edit-none"
                text: "Nichts gefunden"
                explanation: "Trainer aufwecken, Gurt anlegen und erneut suchen."
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
                        description: (page.roleText[modelData.role] || "Sensor") + " · Signal "
                            + page.signalText(modelData.rssi)
                            + (modelData.compat_short ? "\n" + modelData.compat_short : "")
                        icon.name: modelData.compat ? "data-warning" : "network-bluetooth"
                        trailing: Controls.Button {
                            text: modelData.configured ? "Gekoppelt" : "Hinzufügen"
                            icon.name: modelData.configured ? "dialog-ok" : "list-add"
                            enabled: !modelData.configured
                            onClicked: backend.addDevice(modelData.address, modelData.name, modelData.role)
                        }
                    }
                }
            }
        },

        FormCard.FormHeader { title: "Gekoppelte Sensoren" },
        FormCard.FormCard {
            FormCard.FormPlaceholderMessageDelegate {
                visible: page.se.devices.length === 0
                icon.name: "network-bluetooth"
                text: page.se.running ? "Noch keine Sensoren gekoppelt" : "Sensor-Bridge ist aus"
                explanation: page.se.running ? "Oben nach Sensoren suchen und hinzufügen."
                                             : "Zum Verwalten der Sensoren die Bridge einschalten."
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
            title: "Sensor-Bridge"
            trailing: Kirigami.ContextualHelpButton {
                toolTipText: "Zwift kann unter Linux kein Bluetooth nutzen. Die Sensor-Bridge verbindet sich mit "
                    + "Trainer und Pulsgurt und bietet sie Zwift als Wahoo-Geräte mit „Direct Connect“ an; "
                    + "die Zwift Companion App ist dafür nicht nötig."
            }
        },
        FormCard.FormCard {
            FormCard.FormSwitchDelegate {
                text: "Sensor-Bridge"
                description: page.se.running ? "Läuft und bietet die Sensoren Zwift an" : "Aus – Zwift sieht keine Sensoren"
                checked: page.se.running
                enabled: page.se.installed
                onToggled: backend.setBridgeRunning(checked)
            }
            FormCard.FormDelegateSeparator { visible: page.se.adapters.length > 0 }
            FormCard.FormComboBoxDelegate {
                id: adapterBox
                visible: page.se.adapters.length > 1
                text: "Bluetooth-Adapter"
                description: "Über diesen Adapter verbindet die Bridge alle Sensoren."
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
                text: "Bluetooth-Adapter"
                description: page.se.adapters.length ? page.se.adapters[0].chip : ""
                trailing: Kirigami.ContextualHelpButton {
                    toolTipText: "Ein USB-Bluetooth-Stick hilft, wenn der Rechner weit vom Trainer steht (mit "
                        + "Verlängerung neben den Trainer legen) oder der eingebaute Chip einen Sensor nicht "
                        + "verträgt. Angeschlossen lässt er sich hier auswählen."
                }
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormSwitchDelegate {
                text: "Beim Anmelden starten"
                description: "Sonst startet sie mit Tretlager und vor jeder Fahrt."
                checked: page.se.autostart
                enabled: page.se.installed
                onToggled: backend.setBridgeAutostart(checked)
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormSwitchDelegate {
                text: "Im Netz anbieten"
                description: page.se.network
                    ? "Im lokalen Netz sichtbar; jedes Gerät im Netz kann damit den Trainer steuern."
                    : "Nur nötig, wenn Zwift auf einem anderen Gerät läuft (Apple TV, iPad, zweiter Rechner)."
                checked: page.se.network
                enabled: page.se.installed && page.se.running
                onToggled: backend.setBridgeNetwork(checked)
            }
        }
    ]

    // --- Hilfe: über die volle Breite, die Fälle in zwei Spalten (gerade Anzahl) ---
    bottomCards: [
        FormCard.FormHeader { title: "Bei Problemen" },
        FormCard.FormCard {
            GridLayout {
                Layout.fillWidth: true
                columns: page.wide ? 2 : 1
                columnSpacing: 0
                rowSpacing: 0
                Repeater {
                    model: [
                        ["Sensor gerade nicht in Gebrauch", "media-playback-pause",
                         "Pausieren statt entfernen: Tretlager sucht dann nicht mehr danach, und die Kopplung bleibt erhalten."],
                        ["Zwift findet die Sensoren nicht", "network-bluetooth",
                         "Die Bridge muss laufen. In Zwift unter Gekoppelte Geräte „Wahoo KICKR …“ bzw. „Wahoo HRM …“ wählen."],
                        ["Puls viel zu hoch", "emblem-important",
                         "Elektroden anfeuchten, Gurt enger stellen und nur einen Gurt tragen."],
                        ["Gerät bleibt bei „Sucht das Gerät …“", "view-refresh",
                         "Kurz in die Pedale treten oder den Gurt kurz abklipsen; die Bridge sucht alle zehn Sekunden."],
                        ["Gerät verbindet sich nie", "data-warning",
                         "Manche Sensoren vertragen bestimmte Bluetooth-Chips nicht. Bekannte Fälle meldet Tretlager "
                         + "am Gerät; dann hilft ein USB-Bluetooth-Stick, gewählt als Bluetooth-Adapter."],
                        ["Verbindung bricht oft ab", "network-wireless-disconnected",
                         "Bluetooth reicht schlecht durch Wände. Rechner näher an den Trainer stellen oder einen "
                         + "USB-Bluetooth-Stick mit Verlängerung neben den Trainer legen."]
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
        skipText: "Überspringen"
        onSkip: applicationWindow().pageStack.push(Qt.resolvedUrl("FinishPage.qml"))
        nextEnabled: page.se.devices.length > 0
        onNext: applicationWindow().pageStack.push(Qt.resolvedUrl("FinishPage.qml"))
    }
}
