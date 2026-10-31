import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

// Warnhinweise beim ersten Start (und erneut, wenn sich ihr Text ändert: DISCLAIMER_VERSION in
// app.py). Ohne Bestätigung geht es nicht weiter; „Beenden“ schließt Tretlager. Später erreichbar
// unter „Über Tretlager“.
Kirigami.Dialog {
    id: dialog
    // Beim ersten Start muss bestätigt werden; aus „Über Tretlager“ geöffnet genügt Schließen.
    property bool mustConfirm: !backend.disclaimerAccepted

    title: i18n("Before you start")
    preferredWidth: Kirigami.Units.gridUnit * 32
    modal: true
    showCloseButton: !mustConfirm
    closePolicy: mustConfirm ? Controls.Popup.NoAutoClose : Controls.Popup.CloseOnEscape | Controls.Popup.CloseOnPressOutside

    readonly property var points: [
        [i18n("Not an official Zwift app"),
         i18n("Tretlager is a private project. Zwift does not support Linux and has nothing to do with Tretlager; report problems to Tretlager, not to Zwift.")],
        [i18n("At your own risk"),
         i18n("Zwift may not be happy that a software bridge sends data to Zwift that could be manipulated. Restrictions up to a suspended account cannot be ruled out – including the XP and drops earned with so much sweat.")],
        [i18n("Not for races"),
         i18n("Tretlager does not guarantee that the sensor bridge passes power, cadence and heart rate to Zwift correctly. Do not use Tretlager for races or competitions with results.")],
        [i18n("Sign-in outside the launcher"),
         i18n("The official sign-in does not work on Linux. Tretlager's own sign-in window contradicts Zwift's terms of service.")]
    ]

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing
        // Lesebreite: Lange Texte würden den Dialog sonst auf Fensterbreite ziehen
        Layout.preferredWidth: Kirigami.Units.gridUnit * 30
        Layout.maximumWidth: Kirigami.Units.gridUnit * 30

        RowLayout {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.gridUnit

            // Stilisiertes Steigungsschild als Warnzeichen
            Image {
                source: Qt.resolvedUrl("../../data/icons/tretlager-warning.svg")
                sourceSize.width: Kirigami.Units.iconSizes.huge
                sourceSize.height: Kirigami.Units.iconSizes.huge
                Layout.alignment: Qt.AlignTop
                Accessible.name: i18n("Warning sign")
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: Kirigami.Units.largeSpacing

                Repeater {
                    model: dialog.points
                    delegate: ColumnLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: 0
                        Kirigami.Heading {
                            level: 4
                            text: modelData[0]
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                        }
                        Controls.Label {
                            text: modelData[1]
                            Layout.fillWidth: true
                            Layout.preferredWidth: Kirigami.Units.gridUnit * 24
                            wrapMode: Text.WordWrap
                        }
                    }
                }
            }
        }
    }

    standardButtons: mustConfirm ? Kirigami.Dialog.NoButton : Kirigami.Dialog.Close
    customFooterActions: [
        Kirigami.Action {
            visible: dialog.mustConfirm
            text: i18n("Quit")
            icon.name: "application-exit"
            onTriggered: Qt.quit()
        },
        Kirigami.Action {
            visible: dialog.mustConfirm
            text: i18n("Understood, at my own risk")
            icon.name: "dialog-ok-apply"
            onTriggered: {
                backend.acceptDisclaimer()
                dialog.close()
            }
        }
    ]
}
