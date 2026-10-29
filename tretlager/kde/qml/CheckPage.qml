import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

FormCard.FormCardPage {
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

    header: WizardHeader { step: 1; text: "Nur lesend, am System ändert sich nichts." }

    Kirigami.InlineMessage {
        Layout.fillWidth: true
        Layout.maximumWidth: Kirigami.Units.gridUnit * 30
        Layout.alignment: Qt.AlignHCenter
        Layout.topMargin: Kirigami.Units.largeSpacing
        visible: !backend.busy && backend.overall !== ""
        type: backend.overall === "fail" ? Kirigami.MessageType.Error
            : backend.overall === "warn" ? Kirigami.MessageType.Warning
            : Kirigami.MessageType.Positive
        text: backend.overall === "fail" ? "Mindestens ein Punkt verhindert die Einrichtung. Details per Klick auf den Punkt."
            : backend.overall === "warn" ? "Die Einrichtung ist möglich. Die gelb markierten Punkte vorher ansehen."
            : "Alles bereit."
    }

    FormCard.FormHeader { title: "Ergebnis" }
    FormCard.FormCard {
        FormCard.FormPlaceholderMessageDelegate {
            visible: backend.busy
            icon.name: "system-search"
            text: "System wird geprüft …"
        }
        Repeater {
            model: backend.busy ? [] : backend.checks
            delegate: FormCard.AbstractFormDelegate {
                id: row
                required property var modelData
                required property int index
                property bool expanded: false
                enabled: true
                onClicked: if (modelData.details.length > 0) expanded = !expanded

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
                            Controls.Label { text: row.modelData.title; Layout.fillWidth: true; elide: Text.ElideRight }
                            Controls.Label {
                                text: row.modelData.summary
                                wrapMode: Text.WordWrap
                                color: Kirigami.Theme.disabledTextColor
                                font: Kirigami.Theme.smallFont
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
                            font: Kirigami.Theme.smallFont
                            Layout.fillWidth: true
                            Layout.leftMargin: Kirigami.Units.iconSizes.medium + Kirigami.Units.largeSpacing
                        }
                    }
                }
            }
        }
    }

    Item { implicitHeight: Kirigami.Units.gridUnit }

    footer: WizardFooter {
        nextEnabled: !backend.busy && backend.overall !== "" && backend.overall !== "fail"
        onNext: applicationWindow().pageStack.push(Qt.resolvedUrl("PreparePage.qml"))
    }
}
