import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

// Schritt 4 des Assistenten; aus der Übersicht auch zum erneuten Anmelden (ohne Schrittanzeige).
FormCard.FormCardPage {
    id: page
    title: "Anmeldung"

    readonly property var li: backend.loginInfo
    readonly property bool signedIn: li.state === "valid" || li.state === "refreshable"
    readonly property bool wizard: !applicationWindow().navigation

    function days(s) { return Math.round(s / 86400) }

    Component.onCompleted: backend.loadLogin()

    header: WizardHeader {
        visible: page.wizard
        step: 4
        text: "Das Passwort wird nur bei Zwift im Browser eingegeben."
    }

    component Message: Kirigami.InlineMessage {
        Layout.fillWidth: true
        Layout.maximumWidth: Kirigami.Units.gridUnit * 30
        Layout.alignment: Qt.AlignHCenter
        Layout.topMargin: Kirigami.Units.largeSpacing
    }

    Message {
        visible: page.signedIn
        type: Kirigami.MessageType.Positive
        text: "Angemeldet. Tretlager erneuert die Sitzung noch " + page.days(page.li.refresh_left)
              + " Tage lang selbst, danach ist eine neue Anmeldung im Browser nötig."
        actions: [Kirigami.Action { text: "Abmelden"; icon.name: "system-log-out"; onTriggered: backend.logout() }]
    }
    Message {
        visible: page.li.error !== ""
        type: Kirigami.MessageType.Error
        text: page.li.error
    }

    // --- Offiziell: derzeit nicht möglich ---
    FormCard.FormHeader { visible: !page.signedIn; title: "Offizielle Anmeldung" }
    FormCard.FormCard {
        visible: !page.signedIn
        FormCard.FormTextDelegate {
            text: "Derzeit nicht möglich"
            description: "Der Zwift Launcher nutzt seit Version 1.2 eine Windows-Funktion, die Wine noch fehlt. "
                + "Tretlager prüft nach jedem Launcher-Update, ob sie wieder funktioniert."
            icon.name: "data-error"
        }
    }

    // --- Browser: mit Zustimmung ---
    FormCard.FormHeader { visible: !page.signedIn; title: "Anmeldung über den Browser" }
    FormCard.FormCard {
        visible: !page.signedIn
        FormCard.FormTextDelegate {
            text: "So funktioniert es"
            description: "Die Anmeldung erfolgt auf der Zwift-Seite im Browser. Tretlager übernimmt danach die "
                + "Sitzung und legt sie im Schlüsselbund ab."
            icon.name: "internet-web-browser"
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormTextDelegate {
            text: "Nicht von Zwift erlaubt"
            description: "Zwift erlaubt keine fremden Programme an seiner Anmeldung (Nutzungsbedingungen, "
                + "Abschnitt 5). Die Nutzung dieses Wegs erfolgt auf eigenes Risiko."
            icon.name: "dialog-warning"
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormCheckDelegate {
            text: "Risiko verstanden, Anmeldung über den Browser verwenden"
            checked: page.li.consent
            enabled: !page.li.consent
            onToggled: if (checked) backend.giveConsent()
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormButtonDelegate {
            text: page.li.waiting ? "Anmeldeseite erneut öffnen" : "Im Browser anmelden"
            icon.name: "internet-web-browser"
            enabled: page.li.consent && !page.li.busy
            onClicked: backend.startBrowserLogin()
        }
    }

    // --- Rückgabe aus dem Browser ---
    FormCard.FormHeader { visible: !page.signedIn && page.li.waiting; title: "Adresse aus dem Browser" }
    FormCard.FormCard {
        visible: !page.signedIn && page.li.waiting
        FormCard.FormTextDelegate {
            text: "Nach der Anmeldung"
            description: "1. Im Browser bei Zwift anmelden.\n"
                + "2. Die Seite zeigt danach „Bad Request“, das ist normal.\n"
                + "3. Die Adresse aus der Adresszeile kopieren (Strg+L, dann Strg+C). "
                + "Tretlager übernimmt sie von selbst aus der Zwischenablage."
            icon.name: "edit-paste"
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormTextFieldDelegate {
            id: redirect
            label: "Adresse"
            placeholderText: "https://launcher.zwift.com/launcher?…&code=…"
            onAccepted: backend.submitRedirect(text)
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormButtonDelegate {
            text: page.li.busy ? "Wird übernommen …" : "Adresse übernehmen"
            icon.name: "dialog-ok"
            enabled: redirect.text.length > 0 && !page.li.busy
            onClicked: backend.submitRedirect(redirect.text)
        }
    }

    Item { implicitHeight: Kirigami.Units.gridUnit }

    footer: WizardFooter {
        nextText: page.wizard ? "Weiter" : "Zur Übersicht"
        nextIcon: page.wizard ? "go-next" : "go-home"
        nextEnabled: page.signedIn
        onNext: page.wizard ? applicationWindow().pageStack.push(Qt.resolvedUrl("SensorsPage.qml"))
                            : applicationWindow().show("overview")
    }
}
