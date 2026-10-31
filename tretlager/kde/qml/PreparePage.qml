import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

ColumnsPage {
    id: page
    title: i18n("Prepare system")

    readonly property var plan: backend.plan
    readonly property var prep: backend.prepare
    readonly property bool done: prep.result === "done" || plan.nothing_to_do === true
    readonly property bool blocked: (plan.removals || []).length > 0 || (plan.error || "") !== ""
    readonly property bool showPlan: !backend.planBusy && plan.nothing_to_do === false && !blocked

    function mb(bytes) { return i18n("%1 MB", Math.round(bytes / 1e6)) }
    function groups(fpr) { return (fpr || "").replace(/(.{4})/g, "$1 ").trim() }

    Component.onCompleted: backend.loadPlan()

    header: WizardHeader { stepId: "prepare"; text: i18n("One password prompt for all changes.") }

    LogDialog { id: logDialog; text: page.prep.log }

    PageMessage {
        visible: !backend.planBusy && page.plan.nothing_to_do === true
        type: Kirigami.MessageType.Positive
        text: i18n("The WineHQ source and all packages are already present. Nothing to do here.")
    }
    PageMessage {
        visible: (page.plan.error || "") !== ""
        type: Kirigami.MessageType.Error
        text: page.plan.error || ""
        actions: [Kirigami.Action { text: i18n("Try again"); icon.name: "view-refresh"; onTriggered: backend.loadPlan() }]
    }
    PageMessage {
        visible: (page.plan.removals || []).length > 0
        type: Kirigami.MessageType.Error
        text: i18n("APT would have to remove packages for this (%1). Tretlager does not do that. The cause is in the log.", (page.plan.removals || []).join(", "))
    }
    PageMessage {
        visible: page.prep.result === "error"
        type: Kirigami.MessageType.Error
        text: page.prep.error
        actions: [Kirigami.Action { text: i18n("Log"); icon.name: "view-list-text"; onTriggered: logDialog.open() }]
    }
    PageMessage {
        visible: page.prep.result === "done"
        type: Kirigami.MessageType.Positive
        text: i18n("System prepared.")
    }

    FormCard.FormCard {
        visible: backend.planBusy
        FormCard.FormPlaceholderMessageDelegate {
            icon.name: "system-search"
            text: i18n("Determining the required changes…")
            explanation: i18n("APT simulates the installation without changing anything.")
        }
    }

    leftCards: [
        // --- Plan ---
        FormCard.FormHeader {
            visible: page.showPlan
            title: i18n("Changes to the system")
            trailing: Kirigami.ContextualHelpButton {
                toolTipText: i18n("Left unchanged: no 32-bit architecture, no system upgrade, no graphics drivers, nothing is removed. TUXEDO OS automatically takes a snapshot before and after the installation.")
            }
        },
        FormCard.FormCard {
            visible: page.showPlan
            FormCard.FormTextDelegate {
                visible: page.plan.add_source === true
                text: i18n("WineHQ package source")
                description: (page.plan.uri || "") + "\n" + i18n("Key %1", page.groups(page.plan.fingerprint))
                icon.name: "repository"
            }
            FormCard.FormDelegateSeparator { visible: page.plan.add_source === true }
            FormCard.FormTextDelegate {
                text: i18n("Download")
                description: i18n("%1 for %2 packages", page.mb(page.plan.download_bytes || 0), (page.plan.packages || []).length)
                icon.name: "download"
            }
        },

        // --- Fortschritt ---
        FormCard.FormHeader { visible: page.prep.running || page.prep.result !== ""; title: i18n("Progress") },
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
                text: i18n("Log…")
                icon.name: "view-list-text"
                onClicked: logDialog.open()
            }
        }
    ]

    rightCards: [
        FormCard.FormHeader { visible: page.showPlan; title: i18n("Packages") },
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
        nextText: page.done ? i18n("Next") : i18n("Apply changes…")
        nextIcon: page.done ? "go-next" : "dialog-password"
        nextVisible: page.done || !page.blocked
        nextEnabled: page.done || (!backend.planBusy && !page.prep.running
                     && (page.plan.packages || []).length + (page.plan.add_source ? 1 : 0) > 0)
        onNext: page.done ? applicationWindow().pageStack.push(Qt.resolvedUrl("ZwiftPage.qml")) : backend.runPrepare()
    }
}
