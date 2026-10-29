#!/usr/bin/env python3
"""Erzeugt tretlager/data/icons/de.linuxundich.Tretlager.svg.

Motiv: moderne Rennrad-Kurbel von der Antriebsseite (Vorbild Straßen-Kurbeln mit asymmetrischer
Vierarm-Spinne, zwei Kettenblättern und Klickpedalen). Reine Seitenansicht: Die Pedale stehen waagrecht und sitzen
mittig auf dem Auge ihres Kurbelarms; das hintere liegt hinter Arm und Kettenblatt.
"""
import math
from pathlib import Path

CX, CY = 24.0, 23.0
ANGLE = math.radians(15)  # vorderer Kurbelarm zeigt fast waagrecht nach vorn
CRANK = 16.5


def pt(r, a, cx=CX, cy=CY):
    return cx + r * math.cos(a), cy + r * math.sin(a)


def f(*xy):
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in xy)


def gear(r_tip, r_root, teeth, rot=0.0):
    pts = []
    step = 2 * math.pi / teeth
    for i in range(teeth):
        a = rot + i * step
        pts += [pt(r_root, a - step * 0.30), pt(r_tip, a - step * 0.14),
                pt(r_tip, a + step * 0.14), pt(r_root, a + step * 0.30)]
    return "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts) + " Z"


def circle_path(r):
    return (f"M{CX + r:.2f},{CY:.2f} A{r},{r} 0 1,0 {CX - r:.2f},{CY:.2f} "
            f"A{r},{r} 0 1,0 {CX + r:.2f},{CY:.2f}Z")


def arm(a, length, w0, w1):
    """Kurbelarm als verjüngtes Viereck mit runden Enden."""
    nx, ny = -math.sin(a), math.cos(a)
    tx, ty = pt(length, a)
    p = [(CX + nx * w0 / 2, CY + ny * w0 / 2), (tx + nx * w1 / 2, ty + ny * w1 / 2),
         (tx - nx * w1 / 2, ty - ny * w1 / 2), (CX - nx * w0 / 2, CY - ny * w0 / 2)]
    return p, (tx, ty)


def pedal(x, y, s, body, plate, edge):
    """Klickpedal von der Seite: flacher Keil, Nase vorn (rechts), Stahlplatte oben."""
    def P(dx, dy):
        return x + dx * s, y + dy * s
    shape = f(P(-5.4, -1.3), P(4.6, -0.9), P(5.6, -0.2), P(5.0, 0.7), P(0.0, 1.9), P(-5.0, 1.7))
    top = f(P(-4.6, -1.5), P(3.4, -1.15), P(3.4, -0.55), P(-4.6, -0.85))
    return (f'<polygon points="{shape}" fill="{body}"/>'
            f'<polygon points="{top}" fill="{plate}"/>'
            f'<polyline points="{f(P(-5.0, 1.7), P(0.0, 1.9), P(5.0, 0.7))}" fill="none" '
            f'stroke="{edge}" stroke-width="{0.5 * s:.2f}" stroke-linejoin="round"/>')


def build():
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">',
           '  <defs>',
           '    <linearGradient id="crank" x1="0" y1="0" x2="1" y2="1">'
           '<stop offset="0" stop-color="#5d6268"/><stop offset="1" stop-color="#2a2e32"/></linearGradient>',
           '    <linearGradient id="ring" x1="0" y1="0" x2="0" y2="1">'
           '<stop offset="0" stop-color="#454b51"/><stop offset="1" stop-color="#2a2e32"/></linearGradient>',
           '  </defs>']

    # hinteres Pedal und hinterer Arm (Nicht-Antriebsseite), alles hinter den Kettenblättern
    rear_a = ANGLE + math.pi
    rp, rtip = arm(rear_a, CRANK, 4.4, 2.8)
    out.append('  <!-- hinteres Pedal, mittig am Armende -->')
    out.append('  ' + pedal(rtip[0], rtip[1] - 0.2, 0.9, "#1b1e20", "#4d545b", "#000000"))
    out.append('  <!-- hinterer Kurbelarm -->')
    out.append(f'  <polygon points="{f(*rp)}" fill="#232629" stroke="#232629" stroke-width="1.2" '
               'stroke-linejoin="round"/>')

    # Kettenblätter
    out.append('  <!-- großes Kettenblatt mit Schatten, kleines Blatt innen -->')
    ring = gear(16.0, 15.0, 46) + " " + circle_path(10.7)
    out.append(f'  <path transform="translate(0.5 1)" d="{ring}" fill="#000" opacity="0.15" fill-rule="evenodd"/>')
    out.append(f'  <path d="{ring}" fill="url(#ring)" fill-rule="evenodd"/>')
    out.append(f'  <path d="{circle_path(15.0)}" fill="none" stroke="#7f8c8d" stroke-width="0.8" opacity="0.6"/>')
    out.append(f'  <path d="{gear(11.4, 10.6, 34, 0.05)} {circle_path(8.4)}" fill="#3a3f44" fill-rule="evenodd"/>')
    out.append(f'  <path d="{circle_path(10.6)}" fill="none" stroke="#7f8c8d" stroke-width="0.5" opacity="0.5"/>')

    # Spinne: vier breite Arme; einer liegt unter dem Kurbelarm
    out.append('  <!-- asymmetrische Vierarm-Spinne -->')
    for k, off in enumerate((math.radians(80), math.radians(170), math.radians(260))):
        a = ANGLE + off
        p, tip = arm(a, 12.2, 4.6, 3.0)
        out.append(f'  <polygon points="{f(*p)}" fill="#232629" stroke="#232629" stroke-width="1.0" '
                   'stroke-linejoin="round"/>')
        bx, by = pt(11.0, a)
        out.append(f'  <circle cx="{bx:.2f}" cy="{by:.2f}" r="0.9" fill="#bdc3c7"/>')

    # vorderer Kurbelarm mit blauem Streifen
    fp, ftip = arm(ANGLE, CRANK, 6.4, 3.6)
    out.append('  <!-- vorderer Kurbelarm (Antriebsseite) -->')
    out.append(f'  <polygon transform="translate(0.5 1)" points="{f(*fp)}" fill="#000" opacity="0.15" '
               'stroke="#000" stroke-width="1.4" stroke-linejoin="round"/>')
    out.append(f'  <polygon points="{f(*fp)}" fill="url(#crank)" stroke="#2a2e32" stroke-width="1.4" '
               'stroke-linejoin="round"/>')
    s0, s1 = pt(6.5, ANGLE), pt(13.5, ANGLE)
    nx, ny = -math.sin(ANGLE), math.cos(ANGLE)
    out.append(f'  <line x1="{s0[0] - nx * 0.9:.2f}" y1="{s0[1] - ny * 0.9:.2f}" '
               f'x2="{s1[0] - nx * 0.6:.2f}" y2="{s1[1] - ny * 0.6:.2f}" '
               'stroke="#1d99f3" stroke-width="1.3" stroke-linecap="round"/>')

    # vorderes Pedal: mittig auf dem Kurbelauge, Achsende als silberner Punkt
    out.append('  <!-- vorderes Pedal, mittig am Armende -->')
    out.append('  ' + pedal(ftip[0], ftip[1] - 0.2, 1.0, "#232629", "#bdc3c7", "#000000"))
    out.append(f'  <circle cx="{ftip[0]:.2f}" cy="{ftip[1]:.2f}" r="1.0" fill="#bdc3c7"/>')

    # Achse / Kurbelschraube
    out.append('  <!-- Achse -->')
    out.append(f'  <circle cx="{CX}" cy="{CY}" r="3.4" fill="#232629"/>')
    out.append(f'  <circle cx="{CX}" cy="{CY}" r="2.1" fill="none" stroke="#bdc3c7" stroke-width="0.8"/>')
    out.append('</svg>')
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    target = Path(__file__).resolve().parent.parent / "tretlager/data/icons/de.linuxundich.Tretlager.svg"
    target.write_text(build())
    print(target)
