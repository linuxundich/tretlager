import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

// Help in the same scaffold as the other pages: one card per section with entries made of
// keyword and sentence instead of running text. The backend works out which column a section
// goes into (core/helpdoc.py); "If something goes wrong" sits at the bottom across the full width,
// with its entries in two columns.
ColumnsPage {
    id: page
    title: i18n("Help")

    readonly property var sections: backend.helpSections
    function inColumn(c) { return sections.filter(function (s) { return s.column === c }) }

    // One entry: icon (optional), keyword, sentence
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

            // Introduction
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

            // Entries: stacked with separators, wide sections in two columns
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
