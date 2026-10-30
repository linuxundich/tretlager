import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

// Übersicht für den Alltag: oben rahmenlos der Start, darunter zwei Spalten mit FormCards
// (Sensoren | Zwift). Auf schmalen Fenstern stehen die Spalten untereinander.
ColumnsPage {
    id: page
    title: "Übersicht"

    readonly property var la: backend.launchInfo
    readonly property var se: backend.sensors
    readonly property var incompatible: se.devices.filter(function (d) { return d.enabled && d.compat })
    readonly property bool anyUnstable: se.devices.some(function (d) { return d.unstable && !d.compat })

    Component.onCompleted: {
        backend.refreshOverview()
        backend.setSensorPolling(true)
        backend.prewarmBridge()
        if (backend.autoStart) backend.startZwift()
    }

    LogDialog { id: logDialog; text: page.la.log; title: "Protokoll des letzten Starts" }

    // --- Meldungen ---
    PageMessage {
        visible: page.la.needLogin
        type: Kirigami.MessageType.Warning
        text: "Die Zwift-Sitzung ist abgelaufen. Nach einer neuen Anmeldung im Browser startet Zwift wieder mit einem Klick."
        actions: [Kirigami.Action {
            text: "Anmelden …"; icon.name: "user-identity"
            onTriggered: applicationWindow().pageStack.push(Qt.resolvedUrl("LoginPage.qml"))
        }]
    }
    PageMessage {
        visible: page.la.error !== ""
        type: Kirigami.MessageType.Error
        text: page.la.error
        actions: [Kirigami.Action { text: "Protokoll"; icon.name: "view-list-text"; onTriggered: logDialog.open() }]
    }
    PageMessage {
        visible: page.la.gpuErrors !== "" && !page.la.zwiftRunning
        type: Kirigami.MessageType.Error
        text: "Der Grafiktreiber hat bei der letzten Fahrt Fehler gemeldet (" + page.la.gpuErrors + "). "
            + (page.la.powerChanged ? "Kurz davor wechselte die Stromversorgung zwischen Netz und Akku; das ist die "
                                      + "wahrscheinliche Ursache. " : "")
            + "Zwift mit angeschlossenem Netzteil neu starten; hängt es weiter, den Rechner neu starten."
        actions: [Kirigami.Action { text: "Protokoll"; icon.name: "view-list-text"; onTriggered: logDialog.open() }]
    }
    PageMessage {
        visible: page.la.powerChanged && page.la.gpuErrors === ""
        type: Kirigami.MessageType.Warning
        text: page.la.zwiftRunning || page.la.busy
            ? "Die Stromversorgung hat während des Starts gewechselt. Hängt Zwift, Zwift mit Alt+F4 beenden und mit angeschlossenem Netzteil neu starten."
            : "Die Stromversorgung hat während der letzten Fahrt gewechselt. Ein Wechsel zwischen Netz und Akku kann den Grafiktreiber stören; das Netzteil am besten vor dem Start anschließen und während der Fahrt angeschlossen lassen."
    }
    PageMessage {
        visible: page.la.onBattery && !page.la.zwiftRunning && !page.la.powerChanged && page.la.gpuErrors === ""
        type: Kirigami.MessageType.Warning
        text: "Der Rechner läuft auf Akku. Zwift am besten mit angeschlossenem Netzteil starten und es während der "
            + "Fahrt angeschlossen lassen: Ein Wechsel zwischen Netz und Akku kann den Grafiktreiber zum Absturz "
            + "bringen, und auf Akku drosselt die Grafikkarte stark."
    }
    Repeater {
        model: page.incompatible
        delegate: PageMessage {
            required property var modelData
            visible: true
            type: Kirigami.MessageType.Warning
            text: modelData.compat
            actions: [Kirigami.Action { text: "Sensoren"; icon.name: "network-bluetooth"; onTriggered: applicationWindow().show("sensors", { wizard: false }) }]
        }
    }
    PageMessage {
        visible: page.anyUnstable
        type: Kirigami.MessageType.Warning
        text: "Ein Sensor verliert oft die Verbindung. Meist steht der Rechner zu weit vom Trainer entfernt."
        actions: [Kirigami.Action { text: "Sensoren"; icon.name: "network-bluetooth"; onTriggered: applicationWindow().show("sensors", { wizard: false }) }]
    }

    // --- Start (rahmenlos) ---
    PageHero {
        title: page.la.zwiftRunning ? "Gute Fahrt!" : page.la.busy ? "Zwift startet …" : "Bereit zum Fahren"
        text: page.la.zwiftRunning ? "Tretlager wartet minimiert und räumt nach der Fahrt auf."
            : page.la.busy && page.la.text !== "" ? page.la.text
            : "Ein Klick prüft Sensoren und Anmeldung, spielt Updates ein und startet Zwift."
        RowLayout {
            Layout.topMargin: Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.smallSpacing
            Controls.Button {
                text: page.la.zwiftRunning ? "Zwift läuft" : "Zwift starten"
                icon.name: "media-playback-start"
                highlighted: true
                enabled: !page.la.busy && !page.la.zwiftRunning
                onClicked: backend.startZwift()
            }
            Controls.BusyIndicator {
                visible: page.la.busy
                running: visible
                Layout.preferredHeight: Kirigami.Units.iconSizes.medium
                Layout.preferredWidth: Layout.preferredHeight
            }
            Kirigami.ContextualHelpButton {
                toolTipText: "Vor dem Start prüft Tretlager die Sensor-Bridge und erneuert die Zwift-Sitzung. "
                    + "Gibt es eine neue Zwift-Version, sichert Tretlager die alte und spielt das Update ein. "
                    + "Zwift läuft auf der leistungsstärksten Grafikkarte und in der Auflösung des Bildschirms."
            }
        }
    }

    // --- Sensoren ---
    leftCards: [
        FormCard.FormHeader {
            title: "Sensoren"
            maximumWidth: Infinity
            trailing: Kirigami.ContextualHelpButton {
                toolTipText: "Zwift kann unter Linux kein Bluetooth nutzen. Die Sensor-Bridge verbindet sich mit "
                    + "Trainer und Pulsgurt und bietet sie Zwift als Wahoo-Geräte mit „Direct Connect“ an. "
                    + "In Zwift einmalig unter Gekoppelte Geräte auswählen: „Wahoo KICKR …“ für Leistung, "
                    + "Trittfrequenz und Widerstand, „Wahoo HRM …“ für den Puls."
            }
        },
        FormCard.FormCard {
            maximumWidth: Infinity
            FormCard.FormPlaceholderMessageDelegate {
                visible: !page.se.running || page.se.devices.length === 0
                icon.name: "network-bluetooth"
                text: !page.se.running ? "Sensor-Bridge ist aus" : "Keine Geräte eingerichtet"
                explanation: !page.se.running ? "Sie startet mit Tretlager und vor jeder Fahrt."
                                               : "Trainer und Pulsgurt unter Sensoren hinzufügen."
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
                text: "Sensoren verwalten"
                icon.name: "configure"
                onClicked: applicationWindow().show("sensors", { wizard: false })
            }
        }
    ]

    // --- Zwift ---
    rightCards: [
        FormCard.FormHeader { title: "Zwift"; maximumWidth: Infinity },
        FormCard.FormCard {
            maximumWidth: Infinity
            FormCard.FormTextDelegate {
                text: "Version"
                description: (page.la.version || "unbekannt")
                    + (!page.la.remote ? "" : page.la.remote === page.la.version ? ", aktuell"
                       : ", Update auf " + page.la.remote + " beim nächsten Start")
                icon.name: "update-none"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: "Grafik"
                description: page.la.renderer || "Noch nicht geprüft"
                icon.name: "video-display"
                trailing: Kirigami.ContextualHelpButton {
                    toolTipText: "Den Grafikweg hat Tretlager bei der Einrichtung getestet. Auf Notebooks mit "
                        + "zwei Grafikchips läuft Zwift auf der NVIDIA-Karte, der Desktop bleibt auf dem "
                        + "sparsamen Chip. Die Bildschirmauflösung bleibt unverändert."
                }
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: "Anmeldung"
                description: page.la.login || "…"
                icon.name: "user-identity"
                trailing: Kirigami.ContextualHelpButton {
                    toolTipText: "Die offizielle Anmeldung funktioniert unter Linux nicht, deshalb läuft sie über "
                        + "den Browser. Das widerspricht den Zwift-Nutzungsbedingungen. Die Sitzung liegt nur "
                        + "im Schlüsselbund dieses Rechners."
                }
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormButtonDelegate {
                text: "Neu anmelden …"
                icon.name: "view-refresh"
                onClicked: applicationWindow().pageStack.push(Qt.resolvedUrl("LoginPage.qml"))
            }
            FormCard.FormDelegateSeparator { visible: page.la.log !== "" }
            FormCard.FormButtonDelegate {
                visible: page.la.log !== ""
                text: "Protokoll des letzten Starts …"
                icon.name: "view-list-text"
                onClicked: logDialog.open()
            }
        }
    ]
}
