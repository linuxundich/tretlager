import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

// Infoseite im selben Gerüst wie die übrigen Seiten: oben Name, Version und Haftungshinweis,
// darunter links, was der Hinweis auf Zwift bedeutet, rechts die Lizenzen.
ColumnsPage {
    id: page
    title: i18n("Über Tretlager")

    LogDialog {
        id: licenseDialog
        title: i18n("GNU General Public License v3")
        text: backend.licenseText
    }

    PageHero {
        title: i18n("Tretlager %1", backend.version)
        text: i18n("Zwift unter Linux einrichten, aktuell halten und mit Trainer und Pulsgurt verbinden.\nTretlager ist ein privates Projekt und kein Programm von Zwift Inc. Zwift unterstützt den Betrieb unter Linux nicht. Die Benutzung erfolgt auf eigene Gefahr.")
        Controls.Label {
            text: i18n("© 2026 Christoph Langner · GPL-3.0-or-later")
            color: Kirigami.Theme.disabledTextColor
            font: Kirigami.Theme.smallFont
        }
        RowLayout {
            Layout.topMargin: Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.smallSpacing
            Controls.Button {
                text: i18n("Lizenz")
                icon.name: "license"
                onClicked: licenseDialog.open()
            }
            Controls.Button {
                text: "linuxundich.de"
                icon.name: "internet-web-browser"
                onClicked: Qt.openUrlExternally("https://linuxundich.de/")
            }
        }
    }

    // Name, Lizenz, wofür, Link
    readonly property var freeParts: [
        [i18n("Qt und PySide6"), "LGPL-3.0", i18n("Oberfläche"), "https://www.qt.io/licensing/open-source-lgpl-obligations"],
        [i18n("KDE Kirigami und Kirigami Addons"), "LGPL-2.0-or-later", i18n("Oberfläche im Plasma-Stil"), "https://develop.kde.org/frameworks/kirigami/"],
        [i18n("Bleak"), i18n("MIT"), i18n("Bluetooth Low Energy über BlueZ"), "https://github.com/hbldh/bleak"],
        ["dbus-fast", i18n("MIT"), i18n("D-Bus für Bridge und Avahi"), "https://github.com/Bluetooth-Devices/dbus-fast"],
        [i18n("SecretStorage"), i18n("BSD-3-Clause"), i18n("Zwift-Sitzung im Schlüsselbund"), "https://github.com/mitya57/secretstorage"],
        [i18n("Wine (WineHQ)"), "LGPL-2.1-or-later", i18n("führt den Windows-Client von Zwift aus"), "https://www.winehq.org/license"],
        ["winetricks", "LGPL-2.1-or-later", i18n("richtet Windows-Komponenten im Wine-Präfix ein"), "https://github.com/Winetricks/winetricks"]
    ]

    leftCards: [
        FormCard.FormHeader { title: i18n("Was das bedeutet") },
        FormCard.FormCard {
            FormCard.FormTextDelegate {
                text: i18n("Kein Support von Zwift")
                description: i18n("Zwift unterstützt Linux und Wine nicht. Probleme an Tretlager melden, nicht an Zwift.")
                icon.name: "help-about"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: i18n("Anmeldung über den Browser")
                description: i18n("Umgeht den offiziellen Launcher und widerspricht den Zwift-Nutzungsbedingungen. Einschränkungen bis hin zur Sperre des Kontos lassen sich nicht ausschließen.")
                icon.name: "dialog-warning"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: i18n("Zwift bleibt unverändert")
                description: i18n("Tretlager verändert keine Zwift-Dateien und umgeht weder Kopierschutz noch Abo-Prüfung. Ohne gültiges Zwift-Abo ist keine Fahrt möglich.")
                icon.name: "security-high"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: i18n("Sensor-Bridge")
                description: i18n("Gibt sich gegenüber Zwift als Wahoo-Gerät mit „Direct Connect“ aus und reicht die Werte des Geräts weiter, ohne sie zu verändern.")
                icon.name: "network-bluetooth"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: i18n("Nicht für Rennen")
                description: i18n("Es gibt keine Garantie, dass die Sensor-Bridge Leistung, Trittfrequenz und Puls vollständig und korrekt an Zwift weitergibt; Übertragungsfehler und Aussetzer sind möglich. An Rennen und Wettbewerben mit Wertung daher nicht mit Tretlager teilnehmen.")
                icon.name: "flag"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: i18n("Keine Gewährleistung")
                description: i18n("Soweit gesetzlich zulässig (GPL, Abschnitte 15 und 16). Zwift, Wahoo, KICKR, TICKR und Garmin sind Marken ihrer Inhaber; Tretlager steht mit keinem dieser Unternehmen in Verbindung.")
                icon.name: "emblem-important"
            }
        },

        FormCard.FormHeader { title: i18n("Unfreie Software, die Tretlager herunterlädt") },
        FormCard.FormCard {
            FormCard.FormTextDelegate {
                text: i18n("Nicht im Paket enthalten")
                description: i18n("Die Einrichtung lädt diese Teile direkt beim Hersteller; es gelten dessen Lizenzbedingungen.")
                icon.name: "download"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormLinkDelegate {
                text: i18n("Zwift")
                description: i18n("Zwift-Nutzungsbedingungen · das Spiel selbst, lädt Tretlager von Zwift herunter")
                url: "https://www.zwift.com/terms"
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormTextDelegate {
                text: i18n(".NET Framework 4.8, WebView2, Core Fonts, d3dcompiler_47")
                description: i18n("Lizenzbedingungen von Microsoft · braucht der Zwift Launcher, lädt winetricks von Microsoft")
            }
        }
    ]

    rightCards: [
        FormCard.FormHeader { title: i18n("Freie Software, auf der Tretlager aufbaut") },
        FormCard.FormCard {
            Repeater {
                model: page.freeParts
                delegate: FormCard.FormLinkDelegate {
                    required property var modelData
                    text: modelData[0]
                    description: modelData[1] + " · " + modelData[2]
                    url: modelData[3]
                }
            }
            FormCard.FormDelegateSeparator {}
            FormCard.FormLinkDelegate {
                text: "qdomyos-zwift"
                description: i18n("Beschreibung des Protokolls Wahoo „Direct Connect“ (DIRCON), nach der die Bridge umgesetzt ist")
                url: "https://github.com/cagnulein/qdomyos-zwift"
            }
        }
    ]
}
