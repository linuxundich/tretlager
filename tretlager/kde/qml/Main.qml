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

    // Während der Fahrt aus dem Weg gehen, danach zurückkommen bzw. beim Direktstart beenden.
    property bool zwiftWasRunning: false
    Connections {
        target: backend
        // Zweiter Aufruf (Startmenü): dieses Fenster nach vorn, bei „start“ gleich Zwift starten.
        function onRemoteCommand(cmd) {
            root.showNormal()
            root.raise()
            root.requestActivate()
            if (cmd === "start" && backend.setupComplete) backend.startZwift()
        }
        function onLaunchChanged() {
            const running = backend.launchInfo.zwiftRunning
            if (running && !root.zwiftWasRunning) {
                root.showMinimized()
            } else if (!running && root.zwiftWasRunning) {
                if (backend.autoStart) {
                    Qt.quit()
                } else {
                    root.showNormal()
                    root.raise()
                    root.requestActivate()
                }
            }
            root.zwiftWasRunning = running
        }
    }

    // Seiten erst nach dem Aufbau auf den Stapel legen (Kirigami-Falle aus Stafette).
    // Nach abgeschlossener Einrichtung gleich das Hauptfenster, sonst der Assistent.
    Component.onCompleted: pageStack.push(Qt.resolvedUrl(backend.setupComplete ? "MainPage.qml" : "WelcomePage.qml"))
}
