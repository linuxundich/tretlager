import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

// Ein Sensor als Zeile einer FormCard. Die Zeile hat feste Maße: Alle Texte sind einzeilig (lange
// Fehlermeldungen werden gekürzt, vollständig im Tooltip), und die Messwerte stehen in einer
// Spalte fester Breite mit zwei reservierten Zeilen. So springt nichts, wenn Werte kommen und
// gehen oder der Zustand wechselt. Der Entfernen-Knopf bleibt laut HIG immer sichtbar.
FormCard.AbstractFormDelegate {
    id: row
    required property var device
    property bool detailed: false   // Sensorseite: Rolle, Zwift-Name, Pausieren, Entfernen, Chip-Warnung
    readonly property bool paused: device.enabled === false
    signal removeRequested()
    signal pauseRequested(bool pause)

    hoverEnabled: true
    focusPolicy: Qt.NoFocus

    readonly property var roleText: ({ "trainer": "Smart-Trainer", "power": "Leistungsmesser",
        "cadence": "Trittfrequenzsensor", "heartrate": "Pulsgurt", "other": "Sensor" })
    // Messwerte je Rolle: [Schlüssel, Einheit]
    readonly property var valueRows: ({
        "trainer": [["power", "Watt"], ["cadence", "U/min"]],
        "power": [["power", "Watt"], ["cadence", "U/min"]],
        "cadence": [["cadence", "U/min"]],
        "heartrate": [["heart_rate", "Schläge/min"]],
        "other": [] })
    readonly property string iconDir: Qt.resolvedUrl("../../data/icons/")
    readonly property var values: device.values || {}

    function stateColor(st) {
        return st === "verbunden" ? Kirigami.Theme.positiveTextColor
             : st === "verbinde" ? Kirigami.Theme.neutralTextColor
             : st === "fehler" ? Kirigami.Theme.negativeTextColor
             : Kirigami.Theme.disabledTextColor
    }
    function stateLine(d) {
        switch (d.state) {
        case "verbunden": return d.zwift_clients > 0 ? "Mit Zwift verbunden" : "Verbunden, wartet auf Zwift"
        case "verbinde": return "Sucht das Gerät …"
        case "getrennt": return "Getrennt, neuer Versuch folgt"
        case "fehler": return d.error || "Nicht erreichbar"
        case "aus": return "Pausiert"
        }
        return d.state
    }
    function stateHelp(d) {
        switch (d.state) {
        case "verbunden": return "Die Bridge empfängt Daten und bietet das Gerät Zwift an."
        case "verbinde": return "Kurz in die Pedale treten bzw. den Gurt anlegen; ohne Hautkontakt sendet ein Gurt nicht."
        case "fehler": return (d.error ? d.error + ". " : "") + "Das Gerät schläft, ist zu weit entfernt oder mit einem anderen Gerät verbunden. Wird es gerade nicht genutzt: pausieren."
        case "aus": return "Pausiert: Die Bridge sucht das Gerät nicht und bietet es Zwift nicht an. Fortsetzen, sobald es wieder gebraucht wird."
        }
        return ""
    }
    function formatValue(key) {
        const v = row.values[key]
        if (v === undefined) return "–"
        return key === "cadence" ? Math.round(v).toString() : v.toString()
    }

    Controls.ToolTip.text: stateHelp(device)
    Controls.ToolTip.visible: hovered && Controls.ToolTip.text !== ""
    Controls.ToolTip.delay: Kirigami.Units.toolTipDelay

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.smallSpacing

        RowLayout {
            spacing: Kirigami.Units.largeSpacing

            Kirigami.Icon {
                opacity: row.paused ? 0.55 : 1
                source: row.device.role === "heartrate" ? row.iconDir + "tretlager-heartrate-symbolic.svg"
                      : row.device.role === "other" ? "network-bluetooth" : row.iconDir + "tretlager-trainer-symbolic.svg"
                isMask: row.device.role !== "other"
                color: Kirigami.Theme.textColor
                Layout.preferredWidth: Kirigami.Units.iconSizes.medium
                Layout.preferredHeight: Kirigami.Units.iconSizes.medium
                Layout.alignment: Qt.AlignVCenter
            }

            // Name, Zustand, Zwift-Name: je eine Zeile
            ColumnLayout {
                opacity: row.paused ? 0.55 : 1
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
                spacing: 0
                Controls.Label {
                    Layout.fillWidth: true
                    text: row.device.name
                    elide: Text.ElideRight
                    maximumLineCount: 1
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: Kirigami.Units.smallSpacing
                    Rectangle {
                        implicitWidth: Kirigami.Units.smallSpacing * 2
                        implicitHeight: implicitWidth
                        radius: width / 2
                        color: row.stateColor(row.device.state)
                    }
                    Controls.Label {
                        Layout.fillWidth: true
                        text: row.stateLine(row.device)
                        color: Kirigami.Theme.disabledTextColor
                        font: Kirigami.Theme.smallFont
                        elide: Text.ElideRight
                        maximumLineCount: 1
                    }
                }
                Controls.Label {
                    visible: row.detailed
                    Layout.fillWidth: true
                    // Die Rolle zeigt schon das Symbol; der Zwift-Name ist der Name zum Koppeln in Zwift.
                    text: row.device.dircon_name ? "In Zwift: " + row.device.dircon_name
                                                 : (row.roleText[row.device.role] || "Sensor")
                    color: Kirigami.Theme.disabledTextColor
                    font: Kirigami.Theme.smallFont
                    elide: Text.ElideRight
                    maximumLineCount: 1
                }
            }

            // Messwerte: feste Breite, zwei Zeilen reserviert
            ColumnLayout {
                opacity: row.paused ? 0.55 : 1
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredWidth: Kirigami.Units.gridUnit * 6
                Layout.maximumWidth: Kirigami.Units.gridUnit * 6
                spacing: 0
                Repeater {
                    model: 2
                    delegate: Item {
                        required property int index
                        readonly property var spec: (row.valueRows[row.device.role] || [])[index]
                        Layout.fillWidth: true
                        implicitHeight: valueLabel.implicitHeight
                        Controls.Label {
                            id: valueLabel
                            anchors.right: unitLabel.left
                            anchors.rightMargin: Kirigami.Units.smallSpacing
                            text: parent.spec ? row.formatValue(parent.spec[0]) : " "
                            font.bold: true
                            font.features: { "tnum": 1 }
                            color: row.values[parent.spec ? parent.spec[0] : ""] === undefined
                                   ? Kirigami.Theme.disabledTextColor : Kirigami.Theme.textColor
                        }
                        Controls.Label {
                            id: unitLabel
                            anchors.right: parent.right
                            anchors.baseline: valueLabel.baseline
                            width: Kirigami.Units.gridUnit * 4
                            text: parent.spec ? parent.spec[1] : ""
                            color: Kirigami.Theme.disabledTextColor
                            font: Kirigami.Theme.smallFont
                        }
                    }
                }
            }

            Controls.ToolButton {
                visible: row.detailed
                Layout.alignment: Qt.AlignVCenter
                icon.name: row.paused ? "media-playback-start" : "media-playback-pause"
                text: row.paused ? "Fortsetzen" : "Pausieren"
                display: Controls.AbstractButton.IconOnly
                Controls.ToolTip.text: row.paused ? "Fortsetzen: wieder suchen und Zwift anbieten"
                                                  : "Pausieren: nicht mehr suchen, bis zum Fortsetzen"
                Controls.ToolTip.visible: hovered
                Controls.ToolTip.delay: Kirigami.Units.toolTipDelay
                onClicked: row.pauseRequested(!row.paused)
            }
            Controls.ToolButton {
                visible: row.detailed
                Layout.alignment: Qt.AlignVCenter
                icon.name: "edit-delete-remove"
                text: "Gerät entfernen"
                display: Controls.AbstractButton.IconOnly
                Controls.ToolTip.text: text
                Controls.ToolTip.visible: hovered
                Controls.ToolTip.delay: Kirigami.Units.toolTipDelay
                onClicked: row.removeRequested()
            }
            Kirigami.Icon {
                visible: !!row.device.compat && !row.detailed
                source: "data-warning"
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
            }
        }

        // Bekanntes Problem mit dem Bluetooth-Chip: hängt nur vom Gerät ab, nicht von Live-Werten
        Kirigami.InlineMessage {
            visible: row.detailed && !!row.device.compat
            Layout.fillWidth: true
            type: Kirigami.MessageType.Warning
            text: row.device.compat || ""
        }
    }
}
