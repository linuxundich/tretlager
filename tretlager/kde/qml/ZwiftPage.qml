import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

// Platzhalter bis M3: Installer laden und prüfen, Wine-Umgebung, Komponenten, Launcher, Spiel, Grafik.
Kirigami.Page {
    title: "Zwift einrichten"

    Kirigami.PlaceholderMessage {
        anchors.centerIn: parent
        width: parent.width - Kirigami.Units.gridUnit * 4
        icon.name: "run-build"
        text: "Noch nicht umgesetzt"
        explanation: "Dieser Schritt folgt in Meilenstein M3."
    }
}
