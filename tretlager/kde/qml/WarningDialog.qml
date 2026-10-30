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

    title: i18n("Bevor es losgeht")
    preferredWidth: Kirigami.Units.gridUnit * 32
    modal: true
    showCloseButton: !mustConfirm
    closePolicy: mustConfirm ? Controls.Popup.NoAutoClose : Controls.Popup.CloseOnEscape | Controls.Popup.CloseOnPressOutside

    readonly property var points: [
        [i18n("Keine offizielle Zwift-App"),
         i18n("Tretlager ist ein privates Projekt. Zwift unterstützt Linux nicht und hat mit Tretlager nichts zu tun; Probleme an Tretlager melden, nicht an Zwift.")],
        [i18n("Auf eigene Gefahr"),
         i18n("Zwift ist womöglich nicht glücklich darüber, dass eine Software-Bridge Daten an Zwift übermittelt, die sich manipulieren ließen. Einschränkungen bis hin zur Sperre des Kontos lassen sich nicht ausschließen – samt der mühsam erstrampelten XP und Drops.")],
        [i18n("Nicht für Rennen"),
         i18n("Tretlager garantiert nicht, dass die Sensor-Bridge Leistung, Trittfrequenz und Puls korrekt an Zwift weitergibt. An Rennen und Wettbewerben mit Wertung daher nicht mit Tretlager teilnehmen.")],
        [i18n("Anmeldung außerhalb des Launchers"),
         i18n("Die offizielle Anmeldung funktioniert unter Linux nicht. Das eigene Anmeldefenster widerspricht den Zwift-Nutzungsbedingungen.")]
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
                Accessible.name: i18n("Warnzeichen")
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
            text: i18n("Beenden")
            icon.name: "application-exit"
            onTriggered: Qt.quit()
        },
        Kirigami.Action {
            visible: dialog.mustConfirm
            text: i18n("Verstanden, auf eigene Gefahr")
            icon.name: "dialog-ok-apply"
            onTriggered: {
                backend.acceptDisclaimer()
                dialog.close()
            }
        }
    ]
}
