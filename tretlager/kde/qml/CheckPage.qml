import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

ColumnsPage {
    id: page
    title: i18n("System prüfen")

    readonly property var statusIcon: ({ "ok": "data-success", "warn": "data-warning", "fail": "data-error" })

    actions: [
        Kirigami.Action {
            text: i18n("Erneut prüfen")
            icon.name: "view-refresh"
            enabled: !backend.busy
            onTriggered: backend.runChecks()
        }
    ]

    // Direkt geöffnet (Seitenleiste → Einrichtung prüfen) ohne laufende Prüfung: gleich prüfen.
    Component.onCompleted: if (!backend.busy && backend.checks.length === 0) backend.runChecks()

    header: WizardHeader { stepId: "check"; text: i18n("Nur lesend, am System ändert sich nichts.") }

    PageMessage {
        visible: !backend.busy && backend.overall !== ""
        type: backend.overall === "fail" ? Kirigami.MessageType.Error
            : backend.overall === "warn" ? Kirigami.MessageType.Warning
            : Kirigami.MessageType.Positive
        text: backend.overall === "fail" ? i18n("Mindestens ein Punkt verhindert die Einrichtung. Details per Klick auf den Punkt.")
            : backend.overall === "warn" ? i18n("Die Einrichtung ist möglich. Die gelb markierten Punkte vorher ansehen.")
            : i18n("Alles bereit.")
    }

    FormCard.FormHeader { title: i18n("Ergebnis") }
    FormCard.FormCard {
        FormCard.FormPlaceholderMessageDelegate {
            visible: backend.busy
            icon.name: "system-search"
            text: i18n("System wird geprüft …")
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
