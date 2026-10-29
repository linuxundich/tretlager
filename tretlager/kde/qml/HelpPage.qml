import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

Kirigami.ScrollablePage {
    title: "Hilfe"

    // Lesebreite nach HIG: etwa 85 Zeichen je Zeile
    PageContent {
        maximumWidth: Kirigami.Units.gridUnit * 34
        Controls.Label {
            Layout.fillWidth: true
            Layout.topMargin: Kirigami.Units.largeSpacing
            text: backend.helpText
            textFormat: Text.MarkdownText
            wrapMode: Text.WordWrap
            onLinkActivated: (link) => Qt.openUrlExternally(link)
        }
    }
}
