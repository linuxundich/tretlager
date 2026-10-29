import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

// Inhalt einer Seite, mittig und auf eine lesbare Breite begrenzt (auf breiten PC-Bildschirmen
// laufen Texte sonst über die ganze Fensterbreite).
Item {
    id: holder
    default property alias content: column.data
    property real maximumWidth: Kirigami.Units.gridUnit * 46
    property alias spacing: column.spacing

    implicitHeight: column.implicitHeight + Kirigami.Units.largeSpacing * 2

    ColumnLayout {
        id: column
        width: Math.min(holder.width, holder.maximumWidth)
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: Kirigami.Units.largeSpacing
        spacing: Kirigami.Units.largeSpacing
    }
}
