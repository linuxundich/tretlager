import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

// Ein Sensor als Zeile einer FormCard: Symbol, Name, Zustand mit Farbpunkt, Messwerte und
// (optional) Entfernen-Knopf, der laut HIG immer sichtbar bleibt.
FormCard.AbstractFormDelegate {
    id: row
    required property var device
    property bool detailed: false   // Sensorseite: Erklärung und Zwift-Name zeigen
    signal removeRequested()

    hoverEnabled: false
    focusPolicy: Qt.NoFocus

    readonly property var stateText: ({ "verbunden": "Verbunden", "verbinde": "Verbindet …",
        "getrennt": "Getrennt", "fehler": "Nicht erreichbar", "aus": "Ausgeschaltet" })
    readonly property var stateHelp: ({
        "verbunden": "Die Bridge empfängt Daten und bietet das Gerät Zwift an.",
        "verbinde": "Die Bridge sucht das Gerät. Kurz in die Pedale treten bzw. den Gurt anlegen.",
        "getrennt": "Verbindung beendet, die Bridge versucht es erneut.",
        "fehler": "Keine Antwort. Das Gerät schläft, ist zu weit entfernt oder mit einem anderen Gerät verbunden.",
        "aus": "Weiterreichen ist für dieses Gerät abgeschaltet." })
    readonly property var roleText: ({ "trainer": "Smart-Trainer", "power": "Leistungsmesser",
        "cadence": "Trittfrequenzsensor", "heartrate": "Pulsgurt", "other": "Sensor" })
    readonly property string iconDir: Qt.resolvedUrl("../../data/icons/")

    function stateColor(st) {
        return st === "verbunden" ? Kirigami.Theme.positiveTextColor
             : st === "verbinde" ? Kirigami.Theme.neutralTextColor
             : st === "fehler" ? Kirigami.Theme.negativeTextColor
             : Kirigami.Theme.disabledTextColor
    }
    function values(v) {
        var parts = []
        if (v.power !== undefined) parts.push(v.power + " Watt")
        if (v.cadence !== undefined) parts.push(Math.round(v.cadence) + " U/min")
        if (v.heart_rate !== undefined) parts.push(v.heart_rate + " Schläge/min")
        return parts.join("\n")
    }

    contentItem: RowLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.Icon {
            source: row.device.role === "heartrate" ? row.iconDir + "tretlager-heartrate-symbolic.svg"
                  : row.device.role === "other" ? "network-bluetooth" : row.iconDir + "tretlager-trainer-symbolic.svg"
            isMask: row.device.role !== "other"
            color: Kirigami.Theme.textColor
            Layout.preferredWidth: Kirigami.Units.iconSizes.medium
            Layout.preferredHeight: Kirigami.Units.iconSizes.medium
            Layout.alignment: Qt.AlignTop
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 0
            Controls.Label {
                text: row.device.name + (row.detailed ? "  ·  " + (row.roleText[row.device.role] || "") : "")
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
            RowLayout {
                spacing: Kirigami.Units.smallSpacing
                Rectangle {
                    implicitWidth: Kirigami.Units.smallSpacing * 2
                    implicitHeight: implicitWidth
                    radius: width / 2
                    color: row.stateColor(row.device.state)
                }
                Controls.Label {
                    text: (row.stateText[row.device.state] || row.device.state)
                          + (row.device.state === "verbunden"
                             ? (row.device.zwift_clients > 0 ? ", mit Zwift verbunden" : ", wartet auf Zwift") : "")
                    color: Kirigami.Theme.disabledTextColor
                    font: Kirigami.Theme.smallFont
                }
            }
            Kirigami.InlineMessage {
                visible: row.detailed && !!row.device.compat
                Layout.fillWidth: true
                Layout.topMargin: Kirigami.Units.smallSpacing
                type: Kirigami.MessageType.Warning
                text: row.device.compat || ""
            }
            Controls.Label {
                visible: row.detailed
                Layout.fillWidth: true
                Layout.topMargin: Kirigami.Units.smallSpacing
                wrapMode: Text.WordWrap
                color: Kirigami.Theme.disabledTextColor
                font: Kirigami.Theme.smallFont
                text: (row.device.error ? row.device.error : (row.stateHelp[row.device.state] || ""))
                      + (row.device.dircon_name ? "\nIn Zwift: „" + row.device.dircon_name + "“" : "")
            }
        }

        Kirigami.Icon {
            visible: !!row.device.compat && !row.detailed
            source: "data-warning"
            Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
            Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
        }

        Controls.Label {
            text: row.values(row.device.values || {})
            horizontalAlignment: Text.AlignRight
            visible: text !== ""
        }

        Controls.ToolButton {
            visible: row.detailed
            icon.name: "edit-delete-remove"
            text: "Gerät entfernen"
            display: Controls.AbstractButton.IconOnly
            Controls.ToolTip.text: text
            Controls.ToolTip.visible: hovered
            Controls.ToolTip.delay: Kirigami.Units.toolTipDelay
            onClicked: row.removeRequested()
        }
    }
}
