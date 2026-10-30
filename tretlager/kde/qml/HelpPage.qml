import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard

// Hilfe im selben Gerüst wie die übrigen Seiten: jeder Abschnitt der Hilfe ist eine Karte.
// Die Abschnitte verteilen sich der Reihe nach auf zwei Spalten (links bis etwa zur Hälfte des
// Textes); Tabellen brauchen Platz und stehen darunter über die volle Breite.
ColumnsPage {
    id: page
    title: "Hilfe"

    readonly property var sections: {
        const parts = backend.helpText.split(/^## /m).filter(function (p) { return p.trim() !== "" })
        return parts.map(function (p) {
            const nl = p.indexOf("\n")
            return { title: p.slice(0, nl).trim(), body: p.slice(nl + 1).trim(), table: /^\|---/m.test(p) }
        })
    }
    readonly property var flowing: sections.filter(function (s) { return !s.table })
    readonly property int split: {
        const total = flowing.reduce(function (n, s) { return n + s.body.length }, 0)
        let sum = 0
        for (let i = 0; i < flowing.length; ++i) {
            sum += flowing[i].body.length
            if (sum >= total / 2) return i + 1
        }
        return flowing.length
    }

    component Section: ColumnLayout {
        required property var modelData
        Layout.fillWidth: true
        spacing: 0
        FormCard.FormHeader { title: modelData.title; maximumWidth: Infinity }
        FormCard.FormCard {
            maximumWidth: Infinity
            FormCard.AbstractFormDelegate {
                hoverEnabled: false
                focusPolicy: Qt.NoFocus
                contentItem: Controls.Label {
                    text: modelData.body
                    textFormat: Text.MarkdownText
                    wrapMode: Text.WordWrap
                    onLinkActivated: (link) => Qt.openUrlExternally(link)
                }
            }
        }
    }

    leftCards: [
        Repeater { model: page.flowing.slice(0, page.split); delegate: Section {} }
    ]
    rightCards: [
        Repeater { model: page.flowing.slice(page.split); delegate: Section {} }
    ]
    bottomCards: [
        Repeater { model: page.sections.filter(function (s) { return s.table }); delegate: Section {} }
    ]
}
