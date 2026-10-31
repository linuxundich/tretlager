import QtQuick
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

// Log in its own dialog: selectable, monospace font, scrolls for long runs.
Kirigami.Dialog {
    id: dialog
    property string text
    title: i18n("Log")
    preferredWidth: Kirigami.Units.gridUnit * 40
    preferredHeight: Kirigami.Units.gridUnit * 28
    standardButtons: Kirigami.Dialog.Close

    Controls.ScrollView {
        Kirigami.SelectableLabel {
            text: dialog.text
            font.family: "monospace"
            wrapMode: Text.WrapAnywhere
            textMargin: Kirigami.Units.largeSpacing
        }
    }
}
