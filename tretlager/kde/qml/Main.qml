import QtQuick
import QtQuick.Window
import org.kde.kirigami as Kirigami

Kirigami.ApplicationWindow {
    id: root
    title: "Tretlager"
    // Seitenleiste plus Übersicht mit zwei Spalten; auf kleinen Bildschirmen höchstens 90 % der Fläche.
    width: Math.min(Kirigami.Units.gridUnit * 64, Screen.desktopAvailableWidth * 0.9)
    height: Math.min(Kirigami.Units.gridUnit * 46, Screen.desktopAvailableHeight * 0.9)
    minimumWidth: Kirigami.Units.gridUnit * 22
    minimumHeight: Kirigami.Units.gridUnit * 20
    // Immer nur eine Seite zeigen: Der Assistent ist linear (Zurück über die Kopfzeile), und
    // aus der Übersicht geöffnete Seiten wie die Anmeldung brauchen die volle Breite.
    pageStack.columnView.columnResizeMode: Kirigami.ColumnView.SingleColumn

    // Schritte des Assistenten; die Kopfzeile jeder Seite zeigt „Schritt n von 6“.
    readonly property var steps: ["Prüfen", "Vorbereiten", "Zwift", "Anmeldung", "Sensoren", "Fertig"]

    // Seitenleiste erst nach der Einrichtung; der Assistent ist ein linearer Ablauf ohne Sprünge.
    property bool navigation: false
    property string current: ""
    readonly property var destinations: ({
        "overview": "MainPage.qml", "sensors": "SensorsPage.qml", "help": "HelpPage.qml",
        "about": "AboutPage.qml", "setup": "WelcomePage.qml" })

    function show(name, props) {
        current = name
        navigation = name !== "setup"
        pageStack.clear()
        pageStack.push(Qt.resolvedUrl(destinations[name]), props || {})
    }

    globalDrawer: Kirigami.GlobalDrawer {
        id: drawer
        enabled: root.navigation
        modal: !root.wideScreen || !root.navigation
        drawerOpen: root.navigation && root.wideScreen
        handleVisible: root.navigation && modal
        width: Kirigami.Units.gridUnit * 11

        actions: [
            Kirigami.Action {
                text: "Übersicht"
                icon.name: "go-home"
                checkable: true
                checked: root.current === "overview"
                onTriggered: root.show("overview")
            },
            Kirigami.Action {
                text: "Sensoren"
                icon.name: "network-bluetooth"
                checkable: true
                checked: root.current === "sensors"
                onTriggered: root.show("sensors", { wizard: false })
            },
            Kirigami.Action {
                text: "Hilfe"
                icon.name: "help-contents"
                checkable: true
                checked: root.current === "help"
                onTriggered: root.show("help")
            },
            Kirigami.Action { separator: true },
            Kirigami.Action {
                text: "Einrichtung prüfen"
                icon.name: "tools-wizard"
                onTriggered: root.show("setup")
            },
            Kirigami.Action {
                text: "Über Tretlager"
                icon.name: "help-about"
                checkable: true
                checked: root.current === "about"
                onTriggered: root.show("about")
            }
        ]
    }

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
    // Nach abgeschlossener Einrichtung gleich die Übersicht, sonst der Assistent.
    Component.onCompleted: show(backend.setupComplete ? "overview" : "setup")
}
