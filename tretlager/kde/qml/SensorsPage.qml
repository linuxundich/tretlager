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
    readonly property var stateText: ({
        "verbunden": "Verbunden",
        "verbinde": "Verbindet …",
        "getrennt": "Getrennt",
        "fehler": "Nicht erreichbar",
        "aus": "Ausgeschaltet" })
    readonly property var stateHelp: ({
        "verbunden": "Die Bridge empfängt Daten und bietet das Gerät Zwift an.",
        "verbinde": "Die Bridge sucht das Gerät. Trainer kurz treten, Gurt anlegen.",
        "getrennt": "Verbindung beendet; die Bridge versucht es erneut.",
        "fehler": "Gerät antwortet nicht – schläft es, ist es zu weit weg oder mit etwas anderem verbunden?",
        "aus": "Weiterreichen ist für dieses Gerät abgeschaltet." })
    // Eigene Symbole (wie in der GTK-Oberfläche), als Maske in der Textfarbe eingefärbt.
    readonly property string iconDir: Qt.resolvedUrl("../../ui/icons/hicolor/scalable/actions/")
    function roleIcon(role) {
        return role === "heartrate" ? iconDir + "tretlager-heartrate-symbolic.svg"
             : role === "other" ? "network-bluetooth" : iconDir + "tretlager-trainer-symbolic.svg"
    }
    function stateColor(st) {
        return st === "verbunden" ? Kirigami.Theme.positiveTextColor
             : st === "verbinde" ? Kirigami.Theme.neutralTextColor
             : st === "fehler" ? Kirigami.Theme.negativeTextColor
             : Kirigami.Theme.disabledTextColor
    }
    function values(v) {
        var parts = []
        if (v.power !== undefined) parts.push(v.power + " W")
        if (v.cadence !== undefined) parts.push(Math.round(v.cadence) + " U/min")
        if (v.heart_rate !== undefined) parts.push(v.heart_rate + " bpm")
        return parts.join("  ·  ")
    }

    Component.onCompleted: backend.setSensorPolling(true)

    header: Controls.Label {
        visible: page.wizard
        text: "Schritt 5 von " + applicationWindow().steps.length + " · tritt kurz in die Pedale und leg den Pulsgurt an"
        padding: Kirigami.Units.largeSpacing
        color: Kirigami.Theme.disabledTextColor
        wrapMode: Text.WordWrap
    }

    PageContent {
        Controls.Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: "Zwift kann unter Linux kein Bluetooth nutzen. Die <b>Sensor-Bridge</b> verbindet sich mit Trainer und Pulsgurt und bietet sie Zwift als Wahoo-„Direct Connect“-Geräte an. Die Zwift Companion App brauchst du dafür nicht."
            textFormat: Text.StyledText
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: !page.se.installed
            type: Kirigami.MessageType.Error
            text: "Die Sensor-Bridge ist nicht installiert (Dienst tretlager-bridge fehlt). Bitte das Paket tretlager neu installieren."
        }
        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: page.se.error !== ""
            type: Kirigami.MessageType.Error
            text: page.se.error
        }
        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: page.se.devices.some(function (d) { return d.unstable })
            type: Kirigami.MessageType.Warning
            text: "Die Verbindung zu " + page.se.devices.filter(function (d) { return d.unstable })
                  .map(function (d) { return d.name }).join(", ")
                  + " bricht oft ab. Meist ist der Funkweg zu lang: Rechner näher an den Trainer stellen, einen USB-Bluetooth-Stick mit Verlängerungskabel nutzen oder die Bridge auf einem Rechner neben dem Trainer laufen lassen (unten „Im Netz anbieten“)."
        }

        // --- Bridge ---
        Kirigami.Heading { text: "Sensor-Bridge"; level: 2 }
        Kirigami.AbstractCard {
            Layout.fillWidth: true
            contentItem: ColumnLayout {
                spacing: Kirigami.Units.largeSpacing
                Kirigami.FormLayout {
                    Layout.fillWidth: true
                    Controls.Switch {
                        Kirigami.FormData.label: "Bridge:"
                        text: checked ? "läuft" : "aus"
                        checked: page.se.running
                        enabled: page.se.installed
                        onToggled: backend.setBridgeRunning(checked)
                    }
                    Controls.Switch {
                        Kirigami.FormData.label: "Beim Anmelden starten:"
                        text: checked ? "ja" : "nein – Tretlager startet sie beim Öffnen und mit Zwift"
                        checked: page.se.autostart
                        enabled: page.se.installed
                        onToggled: backend.setBridgeAutostart(checked)
                    }
                    Controls.Switch {
                        Kirigami.FormData.label: "Im Netz anbieten:"
                        text: checked ? "ja – auch für Zwift auf anderen Geräten" : "nein – nur für Zwift auf diesem Rechner"
                        checked: page.se.network
                        enabled: page.se.installed && page.se.running
                        onToggled: backend.setBridgeNetwork(checked)
                    }
                }
                Hint {
                    text: page.se.network
                          ? "Die Geräte sind im lokalen Netz sichtbar. So kann ein Rechner neben dem Trainer die Sensoren halten und Zwift auf einem anderen Gerät sie nutzen. Beachte: Jeder im Netz könnte dann den Trainer steuern."
                          : "„Im Netz anbieten“ brauchst du nur, wenn Zwift auf einem anderen Gerät läuft als die Bridge, etwa wenn ein kleiner Rechner neben dem Trainer die Sensoren hält."
                }
            }
        }

        // --- Geräte ---
        Kirigami.Heading { text: "Deine Geräte"; level: 2; Layout.topMargin: Kirigami.Units.largeSpacing }
        Hint {
            visible: page.se.devices.length === 0
            text: page.se.running ? "Noch keine Geräte. Unten nach Geräten in der Nähe suchen und übernehmen."
                                  : "Schalte die Bridge ein, um Geräte zu verwalten."
        }
        Repeater {
            model: page.se.devices
            delegate: Kirigami.AbstractCard {
                required property var modelData
                Layout.fillWidth: true
                contentItem: RowLayout {
                    spacing: Kirigami.Units.gridUnit
                    Kirigami.Icon {
                        source: page.roleIcon(modelData.role)
                        isMask: true
                        Layout.preferredWidth: Kirigami.Units.iconSizes.large
                        Layout.preferredHeight: Kirigami.Units.iconSizes.large
                        Layout.alignment: Qt.AlignTop
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: Kirigami.Units.smallSpacing
                        RowLayout {
                            Kirigami.Heading { text: modelData.name; level: 3 }
                            Controls.Label { text: "· " + (page.roleText[modelData.role] || ""); color: Kirigami.Theme.disabledTextColor }
                        }
                        RowLayout {
                            Rectangle {
                                width: Kirigami.Units.smallSpacing * 2.5; height: width; radius: width / 2
                                color: page.stateColor(modelData.state)
                            }
                            Controls.Label {
                                text: (page.stateText[modelData.state] || modelData.state)
                                      + (modelData.state === "verbunden"
                                         ? (modelData.zwift_clients > 0 ? " · Zwift ist verbunden" : " · wartet auf Zwift") : "")
                                font.bold: true
                            }
                        }
                        Controls.Label {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            color: Kirigami.Theme.disabledTextColor
                            text: modelData.error ? modelData.error : (page.stateHelp[modelData.state] || "")
                        }
                        Controls.Label {
                            visible: modelData.dircon_name !== undefined
                            color: Kirigami.Theme.disabledTextColor
                            text: "In Zwift heißt das Gerät „" + (modelData.dircon_name || "") + "“"
                        }
                    }
                    Controls.Label {
                        text: page.values(modelData.values || {})
                        font.pointSize: Kirigami.Theme.defaultFont.pointSize * 1.6
                        Layout.alignment: Qt.AlignVCenter
                    }
                    Controls.ToolButton {
                        icon.name: "edit-delete"
                        Layout.alignment: Qt.AlignVCenter
                        Controls.ToolTip.text: "Gerät entfernen – die Bridge vergisst es"
                        Controls.ToolTip.visible: hovered
                        onClicked: backend.removeDevice(modelData.address)
                    }
                }
            }
        }

        // --- Suche ---
        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: Kirigami.Units.largeSpacing
            Kirigami.Heading { text: "Neue Geräte"; level: 2; Layout.fillWidth: true }
            Controls.Button {
                text: page.se.scanning ? "Suche läuft …" : "In der Nähe suchen"
                icon.name: "system-search"
                enabled: page.se.running && !page.se.scanning
                onClicked: backend.scanDevices()
            }
        }
        Hint {
            text: "Die Suche dauert etwa zehn Sekunden und findet Smart-Trainer, Leistungsmesser, Trittfrequenzsensoren und Pulsgurte. Wecke den Trainer vorher auf, indem du kurz trittst."
        }
        Controls.BusyIndicator { visible: page.se.scanning; running: visible; Layout.alignment: Qt.AlignHCenter }
        Hint {
            visible: page.se.scanned && !page.se.scanning && page.se.found.length === 0
            icon: "dialog-warning"
            text: "Nichts gefunden. Trainer aufwecken, Gurt anlegen (er schaltet sich ohne Hautkontakt ab) und erneut suchen."
        }
        Repeater {
            model: page.se.found
            delegate: Kirigami.AbstractCard {
                required property var modelData
                Layout.fillWidth: true
                contentItem: RowLayout {
                    spacing: Kirigami.Units.largeSpacing
                    Kirigami.Icon {
                        source: page.roleIcon(modelData.role)
                        isMask: true
                        Layout.preferredWidth: Kirigami.Units.iconSizes.medium
                        Layout.preferredHeight: Kirigami.Units.iconSizes.medium
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0
                        Controls.Label { text: modelData.name; font.bold: true }
                        Controls.Label {
                            text: (page.roleText[modelData.role] || "") + " · Signal " + modelData.rssi + " dBm"
                            color: Kirigami.Theme.disabledTextColor
                        }
                    }
                    Controls.Button {
                        text: modelData.configured ? "Übernommen" : "Übernehmen"
                        icon.name: modelData.configured ? "dialog-ok" : "list-add"
                        enabled: !modelData.configured
                        highlighted: !modelData.configured
                        onClicked: backend.addDevice(modelData.address, modelData.name, modelData.role)
                    }
                }
            }
        }

        // --- Tipps ---
        Kirigami.Heading { text: "Wenn etwas hakt"; level: 2; Layout.topMargin: Kirigami.Units.largeSpacing }
        Hint { icon: "emblem-favorite"; text: "<b>Puls viel zu hoch?</b> Elektroden des Gurts anfeuchten, Gurt enger stellen, nur einen Gurt tragen." }
        Hint { icon: "view-refresh"; text: "<b>Gerät bleibt bei „Verbindet …“?</b> Trainer kurz treten, Gurt kurz abklipsen. Die Bridge sucht alle zehn Sekunden erneut." }
        Hint { icon: "network-wireless"; text: "<b>Verbindung bricht oft ab?</b> Bluetooth reicht durch Wände nur schlecht. Rechner näher an den Trainer oder USB-Bluetooth-Stick mit Verlängerung." }
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
