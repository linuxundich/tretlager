import QtQuick
import QtQuick.Effects
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

// Gemeinsames Seitengerüst aller Seiten (Vorbild: Übersicht). Oben volle Breite (Meldungen,
// Kopf, einzelne Listen), darunter zwei Spalten, auf schmalen Fenstern untereinander, und am
// Ende wieder volle Breite. Alle Seiten nutzen dieselbe Breite, damit beim Wechseln zwischen
// den Seiten nichts springt: das Fenster bis gridUnit * 62, darüber mittig.
//
// FormCards und FormHeader direkt in topItems/leftCards/rightCards/bottomCards füllen ihre Spalte; Kirigami Addons
// begrenzt sie sonst auf eine schmale Lesebreite. Von Repeatern erzeugte Karten setzen
// `maximumWidth: Infinity` selbst.
Kirigami.ScrollablePage {
    id: page

    default property alias topItems: topColumn.data
    property alias leftCards: leftColumn.data
    property alias rightCards: rightColumn.data
    property alias bottomCards: bottomColumn.data

    // Dezente Silhouette einer Radgruppe hinter dem Seitenkopf (build-aux/make-backdrop.py), in
    // der Textfarbe des Farbschemas und mit wenig Deckkraft; nur Übersicht und Willkommen.
    property bool backdrop: false
    readonly property real columnsWidth: Kirigami.Units.gridUnit * 62
    readonly property bool wide: width > Kirigami.Units.gridUnit * 42

    function widen(column) {
        for (let i = 0; i < column.children.length; ++i) {
            const c = column.children[i]
            if (c.maximumWidth !== undefined) c.maximumWidth = Infinity
        }
    }
    Component.onCompleted: [topColumn, leftColumn, rightColumn, bottomColumn].forEach(widen)

    Item {
        implicitHeight: content.implicitHeight

        Image {
            id: backdropImage
            visible: false
            anchors { top: parent.top; horizontalCenter: parent.horizontalCenter }
            width: Math.min(parent.width, page.columnsWidth + Kirigami.Units.gridUnit * 6)
            height: topColumn.y + topColumn.height + Kirigami.Units.gridUnit * 2
            source: page.backdrop ? Qt.resolvedUrl("../../data/backdrop.png") : ""
            fillMode: Image.PreserveAspectCrop
            verticalAlignment: Image.AlignVCenter
            asynchronous: true
        }
        MultiEffect {
            visible: page.backdrop && backdropImage.status === Image.Ready
            anchors.fill: backdropImage
            source: backdropImage
            colorization: 1.0
            colorizationColor: Kirigami.Theme.textColor
            opacity: Kirigami.ColorUtils.brightnessForColor(Kirigami.Theme.backgroundColor) === Kirigami.ColorUtils.Dark
                     ? 0.07 : 0.09
        }

        ColumnLayout {
            id: content
            width: parent.width
            spacing: 0

            ColumnLayout {
                id: topColumn
                Layout.fillWidth: true
                Layout.maximumWidth: page.columnsWidth
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: Kirigami.Units.largeSpacing
                spacing: 0
            }

            GridLayout {
                Layout.fillWidth: true
                Layout.maximumWidth: page.columnsWidth
                Layout.alignment: Qt.AlignHCenter
                columns: page.wide && rightColumn.visibleChildren.length > 0 ? 2 : 1
                columnSpacing: Kirigami.Units.gridUnit
                rowSpacing: 0

                ColumnLayout {
                    id: leftColumn
                    Layout.fillWidth: true
                    Layout.preferredWidth: 1
                    Layout.alignment: Qt.AlignTop
                    spacing: 0
                }
                ColumnLayout {
                    id: rightColumn
                    Layout.fillWidth: true
                    Layout.preferredWidth: 1
                    Layout.alignment: Qt.AlignTop
                    spacing: 0
                }
            }

            ColumnLayout {
                id: bottomColumn
                Layout.fillWidth: true
                Layout.maximumWidth: page.columnsWidth
                Layout.alignment: Qt.AlignHCenter
                spacing: 0
            }

            Item { implicitHeight: Kirigami.Units.gridUnit }
        }
    }
}
