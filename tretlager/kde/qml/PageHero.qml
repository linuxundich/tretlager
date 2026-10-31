import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

// Frameless page header as on the overview: large icon on the left, heading and sentence on the right,
// optionally followed by buttons (children of this element).
RowLayout {
    id: hero
    property string iconName: "de.linuxundich.Tretlager"
    property string title
    property string text
    default property alias extra: extraColumn.data

    Layout.alignment: Qt.AlignHCenter
    Layout.maximumWidth: Kirigami.Units.gridUnit * 40
    Layout.topMargin: Kirigami.Units.gridUnit
    Layout.bottomMargin: Kirigami.Units.gridUnit
    spacing: Kirigami.Units.gridUnit * 1.5

    Kirigami.Icon {
        source: hero.iconName
        fallback: hero.iconName === "de.linuxundich.Tretlager"
                  ? Qt.resolvedUrl("../../data/icons/de.linuxundich.Tretlager.svg") : ""
        Layout.preferredWidth: Kirigami.Units.iconSizes.enormous
        Layout.preferredHeight: Kirigami.Units.iconSizes.enormous
    }
    ColumnLayout {
        id: extraColumn
        Layout.fillWidth: true
        spacing: Kirigami.Units.smallSpacing
        Kirigami.Heading { level: 1; text: hero.title; Layout.fillWidth: true; wrapMode: Text.WordWrap }
        Controls.Label {
            Layout.fillWidth: true
            visible: text !== ""
            wrapMode: Text.WordWrap
            color: Kirigami.Theme.disabledTextColor
            text: hero.text
        }
    }
}
