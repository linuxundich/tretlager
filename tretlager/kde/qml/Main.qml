import QtQuick
import org.kde.kirigami as Kirigami

Kirigami.ApplicationWindow {
    id: root
    title: "Tretlager"
    width: Kirigami.Units.gridUnit * 36
    height: Kirigami.Units.gridUnit * 40
    minimumWidth: Kirigami.Units.gridUnit * 22

    // Schritte des Assistenten; die Kopfzeile jeder Seite zeigt „Schritt n von 6“.
    readonly property var steps: ["Prüfen", "Vorbereiten", "Zwift", "Anmeldung", "Sensoren", "Fertig"]

    // Seiten erst nach dem Aufbau auf den Stapel legen (Kirigami-Falle aus Stafette).
    // Nach abgeschlossener Einrichtung gleich das Hauptfenster, sonst der Assistent.
    Component.onCompleted: pageStack.push(Qt.resolvedUrl(backend.setupComplete ? "MainPage.qml" : "WelcomePage.qml"))
}
