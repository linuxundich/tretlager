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

    readonly property var roleText: ({ "trainer": i18n("Smart-Trainer"), "power": i18n("Leistungsmesser"),
        "cadence": i18n("Trittfrequenzsensor"), "heartrate": i18n("Pulsgurt"), "other": i18n("Sensor") })
    // Messwerte je Rolle: [Schlüssel, Einheit]
    readonly property var valueRows: ({
        "trainer": [["power", i18n("Watt")], ["cadence", i18n("U/min")]],
        "power": [["power", i18n("Watt")], ["cadence", i18n("U/min")]],
        "cadence": [["cadence", i18n("U/min")]],
        "heartrate": [["heart_rate", i18n("Schläge/min")]],
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
        case "verbunden": return d.zwift_clients > 0 ? i18n("Mit Zwift verbunden") : i18n("Verbunden, wartet auf Zwift")
        case "verbinde": return i18n("Sucht das Gerät …")
        case "getrennt": return i18n("Getrennt, neuer Versuch folgt")
        case "fehler": return d.error || i18n("Nicht erreichbar")
        case "aus": return i18n("Pausiert")
        }
        return d.state
    }
    function stateHelp(d) {
        switch (d.state) {
        case "verbunden": return i18n("Die Bridge empfängt Daten und bietet das Gerät Zwift an.")
        case "verbinde": return i18n("Kurz in die Pedale treten bzw. den Gurt anlegen; ohne Hautkontakt sendet ein Gurt nicht.")
        case "fehler": return (d.error ? d.error + ". " : "") + i18n("Das Gerät schläft, ist zu weit entfernt oder mit einem anderen Gerät verbunden. Wird es gerade nicht genutzt: pausieren.")
        case "aus": return i18n("Pausiert: Die Bridge sucht das Gerät nicht und bietet es Zwift nicht an. Fortsetzen, sobald es wieder gebraucht wird.")
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
                    text: row.device.dircon_name ? i18n("In Zwift: %1", row.device.dircon_name)
                                                 : (row.roleText[row.device.role] || i18n("Sensor"))
                    color: Kirigami.Theme.disabledTextColor
                    font: Kirigami.Theme.smallFont
                    elide: Text.ElideRight
                    maximumLineCount: 1
                }
            }

            // Übersicht: Messwerte als Kennzahlen (große Ziffer, Einheit klein darunter), feste
            // Breite je Wert, damit beim Treten nichts springt.
            Repeater {
                model: row.detailed ? [] : (row.valueRows[row.device.role] || [])
                delegate: ColumnLayout {
                    required property var modelData
                    readonly property bool live: row.values[modelData[0]] !== undefined
                    opacity: row.paused ? 0.55 : 1
                    Layout.alignment: Qt.AlignVCenter
                    Layout.preferredWidth: Kirigami.Units.gridUnit * 4.5
                    spacing: 0
                    Kirigami.Heading {
                        Layout.alignment: Qt.AlignRight
                        level: 1
                        text: row.formatValue(modelData[0])
                        font.features: { "tnum": 1 }
                        color: parent.live ? Kirigami.Theme.textColor : Kirigami.Theme.disabledTextColor
                        Accessible.name: text + " " + modelData[1]
                    }
                    Controls.Label {
                        Layout.alignment: Qt.AlignRight
                        text: modelData[1]
                        color: Kirigami.Theme.disabledTextColor
                        font: Kirigami.Theme.smallFont
                    }
                }
            }

            // Sensorseite: Messwerte kompakt, feste Breite, zwei Zeilen reserviert
            ColumnLayout {
                visible: row.detailed
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
                text: row.paused ? i18n("Fortsetzen") : i18n("Pausieren")
                display: Controls.AbstractButton.IconOnly
                Controls.ToolTip.text: row.paused ? i18n("Fortsetzen: wieder suchen und Zwift anbieten")
                                                  : i18n("Pausieren: nicht mehr suchen, bis zum Fortsetzen")
                Controls.ToolTip.visible: hovered
                Controls.ToolTip.delay: Kirigami.Units.toolTipDelay
                onClicked: row.pauseRequested(!row.paused)
            }
            Controls.ToolButton {
                visible: row.detailed
                Layout.alignment: Qt.AlignVCenter
                icon.name: "edit-delete-remove"
                text: i18n("Gerät entfernen")
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
