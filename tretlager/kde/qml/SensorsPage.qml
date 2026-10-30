import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

// Schritt 5 des Assistenten und zugleich die Sensorverwaltung aus der Seitenleiste.
FormCard.FormCardPage {
    id: page
    title: "Sensoren"

    property bool wizard: !applicationWindow().navigation
    readonly property var se: backend.sensors
    readonly property var unstable: se.devices.filter(function (d) { return d.unstable && !d.compat })
    readonly property var roleText: ({ "trainer": "Smart-Trainer", "power": "Leistungsmesser",
        "cadence": "Trittfrequenzsensor", "heartrate": "Pulsgurt", "other": "Sensor" })

    Component.onCompleted: backend.setSensorPolling(true)

    header: WizardHeader {
        visible: page.wizard
        step: 5
        text: "Kurz in die Pedale treten und den Pulsgurt anlegen."
    }

    // --- Meldungen ---
    Kirigami.InlineMessage {
        Layout.fillWidth: true
        Layout.maximumWidth: Kirigami.Units.gridUnit * 30
        Layout.alignment: Qt.AlignHCenter
        Layout.topMargin: Kirigami.Units.largeSpacing
        visible: !page.se.installed
        type: Kirigami.MessageType.Error
        text: "Die Sensor-Bridge ist nicht installiert (Dienst tretlager-bridge fehlt). Das Paket tretlager neu installieren."
    }
    Kirigami.InlineMessage {
        Layout.fillWidth: true
        Layout.maximumWidth: Kirigami.Units.gridUnit * 30
        Layout.alignment: Qt.AlignHCenter
        Layout.topMargin: Kirigami.Units.largeSpacing
        visible: page.se.error !== ""
        type: Kirigami.MessageType.Error
        text: page.se.error
    }
    Kirigami.InlineMessage {
        Layout.fillWidth: true
        Layout.maximumWidth: Kirigami.Units.gridUnit * 30
        Layout.alignment: Qt.AlignHCenter
        Layout.topMargin: Kirigami.Units.largeSpacing
        visible: page.unstable.length > 0
        type: Kirigami.MessageType.Warning
        text: "Die Verbindung zu " + page.unstable.map(function (d) { return d.name }).join(", ")
              + " bricht oft ab. Meist ist der Funkweg zu lang: Rechner näher an den Trainer stellen, "
              + "einen USB-Bluetooth-Stick mit Verlängerung nutzen oder die Bridge auf einem Rechner "
              + "neben dem Trainer betreiben (Im Netz anbieten)."
    }

    // --- Bridge ---
    FormCard.FormHeader {
        title: "Sensor-Bridge"
        trailing: Kirigami.ContextualHelpButton {
            toolTipText: "Zwift kann unter Linux kein Bluetooth nutzen. Die Sensor-Bridge verbindet sich mit "
                + "Trainer und Pulsgurt und bietet sie Zwift als Wahoo-Geräte mit „Direct Connect“ an. "
                + "Die Zwift Companion App ist dafür nicht nötig."
        }
    }
    FormCard.FormCard {
        FormCard.FormSwitchDelegate {
            text: "Sensor-Bridge"
            description: page.se.running ? "Läuft und reicht die Geräte an Zwift weiter" : "Aus"
            checked: page.se.running
            enabled: page.se.installed
            onToggled: backend.setBridgeRunning(checked)
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormSwitchDelegate {
            text: "Beim Anmelden starten"
            description: "Sonst startet Tretlager die Bridge beim Öffnen und vor jeder Fahrt."
            checked: page.se.autostart
            enabled: page.se.installed
            onToggled: backend.setBridgeAutostart(checked)
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormSwitchDelegate {
            text: "Im Netz anbieten"
            description: page.se.network
                ? "Die Geräte sind im lokalen Netz sichtbar. Jedes Gerät im Netz kann damit den Trainer steuern."
                : "Nur nötig, wenn Zwift auf einem anderen Gerät läuft als die Bridge."
            checked: page.se.network
            enabled: page.se.installed && page.se.running
            onToggled: backend.setBridgeNetwork(checked)
        }
    }

    // --- Eingerichtete Geräte ---
    FormCard.FormHeader { title: "Geräte" }
    FormCard.FormCard {
        FormCard.FormPlaceholderMessageDelegate {
            visible: page.se.devices.length === 0
            icon.name: "network-bluetooth"
            text: page.se.running ? "Keine Geräte eingerichtet" : "Sensor-Bridge ist aus"
            explanation: page.se.running ? "Unten nach Geräten in der Nähe suchen und hinzufügen."
                                         : "Zum Verwalten der Geräte die Bridge einschalten."
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
                }
            }
        }
    }

    // --- Suche ---
    FormCard.FormHeader {
        title: "Geräte in der Nähe"
        trailing: Kirigami.ContextualHelpButton {
            toolTipText: "Die Suche dauert etwa zehn Sekunden und findet Smart-Trainer, Leistungsmesser, "
                + "Trittfrequenzsensoren und Pulsgurte. Vorher kurz in die Pedale treten, damit der Trainer "
                + "aufwacht. Ein Pulsgurt sendet nur mit Hautkontakt."
        }
    }
    FormCard.FormCard {
        FormCard.FormButtonDelegate {
            text: page.se.scanning ? "Suche läuft …" : "Nach Geräten suchen"
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
            delegate: FormCard.FormTextDelegate {
                required property var modelData
                text: modelData.name
                description: (page.roleText[modelData.role] || "Sensor") + ", Signal " + modelData.rssi + " dBm"
                    + (modelData.compat ? "\n" + modelData.compat : "")
                icon.name: modelData.compat ? "data-warning" : "network-bluetooth"
                trailing: Controls.Button {
                    text: modelData.configured ? "Hinzugefügt" : "Hinzufügen"
                    icon.name: modelData.configured ? "dialog-ok" : "list-add"
                    enabled: !modelData.configured
                    onClicked: backend.addDevice(modelData.address, modelData.name, modelData.role)
                }
            }
        }
    }

    // --- Hilfe ---
    FormCard.FormHeader { title: "Bei Problemen" }
    FormCard.FormCard {
        FormCard.FormTextDelegate {
            text: "Puls viel zu hoch"
            description: "Elektroden des Gurts anfeuchten, Gurt enger stellen und nur einen Gurt tragen."
            icon.name: "emblem-important"
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormTextDelegate {
            text: "Gerät bleibt bei „Verbindet …“"
            description: "Kurz in die Pedale treten oder den Gurt kurz abklipsen. Die Bridge sucht alle zehn Sekunden erneut."
            icon.name: "view-refresh"
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormTextDelegate {
            text: "Gerät verbindet sich nie"
            description: "Manche Sensoren vertragen bestimmte Bluetooth-Chips nicht. Bekannte Fälle meldet Tretlager direkt am Gerät; sonst den Sensor an einem anderen Rechner gegenprüfen."
            icon.name: "data-warning"
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormTextDelegate {
            text: "Verbindung bricht oft ab"
            description: "Bluetooth reicht schlecht durch Wände. Rechner näher an den Trainer stellen oder einen USB-Bluetooth-Stick mit Verlängerung nutzen."
            icon.name: "network-wireless-disconnected"
        }
    }

    Item { implicitHeight: Kirigami.Units.gridUnit }

    footer: WizardFooter {
        visible: page.wizard
        skipText: "Überspringen"
        onSkip: applicationWindow().pageStack.push(Qt.resolvedUrl("FinishPage.qml"))
        nextEnabled: page.se.devices.length > 0
        onNext: applicationWindow().pageStack.push(Qt.resolvedUrl("FinishPage.qml"))
    }
}
