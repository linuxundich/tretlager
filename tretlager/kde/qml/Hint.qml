import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

// Ruhiger Hinweis: Symbol plus Text in gedämpfter Farbe. Für Erklärungen und Tipps, nicht für
// Warnungen (die bleiben Kirigami.InlineMessage).
RowLayout {
    property alias text: label.text
    property string icon: ""  // leer = neutrales Info-Symbol in Textfarbe

    Layout.fillWidth: true
    spacing: Kirigami.Units.largeSpacing

    Kirigami.Icon {
        source: parent.icon || "help-about-symbolic"
        isMask: !parent.icon
        color: Kirigami.Theme.disabledTextColor
        Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
        Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
        Layout.alignment: Qt.AlignTop
    }
    Controls.Label {
        id: label
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        color: Kirigami.Theme.disabledTextColor
        textFormat: Text.StyledText
    }
}
