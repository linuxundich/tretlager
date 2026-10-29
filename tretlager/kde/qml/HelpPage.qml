import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

Kirigami.ScrollablePage {
    title: "Hilfe"

    Controls.Label {
        text: backend.helpText
        textFormat: Text.MarkdownText
        wrapMode: Text.WordWrap
        onLinkActivated: (link) => Qt.openUrlExternally(link)
    }
}
