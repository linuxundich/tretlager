import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

Kirigami.ScrollablePage {
    id: page
    title: "Tretlager"

    readonly property var la: backend.launchInfo
    readonly property var se: backend.sensors

    function values(v) {
        var parts = []
        if (v.power !== undefined) parts.push(v.power + " W")
        if (v.heart_rate !== undefined) parts.push(v.heart_rate + " bpm")
        return parts.join(" · ")
    }

    Component.onCompleted: { backend.refreshOverview(); backend.setSensorPolling(true) }

    actions: [
        Kirigami.Action {
            text: "Sensoren"
            icon.name: "network-bluetooth"
            onTriggered: applicationWindow().pageStack.push(Qt.resolvedUrl("SensorsPage.qml"), { wizard: false })
        },
        Kirigami.Action {
            text: "Einrichtung prüfen"
            icon.name: "tools-wizard"
            displayHint: Kirigami.DisplayHint.AlwaysHide
            onTriggered: applicationWindow().pageStack.push(Qt.resolvedUrl("WelcomePage.qml"))
        },
        Kirigami.Action {
            text: "Neu anmelden"
            icon.name: "user-identity"
            displayHint: Kirigami.DisplayHint.AlwaysHide
            onTriggered: applicationWindow().pageStack.push(Qt.resolvedUrl("LoginPage.qml"))
        }
    ]

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.Heading {
            text: page.la.zwiftRunning ? "Gute Fahrt!" : "Bereit zum Fahren"
            level: 1
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: Kirigami.Units.gridUnit * 2
        }

        Controls.Button {
            text: page.la.zwiftRunning ? "Zwift läuft" : (page.la.busy ? "Startet …" : "Zwift starten")
            icon.name: "media-playback-start"
            highlighted: true
            enabled: !page.la.busy && !page.la.zwiftRunning
            font.pointSize: Kirigami.Theme.defaultFont.pointSize * 1.4
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: Kirigami.Units.gridUnit * 16
            Layout.preferredHeight: Kirigami.Units.gridUnit * 3
            onClicked: backend.startZwift()
        }

        Controls.Label {
            text: page.la.text
            visible: text !== ""
            color: Kirigami.Theme.disabledTextColor
            Layout.alignment: Qt.AlignHCenter
        }
        Controls.BusyIndicator { visible: page.la.busy; running: visible; Layout.alignment: Qt.AlignHCenter }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: page.la.needLogin
            type: Kirigami.MessageType.Warning
            text: "Die Zwift-Sitzung ist abgelaufen. Bitte im Browser neu anmelden."
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

        Kirigami.Separator { Layout.fillWidth: true; Layout.topMargin: Kirigami.Units.largeSpacing }

        Kirigami.FormLayout {
            Layout.fillWidth: true
            Controls.Label {
                Kirigami.FormData.label: "Sensoren:"
                text: !page.se.running ? "Bridge aus (startet mit Zwift)"
                    : page.se.devices.length === 0 ? "keine Geräte eingerichtet"
                    : page.se.devices.map(function (d) {
                          var v = page.values(d.values || {})
                          return d.name + (d.state === "verbunden" ? " ●" : " ○") + (v ? " " + v : "")
                      }).join("\n")
            }
            Controls.Label {
                Kirigami.FormData.label: "Zwift:"
                text: (page.la.version || "unbekannt") + (page.la.remote && page.la.remote !== page.la.version
                      ? " · Update auf " + page.la.remote + " beim nächsten Start" : "")
            }
            Controls.Label { Kirigami.FormData.label: "Grafik:"; text: page.la.renderer || "nicht geprüft" }
            Controls.Label { Kirigami.FormData.label: "Anmeldung:"; text: page.la.login || "…"; wrapMode: Text.WordWrap }
        }

        Controls.Button {
            text: logArea.visible ? "Protokoll ausblenden" : "Protokoll zeigen"
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
            Layout.preferredHeight: Kirigami.Units.gridUnit * 10
        }
    }
}
