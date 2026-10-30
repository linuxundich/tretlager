import QtQuick
import QtQuick.Window
import org.kde.kirigami as Kirigami

Kirigami.ApplicationWindow {
    id: root
    title: i18n("Tretlager")
    // Seitenleiste plus Übersicht mit zwei Spalten; auf kleinen Bildschirmen höchstens 90 % der Fläche.
    width: Math.min(Kirigami.Units.gridUnit * 64, Screen.desktopAvailableWidth * 0.9)
    height: Math.min(Kirigami.Units.gridUnit * 46, Screen.desktopAvailableHeight * 0.9)
    minimumWidth: Kirigami.Units.gridUnit * 22
    minimumHeight: Kirigami.Units.gridUnit * 20
    // Immer nur eine Seite zeigen: Der Assistent ist linear (Zurück über die Kopfzeile), und
    // aus der Übersicht geöffnete Seiten wie die Anmeldung brauchen die volle Breite.
    pageStack.columnView.columnResizeMode: Kirigami.ColumnView.SingleColumn

    // Schritte des Assistenten; die Kopfzeile jeder Seite zeigt „Schritt n von 6“.
    // Im Flatpak entfällt „Vorbereiten“ (Wine ist im Paket), die Schritte zählen dann 1–5.
    readonly property var stepIds: backend.flatpak ? ["check", "zwift", "login", "sensors", "finish"]
                                                   : ["check", "prepare", "zwift", "login", "sensors", "finish"]
    readonly property var steps: stepIds

    // Assistent: linearer Ablauf mit Schrittanzeige. Bei der ersten Einrichtung ohne Seitenleiste
    // (nichts außer dem Assistenten ergibt dann Sinn); über „Einrichtung prüfen“ nach der
    // Einrichtung bleibt die Seitenleiste nutzbar, und der Assistent beginnt gleich bei Schritt 1.
    property string current: ""
    readonly property bool inWizard: current === "setup"
    readonly property bool navigation: !inWizard || backend.setupComplete
    readonly property var destinations: ({
        "overview": "MainPage.qml", "sensors": "SensorsPage.qml", "help": "HelpPage.qml",
        "about": "AboutPage.qml" })

    function show(name, props) {
        current = name
        pageStack.clear()
        const page = name === "setup" ? (backend.setupComplete ? "CheckPage.qml" : "WelcomePage.qml")
                                      : destinations[name]
        pageStack.push(Qt.resolvedUrl(page), props || {})
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
                text: i18n("Übersicht")
                icon.name: "go-home"
                checkable: true
                checked: root.current === "overview"
                onTriggered: root.show("overview")
            },
            Kirigami.Action {
                text: i18n("Sensoren")
                icon.name: "network-bluetooth"
                checkable: true
                checked: root.current === "sensors"
                onTriggered: root.show("sensors", { wizard: false })
            },
            Kirigami.Action {
                text: i18n("Hilfe")
                icon.name: "help-contents"
                checkable: true
                checked: root.current === "help"
                onTriggered: root.show("help")
            },
            Kirigami.Action { separator: true },
            Kirigami.Action {
                text: i18n("Einrichtung prüfen")
                icon.name: "tools-wizard"
                checkable: true
                checked: root.inWizard
                onTriggered: root.show("setup")
            },
            Kirigami.Action {
                text: i18n("Über Tretlager")
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
