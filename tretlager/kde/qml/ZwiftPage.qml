import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

ColumnsPage {
    id: page
    title: i18n("Zwift einrichten")

    readonly property var st: backend.zwiftSetup
    readonly property var stepIcon: ({
        "pending": "chronometer", "running": "media-playback-start",
        "done": "data-success", "skipped": "data-success", "error": "data-error"
    })

    Component.onCompleted: if (!st.running && st.result !== "done") backend.runSetup()

    header: WizardHeader { step: 3; text: i18n("Läuft von selbst, etwa zehn Minuten.") }

    LogDialog { id: logDialog; text: page.st.log }

    PageMessage {
        visible: page.st.result === "error"
        type: Kirigami.MessageType.Error
        text: i18n("%1 Bereits Erledigtes bleibt erhalten.", page.st.error)
        actions: [
            Kirigami.Action { text: i18n("Erneut versuchen"); icon.name: "view-refresh"; onTriggered: backend.runSetup() },
            Kirigami.Action { text: i18n("Protokoll"); icon.name: "view-list-text"; onTriggered: logDialog.open() }
        ]
    }
    PageMessage {
        visible: page.st.result === "done"
        type: Kirigami.MessageType.Positive
        text: i18n("Zwift ist eingerichtet.")
    }

    FormCard.FormHeader {
        title: i18n("Schritte")
        trailing: Kirigami.ContextualHelpButton {
            toolTipText: i18n("Das Fenster darf geschlossen werden; beim nächsten Start macht Tretlager an derselben Stelle weiter. Die Komponenten von Microsoft (.NET, WebView2, Schriften) unterliegen den Lizenzbedingungen von Microsoft.")
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
                            text: i18n("schon erledigt")
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
            text: i18n("Protokoll …")
            icon.name: "view-list-text"
            onClicked: logDialog.open()
        }
    }

    footer: WizardFooter {
        skipText: page.st.running ? i18n("Abbrechen") : ""
        onSkip: backend.cancelSetup()
        nextEnabled: page.st.result === "done"
        onNext: applicationWindow().pageStack.push(Qt.resolvedUrl("LoginPage.qml"))
    }
}
