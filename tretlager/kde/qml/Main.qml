import QtQuick
import QtQuick.Window
import org.kde.kirigami as Kirigami

Kirigami.ApplicationWindow {
    id: root
    title: i18n("Tretlager")
    // Sidebar plus two-column overview; on small screens at most 90 % of the area.
    width: Math.min(Kirigami.Units.gridUnit * 64, Screen.desktopAvailableWidth * 0.9)
    height: Math.min(Kirigami.Units.gridUnit * 46, Screen.desktopAvailableHeight * 0.9)
    minimumWidth: Kirigami.Units.gridUnit * 22
    minimumHeight: Kirigami.Units.gridUnit * 20
    // Always show only one page: the wizard is linear (Back via the header), and
    // pages opened from the overview, such as sign-in, need the full width.
    pageStack.columnView.columnResizeMode: Kirigami.ColumnView.SingleColumn

    // Wizard steps; the header of each page shows "Step n of 6".
    // The Flatpak has no "Prepare" step (Wine is bundled), so the steps count 1-5.
    readonly property var stepIds: backend.flatpak ? ["check", "zwift", "login", "sensors", "finish"]
                                                   : ["check", "prepare", "zwift", "login", "sensors", "finish"]
    readonly property var steps: stepIds

    // Wizard: linear flow with step indicator. On first setup without a sidebar
    // (nothing but the wizard makes sense then); when opened via "Check setup" after
    // setup, the sidebar stays usable and the wizard starts right at step 1.
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
                text: i18n("Overview")
                icon.name: "go-home"
                checkable: true
                checked: root.current === "overview"
                onTriggered: root.show("overview")
            },
            Kirigami.Action {
                text: i18n("Sensors")
                icon.name: "network-bluetooth"
                checkable: true
                checked: root.current === "sensors"
                onTriggered: root.show("sensors", { wizard: false })
            },
            Kirigami.Action {
                text: i18n("Help")
                icon.name: "help-contents"
                checkable: true
                checked: root.current === "help"
                onTriggered: root.show("help")
            },
            Kirigami.Action { separator: true },
            Kirigami.Action {
                text: i18n("Check setup")
                icon.name: "tools-wizard"
                checkable: true
                checked: root.inWizard
                onTriggered: root.show("setup")
            },
            Kirigami.Action {
                text: i18n("About Tretlager")
                icon.name: "help-about"
                checkable: true
                checked: root.current === "about"
                onTriggered: root.show("about")
            }
        ]
    }

    // Poll the sensors less often during a ride and while minimised. On Wayland Qt does not
    // always report minimising, so a running ride counts as well.
    readonly property bool quiet: visibility === Window.Minimized || visibility === Window.Hidden
                                  || backend.launchInfo.zwiftRunning
    onQuietChanged: backend.setWindowHidden(quiet)

    // Closing during a ride only after confirmation: in the Flatpak Zwift runs in the same instance
    // and ends with the window; also, Tretlager would otherwise not clean up after the ride.
    onClosing: function (close) {
        if (backend.launchInfo.zwiftRunning && !quitDialog.confirmed) {
            close.accepted = false
            quitDialog.open()
        }
    }
    Kirigami.PromptDialog {
        id: quitDialog
        property bool confirmed: false
        title: i18n("Zwift is still running")
        subtitle: backend.flatpak
            ? i18n("If Tretlager quits now, Zwift ends too. Best save and end the ride in Zwift first; Tretlager only minimises itself during the ride.")
            : i18n("Tretlager will then not tidy up after the ride. Best end the ride in Zwift first; Tretlager only minimises itself during the ride.")
        standardButtons: Kirigami.Dialog.Cancel
        customFooterActions: [
            Kirigami.Action {
                text: i18n("Quit anyway")
                icon.name: "application-exit"
                onTriggered: { quitDialog.confirmed = true; backend.quitNow() }
            }
        ]
    }

    // Get out of the way during the ride, come back afterwards, or quit after a direct start.
    property bool zwiftWasRunning: false
    Connections {
        target: backend
        // Second invocation (start menu): raise this window; with "start", launch Zwift right away.
        function onRemoteCommand(cmd) {
            root.showNormal()
            root.raise()
            root.requestActivate()
            if (cmd === "start" && backend.setupComplete && backend.disclaimerAccepted) backend.startZwift()
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

    // Push pages onto the stack only after construction (Kirigami pitfall learned in Stafette).
    // Show the overview right away once setup is complete, otherwise the wizard.
    Component.onCompleted: {
        show(backend.setupComplete ? "overview" : "setup")
        if (!backend.disclaimerAccepted) warningDialog.open()
    }

    // Warnings: to be confirmed on first start, later available for reference from "About Tretlager"
    WarningDialog { id: warningDialog }
    function showWarnings() { warningDialog.open() }
}
