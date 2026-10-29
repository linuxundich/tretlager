import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

FormCard.FormCardPage {
    id: page
    title: "Zwift einrichten"

    readonly property var st: backend.zwiftSetup
    readonly property var stepIcon: ({
        "pending": "chronometer", "running": "media-playback-start",
        "done": "data-success", "skipped": "data-success", "error": "data-error"
    })

    Component.onCompleted: if (!st.running && st.result !== "done") backend.runSetup()

    header: WizardHeader { step: 3; text: "Läuft von selbst, etwa zehn Minuten." }

    LogDialog { id: logDialog; text: page.st.log }

    Kirigami.InlineMessage {
        Layout.fillWidth: true
        Layout.maximumWidth: Kirigami.Units.gridUnit * 30
        Layout.alignment: Qt.AlignHCenter
        Layout.topMargin: Kirigami.Units.largeSpacing
        visible: page.st.result === "error"
        type: Kirigami.MessageType.Error
        text: page.st.error + " Bereits Erledigtes bleibt erhalten."
        actions: [
            Kirigami.Action { text: "Erneut versuchen"; icon.name: "view-refresh"; onTriggered: backend.runSetup() },
            Kirigami.Action { text: "Protokoll"; icon.name: "view-list-text"; onTriggered: logDialog.open() }
        ]
    }
    Kirigami.InlineMessage {
        Layout.fillWidth: true
        Layout.maximumWidth: Kirigami.Units.gridUnit * 30
        Layout.alignment: Qt.AlignHCenter
        Layout.topMargin: Kirigami.Units.largeSpacing
        visible: page.st.result === "done"
        type: Kirigami.MessageType.Positive
        text: "Zwift ist eingerichtet."
    }

    FormCard.FormHeader {
        title: "Schritte"
        trailing: Kirigami.ContextualHelpButton {
            toolTipText: "Das Fenster darf geschlossen werden; beim nächsten Start macht Tretlager an derselben "
                + "Stelle weiter. Die Komponenten von Microsoft (.NET, WebView2, Schriften) unterliegen den "
                + "Lizenzbedingungen von Microsoft."
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
            text: "Protokoll …"
            icon.name: "view-list-text"
            onClicked: logDialog.open()
        }
    }

    Item { implicitHeight: Kirigami.Units.gridUnit }

    footer: WizardFooter {
        skipText: page.st.running ? "Abbrechen" : ""
        onSkip: backend.cancelSetup()
        nextEnabled: page.st.result === "done"
        onNext: applicationWindow().pageStack.push(Qt.resolvedUrl("LoginPage.qml"))
    }
}
