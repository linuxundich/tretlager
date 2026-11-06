import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

// Overview for everyday use: frameless start area at the top, two columns of FormCards below
// (Sensors | Zwift). On narrow windows the columns are stacked.
ColumnsPage {
    id: page
    title: i18n("Overview")
    backdrop: true

    readonly property var la: backend.launchInfo
    readonly property var se: backend.sensors
    readonly property var incompatible: se.devices.filter(function (d) { return d.enabled && d.compat })
    readonly property string wineText: !la.wine.active ? "…"
        : la.wine.useKept ? i18n("%1, previous version (bundled: %2)", la.wine.active, la.wine.bundled)
        : la.wine.kept && la.wine.kept !== la.wine.bundled ? i18n("%1, new with Tretlager; %2 kept", la.wine.active, la.wine.kept)
        : la.wine.kept ? i18n("%1, proven and kept", la.wine.active)
        : i18n("%1, bundled with Tretlager", la.wine.active)
    readonly property bool anyUnstable: se.devices.some(function (d) { return d.unstable && !d.compat })
    // Readiness at a glance: which enabled sensors are connected?
    readonly property var activeDevices: se.devices.filter(function (d) { return d.enabled })
    readonly property var waitingDevices: activeDevices.filter(function (d) { return d.state !== "connected" })
    readonly property bool sensorsReady: se.running && waitingDevices.length === 0
    readonly property var audioOthers: se.running && waitingDevices.length > 0
                                       ? (se.otherDevices || []).filter(function (o) { return o.audio }) : []
    readonly property string readinessText: {
        if (!se.running)
            return i18n("The sensor bridge is starting …")
        if (activeDevices.length === 0)
            return i18n("No sensors set up. Zwift starts anyway; sensors can be added under Sensors.")
        if (waitingDevices.length === 0)
            return i18np("Sensor connected: %2", "All %1 sensors connected: %2", activeDevices.length,
                         activeDevices.map(function (d) { return d.name }).join(", "))
        return i18n("%1 of %2 sensors connected. Still searching: %3 – pedal briefly or put on the strap.",
                    activeDevices.length - waitingDevices.length, activeDevices.length,
                    waitingDevices.map(function (d) { return d.name }).join(", "))
    }

    Component.onCompleted: {
        backend.refreshOverview()
        backend.setSensorPolling(true)
        backend.prewarmBridge()
        if (backend.autoStart) backend.startZwift()
    }

    LogDialog { id: logDialog; text: page.la.log; title: i18n("Log of the last start") }

    // --- Messages ---
    PageMessage {
        visible: page.la.needLogin
        type: Kirigami.MessageType.Warning
        text: i18n("The Zwift session has expired. After signing in again, Zwift starts with one click again.")
        actions: [Kirigami.Action {
            text: i18n("Sign in…"); icon.name: "user-identity"
            onTriggered: applicationWindow().pageStack.push(Qt.resolvedUrl("LoginPage.qml"))
        }]
    }
    PageMessage {
        visible: page.la.error !== ""
        type: Kirigami.MessageType.Error
        text: page.la.error
        actions: [Kirigami.Action { text: i18n("Log"); icon.name: "view-list-text"; onTriggered: logDialog.open() }]
    }
    PageMessage {
        visible: page.la.gpuErrors !== "" && !page.la.zwiftRunning
        type: Kirigami.MessageType.Error
        text: (page.la.powerChanged
               ? i18n("The graphics driver reported errors during the last ride (%1). Shortly before, the power source switched between AC and battery; that is the likely cause.", page.la.gpuErrors)
               : i18n("The graphics driver reported errors during the last ride (%1).", page.la.gpuErrors))
            + " " + i18n("Restart Zwift with the power adapter connected; if it still hangs, restart the computer.")
        actions: [Kirigami.Action { text: i18n("Log"); icon.name: "view-list-text"; onTriggered: logDialog.open() }]
    }
    PageMessage {
        visible: page.la.powerChanged && page.la.gpuErrors === ""
        type: Kirigami.MessageType.Warning
        text: page.la.zwiftRunning || page.la.busy
            ? i18n("The power source changed during the start. If Zwift hangs, close it with Alt+F4 and restart it with the power adapter connected.")
            : i18n("The power source changed during the last ride. Switching between AC and battery can upset the graphics driver; best connect the power adapter before starting and keep it connected during the ride.")
    }
    PageMessage {
        visible: page.la.onBattery && !page.la.zwiftRunning && !page.la.powerChanged && page.la.gpuErrors === ""
        type: Kirigami.MessageType.Warning
        text: i18n("The computer is running on battery. Best start Zwift with the power adapter connected and keep it connected during the ride: switching between AC and battery can crash the graphics driver, and on battery the graphics card is heavily throttled.")
    }
    Repeater {
        model: page.incompatible
        delegate: PageMessage {
            required property var modelData
            visible: true
            type: Kirigami.MessageType.Warning
            text: modelData.compat
            actions: [Kirigami.Action { text: i18n("Sensors"); icon.name: "network-bluetooth"; onTriggered: applicationWindow().show("sensors", { wizard: false }) }]
        }
    }
    PageMessage {
        visible: page.audioOthers.length > 0
        type: Kirigami.MessageType.Warning
        text: i18n("%1 shares the Bluetooth adapter with the sensors and crowds them out while it plays audio. Disconnect it, or connect it through another Bluetooth adapter.",
                   page.audioOthers.map(function (o) { return o.name }).join(", "))
        actions: [Kirigami.Action { text: i18n("Sensors"); icon.name: "network-bluetooth"; onTriggered: applicationWindow().show("sensors", { wizard: false }) }]
    }
    PageMessage {
        visible: page.anyUnstable
        type: Kirigami.MessageType.Warning
        text: i18n("A sensor often loses its connection. Usually the computer is too far from the trainer.")
        actions: [Kirigami.Action { text: i18n("Sensors"); icon.name: "network-bluetooth"; onTriggered: applicationWindow().show("sensors", { wizard: false }) }]
    }

    // --- Start (frameless) ---
    PageHero {
        title: page.la.zwiftRunning ? i18n("Enjoy the ride!")
             : page.la.busy && page.la.updating ? i18n("Zwift is being updated…")
             : page.la.busy ? i18n("Zwift is starting…")
             : page.sensorsReady ? i18n("Ready to ride") : i18n("Almost ready")
        text: page.la.zwiftRunning ? i18n("Tretlager waits minimised and tidies up after the ride.")
            : page.la.busy && page.la.text !== "" ? page.la.text
            : page.readinessText
        RowLayout {
            Layout.topMargin: Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.smallSpacing
            // The one main action: larger than all other buttons and the only one highlighted.
            Controls.Button {
                id: startButton
                text: page.la.zwiftRunning ? i18n("Zwift is running") : i18n("Start Zwift")
                icon.name: "media-playback-start"
                icon.width: Kirigami.Units.iconSizes.smallMedium
                icon.height: Kirigami.Units.iconSizes.smallMedium
                // The Plasma style sizes buttons itself and ignores padding; set the size directly.
                implicitHeight: Kirigami.Units.gridUnit * 2.4
                implicitWidth: Math.max(implicitContentWidth + Kirigami.Units.gridUnit * 2, Kirigami.Units.gridUnit * 11)
                highlighted: true
                enabled: !page.la.busy && !page.la.zwiftRunning
                onClicked: backend.startZwift()
                Component.onCompleted: if (!backend.autoStart) forceActiveFocus()
            }
            Controls.BusyIndicator {
                visible: page.la.busy
                running: visible
                Layout.preferredHeight: Kirigami.Units.iconSizes.medium
                Layout.preferredWidth: Layout.preferredHeight
            }
            Kirigami.ContextualHelpButton {
                toolTipText: i18n("Before starting, Tretlager checks the sensor bridge and renews the Zwift session. After a Tretlager update it adapts the Zwift environment, and it installs a new Zwift version through the Zwift launcher. Zwift runs on the most powerful graphics card and at the screen's resolution.")
            }
        }
        // Progress of long steps (Zwift update, reinstalling), invisible otherwise
        Controls.ProgressBar {
            visible: page.la.busy && page.la.percent >= 0
            Layout.fillWidth: true
            Layout.topMargin: Kirigami.Units.smallSpacing
            from: 0
            to: 100
            value: page.la.percent
        }
        // Disclaimer right next to the main action: the bridge values are not guaranteed.
        Controls.Label {
            Layout.fillWidth: true
            Layout.topMargin: Kirigami.Units.smallSpacing
            wrapMode: Text.WordWrap
            color: Kirigami.Theme.disabledTextColor
            font: Kirigami.Theme.smallFont
            text: i18n("Not an official Zwift app, use at your own risk. Not for races: Tretlager does not guarantee that the sensor bridge passes power, cadence and heart rate to Zwift correctly.")
        }
    }

    // --- Sensors ---
    leftCards: [
        FormCard.FormHeader {
            title: i18n("Sensors")
            maximumWidth: Infinity
            trailing: Kirigami.ContextualHelpButton {
                toolTipText: i18n("Zwift cannot use Bluetooth on Linux. The sensor bridge connects to the trainer and heart rate strap and offers them to Zwift as Wahoo devices with “Direct Connect”. Select them once in Zwift under Paired Devices: “Wahoo KICKR …” for power, cadence and resistance, “Wahoo HRM …” for heart rate.")
            }
        },
        FormCard.FormCard {
            maximumWidth: Infinity
            FormCard.FormPlaceholderMessageDelegate {
                visible: !page.se.running || page.se.devices.length === 0
                icon.name: "network-bluetooth"
                text: !page.se.running ? i18n("Sensor bridge is off") : i18n("No devices set up")
                explanation: !page.se.running ? i18n("It starts with Tretlager and before every ride.")
                                               : i18n("Add the trainer and heart rate strap under Sensors.")
            }
            Repeater {
                model: page.se.running ? page.se.devices : []
                delegate: ColumnLayout {
                    required property var modelData
                    required property int index
                    Layout.fillWidth: true
                    spacing: 0
                    FormCard.FormDelegateSeparator { visible: index > 0 }
                    DeviceDelegate { device: modelData; Layout.fillWidth: true }
                }
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormButtonDelegate {
                text: i18n("Manage sensors")
                icon.name: "configure"
                onClicked: applicationWindow().show("sensors", { wizard: false })
            }
        }
    ]

    // --- Zwift ---
    rightCards: [
        FormCard.FormHeader { title: i18n("Zwift"); maximumWidth: Infinity },
        FormCard.FormCard {
            maximumWidth: Infinity
            FormCard.FormTextDelegate {
                text: i18n("Version")
                description: page.la.busy && page.la.updating && page.la.remote
                    ? i18n("Updating from %1 to %2 – Zwift starts afterwards", page.la.version || i18n("unknown"), page.la.remote)
                    : !page.la.remote ? (page.la.version || i18n("unknown"))
                    : page.la.remote === page.la.version ? i18n("%1, up to date", page.la.version)
                    : i18n("%1, update to %2 at the next start", page.la.version || i18n("unknown"), page.la.remote)
                icon.name: "update-none"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: i18n("Graphics")
                description: page.la.renderer || i18n("Not checked yet")
                icon.name: "video-display"
                trailing: Kirigami.ContextualHelpButton {
                    toolTipText: i18n("Tretlager tested the graphics path during setup. On laptops with two graphics chips, Zwift runs on the NVIDIA card while the desktop stays on the power-saving chip. The screen resolution stays unchanged.")
                }
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: i18n("Wine")
                description: page.wineText
                icon.name: "system-run"
                trailing: Kirigami.ContextualHelpButton {
                    toolTipText: i18n("Wine comes with Tretlager and is updated with Tretlager. Tretlager keeps the last proven version: if Zwift runs worse after an update, the switch below starts Zwift with it again. A new Wine counts as proven after two rides and then replaces the kept version.")
                }
            }
            FormCard.FormDelegateSeparator { visible: rollback.visible }
            FormCard.FormSwitchDelegate {
                id: rollback
                visible: page.la.wine.kept !== "" && page.la.wine.kept !== page.la.wine.bundled
                text: i18n("Use previous Wine version")
                description: i18n("%1 instead of %2. Only needed if Zwift has not run properly since the last Tretlager update.",
                                  page.la.wine.kept, page.la.wine.bundled)
                checked: page.la.wine.useKept
                enabled: !page.la.busy && !page.la.zwiftRunning
                onToggled: backend.setUseKeptWine(checked)
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormSwitchDelegate {
                text: i18n("Keep screen on during the ride")
                description: i18n("The screen does not dim, switch off or lock while Zwift runs, even during a break.")
                icon.name: "system-suspend-inhibited"
                checked: backend.keepScreenOn
                onToggled: backend.setKeepScreenOn(checked)
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: i18n("Sign-in")
                description: page.la.login || "…"
                icon.name: "user-identity"
                trailing: Kirigami.ContextualHelpButton {
                    toolTipText: i18n("The official sign-in does not work on Linux, so it runs through a separate sign-in window. This contradicts Zwift's terms of service. The session is only stored in this computer's keyring.")
                }
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormButtonDelegate {
                text: i18n("Sign in again…")
                icon.name: "view-refresh"
                onClicked: applicationWindow().pageStack.push(Qt.resolvedUrl("LoginPage.qml"))
            }
            FormCard.FormDelegateSeparator { visible: page.la.log !== "" }
            FormCard.FormButtonDelegate {
                visible: page.la.log !== ""
                text: i18n("Log of the last start…")
                icon.name: "view-list-text"
                onClicked: logDialog.open()
            }
        }
    ]
}
