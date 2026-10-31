import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

ColumnsPage {
    id: page
    title: i18n("Set up Zwift")

    readonly property var st: backend.zwiftSetup
    readonly property var stepIcon: ({
        "pending": "chronometer", "running": "media-playback-start",
        "done": "data-success", "skipped": "data-success", "error": "data-error"
    })

    Component.onCompleted: if (!st.running && st.result !== "done") backend.runSetup()

    header: WizardHeader { stepId: "zwift"; text: i18n("Runs by itself, about ten minutes.") }

    LogDialog { id: logDialog; text: page.st.log }

    PageMessage {
        visible: page.st.result === "error"
        type: Kirigami.MessageType.Error
        text: i18n("%1 Steps already completed are kept.", page.st.error)
        actions: [
            Kirigami.Action { text: i18n("Try again"); icon.name: "view-refresh"; onTriggered: backend.runSetup() },
            Kirigami.Action { text: i18n("Log"); icon.name: "view-list-text"; onTriggered: logDialog.open() }
        ]
    }
    PageMessage {
        visible: page.st.result === "done"
        type: Kirigami.MessageType.Positive
        text: i18n("Zwift is set up.")
    }

    FormCard.FormHeader {
        title: i18n("Steps")
        trailing: Kirigami.ContextualHelpButton {
            toolTipText: i18n("You may close the window; at the next start Tretlager continues where it left off. The Microsoft components (.NET, WebView2, fonts) are subject to Microsoft's license terms.")
        }
    }
    FormCard.FormCard {
        Repeater {
            model: page.st.steps
            delegate: FormCard.AbstractFormDelegate {
                id: stepRow
                required property var modelData
                readonly property bool active: modelData.status === "running"
                hoverEnabled: false
                focusPolicy: Qt.NoFocus

                contentItem: ColumnLayout {
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
                            text: i18n("already done")
                            color: Kirigami.Theme.disabledTextColor
                        }
                    }
                    Controls.ProgressBar {
                        visible: stepRow.active
                        Layout.fillWidth: true
                        Layout.leftMargin: Kirigami.Units.iconSizes.smallMedium + Kirigami.Units.largeSpacing
                        from: 0; to: 100
                        value: page.st.current === stepRow.modelData.id ? page.st.percent : 0
                        indeterminate: visible && page.st.percent <= 0
                    }
                    Controls.Label {
                        visible: stepRow.active && page.st.text !== ""
                        text: page.st.text
                        color: Kirigami.Theme.disabledTextColor
                        font: Kirigami.Theme.smallFont
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                        Layout.leftMargin: Kirigami.Units.iconSizes.smallMedium + Kirigami.Units.largeSpacing
                    }
                }
            }
        }
        FormCard.FormDelegateSeparator { visible: page.st.log !== "" }
        FormCard.FormButtonDelegate {
            visible: page.st.log !== ""
            text: i18n("Log…")
            icon.name: "view-list-text"
            onClicked: logDialog.open()
        }
    }

    footer: WizardFooter {
        skipText: page.st.running ? i18n("Cancel") : ""
        onSkip: backend.cancelSetup()
        nextEnabled: page.st.result === "done"
        onNext: applicationWindow().pageStack.push(Qt.resolvedUrl("LoginPage.qml"))
    }
}
