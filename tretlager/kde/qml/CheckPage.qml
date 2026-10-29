import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

Kirigami.ScrollablePage {
    id: page
    title: "System prüfen"

    readonly property var statusIcon: ({ "ok": "data-success", "warn": "data-warning", "fail": "data-error" })

    actions: [
        Kirigami.Action {
            text: "Erneut prüfen"
            icon.name: "view-refresh"
            enabled: !backend.busy
            onTriggered: backend.runChecks()
        }
    ]

    header: Controls.Label {
        text: "Schritt 1 von " + applicationWindow().steps.length + " · nur lesend, ändert nichts am System"
        padding: Kirigami.Units.largeSpacing
        color: Kirigami.Theme.disabledTextColor
    }

    ListView {
        id: list
        model: backend.checks
        spacing: Kirigami.Units.smallSpacing

        delegate: Controls.ItemDelegate {
            id: row
            required property var modelData
            property bool expanded: false
            width: ListView.view.width
            onClicked: expanded = !expanded

            contentItem: ColumnLayout {
                spacing: Kirigami.Units.smallSpacing
                RowLayout {
                    spacing: Kirigami.Units.largeSpacing
                    Kirigami.Icon {
                        source: page.statusIcon[row.modelData.status]
                        Layout.preferredWidth: Kirigami.Units.iconSizes.medium
                        Layout.preferredHeight: Kirigami.Units.iconSizes.medium
                    }
                    ColumnLayout {
                        spacing: 0
                        Layout.fillWidth: true
                        Controls.Label { text: row.modelData.title; font.bold: true }
                        Controls.Label {
                            text: row.modelData.summary
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                    Kirigami.Icon {
                        visible: row.modelData.details.length > 0
                        source: row.expanded ? "arrow-up" : "arrow-down"
                        Layout.preferredWidth: Kirigami.Units.iconSizes.small
                        Layout.preferredHeight: Kirigami.Units.iconSizes.small
                    }
                }
                Repeater {
                    model: row.expanded ? row.modelData.details : []
                    delegate: Controls.Label {
                        required property string modelData
                        text: modelData
                        wrapMode: Text.WordWrap
                        color: Kirigami.Theme.disabledTextColor
                        Layout.fillWidth: true
                        Layout.leftMargin: Kirigami.Units.iconSizes.medium + Kirigami.Units.largeSpacing
                    }
                }
            }
        }

        Kirigami.PlaceholderMessage {
            anchors.centerIn: parent
            width: parent.width - Kirigami.Units.gridUnit * 4
            visible: backend.busy
            icon.name: "system-search"
            text: "System wird geprüft …"
        }
    }

    footer: ColumnLayout {
        spacing: 0
        Kirigami.InlineMessage {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.largeSpacing
            visible: !backend.busy && backend.overall !== ""
            type: backend.overall === "fail" ? Kirigami.MessageType.Error
                : backend.overall === "warn" ? Kirigami.MessageType.Warning
                : Kirigami.MessageType.Positive
            text: backend.overall === "fail" ? "Mindestens ein Punkt verhindert die Einrichtung. Details per Klick."
                : backend.overall === "warn" ? "Es geht weiter; die gelben Punkte solltest du kennen."
                : "Alles bereit."
        }
        Controls.ToolBar {
            Layout.fillWidth: true
            contentItem: RowLayout {
                Item { Layout.fillWidth: true }
                Controls.Button {
                    text: "Weiter"
                    icon.name: "go-next"
                    highlighted: true
                    enabled: !backend.busy && backend.overall !== "" && backend.overall !== "fail"
                    onClicked: applicationWindow().pageStack.push(Qt.resolvedUrl("PreparePage.qml"))
                }
            }
        }
    }
}
