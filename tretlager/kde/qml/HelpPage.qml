import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

Kirigami.ScrollablePage {
    title: "Hilfe"

    PageContent {
        maximumWidth: Kirigami.Units.gridUnit * 50
        Controls.Label {
            Layout.fillWidth: true
            text: backend.helpText
            textFormat: Text.MarkdownText
            wrapMode: Text.WordWrap
            onLinkActivated: (link) => Qt.openUrlExternally(link)
        }
    }
}
