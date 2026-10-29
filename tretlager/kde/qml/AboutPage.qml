import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

// Über Tretlager: Version, Hinweis zu Zwift und Haftung, Lizenz, Fremdkomponenten.
Kirigami.ScrollablePage {
    id: page
    title: "Über Tretlager"

    // Name, Lizenz, wofür, Link
    readonly property var parts: [
        ["Qt und PySide6", "LGPL-3.0", "Oberfläche", "https://www.qt.io/licensing/open-source-lgpl-obligations"],
        ["KDE Kirigami", "LGPL-2.0-or-later", "Oberfläche im Plasma-Stil", "https://develop.kde.org/frameworks/kirigami/"],
        ["Bleak", "MIT", "Bluetooth Low Energy über BlueZ", "https://github.com/hbldh/bleak"],
        ["dbus-fast", "MIT", "D-Bus für Bridge und Avahi", "https://github.com/Bluetooth-Devices/dbus-fast"],
        ["SecretStorage", "BSD-3-Clause", "Zwift-Sitzung im Schlüsselbund", "https://github.com/mitya57/secretstorage"],
        ["Wine (WineHQ)", "LGPL-2.1-or-later", "führt den Windows-Client von Zwift aus", "https://www.winehq.org/license"],
        ["winetricks", "LGPL-2.1-or-later", "richtet Windows-Komponenten im Wine-Präfix ein", "https://github.com/Winetricks/winetricks"]
    ]
    readonly property var proprietary: [
        ["Zwift", "Zwift-Nutzungsbedingungen", "das Spiel selbst; Tretlager lädt es von Zwift herunter", "https://www.zwift.com/terms"],
        [".NET Framework 4.8, WebView2, Core Fonts, d3dcompiler_47", "Lizenzbedingungen von Microsoft", "braucht der Zwift Launcher; winetricks lädt sie von Microsoft", ""]
    ]

    PageContent {
        maximumWidth: Kirigami.Units.gridUnit * 50

        // --- Kopf ---
        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: Kirigami.Units.gridUnit
            spacing: Kirigami.Units.gridUnit
            Kirigami.Icon {
                source: "de.linuxundich.Tretlager"
                Layout.preferredWidth: Kirigami.Units.iconSizes.enormous
                Layout.preferredHeight: Kirigami.Units.iconSizes.enormous
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: Kirigami.Units.smallSpacing
                Kirigami.Heading { text: "Tretlager"; level: 1 }
                Controls.Label { text: "Version " + backend.version; color: Kirigami.Theme.disabledTextColor }
                Controls.Label {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: "Richtet Zwift unter Linux ein, hält es aktuell und verbindet Trainer und Pulsgurt über die Sensor-Bridge – ohne Zwift Companion."
                }
                Controls.Label {
                    text: "© 2026 Christoph Langner · <a href=\"https://linuxundich.de/\">linuxundich.de</a>"
                    textFormat: Text.StyledText
                    onLinkActivated: (link) => Qt.openUrlExternally(link)
                }
            }
        }

        // --- Hinweis zu Zwift und Haftung ---
        Kirigami.InlineMessage {
            Layout.fillWidth: true
            Layout.topMargin: Kirigami.Units.largeSpacing
            visible: true
            type: Kirigami.MessageType.Warning
            text: "<b>Kein offizielles Zwift-Programm.</b> Tretlager ist ein privates Projekt und wird von Zwift Inc. weder entwickelt noch unterstützt. Die Benutzung erfolgt auf eigene Gefahr."
        }

        SectionCard {
            title: "Was das bedeutet"
            iconName: "dialog-warning"
            Layout.fillHeight: false
            Repeater {
                model: [
                    "Zwift unterstützt Linux und Wine nicht. Bei Problemen hilft der Zwift-Support nicht weiter; melde sie bei Tretlager, nicht bei Zwift.",
                    "Die Anmeldung über den Browser umgeht den offiziellen Launcher und widerspricht den Zwift-Nutzungsbedingungen. Dass Zwift darauf mit Einschränkungen bis hin zur Sperre des Kontos reagiert, lässt sich nicht ausschließen.",
                    "Tretlager verändert keine Zwift-Dateien und umgeht weder Kopierschutz noch Abo-Prüfung. Ohne gültiges Zwift-Abo fährst du auch mit Tretlager nicht.",
                    "Die Sensor-Bridge gibt sich gegenüber Zwift als Wahoo-Gerät mit „Direct Connect“ aus. Werte und Widerstand kommen unverändert vom Gerät, trotzdem gibt es keine Garantie, dass alles stimmt – etwa bei Rennen mit Wertung.",
                    "Tretlager wird ohne jede Gewährleistung bereitgestellt, soweit das Gesetz es zulässt (GPL, Abschnitte 15 und 16)."
                ]
                delegate: RowLayout {
                    required property string modelData
                    Layout.fillWidth: true
                    spacing: Kirigami.Units.largeSpacing
                    Controls.Label { text: "•"; Layout.alignment: Qt.AlignTop }
                    Controls.Label { text: modelData; Layout.fillWidth: true; wrapMode: Text.WordWrap }
                }
            }
            Hint {
                text: "Zwift, Wahoo, KICKR, TICKR und Garmin sind Marken ihrer jeweiligen Inhaber. Tretlager steht mit keinem dieser Unternehmen in Verbindung."
            }
        }

        // --- Lizenz ---
        SectionCard {
            title: "Lizenz"
            iconName: "license"
            Layout.fillHeight: false
            Controls.Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                textFormat: Text.StyledText
                onLinkActivated: (link) => Qt.openUrlExternally(link)
                text: "Tretlager ist freie Software unter der <a href=\"https://www.gnu.org/licenses/gpl-3.0.html\">GNU General Public License, Version 3 oder später</a> (GPL-3.0-or-later). Du darfst das Programm nutzen, untersuchen, verändern und weitergeben. Gibst du es weiter, auch verändert, muss das unter derselben Lizenz und mit Quelltext geschehen. Das gilt auch für das Programmsymbol."
            }
            Hint {
                text: "Die Lizenz gilt nur für Tretlager selbst. Die Programme, die Tretlager einrichtet oder nutzt, stehen unter ihren eigenen Lizenzen – siehe unten."
            }
        }

        // --- Freie Komponenten ---
        SectionCard {
            title: "Freie Software, auf der Tretlager aufbaut"
            iconName: "code-context"
            Layout.fillHeight: false
            Repeater {
                model: page.parts
                delegate: componentRow
            }
            Hint {
                text: "Das Protokoll für Wahoo „Direct Connect“ (DIRCON) hat Tretlager nach der öffentlichen Beschreibung im Projekt <a href=\"https://github.com/cagnulein/qdomyos-zwift\">qdomyos-zwift</a> umgesetzt."
            }
        }

        // --- Proprietäre Komponenten ---
        SectionCard {
            title: "Unfreie Software, die Tretlager herunterlädt"
            iconName: "download"
            Layout.fillHeight: false
            Controls.Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: "Diese Teile liefert Tretlager nicht mit. Die Einrichtung lädt sie direkt vom Hersteller, und es gelten dessen Lizenzbedingungen."
            }
            Repeater {
                model: page.proprietary
                delegate: componentRow
            }
        }

        Component {
            id: componentRow
            ColumnLayout {
                required property var modelData
                Layout.fillWidth: true
                spacing: 0
                RowLayout {
                    Layout.fillWidth: true
                    Controls.Label {
                        text: modelData[3] ? "<a href=\"" + modelData[3] + "\">" + modelData[0] + "</a>" : modelData[0]
                        textFormat: Text.StyledText
                        font.bold: true
                        onLinkActivated: (link) => Qt.openUrlExternally(link)
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                    }
                    Controls.Label { text: modelData[1]; color: Kirigami.Theme.disabledTextColor }
                }
                Controls.Label {
                    text: modelData[2]
                    color: Kirigami.Theme.disabledTextColor
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                }
            }
        }
    }
}
