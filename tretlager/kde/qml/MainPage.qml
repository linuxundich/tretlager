import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

// Übersicht für den Alltag: oben rahmenlos der Start, darunter zwei Spalten mit FormCards
// (Sensoren | Zwift). Auf schmalen Fenstern stehen die Spalten untereinander.
ColumnsPage {
    id: page
    title: i18n("Übersicht")

    readonly property var la: backend.launchInfo
    readonly property var se: backend.sensors
    readonly property var incompatible: se.devices.filter(function (d) { return d.enabled && d.compat })
    readonly property bool anyUnstable: se.devices.some(function (d) { return d.unstable && !d.compat })
    // Startbereitschaft auf einen Blick: Welche eingeschalteten Sensoren sind verbunden?
    readonly property var activeDevices: se.devices.filter(function (d) { return d.enabled })
    readonly property var waitingDevices: activeDevices.filter(function (d) { return d.state !== "verbunden" })
    readonly property bool sensorsReady: se.running && waitingDevices.length === 0
    readonly property string readinessText: {
        if (!se.running)
            return i18n("Die Sensor-Bridge startet …")
        if (activeDevices.length === 0)
            return i18n("Keine Sensoren eingerichtet. Zwift startet trotzdem; Sensoren lassen sich unter Sensoren hinzufügen.")
        if (waitingDevices.length === 0)
            return i18np("Sensor verbunden: %2", "Alle %1 Sensoren verbunden: %2", activeDevices.length,
                         activeDevices.map(function (d) { return d.name }).join(", "))
        return i18n("%1 von %2 Sensoren verbunden. Noch gesucht: %3 – kurz in die Pedale treten bzw. den Gurt anlegen.",
                    activeDevices.length - waitingDevices.length, activeDevices.length,
                    waitingDevices.map(function (d) { return d.name }).join(", "))
    }

    Component.onCompleted: {
        backend.refreshOverview()
        backend.setSensorPolling(true)
        backend.prewarmBridge()
        if (backend.autoStart) backend.startZwift()
    }

    LogDialog { id: logDialog; text: page.la.log; title: i18n("Protokoll des letzten Starts") }

    // --- Meldungen ---
    PageMessage {
        visible: page.la.needLogin
        type: Kirigami.MessageType.Warning
        text: i18n("Die Zwift-Sitzung ist abgelaufen. Nach einer neuen Anmeldung im Browser startet Zwift wieder mit einem Klick.")
        actions: [Kirigami.Action {
            text: i18n("Anmelden …"); icon.name: "user-identity"
            onTriggered: applicationWindow().pageStack.push(Qt.resolvedUrl("LoginPage.qml"))
        }]
    }
    PageMessage {
        visible: page.la.error !== ""
        type: Kirigami.MessageType.Error
        text: page.la.error
        actions: [Kirigami.Action { text: i18n("Protokoll"); icon.name: "view-list-text"; onTriggered: logDialog.open() }]
    }
    PageMessage {
        visible: page.la.gpuErrors !== "" && !page.la.zwiftRunning
        type: Kirigami.MessageType.Error
        text: (page.la.powerChanged
               ? i18n("Der Grafiktreiber hat bei der letzten Fahrt Fehler gemeldet (%1). Kurz davor wechselte die Stromversorgung zwischen Netz und Akku; das ist die wahrscheinliche Ursache.", page.la.gpuErrors)
               : i18n("Der Grafiktreiber hat bei der letzten Fahrt Fehler gemeldet (%1).", page.la.gpuErrors))
            + " " + i18n("Zwift mit angeschlossenem Netzteil neu starten; hängt es weiter, den Rechner neu starten.")
        actions: [Kirigami.Action { text: i18n("Protokoll"); icon.name: "view-list-text"; onTriggered: logDialog.open() }]
    }
    PageMessage {
        visible: page.la.powerChanged && page.la.gpuErrors === ""
        type: Kirigami.MessageType.Warning
        text: page.la.zwiftRunning || page.la.busy
            ? i18n("Die Stromversorgung hat während des Starts gewechselt. Hängt Zwift, Zwift mit Alt+F4 beenden und mit angeschlossenem Netzteil neu starten.")
            : i18n("Die Stromversorgung hat während der letzten Fahrt gewechselt. Ein Wechsel zwischen Netz und Akku kann den Grafiktreiber stören; das Netzteil am besten vor dem Start anschließen und während der Fahrt angeschlossen lassen.")
    }
    PageMessage {
        visible: page.la.onBattery && !page.la.zwiftRunning && !page.la.powerChanged && page.la.gpuErrors === ""
        type: Kirigami.MessageType.Warning
        text: i18n("Der Rechner läuft auf Akku. Zwift am besten mit angeschlossenem Netzteil starten und es während der Fahrt angeschlossen lassen: Ein Wechsel zwischen Netz und Akku kann den Grafiktreiber zum Absturz bringen, und auf Akku drosselt die Grafikkarte stark.")
    }
    Repeater {
        model: page.incompatible
        delegate: PageMessage {
            required property var modelData
            visible: true
            type: Kirigami.MessageType.Warning
            text: modelData.compat
            actions: [Kirigami.Action { text: i18n("Sensoren"); icon.name: "network-bluetooth"; onTriggered: applicationWindow().show("sensors", { wizard: false }) }]
        }
    }
    PageMessage {
        visible: page.anyUnstable
        type: Kirigami.MessageType.Warning
        text: i18n("Ein Sensor verliert oft die Verbindung. Meist steht der Rechner zu weit vom Trainer entfernt.")
        actions: [Kirigami.Action { text: i18n("Sensoren"); icon.name: "network-bluetooth"; onTriggered: applicationWindow().show("sensors", { wizard: false }) }]
    }

    // --- Start (rahmenlos) ---
    PageHero {
        title: page.la.zwiftRunning ? i18n("Gute Fahrt!") : page.la.busy ? i18n("Zwift startet …")
             : page.sensorsReady ? i18n("Bereit zum Fahren") : i18n("Fast bereit")
        text: page.la.zwiftRunning ? i18n("Tretlager wartet minimiert und räumt nach der Fahrt auf.")
            : page.la.busy && page.la.text !== "" ? page.la.text
            : page.readinessText
        RowLayout {
            Layout.topMargin: Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.smallSpacing
            // Die eine Hauptaktion: größer als alle anderen Knöpfe und als einziger hervorgehoben.
            Controls.Button {
                id: startButton
                text: page.la.zwiftRunning ? i18n("Zwift läuft") : i18n("Zwift starten")
                icon.name: "media-playback-start"
                icon.width: Kirigami.Units.iconSizes.smallMedium
                icon.height: Kirigami.Units.iconSizes.smallMedium
                // Der Plasma-Stil misst Knöpfe selbst und übergeht Polsterwerte; Größe direkt setzen.
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
                toolTipText: i18n("Vor dem Start prüft Tretlager die Sensor-Bridge und erneuert die Zwift-Sitzung. Gibt es eine neue Zwift-Version, sichert Tretlager die alte und spielt das Update ein. Zwift läuft auf der leistungsstärksten Grafikkarte und in der Auflösung des Bildschirms.")
            }
        }
        // Haftungshinweis direkt an der Hauptaktion: Die Werte der Bridge sind nicht abgesichert.
        Controls.Label {
            Layout.fillWidth: true
            Layout.topMargin: Kirigami.Units.smallSpacing
            wrapMode: Text.WordWrap
            color: Kirigami.Theme.disabledTextColor
            font: Kirigami.Theme.smallFont
            text: i18n("Nicht für Rennen: Tretlager garantiert nicht, dass die Sensor-Bridge Leistung, Trittfrequenz und Puls korrekt an Zwift weitergibt.")
        }
    }

    // --- Sensoren ---
    leftCards: [
        FormCard.FormHeader {
            title: i18n("Sensoren")
            maximumWidth: Infinity
            trailing: Kirigami.ContextualHelpButton {
                toolTipText: i18n("Zwift kann unter Linux kein Bluetooth nutzen. Die Sensor-Bridge verbindet sich mit Trainer und Pulsgurt und bietet sie Zwift als Wahoo-Geräte mit „Direct Connect“ an. In Zwift einmalig unter Gekoppelte Geräte auswählen: „Wahoo KICKR …“ für Leistung, Trittfrequenz und Widerstand, „Wahoo HRM …“ für den Puls.")
            }
        },
        FormCard.FormCard {
            maximumWidth: Infinity
            FormCard.FormPlaceholderMessageDelegate {
                visible: !page.se.running || page.se.devices.length === 0
                icon.name: "network-bluetooth"
                text: !page.se.running ? i18n("Sensor-Bridge ist aus") : i18n("Keine Geräte eingerichtet")
                explanation: !page.se.running ? i18n("Sie startet mit Tretlager und vor jeder Fahrt.")
                                               : i18n("Trainer und Pulsgurt unter Sensoren hinzufügen.")
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
                text: i18n("Sensoren verwalten")
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
                description: !page.la.remote ? (page.la.version || i18n("unbekannt"))
                    : page.la.remote === page.la.version ? i18n("%1, aktuell", page.la.version)
                    : i18n("%1, Update auf %2 beim nächsten Start", page.la.version || i18n("unbekannt"), page.la.remote)
                icon.name: "update-none"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: i18n("Grafik")
                description: page.la.renderer || i18n("Noch nicht geprüft")
                icon.name: "video-display"
                trailing: Kirigami.ContextualHelpButton {
                    toolTipText: i18n("Den Grafikweg hat Tretlager bei der Einrichtung getestet. Auf Notebooks mit zwei Grafikchips läuft Zwift auf der NVIDIA-Karte, der Desktop bleibt auf dem sparsamen Chip. Die Bildschirmauflösung bleibt unverändert.")
                }
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: i18n("Anmeldung")
                description: page.la.login || "…"
                icon.name: "user-identity"
                trailing: Kirigami.ContextualHelpButton {
                    toolTipText: i18n("Die offizielle Anmeldung funktioniert unter Linux nicht, deshalb läuft sie über ein eigenes Anmeldefenster. Das widerspricht den Zwift-Nutzungsbedingungen. Die Sitzung liegt nur im Schlüsselbund dieses Rechners.")
                }
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormButtonDelegate {
                text: i18n("Neu anmelden …")
                icon.name: "view-refresh"
                onClicked: applicationWindow().pageStack.push(Qt.resolvedUrl("LoginPage.qml"))
            }
            FormCard.FormDelegateSeparator { visible: page.la.log !== "" }
            FormCard.FormButtonDelegate {
                visible: page.la.log !== ""
                text: i18n("Protokoll des letzten Starts …")
                icon.name: "view-list-text"
                onClicked: logDialog.open()
            }
        }
    ]
}
