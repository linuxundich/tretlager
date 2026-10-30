import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

ColumnsPage {
    id: page
    title: "System vorbereiten"

    readonly property var plan: backend.plan
    readonly property var prep: backend.prepare
    readonly property bool done: prep.result === "done" || plan.nothing_to_do === true
    readonly property bool blocked: (plan.removals || []).length > 0 || (plan.error || "") !== ""
    readonly property bool showPlan: !backend.planBusy && plan.nothing_to_do === false && !blocked

    function mb(bytes) { return Math.round(bytes / 1e6) + " MB" }
    function groups(fpr) { return (fpr || "").replace(/(.{4})/g, "$1 ").trim() }

    Component.onCompleted: backend.loadPlan()

    header: WizardHeader { step: 2; text: "Eine Passwortabfrage für alle Änderungen." }

    LogDialog { id: logDialog; text: page.prep.log }

    PageMessage {
        visible: !backend.planBusy && page.plan.nothing_to_do === true
        type: Kirigami.MessageType.Positive
        text: "WineHQ-Quelle und alle Pakete sind schon vorhanden. Hier gibt es nichts zu tun."
    }
    PageMessage {
        visible: (page.plan.error || "") !== ""
        type: Kirigami.MessageType.Error
        text: page.plan.error || ""
        actions: [Kirigami.Action { text: "Erneut versuchen"; icon.name: "view-refresh"; onTriggered: backend.loadPlan() }]
    }
    PageMessage {
        visible: (page.plan.removals || []).length > 0
        type: Kirigami.MessageType.Error
        text: "APT müsste dafür Pakete entfernen (" + (page.plan.removals || []).join(", ") + "). Das macht Tretlager nicht. Die Ursache steht im Protokoll."
    }
    PageMessage {
        visible: page.prep.result === "error"
        type: Kirigami.MessageType.Error
        text: page.prep.error
        actions: [Kirigami.Action { text: "Protokoll"; icon.name: "view-list-text"; onTriggered: logDialog.open() }]
    }
    PageMessage {
        visible: page.prep.result === "done"
        type: Kirigami.MessageType.Positive
        text: "System vorbereitet."
    }

    FormCard.FormCard {
        visible: backend.planBusy
        FormCard.FormPlaceholderMessageDelegate {
            icon.name: "system-search"
            text: "Nötige Änderungen werden ermittelt …"
            explanation: "APT rechnet die Installation probeweise durch, ohne etwas zu verändern."
        }
    }

    leftCards: [
        // --- Plan ---
        FormCard.FormHeader {
            visible: page.showPlan
            title: "Änderungen am System"
            trailing: Kirigami.ContextualHelpButton {
                toolTipText: "Unverändert bleiben: keine 32-Bit-Architektur, kein Systemupgrade, keine Grafiktreiber, "
                    + "nichts wird entfernt. TUXEDO OS legt vor und nach der Installation automatisch einen "
                    + "Schnappschuss an."
            }
        },
        FormCard.FormCard {
            visible: page.showPlan
            FormCard.FormTextDelegate {
                visible: page.plan.add_source === true
                text: "Paketquelle WineHQ"
                description: (page.plan.uri || "") + "\nSchlüssel " + page.groups(page.plan.fingerprint)
                icon.name: "repository"
            }
            FormCard.FormDelegateSeparator { visible: page.plan.add_source === true }
            FormCard.FormTextDelegate {
                text: "Download"
                description: page.mb(page.plan.download_bytes || 0) + " für " + (page.plan.packages || []).length + " Pakete"
                icon.name: "download"
            }
        },

        // --- Fortschritt ---
        FormCard.FormHeader { visible: page.prep.running || page.prep.result !== ""; title: "Fortschritt" },
        FormCard.FormCard {
            visible: page.prep.running || page.prep.result !== ""
            FormCard.AbstractFormDelegate {
                hoverEnabled: false
                focusPolicy: Qt.NoFocus
                contentItem: ColumnLayout {
                    spacing: Kirigami.Units.smallSpacing
                    Controls.Label { text: page.prep.step; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Controls.ProgressBar {
                        Layout.fillWidth: true
                        from: 0; to: 100
                        value: page.prep.percent
                        indeterminate: visible && page.prep.running && page.prep.percent === 0
                    }
                }
            }
            FormCard.FormDelegateSeparator { visible: page.prep.log !== "" }
            FormCard.FormButtonDelegate {
                visible: page.prep.log !== ""
                text: "Protokoll …"
                icon.name: "view-list-text"
                onClicked: logDialog.open()
            }
        }
    ]

    rightCards: [
        FormCard.FormHeader { visible: page.showPlan; title: "Pakete" },
        FormCard.FormCard {
            visible: page.showPlan
            Repeater {
                model: page.plan.packages || []
                delegate: FormCard.FormTextDelegate {
                    required property var modelData
                    text: modelData.name
                    description: modelData.version
                    icon.name: "package-x-generic"
                    trailing: Controls.Label {
                        text: modelData.size > 0 ? page.mb(modelData.size) : ""
                        color: Kirigami.Theme.disabledTextColor
                    }
                }
            }
        }
    ]

    footer: WizardFooter {
        nextText: page.done ? "Weiter" : "Änderungen vornehmen …"
        nextIcon: page.done ? "go-next" : "dialog-password"
        nextVisible: page.done || !page.blocked
        nextEnabled: page.done || (!backend.planBusy && !page.prep.running
                     && (page.plan.packages || []).length + (page.plan.add_source ? 1 : 0) > 0)
        onNext: page.done ? applicationWindow().pageStack.push(Qt.resolvedUrl("ZwiftPage.qml")) : backend.runPrepare()
    }
}
