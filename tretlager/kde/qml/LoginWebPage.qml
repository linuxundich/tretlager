import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import QtWebEngine
import org.kde.kirigami as Kirigami

// Zwift sign-in page in an embedded, private browser view, just like in the official launcher.
// The redirect back to launcher.zwift.com is intercepted before the page loads, so no error page
// appears and nothing has to be copied. Tretlager does not read the page contents.
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

    // Go back after a successful exchange; on error the page stays open with a message.
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
        // Quiet info line instead of a message box (in the accent colour that would look like an error)
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
        // Profile without storage (off the record): no cookies or history on disk.
        // WebEngineProfilePrototype (recommended since Qt 6.9) crashed with Qt 6.11 without storageName;
        // until that is fixed we keep the old type, which only writes a notice to the log.
        profile: WebEngineProfile { offTheRecord: true }
        settings.javascriptCanOpenWindows: false

        onNavigationRequested: function (request) {
            if (page.intercept(request.url)) request.reject()
        }
        // Fallback in case the redirect arrives as a redirect without a navigation request.
        onUrlChanged: if (page.intercept(url)) stop()
        // Open new windows (e.g. links in the fine print) in the user's own browser.
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
