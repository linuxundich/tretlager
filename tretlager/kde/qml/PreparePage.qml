import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

// Platzhalter bis M2: Hier kommt die Liste der Systemänderungen mit einer Polkit-Abfrage hin.
Kirigami.Page {
    title: "System vorbereiten"

    Kirigami.PlaceholderMessage {
        anchors.centerIn: parent
        width: parent.width - Kirigami.Units.gridUnit * 4
        icon.name: "run-build"
        text: "Noch nicht umgesetzt"
        explanation: "Dieser Schritt folgt in Meilenstein M2: WineHQ-Paketquelle und Pakete mit einer einzigen Passwortabfrage. Bisher ändert Tretlager nichts am System."
    }
}
