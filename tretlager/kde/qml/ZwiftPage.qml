import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

Kirigami.ScrollablePage {
    id: page
    title: "Zwift einrichten"

    readonly property var st: backend.zwiftSetup
    readonly property var stepIcon: ({
        "pending": "chronometer", "running": "media-playback-start",
        "done": "data-success", "skipped": "data-success", "error": "data-error"
    })

    Component.onCompleted: if (!st.running && st.result !== "done") backend.runSetup()

    header: Controls.Label {
        text: "Schritt 3 von " + applicationWindow().steps.length + " · läuft ohne dein Zutun, etwa 10 Minuten"
        padding: Kirigami.Units.largeSpacing
        color: Kirigami.Theme.disabledTextColor
    }

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Repeater {
            model: page.st.steps
            delegate: ColumnLayout {
                id: stepRow
                required property var modelData
                readonly property bool active: modelData.status === "running"
                Layout.fillWidth: true
                spacing: Kirigami.Units.smallSpacing

                RowLayout {
                    spacing: Kirigami.Units.largeSpacing
                    Kirigami.Icon {
                        source: page.stepIcon[stepRow.modelData.status]
                        opacity: stepRow.modelData.status === "pending" ? 0.4 : 1
                        Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                        Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
                    }
                    Controls.Label {
                        text: stepRow.modelData.title
                        font.bold: stepRow.active
                        opacity: stepRow.modelData.status === "pending" ? 0.6 : 1
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                    Controls.Label {
                        visible: stepRow.modelData.status === "skipped"
                        text: "schon erledigt"
                        color: Kirigami.Theme.disabledTextColor
                    }
                }
                Controls.ProgressBar {
                    visible: stepRow.active
                    Layout.fillWidth: true
                    Layout.leftMargin: Kirigami.Units.iconSizes.smallMedium + Kirigami.Units.largeSpacing
                    from: 0; to: 100
                    value: page.st.current === stepRow.modelData.id ? page.st.percent : 0
                    indeterminate: page.st.percent <= 0
                }
                Controls.Label {
                    visible: stepRow.active && page.st.text !== ""
                    text: page.st.text
                    color: Kirigami.Theme.disabledTextColor
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                    Layout.leftMargin: Kirigami.Units.iconSizes.smallMedium + Kirigami.Units.largeSpacing
                }
            }
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: page.st.result === "error"
            type: Kirigami.MessageType.Error
            text: page.st.error + " Bereits Erledigtes bleibt erhalten."
            actions: [Kirigami.Action { text: "Erneut versuchen"; icon.name: "view-refresh"; onTriggered: backend.runSetup() }]
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: page.st.result === "done"
            type: Kirigami.MessageType.Positive
            text: "Zwift ist eingerichtet."
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: page.st.running
            type: Kirigami.MessageType.Information
            text: "Du kannst das Fenster schließen; beim nächsten Start macht Tretlager dort weiter. Die Komponenten von Microsoft (.NET, WebView2, Schriften) unterliegen Microsofts Lizenzbedingungen."
        }

        Controls.Button {
            text: logArea.visible ? "Protokoll ausblenden" : "Protokoll zeigen"
            flat: true
            visible: page.st.log !== ""
            onClicked: logArea.visible = !logArea.visible
        }
        Controls.TextArea {
            id: logArea
            visible: false
            readOnly: true
            text: page.st.log
            font.family: "monospace"
            wrapMode: Text.WrapAnywhere
            Layout.fillWidth: true
            Layout.preferredHeight: Kirigami.Units.gridUnit * 14
        }
    }

    footer: Controls.ToolBar {
        contentItem: RowLayout {
            Controls.Button {
                text: "Abbrechen"
                icon.name: "dialog-cancel"
                visible: page.st.running
                onClicked: backend.cancelSetup()
            }
            Item { Layout.fillWidth: true }
            Controls.Button {
                text: "Weiter"
                icon.name: "go-next"
                highlighted: true
                enabled: page.st.result === "done"
                onClicked: applicationWindow().pageStack.push(Qt.resolvedUrl("LoginPage.qml"))
            }
        }
    }
}
