import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

Kirigami.ScrollablePage {
    id: page
    title: "System vorbereiten"

    readonly property var plan: backend.plan
    readonly property var prep: backend.prepare
    readonly property bool done: prep.result === "done" || plan.nothing_to_do === true
    readonly property bool blocked: (plan.removals || []).length > 0 || (plan.error || "") !== ""

    function mb(bytes) { return Math.round(bytes / 1e6) + " MB" }
    function groups(fpr) { return (fpr || "").replace(/(.{4})/g, "$1 ").trim() }

    Component.onCompleted: backend.loadPlan()

    header: Controls.Label {
        text: "Schritt 2 von " + applicationWindow().steps.length + " · eine Passwortabfrage für alle Änderungen"
        padding: Kirigami.Units.largeSpacing
        color: Kirigami.Theme.disabledTextColor
    }

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.PlaceholderMessage {
            Layout.fillWidth: true
            visible: backend.planBusy
            icon.name: "system-search"
            text: "Ermittle die nötigen Änderungen …"
            explanation: "APT rechnet die Installation probeweise durch, ohne etwas zu verändern."
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: !backend.planBusy && page.plan.nothing_to_do === true
            type: Kirigami.MessageType.Positive
            text: "WineHQ-Quelle und alle Pakete sind schon vorhanden. Hier gibt es nichts zu tun."
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: (page.plan.error || "") !== ""
            type: Kirigami.MessageType.Error
            text: page.plan.error || ""
            actions: [Kirigami.Action { text: "Erneut versuchen"; icon.name: "view-refresh"; onTriggered: backend.loadPlan() }]
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: (page.plan.removals || []).length > 0
            type: Kirigami.MessageType.Error
            text: "APT müsste dafür Pakete entfernen (" + (page.plan.removals || []).join(", ") + "). Tretlager macht das nicht; bitte die Ursache im Protokoll prüfen."
        }

        ColumnLayout {
            visible: !backend.planBusy && page.plan.nothing_to_do === false && !page.blocked
            spacing: Kirigami.Units.largeSpacing
            Layout.fillWidth: true

            Kirigami.Heading { text: "Diese Änderungen nehme ich am System vor"; level: 2 }

            Kirigami.FormLayout {
                Layout.fillWidth: true
                Controls.Label {
                    Kirigami.FormData.label: "Paketquelle:"
                    visible: page.plan.add_source === true
                    text: "WineHQ, " + (page.plan.uri || "")
                    wrapMode: Text.WrapAnywhere
                }
                Controls.Label {
                    Kirigami.FormData.label: "Schlüssel:"
                    visible: page.plan.add_source === true
                    text: page.groups(page.plan.fingerprint)
                    font.family: "monospace"
                    wrapMode: Text.WordWrap
                }
                Controls.Label {
                    Kirigami.FormData.label: "Download:"
                    text: page.mb(page.plan.download_bytes || 0) + " für " + (page.plan.packages || []).length + " Pakete"
                }
            }

            Repeater {
                model: page.plan.packages || []
                delegate: RowLayout {
                    required property var modelData
                    Layout.fillWidth: true
                    Kirigami.Icon {
                        source: "package-x-generic"
                        Layout.preferredWidth: Kirigami.Units.iconSizes.small
                        Layout.preferredHeight: Kirigami.Units.iconSizes.small
                    }
                    Controls.Label { text: modelData.name; Layout.fillWidth: true }
                    Controls.Label { text: modelData.version; color: Kirigami.Theme.disabledTextColor }
                    Controls.Label {
                        text: modelData.size > 0 ? page.mb(modelData.size) : ""
                        horizontalAlignment: Text.AlignRight
                        Layout.preferredWidth: Kirigami.Units.gridUnit * 4
                    }
                }
            }

            Kirigami.InlineMessage {
                Layout.fillWidth: true
                visible: true
                type: Kirigami.MessageType.Information
                text: "Nicht verändert werden: keine 32-Bit-Architektur, kein Systemupgrade, keine Grafiktreiber, nichts wird entfernt. TUXEDO OS legt vor und nach der Installation automatisch einen Schnappschuss an."
            }
        }

        // Fortschritt während und nach der Ausführung
        ColumnLayout {
            visible: page.prep.running || page.prep.result !== ""
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing

            Controls.Label { text: page.prep.step; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            Controls.ProgressBar {
                Layout.fillWidth: true
                from: 0; to: 100
                value: page.prep.percent
                indeterminate: visible && page.prep.running && page.prep.percent === 0
            }
            Kirigami.InlineMessage {
                Layout.fillWidth: true
                visible: page.prep.result === "error"
                type: Kirigami.MessageType.Error
                text: page.prep.error
            }
            Kirigami.InlineMessage {
                Layout.fillWidth: true
                visible: page.prep.result === "done"
                type: Kirigami.MessageType.Positive
                text: "System vorbereitet."
            }
            Controls.Button {
                text: logArea.visible ? "Protokoll ausblenden" : "Protokoll zeigen"
                flat: true
                visible: page.prep.log !== ""
                onClicked: logArea.visible = !logArea.visible
            }
            Controls.TextArea {
                id: logArea
                visible: false
                readOnly: true
                text: page.prep.log
                font.family: "monospace"
                wrapMode: Text.WrapAnywhere
                Layout.fillWidth: true
                Layout.preferredHeight: Kirigami.Units.gridUnit * 12
            }
        }
    }

    footer: Controls.ToolBar {
        contentItem: RowLayout {
            Item { Layout.fillWidth: true }
            Controls.Button {
                text: "Ändern"
                icon.name: "dialog-password"
                visible: !page.done && !page.blocked
                enabled: !backend.planBusy && !page.prep.running && (page.plan.packages || []).length + (page.plan.add_source ? 1 : 0) > 0
                highlighted: true
                onClicked: backend.runPrepare()
            }
            Controls.Button {
                text: "Weiter"
                icon.name: "go-next"
                visible: page.done
                highlighted: true
                onClicked: applicationWindow().pageStack.push(Qt.resolvedUrl("ZwiftPage.qml"))
            }
        }
    }
}
