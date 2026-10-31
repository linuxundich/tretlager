import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import QtWebEngine
import org.kde.kirigami as Kirigami

// Zwift-Anmeldeseite in einem eingebetteten, privaten Browserfenster – so wie im offiziellen Launcher.
// Der Rücksprung auf launcher.zwift.com wird abgefangen, bevor die Seite lädt; damit erscheint
// keine Fehlerseite, und nichts muss kopiert werden. Tretlager liest die Seite nicht aus.
Kirigami.Page {
    id: page
    title: i18n("Sign in to Zwift")
    padding: 0

    readonly property string redirectPrefix: "https://launcher.zwift.com/launcher"
    readonly property var li: backend.loginInfo
    property bool handedOver: false

    function intercept(url) {
        const u = url.toString()
        if (!u.startsWith(page.redirectPrefix)) return false
        if (!page.handedOver) {
            page.handedOver = true
            backend.submitRedirect(u)
        }
        return true
    }

    // Nach erfolgreichem Tausch zurück; bei einem Fehler bleibt die Seite mit Meldung stehen.
    Connections {
        target: backend
        function onLoginChanged() {
            if (!page.handedOver || page.li.busy || page.li.error !== "") return
            if (page.li.state === "valid" || page.li.state === "refreshable") {
                applicationWindow().pageStack.pop()
            }
        }
    }

    header: ColumnLayout {
        spacing: 0
        // Ruhige Infozeile statt Meldungskasten (der würde in der Akzentfarbe wie ein Fehler wirken)
        Controls.Control {
            Layout.fillWidth: true
            padding: Kirigami.Units.largeSpacing
            background: Rectangle { color: Kirigami.Theme.backgroundColor }
            contentItem: RowLayout {
                spacing: Kirigami.Units.largeSpacing
                Kirigami.Icon {
                    source: "security-high"
                    Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                    Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
                }
                Controls.Label {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    color: Kirigami.Theme.disabledTextColor
                    text: i18n("Zwift's sign-in page in a private window: it stores nothing and forgets what you entered when closed. Tretlager only takes over the session afterwards.")
                }
            }
        }
        Kirigami.Separator { Layout.fillWidth: true }
        Kirigami.InlineMessage {
            Layout.fillWidth: true
            position: Kirigami.InlineMessage.Position.Header
            visible: page.li.error !== ""
            type: Kirigami.MessageType.Error
            text: page.li.error
            actions: [Kirigami.Action {
                text: i18n("Try again")
                icon.name: "view-refresh"
                onTriggered: { page.handedOver = false; web.url = backend.startEmbeddedLogin() }
            }]
        }
        Controls.ProgressBar {
            Layout.fillWidth: true
            visible: web.loading || page.li.busy
            indeterminate: visible
        }
    }

    WebEngineView {
        id: web
        anchors.fill: parent
        visible: !page.handedOver || page.li.error !== ""
        // Profil ohne Speicherort (off the record): keine Cookies oder Verläufe auf der Platte.
        // WebEngineProfilePrototype (ab Qt 6.9 empfohlen) stürzte mit Qt 6.11 ohne storageName ab;
        // bis dahin bleibt es beim alten Typ, der nur einen Hinweis ins Protokoll schreibt.
        profile: WebEngineProfile { offTheRecord: true }
        settings.javascriptCanOpenWindows: false

        onNavigationRequested: function (request) {
            if (page.intercept(request.url)) request.reject()
        }
        // Rückfall, falls der Rücksprung als Weiterleitung ohne Navigationsanfrage kommt.
        onUrlChanged: if (page.intercept(url)) stop()
        // Neue Fenster (z. B. Links im Kleingedruckten) im eigenen Browser öffnen.
        onNewWindowRequested: function (request) { Qt.openUrlExternally(request.requestedUrl) }

        Component.onCompleted: url = backend.startEmbeddedLogin()
    }

    Kirigami.PlaceholderMessage {
        anchors.centerIn: parent
        width: parent.width - Kirigami.Units.gridUnit * 4
        visible: page.handedOver && page.li.error === ""
        icon.name: "user-identity"
        text: i18n("Taking over the sign-in…")
    }
}
