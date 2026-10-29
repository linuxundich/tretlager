import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

// Schritt 5 des Assistenten und zugleich die Sensorverwaltung aus dem Hauptfenster.
Kirigami.ScrollablePage {
    id: page
    title: "Sensoren"

    property bool wizard: true
    readonly property var se: backend.sensors
    readonly property var roleText: ({ "trainer": "Smart-Trainer", "power": "Leistungsmesser",
        "cadence": "Geschwindigkeit/Trittfrequenz", "heartrate": "Pulsgurt", "other": "Sensor" })
    // Eigene Symbole (wie in der GTK-Oberfläche), als Maske in der Textfarbe eingefärbt.
    readonly property string iconDir: Qt.resolvedUrl("../../ui/icons/hicolor/scalable/actions/")
    readonly property var roleIcon: ({ "trainer": iconDir + "tretlager-trainer-symbolic.svg",
        "power": iconDir + "tretlager-trainer-symbolic.svg", "cadence": iconDir + "tretlager-trainer-symbolic.svg",
        "heartrate": iconDir + "tretlager-heartrate-symbolic.svg", "other": "network-bluetooth" })
    readonly property var stateText: ({ "verbunden": "verbunden", "verbinde": "verbinde …", "getrennt": "getrennt",
        "fehler": "Fehler", "aus": "ausgeschaltet" })

    function values(v) {
        var parts = []
        if (v.power !== undefined) parts.push(v.power + " W")
        if (v.cadence !== undefined) parts.push(Math.round(v.cadence) + " U/min")
        if (v.heart_rate !== undefined) parts.push(v.heart_rate + " bpm")
        return parts.join(" · ")
    }

    Component.onCompleted: backend.setSensorPolling(true)
    Component.onDestruction: backend.setSensorPolling(false)

    header: Controls.Label {
        visible: page.wizard
        text: "Schritt 5 von " + applicationWindow().steps.length + " · tritt kurz in die Pedale und leg den Pulsgurt an"
        padding: Kirigami.Units.largeSpacing
        color: Kirigami.Theme.disabledTextColor
        wrapMode: Text.WordWrap
    }

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Controls.Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: "Zwift kann unter Linux kein Bluetooth nutzen. Die Sensor-Bridge hält Trainer und Pulsgurt und bietet sie Zwift als Wahoo-„Direct Connect“-Geräte an."
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: !page.se.installed
            type: Kirigami.MessageType.Error
            text: "Die Sensor-Bridge ist nicht installiert (Dienst tretlager-bridge fehlt)."
        }
        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: page.se.error !== ""
            type: Kirigami.MessageType.Error
            text: page.se.error
        }

        Kirigami.FormLayout {
            Layout.fillWidth: true
            Controls.Switch {
                Kirigami.FormData.label: "Sensor-Bridge:"
                text: checked ? "läuft" : "aus"
                checked: page.se.running
                enabled: page.se.installed
                onToggled: backend.setBridgeRunning(checked)
            }
            Controls.Switch {
                Kirigami.FormData.label: "Im Netz anbieten:"
                text: checked ? "ja – auch für Zwift auf anderen Geräten" : "nein – nur Zwift auf diesem Rechner"
                checked: page.se.network
                enabled: page.se.installed && page.se.running
                onToggled: backend.setBridgeNetwork(checked)
            }
            Controls.Switch {
                Kirigami.FormData.label: "Beim Anmelden starten:"
                text: checked ? "ja" : "nein (Tretlager startet sie mit Zwift)"
                checked: page.se.autostart
                enabled: page.se.installed
                onToggled: backend.setBridgeAutostart(checked)
            }
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: page.se.network
            type: Kirigami.MessageType.Information
            text: "Die Bridge ist im lokalen Netz sichtbar. So kann ein Rechner neben dem Trainer die Sensoren halten und Zwift auf einem anderen Gerät sie nutzen. Jeder im Netz könnte dann aber auch den Trainer steuern."
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: page.se.devices.some(function (d) { return d.unstable })
            type: Kirigami.MessageType.Warning
            text: "Die Bluetooth-Verbindung zu " + page.se.devices.filter(function (d) { return d.unstable })
                  .map(function (d) { return d.name }).join(", ")
                  + " bricht oft ab. Meist ist der Funkweg zu lang: Rechner näher an den Trainer stellen, einen USB-Bluetooth-Stick mit Verlängerungskabel nutzen oder die Bridge auf einem Rechner neben dem Trainer laufen lassen (Schalter „Im Netz anbieten“)."
        }

        Kirigami.Heading { text: "Deine Geräte"; level: 2 }

        Controls.Label {
            visible: page.se.devices.length === 0
            text: page.se.running ? "Noch keine Geräte – unten suchen und übernehmen." : "Schalte die Bridge ein, um Geräte zu verwalten."
            color: Kirigami.Theme.disabledTextColor
        }

        Repeater {
            model: page.se.devices
            delegate: Kirigami.AbstractCard {
                required property var modelData
                Layout.fillWidth: true
                contentItem: RowLayout {
                    spacing: Kirigami.Units.largeSpacing
                    Kirigami.Icon {
                        source: page.roleIcon[modelData.role] || "network-bluetooth"
                        isMask: true
                        Layout.preferredWidth: Kirigami.Units.iconSizes.medium
                        Layout.preferredHeight: Kirigami.Units.iconSizes.medium
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0
                        Controls.Label { text: modelData.name; font.bold: true }
                        Controls.Label {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            color: Kirigami.Theme.disabledTextColor
                            text: (page.roleText[modelData.role] || "") + " · " + (page.stateText[modelData.state] || modelData.state)
                                  + (modelData.state === "verbunden" ? (modelData.zwift_clients > 0 ? " · Zwift verbunden" : " · wartet auf Zwift") : "")
                                  + (modelData.error ? " · " + modelData.error : "")
                        }
                        Controls.Label {
                            visible: modelData.dircon_name !== undefined
                            text: "In Zwift: " + (modelData.dircon_name || "")
                            color: Kirigami.Theme.disabledTextColor
                        }
                    }
                    Controls.Label {
                        text: page.values(modelData.values || {})
                        font.pointSize: Kirigami.Theme.defaultFont.pointSize * 1.3
                    }
                    Controls.ToolButton {
                        icon.name: "edit-delete"
                        Controls.ToolTip.text: "Gerät entfernen"
                        Controls.ToolTip.visible: hovered
                        onClicked: backend.removeDevice(modelData.address)
                    }
                }
            }
        }

        RowLayout {
            Kirigami.Heading { text: "Geräte in der Nähe"; level: 2; Layout.fillWidth: true }
            Controls.Button {
                text: page.se.scanning ? "Suche läuft …" : "Suchen"
                icon.name: "system-search"
                enabled: page.se.running && !page.se.scanning
                onClicked: backend.scanDevices()
            }
        }
        Controls.BusyIndicator { visible: page.se.scanning; running: visible; Layout.alignment: Qt.AlignHCenter }
        Controls.Label {
            visible: page.se.scanned && !page.se.scanning && page.se.found.length === 0
            text: "Nichts gefunden. Trainer aufwecken (kurz treten), Gurt anlegen und erneut suchen."
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
            color: Kirigami.Theme.disabledTextColor
        }
        Repeater {
            model: page.se.found
            delegate: RowLayout {
                required property var modelData
                Layout.fillWidth: true
                Kirigami.Icon {
                    source: page.roleIcon[modelData.role] || "network-bluetooth"
                    isMask: true
                    Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                    Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
                }
                Controls.Label {
                    text: modelData.name + " · " + (page.roleText[modelData.role] || "") + " · " + modelData.rssi + " dBm"
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                }
                Controls.Button {
                    text: modelData.configured ? "Übernommen" : "Übernehmen"
                    enabled: !modelData.configured
                    highlighted: !modelData.configured
                    onClicked: backend.addDevice(modelData.address, modelData.name, modelData.role)
                }
            }
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: true
            type: Kirigami.MessageType.Information
            text: "Zeigt ein Pulsgurt unplausible Werte, Elektroden anfeuchten und nur einen Gurt tragen. Bleibt ein Gerät auf „verbinde …“, kurz abklipsen bzw. aus- und einschalten."
        }
    }

    footer: Controls.ToolBar {
        visible: page.wizard
        contentItem: RowLayout {
            Controls.Button {
                text: "Überspringen"
                flat: true
                onClicked: applicationWindow().pageStack.push(Qt.resolvedUrl("FinishPage.qml"))
            }
            Item { Layout.fillWidth: true }
            Controls.Button {
                text: "Weiter"
                icon.name: "go-next"
                highlighted: true
                enabled: page.se.devices.length > 0
                onClicked: applicationWindow().pageStack.push(Qt.resolvedUrl("FinishPage.qml"))
            }
        }
    }
}
