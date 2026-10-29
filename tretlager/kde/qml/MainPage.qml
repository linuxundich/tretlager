import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

// Übersicht für den Alltag: großer Startbereich, darunter Karten zu Sensoren, Zwift, Grafik,
// Anmeldung und Hilfe. Für PC-Bildschirme gedacht; auf schmalen Fenstern stapeln sich die Karten.
Kirigami.ScrollablePage {
    id: page
    title: "Tretlager"

    readonly property var la: backend.launchInfo
    readonly property var se: backend.sensors
    readonly property bool anyUnstable: se.devices.some(function (d) { return d.unstable })
    readonly property var stateText: ({ "verbunden": "verbunden", "verbinde": "verbindet …", "getrennt": "getrennt",
        "fehler": "nicht erreichbar", "aus": "ausgeschaltet" })
    readonly property string iconDir: Qt.resolvedUrl("../../ui/icons/hicolor/scalable/actions/")

    function stateColor(st) {
        return st === "verbunden" ? Kirigami.Theme.positiveTextColor
             : st === "verbinde" ? Kirigami.Theme.neutralTextColor
             : st === "fehler" ? Kirigami.Theme.negativeTextColor
             : Kirigami.Theme.disabledTextColor
    }
    function values(v) {
        var parts = []
        if (v.power !== undefined) parts.push(v.power + " W")
        if (v.cadence !== undefined) parts.push(Math.round(v.cadence) + " U/min")
        if (v.heart_rate !== undefined) parts.push(v.heart_rate + " bpm")
        return parts.join("  ·  ")
    }
    function openSensors() {
        applicationWindow().pageStack.push(Qt.resolvedUrl("SensorsPage.qml"), { wizard: false })
    }

    Component.onCompleted: {
        backend.refreshOverview()
        backend.setSensorPolling(true)
        backend.prewarmBridge()
        if (backend.autoStart) backend.startZwift()
    }

    actions: [
        Kirigami.Action {
            text: "Sensoren verwalten"
            icon.name: "network-bluetooth"
            onTriggered: page.openSensors()
        },
        Kirigami.Action {
            text: "Hilfe"
            icon.name: "help-contents"
            onTriggered: applicationWindow().pageStack.push(Qt.resolvedUrl("HelpPage.qml"))
        },
        Kirigami.Action {
            text: "Einrichtung prüfen"
            icon.name: "tools-wizard"
            displayHint: Kirigami.DisplayHint.AlwaysHide
            onTriggered: applicationWindow().pageStack.push(Qt.resolvedUrl("WelcomePage.qml"))
        }
    ]

    PageContent {
        maximumWidth: Kirigami.Units.gridUnit * 72

        // --- Warnungen ---
        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: page.la.needLogin
            type: Kirigami.MessageType.Warning
            text: "Die Zwift-Sitzung ist abgelaufen. Melde dich einmal im Browser neu an, danach startet Zwift wieder mit einem Klick."
            actions: [Kirigami.Action {
                text: "Anmelden"; icon.name: "user-identity"
                onTriggered: applicationWindow().pageStack.push(Qt.resolvedUrl("LoginPage.qml"))
            }]
        }
        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: page.la.error !== ""
            type: Kirigami.MessageType.Error
            text: page.la.error
        }
        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: page.anyUnstable
            type: Kirigami.MessageType.Warning
            text: "Ein Sensor verliert oft die Verbindung. Meist steht der Rechner zu weit vom Trainer entfernt."
            actions: [Kirigami.Action { text: "Details"; icon.name: "network-bluetooth"; onTriggered: page.openSensors() }]
        }

        // --- Startbereich ---
        Kirigami.AbstractCard {
            Layout.fillWidth: true
            contentItem: RowLayout {
                spacing: Kirigami.Units.gridUnit * 2

                Kirigami.Icon {
                    source: Qt.resolvedUrl("../../data/icons/de.linuxundich.Tretlager.svg")
                    Layout.preferredWidth: Kirigami.Units.iconSizes.enormous * 1.5
                    Layout.preferredHeight: Kirigami.Units.iconSizes.enormous * 1.5
                    Layout.alignment: Qt.AlignVCenter
                    Layout.margins: Kirigami.Units.largeSpacing
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: Kirigami.Units.largeSpacing

                    Kirigami.Heading {
                        level: 1
                        text: page.la.zwiftRunning ? "Gute Fahrt!" : page.la.busy ? "Zwift startet …" : "Bereit zum Fahren"
                    }
                    Controls.Label {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        text: page.la.zwiftRunning
                              ? "Zwift läuft. Tretlager wartet in der Taskleiste und räumt nach der Fahrt auf."
                              : "Ein Klick erledigt alles: Tretlager prüft die Sensor-Bridge, erneuert die Anmeldung, "
                                + "spielt ein Zwift-Update ein (vorher mit Sicherung) und startet Zwift auf der Grafikkarte."
                    }
                    RowLayout {
                        spacing: Kirigami.Units.largeSpacing
                        Controls.Button {
                            text: page.la.zwiftRunning ? "Zwift läuft" : (page.la.busy ? "Startet …" : "Zwift starten")
                            icon.name: "media-playback-start"
                            highlighted: true
                            enabled: !page.la.busy && !page.la.zwiftRunning
                            font.pointSize: Kirigami.Theme.defaultFont.pointSize * 1.3
                            Layout.preferredWidth: Kirigami.Units.gridUnit * 14
                            Layout.preferredHeight: Kirigami.Units.gridUnit * 2.8
                            onClicked: backend.startZwift()
                        }
                        Controls.BusyIndicator { visible: page.la.busy; running: visible }
                        Controls.Label {
                            visible: page.la.text !== ""
                            text: page.la.text
                            color: Kirigami.Theme.disabledTextColor
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                        }
                    }
                }
            }
        }

        // --- Karten: zwei gleich breite Spalten, auf schmalen Fenstern eine ---
        GridLayout {
            Layout.fillWidth: true
            columns: width > Kirigami.Units.gridUnit * 44 ? 2 : 1
            columnSpacing: Kirigami.Units.largeSpacing * 2
            rowSpacing: Kirigami.Units.largeSpacing * 2

            SectionCard {
                title: "Sensoren"
                iconName: "network-bluetooth"
                Controls.Label {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: !page.se.running ? "Die Sensor-Bridge ist aus. Sie startet beim Öffnen von Tretlager und mit Zwift."
                        : page.se.devices.length === 0 ? "Noch keine Geräte eingerichtet."
                        : "Die Bridge hält diese Geräte und reicht sie an Zwift weiter:"
                }
                Repeater {
                    model: page.se.devices
                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: Kirigami.Units.largeSpacing
                        Kirigami.Icon {
                            source: modelData.role === "heartrate" ? page.iconDir + "tretlager-heartrate-symbolic.svg"
                                                                   : page.iconDir + "tretlager-trainer-symbolic.svg"
                            isMask: true
                            Layout.preferredWidth: Kirigami.Units.iconSizes.medium
                            Layout.preferredHeight: Kirigami.Units.iconSizes.medium
                        }
                        ColumnLayout {
                            spacing: 0
                            Layout.fillWidth: true
                            Controls.Label { text: modelData.name; font.bold: true; elide: Text.ElideRight; Layout.fillWidth: true }
                            RowLayout {
                                Rectangle {
                                    width: Kirigami.Units.smallSpacing * 2; height: width; radius: width / 2
                                    color: page.stateColor(modelData.state)
                                }
                                Controls.Label {
                                    text: (page.stateText[modelData.state] || modelData.state)
                                          + (modelData.state === "verbunden" && modelData.zwift_clients > 0 ? " · in Zwift" : "")
                                    color: Kirigami.Theme.disabledTextColor
                                }
                            }
                        }
                        Controls.Label {
                            text: page.values(modelData.values || {})
                            font.pointSize: Kirigami.Theme.defaultFont.pointSize * 1.3
                        }
                    }
                }
                buttons: [Controls.Button { text: "Sensoren verwalten"; icon.name: "configure"; flat: true; onClicked: page.openSensors() }]
            }

            SectionCard {
                title: "Zwift"
                iconName: "media-playback-start"
                GridLayout {
                    columns: 2
                    columnSpacing: Kirigami.Units.largeSpacing
                    Layout.fillWidth: true
                    Controls.Label { text: "Installiert:"; color: Kirigami.Theme.disabledTextColor }
                    Controls.Label { text: page.la.version || "unbekannt"; Layout.fillWidth: true }
                    Controls.Label { text: "Aktuell bei Zwift:"; color: Kirigami.Theme.disabledTextColor }
                    Controls.Label {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        text: !page.la.remote ? "wird geprüft …"
                            : page.la.remote === page.la.version ? page.la.remote + " – auf dem neuesten Stand"
                            : page.la.remote + " – wird beim nächsten Start eingespielt"
                    }
                }
                Hint {
                    text: "Sensoren koppelst du einmalig in Zwift unter <i>Gekoppelte Geräte</i>: „Wahoo KICKR …“ für Leistung, Trittfrequenz und Widerstand, „Wahoo HRM …“ für den Puls."
                }
            }

            SectionCard {
                title: "Grafik"
                iconName: "video-display"
                Controls.Label {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: page.la.renderer ? "Zwift rendert auf: <b>" + page.la.renderer + "</b>" : "Grafik noch nicht geprüft."
                    textFormat: Text.StyledText
                }
                Hint {
                    text: "Den Grafikweg hat Tretlager bei der Einrichtung selbst getestet. Auf Notebooks mit zwei Grafikchips läuft Zwift auf der NVIDIA-Karte, der Desktop bleibt auf dem sparsamen Chip. Die Bildschirmauflösung stellt Zwift nicht um."
                }
            }

            SectionCard {
                title: "Anmeldung"
                iconName: "user-identity"
                Controls.Label { Layout.fillWidth: true; wrapMode: Text.WordWrap; text: "Zwift-Sitzung: " + (page.la.login || "…") }
                Hint {
                    icon: "dialog-warning"
                    text: "Die Anmeldung läuft über den Browser, weil die offizielle Anmeldung unter Linux nicht funktioniert. Das widerspricht den Zwift-Nutzungsbedingungen; die Sitzung liegt nur in deinem Schlüsselbund."
                }
                buttons: [Controls.Button {
                    text: "Neu anmelden"; icon.name: "view-refresh"; flat: true
                    onClicked: applicationWindow().pageStack.push(Qt.resolvedUrl("LoginPage.qml"))
                }]
            }

            SectionCard {
                title: "Hilfe und Wartung"
                iconName: "help-contents"
                Layout.columnSpan: parent.columns
                Controls.Label {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: "Die Hilfe erklärt Einrichtung, Alltag und typische Probleme. „Einrichtung prüfen“ geht alle Schritte erneut durch; Erledigtes wird nur kontrolliert, nicht wiederholt."
                }
                buttons: [
                    Controls.Button { text: "Hilfe öffnen"; icon.name: "help-contents"; flat: true
                        onClicked: applicationWindow().pageStack.push(Qt.resolvedUrl("HelpPage.qml")) },
                    Controls.Button { text: "Einrichtung prüfen"; icon.name: "tools-wizard"; flat: true
                        onClicked: applicationWindow().pageStack.push(Qt.resolvedUrl("WelcomePage.qml")) }
                ]
            }
        }

        // --- Protokoll ---
        Controls.Button {
            text: logArea.visible ? "Protokoll ausblenden" : "Protokoll des letzten Starts zeigen"
            icon.name: "view-list-text"
            flat: true
            visible: page.la.log !== ""
            onClicked: logArea.visible = !logArea.visible
        }
        Controls.TextArea {
            id: logArea
            visible: false
            readOnly: true
            text: page.la.log
            font.family: "monospace"
            wrapMode: Text.WrapAnywhere
            Layout.fillWidth: true
            Layout.preferredHeight: Kirigami.Units.gridUnit * 12
        }
    }
}
