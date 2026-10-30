import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

// Schritt 4 des Assistenten; aus der Übersicht auch zum erneuten Anmelden (ohne Schrittanzeige).
ColumnsPage {
    id: page
    title: i18n("Anmeldung")

    readonly property var li: backend.loginInfo
    readonly property bool signedIn: li.state === "valid" || li.state === "refreshable"
    readonly property bool wizard: applicationWindow().inWizard

    function days(s) { return Math.round(s / 86400) }

    Component.onCompleted: backend.loadLogin()

    header: WizardHeader {
        visible: page.wizard
        step: 4
        text: i18n("Das Passwort wird nur auf der Anmeldeseite von Zwift eingegeben.")
    }

    PageMessage {
        visible: page.signedIn
        type: Kirigami.MessageType.Positive
        text: i18np("Angemeldet. Tretlager erneuert die Sitzung noch einen Tag lang selbst, danach ist eine neue Anmeldung nötig.",
                     "Angemeldet. Tretlager erneuert die Sitzung noch %1 Tage lang selbst, danach ist eine neue Anmeldung nötig.",
                     page.days(page.li.refresh_left))
        actions: [Kirigami.Action { text: i18n("Abmelden"); icon.name: "system-log-out"; onTriggered: backend.logout() }]
    }
    PageMessage {
        visible: page.li.error !== ""
        type: Kirigami.MessageType.Error
        text: page.li.error
    }

    leftCards: [
        // --- Ersatzweg: mit Zustimmung ---
        FormCard.FormHeader { visible: !page.signedIn; title: i18n("Anmeldung über Tretlager") },
        FormCard.FormCard {
            visible: !page.signedIn
            FormCard.FormTextDelegate {
                text: i18n("So funktioniert es")
                description: backend.embeddedLogin
                    ? i18n("Die Anmeldeseite von Zwift öffnet sich in einem privaten Fenster von Tretlager, wie im offiziellen Launcher. Danach übernimmt Tretlager die Sitzung und legt sie im Schlüsselbund ab. Das Passwort liest und speichert Tretlager nicht.")
                    : i18n("Die Anmeldung erfolgt auf der Zwift-Seite im Browser. Tretlager übernimmt danach die Sitzung und legt sie im Schlüsselbund ab.")
                icon.name: "user-identity"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: i18n("Nicht von Zwift erlaubt")
                description: i18n("Zwift erlaubt keine fremden Programme an seiner Anmeldung (Nutzungsbedingungen, Abschnitt 5). Die Nutzung dieses Wegs erfolgt auf eigenes Risiko.")
                icon.name: "dialog-warning"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormCheckDelegate {
                text: i18n("Risiko verstanden, diesen Weg verwenden")
                checked: page.li.consent
                enabled: !page.li.consent
                onToggled: if (checked) backend.giveConsent()
            }
            FormCard.FormDelegateSeparator { visible: backend.embeddedLogin }
            FormCard.FormButtonDelegate {
                visible: backend.embeddedLogin
                text: i18n("Bei Zwift anmelden …")
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
            title: backend.embeddedLogin ? i18n("Alternative: eigener Browser") : i18n("Im Browser anmelden")
            trailing: Kirigami.ContextualHelpButton {
                visible: backend.embeddedLogin
                toolTipText: i18n("Sinnvoll, wenn das Passwort im Passwortmanager des Browsers liegt oder die Anmeldung über Google oder Apple läuft; diese Anbieter sperren eingebettete Fenster oft. Nach der Anmeldung zeigt der Browser eine Fehlerseite, deren Adresse Tretlager braucht.")
            }
        },
        FormCard.FormCard {
            visible: !page.signedIn
            FormCard.FormButtonDelegate {
                text: page.li.waiting ? i18n("Anmeldeseite erneut öffnen") : i18n("Im eigenen Browser anmelden")
                icon.name: "internet-web-browser"
                enabled: page.li.consent && !page.li.busy
                onClicked: backend.startBrowserLogin()
            }
            FormCard.FormDelegateSeparator { visible: page.li.waiting }
            FormCard.FormTextDelegate {
                visible: page.li.waiting
                text: i18n("Nach der Anmeldung")
                description: i18n("Der Browser zeigt „Bad Request“, das ist bei diesem Weg normal. Die Adresse aus der Adresszeile kopieren (Strg+L, dann Strg+C); Tretlager übernimmt sie von selbst aus der Zwischenablage.")
                icon.name: "edit-paste"
            }
            FormCard.FormDelegateSeparator { visible: page.li.waiting }
            FormCard.FormTextFieldDelegate {
                id: redirect
                visible: page.li.waiting
                label: i18n("Adresse")
                placeholderText: "https://launcher.zwift.com/launcher?…&code=…"
                onAccepted: backend.submitRedirect(text)
            }
            FormCard.FormDelegateSeparator { visible: page.li.waiting }
            FormCard.FormButtonDelegate {
                visible: page.li.waiting
                text: page.li.busy ? i18n("Wird übernommen …") : i18n("Adresse übernehmen")
                icon.name: "dialog-ok"
                enabled: redirect.text.length > 0 && !page.li.busy
                onClicked: backend.submitRedirect(redirect.text)
            }
        },

        // --- Offiziell: derzeit nicht möglich ---
        FormCard.FormHeader { visible: !page.signedIn; title: i18n("Offizielle Anmeldung") },
        FormCard.FormCard {
            visible: !page.signedIn
            FormCard.FormTextDelegate {
                text: i18n("Derzeit nicht möglich")
                description: i18n("Der Zwift Launcher nutzt seit Version 1.2 eine Windows-Funktion, die Wine noch fehlt.")
                icon.name: "data-error"
            }
        }
    ]

    footer: WizardFooter {
        nextText: page.wizard ? i18n("Weiter") : i18n("Zur Übersicht")
        nextIcon: page.wizard ? "go-next" : "go-home"
        nextEnabled: page.signedIn
        onNext: page.wizard ? applicationWindow().pageStack.push(Qt.resolvedUrl("SensorsPage.qml"))
                            : applicationWindow().show("overview")
    }
}
