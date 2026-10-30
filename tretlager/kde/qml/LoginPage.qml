import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

// Schritt 4 des Assistenten; aus der Übersicht auch zum erneuten Anmelden (ohne Schrittanzeige).
ColumnsPage {
    id: page
    title: "Anmeldung"

    readonly property var li: backend.loginInfo
    readonly property bool signedIn: li.state === "valid" || li.state === "refreshable"
    readonly property bool wizard: applicationWindow().inWizard

    function days(s) { return Math.round(s / 86400) }

    Component.onCompleted: backend.loadLogin()

    header: WizardHeader {
        visible: page.wizard
        step: 4
        text: "Das Passwort wird nur auf der Anmeldeseite von Zwift eingegeben."
    }

    PageMessage {
        visible: page.signedIn
        type: Kirigami.MessageType.Positive
        text: "Angemeldet. Tretlager erneuert die Sitzung noch " + page.days(page.li.refresh_left)
              + " Tage lang selbst, danach ist eine neue Anmeldung im Browser nötig."
        actions: [Kirigami.Action { text: "Abmelden"; icon.name: "system-log-out"; onTriggered: backend.logout() }]
    }
    PageMessage {
        visible: page.li.error !== ""
        type: Kirigami.MessageType.Error
        text: page.li.error
    }

    leftCards: [
        // --- Ersatzweg: mit Zustimmung ---
        FormCard.FormHeader { visible: !page.signedIn; title: "Anmeldung über Tretlager" },
        FormCard.FormCard {
            visible: !page.signedIn
            FormCard.FormTextDelegate {
                text: "So funktioniert es"
                description: backend.embeddedLogin
                    ? "Die Anmeldeseite von Zwift öffnet sich in einem privaten Fenster von Tretlager, wie im "
                      + "offiziellen Launcher. Danach übernimmt Tretlager die Sitzung und legt sie im "
                      + "Schlüsselbund ab. Das Passwort liest und speichert Tretlager nicht."
                    : "Die Anmeldung erfolgt auf der Zwift-Seite im Browser. Tretlager übernimmt danach die "
                      + "Sitzung und legt sie im Schlüsselbund ab."
                icon.name: "user-identity"
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
                text: "Risiko verstanden, diesen Weg verwenden"
                checked: page.li.consent
                enabled: !page.li.consent
                onToggled: if (checked) backend.giveConsent()
            }
            FormCard.FormDelegateSeparator { visible: backend.embeddedLogin }
            FormCard.FormButtonDelegate {
                visible: backend.embeddedLogin
                text: "Bei Zwift anmelden …"
                icon.name: "go-next"
                enabled: page.li.consent && !page.li.busy
                onClicked: applicationWindow().pageStack.push(Qt.resolvedUrl("LoginWebPage.qml"))
            }
        }
    ]

    rightCards: [
        // --- Ausweichweg: eigener Browser (Passwortmanager, Anmeldung mit Google oder Apple) ---
        FormCard.FormHeader {
            visible: !page.signedIn
            title: backend.embeddedLogin ? "Alternative: eigener Browser" : "Im Browser anmelden"
            trailing: Kirigami.ContextualHelpButton {
                visible: backend.embeddedLogin
                toolTipText: "Sinnvoll, wenn das Passwort im Passwortmanager des Browsers liegt oder die "
                    + "Anmeldung über Google oder Apple läuft; diese Anbieter sperren eingebettete Fenster oft. "
                    + "Nach der Anmeldung zeigt der Browser eine Fehlerseite, deren Adresse Tretlager braucht."
            }
        },
        FormCard.FormCard {
            visible: !page.signedIn
            FormCard.FormButtonDelegate {
                text: page.li.waiting ? "Anmeldeseite erneut öffnen" : "Im eigenen Browser anmelden"
                icon.name: "internet-web-browser"
                enabled: page.li.consent && !page.li.busy
                onClicked: backend.startBrowserLogin()
            }
            FormCard.FormDelegateSeparator { visible: page.li.waiting }
            FormCard.FormTextDelegate {
                visible: page.li.waiting
                text: "Nach der Anmeldung"
                description: "Der Browser zeigt „Bad Request“, das ist bei diesem Weg normal. Die Adresse aus "
                    + "der Adresszeile kopieren (Strg+L, dann Strg+C); Tretlager übernimmt sie von selbst "
                    + "aus der Zwischenablage."
                icon.name: "edit-paste"
            }
            FormCard.FormDelegateSeparator { visible: page.li.waiting }
            FormCard.FormTextFieldDelegate {
                id: redirect
                visible: page.li.waiting
                label: "Adresse"
                placeholderText: "https://launcher.zwift.com/launcher?…&code=…"
                onAccepted: backend.submitRedirect(text)
            }
            FormCard.FormDelegateSeparator { visible: page.li.waiting }
            FormCard.FormButtonDelegate {
                visible: page.li.waiting
                text: page.li.busy ? "Wird übernommen …" : "Adresse übernehmen"
                icon.name: "dialog-ok"
                enabled: redirect.text.length > 0 && !page.li.busy
                onClicked: backend.submitRedirect(redirect.text)
            }
        },

        // --- Offiziell: derzeit nicht möglich ---
        FormCard.FormHeader { visible: !page.signedIn; title: "Offizielle Anmeldung" },
        FormCard.FormCard {
            visible: !page.signedIn
            FormCard.FormTextDelegate {
                text: "Derzeit nicht möglich"
                description: "Der Zwift Launcher nutzt seit Version 1.2 eine Windows-Funktion, die Wine noch fehlt. "
                    + "Tretlager prüft nach jedem Launcher-Update, ob sie wieder funktioniert."
                icon.name: "data-error"
            }
        }
    ]

    footer: WizardFooter {
        nextText: page.wizard ? "Weiter" : "Zur Übersicht"
        nextIcon: page.wizard ? "go-next" : "go-home"
        nextEnabled: page.signedIn
        onNext: page.wizard ? applicationWindow().pageStack.push(Qt.resolvedUrl("SensorsPage.qml"))
                            : applicationWindow().show("overview")
    }
}
