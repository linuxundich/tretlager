import QtQuick
import QtQuick.Effects
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

// Shared page scaffold for all pages (modelled on the overview). Full width at the top (messages,
// header, single lists), two columns below, stacked on narrow windows, and full width again
// at the end. All pages use the same width so nothing jumps when switching between
// pages: the window width up to gridUnit * 62, centred beyond that.
//
// FormCards and FormHeaders placed directly in topItems/leftCards/rightCards/bottomCards fill their column; Kirigami Addons
// would otherwise limit them to a narrow reading width. Cards created by Repeaters set
// `maximumWidth: Infinity` themselves.
Kirigami.ScrollablePage {
    id: page

    default property alias topItems: topColumn.data
    property alias leftCards: leftColumn.data
    property alias rightCards: rightColumn.data
    property alias bottomCards: bottomColumn.data

    // Subtle silhouette of a group of cyclists behind the page header (build-aux/make-backdrop.py), in
    // the colour scheme's text colour at low opacity; only on the overview and welcome pages.
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
