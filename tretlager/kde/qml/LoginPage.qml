import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

// Platzhalter bis M4: offizielle Anmeldung (derzeit nicht möglich) und Browser-Anmeldung mit Hinweis.
Kirigami.Page {
    title: "Anmeldung"

    Kirigami.PlaceholderMessage {
        anchors.centerIn: parent
        width: parent.width - Kirigami.Units.gridUnit * 4
        icon.name: "user-identity"
        text: "Noch nicht umgesetzt"
        explanation: "Dieser Schritt folgt in Meilenstein M4."
    }
}
