import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

// Karte der Übersicht: kleiner einfarbiger Kopf (Symbol + Titel), Inhalt, optional Knöpfe unten.
// Eigene Vorlage statt Kirigami.Card, weil deren Höhe umgebrochene Texte nicht sicher einrechnet.
Kirigami.AbstractCard {
    id: card
    property string title
    property string iconName
    default property alias body: bodyColumn.data
    property alias buttons: buttonRow.data

    Layout.fillWidth: true
    Layout.fillHeight: true
    Layout.preferredWidth: 1  // gleich breite Spalten im Raster
    Layout.alignment: Qt.AlignTop

    contentItem: ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        RowLayout {
            spacing: Kirigami.Units.smallSpacing * 2
            Kirigami.Icon {
                source: card.iconName
                Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
            }
            Kirigami.Heading { text: card.title; level: 3; Layout.fillWidth: true }
        }
        Kirigami.Separator { Layout.fillWidth: true }

        ColumnLayout {
            id: bodyColumn
            Layout.fillWidth: true
            spacing: Kirigami.Units.largeSpacing
        }

        Item { Layout.fillHeight: true }

        RowLayout {
            id: buttonRow
            visible: children.length > 0
            Layout.alignment: Qt.AlignRight
            spacing: Kirigami.Units.smallSpacing
        }
    }
}
