import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

// Message at the top of a page, as wide as the content.
Kirigami.InlineMessage {
    Layout.fillWidth: true
    Layout.bottomMargin: Kirigami.Units.largeSpacing
}
