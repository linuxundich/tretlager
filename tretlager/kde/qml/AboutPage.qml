import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

// Standard-Infoseite von KDE (Kirigami Addons) mit eigenen Abschnitten für den Hinweis zu Zwift
// und die Lizenzen der Komponenten.
FormCard.AboutPage {
    id: page
    title: "Über Tretlager"
    showLibraries: false

    aboutData: ({
        displayName: "Tretlager",
        productName: "tretlager",
        componentName: "tretlager",
        programIconName: "de.linuxundich.Tretlager",
        desktopFileName: "de.linuxundich.Tretlager",
        shortDescription: "Zwift unter Linux einrichten, aktuell halten und mit Trainer und Pulsgurt verbinden",
        version: backend.version,
        homepage: "https://linuxundich.de/",
        bugAddress: "",
        copyrightStatement: "© 2026 Christoph Langner",
        otherText: "Tretlager ist ein privates Projekt und kein Programm von Zwift Inc. Zwift unterstützt "
            + "den Betrieb unter Linux nicht. Die Benutzung erfolgt auf eigene Gefahr.",
        authors: [{ name: "Christoph Langner", task: "Entwicklung", emailAddress: "",
                    webAddress: "https://linuxundich.de/", ocsUsername: "" }],
        credits: [],
        translators: [],
        licenses: [{ name: "GNU General Public License v3 oder später", text: backend.licenseText,
                     spdx: "GPL-3.0-or-later" }]
    })

    // Name, Lizenz, wofür, Link
    readonly property var freeParts: [
        ["Qt und PySide6", "LGPL-3.0", "Oberfläche", "https://www.qt.io/licensing/open-source-lgpl-obligations"],
        ["KDE Kirigami und Kirigami Addons", "LGPL-2.0-or-later", "Oberfläche im Plasma-Stil", "https://develop.kde.org/frameworks/kirigami/"],
        ["Bleak", "MIT", "Bluetooth Low Energy über BlueZ", "https://github.com/hbldh/bleak"],
        ["dbus-fast", "MIT", "D-Bus für Bridge und Avahi", "https://github.com/Bluetooth-Devices/dbus-fast"],
        ["SecretStorage", "BSD-3-Clause", "Zwift-Sitzung im Schlüsselbund", "https://github.com/mitya57/secretstorage"],
        ["Wine (WineHQ)", "LGPL-2.1-or-later", "führt den Windows-Client von Zwift aus", "https://www.winehq.org/license"],
        ["winetricks", "LGPL-2.1-or-later", "richtet Windows-Komponenten im Wine-Präfix ein", "https://github.com/Winetricks/winetricks"]
    ]

    FormCard.FormHeader { title: "Was das bedeutet" }
    FormCard.FormCard {
        FormCard.FormTextDelegate {
            text: "Kein Support von Zwift"
            description: "Zwift unterstützt Linux und Wine nicht. Probleme an Tretlager melden, nicht an Zwift."
            icon.name: "help-about"
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormTextDelegate {
            text: "Anmeldung über den Browser"
            description: "Umgeht den offiziellen Launcher und widerspricht den Zwift-Nutzungsbedingungen. "
                + "Einschränkungen bis hin zur Sperre des Kontos lassen sich nicht ausschließen."
            icon.name: "dialog-warning"
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormTextDelegate {
            text: "Zwift bleibt unverändert"
            description: "Tretlager verändert keine Zwift-Dateien und umgeht weder Kopierschutz noch Abo-Prüfung. "
                + "Ohne gültiges Zwift-Abo ist keine Fahrt möglich."
            icon.name: "security-high"
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormTextDelegate {
            text: "Sensor-Bridge"
            description: "Gibt sich gegenüber Zwift als Wahoo-Gerät mit „Direct Connect“ aus. Werte und Widerstand "
                + "kommen unverändert vom Gerät; eine Garantie für ihre Richtigkeit gibt es nicht, etwa bei "
                + "Rennen mit Wertung."
            icon.name: "network-bluetooth"
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormTextDelegate {
            text: "Keine Gewährleistung"
            description: "Soweit gesetzlich zulässig (GPL, Abschnitte 15 und 16). Zwift, Wahoo, KICKR, TICKR und "
                + "Garmin sind Marken ihrer Inhaber; Tretlager steht mit keinem dieser Unternehmen in Verbindung."
            icon.name: "emblem-important"
        }
    }

    FormCard.FormHeader { title: "Freie Software, auf der Tretlager aufbaut" }
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
            description: "Beschreibung des Protokolls Wahoo „Direct Connect“ (DIRCON), nach der die Bridge umgesetzt ist"
            url: "https://github.com/cagnulein/qdomyos-zwift"
        }
    }

    FormCard.FormHeader { title: "Unfreie Software, die Tretlager herunterlädt" }
    FormCard.FormCard {
        FormCard.FormTextDelegate {
            text: "Nicht im Paket enthalten"
            description: "Die Einrichtung lädt diese Teile direkt beim Hersteller; es gelten dessen Lizenzbedingungen."
            icon.name: "download"
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormLinkDelegate {
            text: "Zwift"
            description: "Zwift-Nutzungsbedingungen · das Spiel selbst, lädt Tretlager von Zwift herunter"
            url: "https://www.zwift.com/terms"
        }
        FormCard.FormDelegateSeparator {}
        FormCard.FormTextDelegate {
            text: ".NET Framework 4.8, WebView2, Core Fonts, d3dcompiler_47"
            description: "Lizenzbedingungen von Microsoft · braucht der Zwift Launcher, lädt winetricks von Microsoft"
        }
    }

    Item { implicitHeight: Kirigami.Units.gridUnit }
}
