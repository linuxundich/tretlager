import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

// Hilfe im selben Gerüst wie die übrigen Seiten: je Abschnitt eine Karte mit Einträgen aus
// Stichwort und Satz statt Fließtext. Welche Spalte ein Abschnitt bekommt, rechnet das Backend
// aus (core/helpdoc.py); „Wenn etwas nicht klappt“ steht unten über die volle Breite, die
// Einträge dort in zwei Spalten.
ColumnsPage {
    id: page
    title: i18n("Help")

    readonly property var sections: backend.helpSections
    function inColumn(c) { return sections.filter(function (s) { return s.column === c }) }

    // Ein Eintrag: Symbol (optional), Stichwort, Satz
    component Entry: FormCard.AbstractFormDelegate {
        id: entry
        required property var item
        hoverEnabled: false
        focusPolicy: Qt.NoFocus
        contentItem: RowLayout {
            spacing: Kirigami.Units.largeSpacing
            Kirigami.Icon {
                visible: entry.item.icon !== ""
                source: entry.item.icon
                Layout.alignment: Qt.AlignTop
                Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: Kirigami.Units.smallSpacing / 2
                Controls.Label {
                    Layout.fillWidth: true
                    text: entry.item.title
                    textFormat: Text.RichText
                    wrapMode: Text.WordWrap
                    font.weight: Font.DemiBold
                }
                Controls.Label {
                    Layout.fillWidth: true
                    text: entry.item.text
                    textFormat: Text.RichText
                    wrapMode: Text.WordWrap
                    color: Kirigami.Theme.disabledTextColor
                }
            }
        }
    }

    component Section: ColumnLayout {
        id: section
        required property var modelData
        readonly property bool twoColumns: modelData.wide && page.wide
        Layout.fillWidth: true
        spacing: 0

        FormCard.FormHeader { title: section.modelData.title; maximumWidth: Infinity }
        FormCard.FormCard {
            maximumWidth: Infinity

            // Einleitung
            Repeater {
                model: section.modelData.intro
                delegate: FormCard.AbstractFormDelegate {
                    required property string modelData
                    hoverEnabled: false
                    focusPolicy: Qt.NoFocus
                    contentItem: Controls.Label {
                        text: modelData
                        textFormat: Text.RichText
                        wrapMode: Text.WordWrap
                    }
                }
            }
            FormCard.FormDelegateSeparator { visible: section.modelData.intro.length > 0 }

            // Einträge: untereinander mit Trennlinien, breite Abschnitte in zwei Spalten
            GridLayout {
                Layout.fillWidth: true
                columns: section.twoColumns ? 2 : 1
                columnSpacing: 0
                rowSpacing: 0
                Repeater {
                    model: section.modelData.items
                    delegate: ColumnLayout {
                        required property var modelData
                        required property int index
                        Layout.fillWidth: true
                        Layout.preferredWidth: 1
                        Layout.alignment: Qt.AlignTop
                        spacing: 0
                        FormCard.FormDelegateSeparator {
                            visible: index >= (section.twoColumns ? 2 : 1)
                        }
                        Entry { item: modelData; Layout.fillWidth: true }
                    }
                }
            }
        }
    }

    leftCards: [
        Repeater { model: page.inColumn(0); delegate: Section {} }
    ]
    rightCards: [
        Repeater { model: page.inColumn(1); delegate: Section {} }
    ]
    bottomCards: [
        Repeater { model: page.inColumn(2); delegate: Section {} }
    ]
}
