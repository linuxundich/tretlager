import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

// Platzhalter bis M5: Sensor-Bridge einrichten, Trainer und Pulsgurt übernehmen, Live-Werte.
Kirigami.Page {
    title: "Sensoren"

    Kirigami.PlaceholderMessage {
        anchors.centerIn: parent
        width: parent.width - Kirigami.Units.gridUnit * 4
        icon.name: "network-bluetooth"
        text: "Noch nicht umgesetzt"
        explanation: "Dieser Schritt folgt in Meilenstein M5. Bis dahin verwaltest du Sensoren in der GTK-Oberfläche der Bridge."
    }
}
