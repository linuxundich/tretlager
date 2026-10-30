import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

// Meldung oben auf einer Seite, so breit wie der Inhalt.
Kirigami.InlineMessage {
    Layout.fillWidth: true
    Layout.bottomMargin: Kirigami.Units.largeSpacing
}
