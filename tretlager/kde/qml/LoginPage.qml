import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

// Schritt 4 des Assistenten; aus der Übersicht auch zum erneuten Anmelden (ohne Schrittanzeige).
ColumnsPage {
    id: page
    title: i18n("Sign-in")

    readonly property var li: backend.loginInfo
    readonly property bool signedIn: li.state === "valid" || li.state === "refreshable"
    readonly property bool wizard: applicationWindow().inWizard

    function days(s) { return Math.round(s / 86400) }

    Component.onCompleted: backend.loadLogin()

    header: WizardHeader {
        visible: page.wizard
        stepId: "login"
        text: i18n("The password is only entered on Zwift's sign-in page.")
    }

    PageMessage {
        visible: page.signedIn
        type: Kirigami.MessageType.Positive
        text: i18np("Signed in. Tretlager renews the session by itself for one more day; after that, signing in again is required.",
                     "Signed in. Tretlager renews the session by itself for %1 more days; after that, signing in again is required.",
                     page.days(page.li.refresh_left))
        actions: [Kirigami.Action { text: i18n("Sign out"); icon.name: "system-log-out"; onTriggered: backend.logout() }]
    }
    PageMessage {
        visible: page.li.error !== ""
        type: Kirigami.MessageType.Error
        text: page.li.error
    }

    leftCards: [
        // --- Ersatzweg: mit Zustimmung ---
        FormCard.FormHeader { visible: !page.signedIn; title: i18n("Sign in through Tretlager") },
        FormCard.FormCard {
            visible: !page.signedIn
            FormCard.FormTextDelegate {
                text: i18n("How it works")
                description: backend.embeddedLogin
                    ? i18n("Zwift's sign-in page opens in a private Tretlager window, as in the official launcher. Tretlager then takes over the session and stores it in the keyring. Tretlager neither reads nor stores the password.")
                    : i18n("You sign in on Zwift's page in the browser. Tretlager then takes over the session and stores it in the keyring.")
                icon.name: "user-identity"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: i18n("Not permitted by Zwift")
                description: i18n("Zwift does not allow third-party programs to use its sign-in (terms of service, section 5). Using this route is at your own risk.")
                icon.name: "dialog-warning"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormCheckDelegate {
                text: i18n("I understand the risk, use this route")
                checked: page.li.consent
                enabled: !page.li.consent
                onToggled: if (checked) backend.giveConsent()
            }
            FormCard.FormDelegateSeparator { visible: backend.embeddedLogin }
            FormCard.FormButtonDelegate {
                visible: backend.embeddedLogin
                text: i18n("Sign in to Zwift…")
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
            title: backend.embeddedLogin ? i18n("Alternative: your own browser") : i18n("Sign in in the browser")
            trailing: Kirigami.ContextualHelpButton {
                visible: backend.embeddedLogin
                toolTipText: i18n("Useful if the password is stored in the browser's password manager or you sign in with Google or Apple; these providers often block embedded windows. After signing in, the browser shows an error page whose address Tretlager needs.")
            }
        },
        FormCard.FormCard {
            visible: !page.signedIn
            FormCard.FormButtonDelegate {
                text: page.li.waiting ? i18n("Open the sign-in page again") : i18n("Sign in in your own browser")
                icon.name: "internet-web-browser"
                enabled: page.li.consent && !page.li.busy
                onClicked: backend.startBrowserLogin()
            }
            FormCard.FormDelegateSeparator { visible: page.li.waiting }
            FormCard.FormTextDelegate {
                visible: page.li.waiting
                text: i18n("After signing in")
                description: i18n("The browser shows “Bad Request”; that is normal for this route. Copy the address from the address bar (Ctrl+L, then Ctrl+C); Tretlager picks it up from the clipboard by itself.")
                icon.name: "edit-paste"
            }
            FormCard.FormDelegateSeparator { visible: page.li.waiting }
            FormCard.FormTextFieldDelegate {
                id: redirect
                visible: page.li.waiting
                label: i18n("Address")
                placeholderText: "https://launcher.zwift.com/launcher?…&code=…"
                onAccepted: backend.submitRedirect(text)
            }
            FormCard.FormDelegateSeparator { visible: page.li.waiting }
            FormCard.FormButtonDelegate {
                visible: page.li.waiting
                text: page.li.busy ? i18n("Taking over…") : i18n("Use address")
                icon.name: "dialog-ok"
                enabled: redirect.text.length > 0 && !page.li.busy
                onClicked: backend.submitRedirect(redirect.text)
            }
        },

        // --- Offiziell: derzeit nicht möglich ---
        FormCard.FormHeader { visible: !page.signedIn; title: i18n("Official sign-in") },
        FormCard.FormCard {
            visible: !page.signedIn
            FormCard.FormTextDelegate {
                text: i18n("Currently not possible")
                description: i18n("Since version 1.2, the Zwift launcher uses a Windows feature that Wine does not provide yet.")
                icon.name: "data-error"
            }
        }
    ]

    footer: WizardFooter {
        nextText: page.wizard ? i18n("Next") : i18n("Go to overview")
        nextIcon: page.wizard ? "go-next" : "go-home"
        nextEnabled: page.signedIn
        onNext: page.wizard ? applicationWindow().pageStack.push(Qt.resolvedUrl("SensorsPage.qml"))
                            : applicationWindow().show("overview")
    }
}
