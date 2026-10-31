import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

// One sensor as a row of a FormCard. The row has fixed dimensions: all texts are single-line (long
// error messages are elided, shown in full in the tooltip), and the readings sit in a
// fixed-width column with two reserved lines. That way nothing jumps when values come and
// go or the state changes. Per the HIG, the remove button always stays visible.
FormCard.AbstractFormDelegate {
    id: row
    required property var device
    property bool detailed: false   // Sensors page: role, Zwift name, pause, remove, chip warning
    readonly property bool paused: device.enabled === false
    signal removeRequested()
    signal pauseRequested(bool pause)

    hoverEnabled: true
    focusPolicy: Qt.NoFocus

    readonly property var roleText: ({ "trainer": i18n("Smart trainer"), "power": i18n("Power meter"),
        "cadence": i18n("Cadence sensor"), "heartrate": i18n("Heart rate strap"), "other": i18n("Sensor") })
    // Readings per role: [key, unit]
    readonly property var valueRows: ({
        "trainer": [["power", i18n("watts")], ["cadence", i18n("rpm")]],
        "power": [["power", i18n("watts")], ["cadence", i18n("rpm")]],
        "cadence": [["cadence", i18n("rpm")]],
        "heartrate": [["heart_rate", i18n("bpm")]],
        "other": [] })
    readonly property string iconDir: Qt.resolvedUrl("../../data/icons/")
    readonly property var values: device.values || {}

    function stateColor(st) {
        return st === "connected" ? Kirigami.Theme.positiveTextColor
             : st === "connecting" ? Kirigami.Theme.neutralTextColor
             : st === "error" ? Kirigami.Theme.negativeTextColor
             : Kirigami.Theme.disabledTextColor
    }
    function stateLine(d) {
        switch (d.state) {
        case "connected": return d.zwift_clients > 0 ? i18n("Connected to Zwift") : i18n("Connected, waiting for Zwift")
        case "connecting": return i18n("Searching for the device…")
        case "disconnected": return i18n("Disconnected, trying again")
        case "error": return d.error || i18n("Unreachable")
        case "paused": return i18n("Paused")
        }
        return d.state
    }
    function stateHelp(d) {
        switch (d.state) {
        case "connected": return i18n("The bridge receives data and offers the device to Zwift.")
        case "connecting": return i18n("Pedal briefly or put on the strap; a strap does not transmit without skin contact.")
        case "error": return (d.error ? d.error + ". " : "") + i18n("The device is asleep, too far away or connected to another device. If it is not in use right now: pause it.")
        case "paused": return i18n("Paused: the bridge does not search for the device or offer it to Zwift. Resume as soon as it is needed again.")
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

            // Name, state, Zwift name: one line each
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
                    // The icon already shows the role; the Zwift name is the name to pair with in Zwift.
                    text: row.device.dircon_name ? i18n("In Zwift: %1", row.device.dircon_name)
                                                 : (row.roleText[row.device.role] || i18n("Sensor"))
                    color: Kirigami.Theme.disabledTextColor
                    font: Kirigami.Theme.smallFont
                    elide: Text.ElideRight
                    maximumLineCount: 1
                }
            }

            // Overview: readings as key figures (large digits, small unit below), fixed
            // width per value so nothing jumps while pedalling.
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

            // Sensors page: compact readings, fixed width, two lines reserved
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
                text: row.paused ? i18n("Resume") : i18n("Pause")
                display: Controls.AbstractButton.IconOnly
                Controls.ToolTip.text: row.paused ? i18n("Resume: search again and offer to Zwift")
                                                  : i18n("Pause: stop searching until resumed")
                Controls.ToolTip.visible: hovered
                Controls.ToolTip.delay: Kirigami.Units.toolTipDelay
                onClicked: row.pauseRequested(!row.paused)
            }
            Controls.ToolButton {
                visible: row.detailed
                Layout.alignment: Qt.AlignVCenter
                icon.name: "edit-delete-remove"
                text: i18n("Remove device")
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

        // Known issue with the Bluetooth chip: depends only on the device, not on live values
        Kirigami.InlineMessage {
            visible: row.detailed && !!row.device.compat
            Layout.fillWidth: true
            type: Kirigami.MessageType.Warning
            text: row.device.compat || ""
        }
    }
}
