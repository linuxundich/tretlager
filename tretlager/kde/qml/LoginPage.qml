import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

Kirigami.ScrollablePage {
    id: page
    title: "Anmeldung"

    readonly property var li: backend.loginInfo
    readonly property bool signedIn: li.state === "valid" || li.state === "refreshable"

    function hours(s) { return Math.round(s / 3600) }
    function days(s) { return Math.round(s / 86400) }

    Component.onCompleted: backend.loadLogin()

    header: Controls.Label {
        text: "Schritt 4 von " + applicationWindow().steps.length + " · dein Passwort gibst du nur bei Zwift im Browser ein"
        padding: Kirigami.Units.largeSpacing
        color: Kirigami.Theme.disabledTextColor
        wrapMode: Text.WordWrap
    }

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: page.signedIn
            type: Kirigami.MessageType.Positive
            text: "Angemeldet. Die Sitzung erneuert Tretlager selbst, noch " + page.days(page.li.refresh_left)
                  + " Tage lang; danach meldest du dich wieder im Browser an."
            actions: [Kirigami.Action { text: "Abmelden"; icon.name: "system-log-out"; onTriggered: backend.logout() }]
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: page.li.error !== ""
            type: Kirigami.MessageType.Error
            text: page.li.error
        }

        // Weg 1: offiziell – derzeit nicht möglich
        Kirigami.AbstractCard {
            Layout.fillWidth: true
            visible: !page.signedIn
            contentItem: ColumnLayout {
                spacing: Kirigami.Units.smallSpacing
                RowLayout {
                    Kirigami.Icon { source: "data-error"; Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium; Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium }
                    Kirigami.Heading { text: "Offizielle Anmeldung"; level: 3; Layout.fillWidth: true }
                }
                Controls.Label {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: "Funktioniert unter Linux derzeit nicht: Der Zwift-Launcher nutzt seit Version 1.2 eine Windows-Funktion, die Wine noch fehlt. Tretlager prüft nach jedem Launcher-Update, ob sie wieder geht."
                }
            }
        }

        // Weg 2: Browser – mit Zustimmung
        Kirigami.AbstractCard {
            Layout.fillWidth: true
            visible: !page.signedIn
            contentItem: ColumnLayout {
                spacing: Kirigami.Units.largeSpacing
                RowLayout {
                    Kirigami.Icon { source: "internet-web-browser"; Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium; Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium }
                    Kirigami.Heading { text: "Anmeldung über den Browser"; level: 3; Layout.fillWidth: true }
                }
                Controls.Label {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: "Du meldest dich auf der Zwift-Seite in deinem Browser an. Tretlager übernimmt danach die Sitzung und legt sie in deinem Schlüsselbund ab."
                }
                Kirigami.InlineMessage {
                    Layout.fillWidth: true
                    visible: true
                    type: Kirigami.MessageType.Warning
                    text: "Zwift erlaubt keine fremden Programme an seiner Anmeldung (Nutzungsbedingungen, Abschnitt 5). Du nutzt diesen Weg auf eigenes Risiko."
                }
                Controls.CheckBox {
                    id: consent
                    text: "Verstanden, ich nutze diesen Weg auf eigenes Risiko"
                    checked: page.li.consent
                    enabled: !page.li.consent
                    onToggled: if (checked) backend.giveConsent()
                }
                Controls.Button {
                    text: page.li.waiting ? "Anmeldeseite erneut öffnen" : "Im Browser anmelden"
                    icon.name: "internet-web-browser"
                    highlighted: !page.li.waiting
                    enabled: page.li.consent && !page.li.busy
                    onClicked: backend.startBrowserLogin()
                }

                ColumnLayout {
                    visible: page.li.waiting
                    Layout.fillWidth: true
                    spacing: Kirigami.Units.smallSpacing
                    Kirigami.Separator { Layout.fillWidth: true }
                    Controls.Label {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        text: "1. Melde dich im Browser bei Zwift an.\n"
                              + "2. Danach zeigt die Seite „Bad Request“ – das ist normal.\n"
                              + "3. Kopiere die Adresse aus der Adresszeile (Strg+L, dann Strg+C) und komm hierher zurück. Tretlager übernimmt sie von selbst."
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Controls.TextField {
                            id: redirect
                            Layout.fillWidth: true
                            placeholderText: "https://launcher.zwift.com/launcher?…&code=…"
                            onAccepted: backend.submitRedirect(text)
                        }
                        Controls.Button {
                            text: "Übernehmen"
                            enabled: redirect.text.length > 0 && !page.li.busy
                            onClicked: backend.submitRedirect(redirect.text)
                        }
                    }
                    Controls.BusyIndicator {
                        visible: page.li.busy
                        running: visible
                        Layout.alignment: Qt.AlignHCenter
                    }
                }
            }
        }
    }

    footer: Controls.ToolBar {
        contentItem: RowLayout {
            Item { Layout.fillWidth: true }
            Controls.Button {
                text: "Weiter"
                icon.name: "go-next"
                highlighted: true
                enabled: page.signedIn
                onClicked: applicationWindow().pageStack.push(Qt.resolvedUrl("SensorsPage.qml"))
            }
        }
    }
}
