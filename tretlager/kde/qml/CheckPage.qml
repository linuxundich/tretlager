import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

ColumnsPage {
    id: page
    title: i18n("Check system")

    readonly property var statusIcon: ({ "ok": "data-success", "warn": "data-warning", "fail": "data-error" })

    actions: [
        Kirigami.Action {
            text: i18n("Check again")
            icon.name: "view-refresh"
            enabled: !backend.busy
            onTriggered: backend.runChecks()
        }
    ]

    // Direkt geöffnet (Seitenleiste → Einrichtung prüfen) ohne laufende Prüfung: gleich prüfen.
    Component.onCompleted: if (!backend.busy && backend.checks.length === 0) backend.runChecks()

    header: WizardHeader { stepId: "check"; text: i18n("Read-only, nothing on the system changes.") }

    PageMessage {
        visible: !backend.busy && backend.overall !== ""
        type: backend.overall === "fail" ? Kirigami.MessageType.Error
            : backend.overall === "warn" ? Kirigami.MessageType.Warning
            : Kirigami.MessageType.Positive
        text: backend.overall === "fail" ? i18n("At least one item prevents the setup. Click an item for details.")
            : backend.overall === "warn" ? i18n("Setup is possible. Have a look at the items marked yellow first.")
            : i18n("All set.")
    }

    FormCard.FormHeader { title: i18n("Result") }
    FormCard.FormCard {
        FormCard.FormPlaceholderMessageDelegate {
            visible: backend.busy
            icon.name: "system-search"
            text: i18n("Checking the system…")
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

    footer: WizardFooter {
        nextEnabled: !backend.busy && backend.overall !== "" && backend.overall !== "fail"
        onNext: applicationWindow().pageStack.push(Qt.resolvedUrl(backend.flatpak ? "ZwiftPage.qml" : "PreparePage.qml"))
    }
}
