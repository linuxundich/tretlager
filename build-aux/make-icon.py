#!/usr/bin/env python3
"""Generates tretlager/data/icons/de.linuxundich.Tretlager.svg.

Motif: modern road bike crankset seen from the drive side, silver chainrings with a dark edge (the earlier,
all-dark version was barely visible on a dark panel), modelled on road cranksets with an asymmetric four-arm
spider, two chainrings and clipless pedals. Pure side view: the pedals are horizontal and sit centred on the
eye of their crank arm; the rear one lies behind the arm and the chainring.
"""
import math
from pathlib import Path

CX, CY = 24.0, 23.0
ANGLE = math.radians(15)  # front crank arm points forward, almost horizontally
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
    """Crank arm as a tapered quadrilateral with round ends."""
    nx, ny = -math.sin(a), math.cos(a)
    tx, ty = pt(length, a)
    p = [(CX + nx * w0 / 2, CY + ny * w0 / 2), (tx + nx * w1 / 2, ty + ny * w1 / 2),
         (tx - nx * w1 / 2, ty - ny * w1 / 2), (CX - nx * w0 / 2, CY - ny * w0 / 2)]
    return p, (tx, ty)


def pedal(x, y, s, body, plate, edge):
    """Clipless pedal from the side: flat wedge, nose at the front (right), steel plate on top."""
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
           '<stop offset="0" stop-color="#e3e6e9"/><stop offset="1" stop-color="#a7aeb5"/></linearGradient>',
           '  </defs>']

    # rear pedal and rear arm (non-drive side), all behind the chainrings
    rear_a = ANGLE + math.pi
    rp, rtip = arm(rear_a, CRANK, 4.4, 2.8)
    out.append('  <!-- rear pedal, centred on the arm end -->')
    out.append('  ' + pedal(rtip[0], rtip[1] - 0.2, 0.9, "#1b1e20", "#4d545b", "#000000"))
    out.append('  <!-- rear crank arm -->')
    out.append(f'  <polygon points="{f(*rp)}" fill="#232629" stroke="#232629" stroke-width="1.2" '
               'stroke-linejoin="round"/>')

    # Chainrings
    out.append('  <!-- large chainring with shadow, small ring inside -->')
    ring = gear(16.0, 15.0, 46) + " " + circle_path(10.7)
    out.append(f'  <path transform="translate(0.5 1)" d="{ring}" fill="#000" opacity="0.15" fill-rule="evenodd"/>')
    # Silver rings with a dark edge: clearly visible on dark and light panels alike
    out.append(f'  <path d="{ring}" fill="url(#ring)" stroke="#31363b" stroke-width="0.7" '
               'stroke-linejoin="round" fill-rule="evenodd"/>')
    out.append(f'  <path d="{circle_path(15.0)}" fill="none" stroke="#7f8c8d" stroke-width="0.8" opacity="0.6"/>')
    out.append(f'  <path d="{gear(11.4, 10.6, 34, 0.05)} {circle_path(8.4)}" fill="#c9ced3" stroke="#31363b" stroke-width="0.5" '
               'fill-rule="evenodd"/>')
    out.append(f'  <path d="{circle_path(10.6)}" fill="none" stroke="#7f8c8d" stroke-width="0.5" opacity="0.5"/>')

    # Spider: four wide arms; one lies under the crank arm
    out.append('  <!-- asymmetric four-arm spider -->')
    for k, off in enumerate((math.radians(80), math.radians(170), math.radians(260))):
        a = ANGLE + off
        p, tip = arm(a, 12.2, 4.6, 3.0)
        out.append(f'  <polygon points="{f(*p)}" fill="#232629" stroke="#232629" stroke-width="1.0" '
                   'stroke-linejoin="round"/>')
        bx, by = pt(11.0, a)
        out.append(f'  <circle cx="{bx:.2f}" cy="{by:.2f}" r="0.9" fill="#bdc3c7"/>')

    # front crank arm with a blue stripe
    fp, ftip = arm(ANGLE, CRANK, 6.4, 3.6)
    out.append('  <!-- front crank arm (drive side) -->')
    out.append(f'  <polygon transform="translate(0.5 1)" points="{f(*fp)}" fill="#000" opacity="0.15" '
               'stroke="#000" stroke-width="1.4" stroke-linejoin="round"/>')
    out.append(f'  <polygon points="{f(*fp)}" fill="url(#crank)" stroke="#2a2e32" stroke-width="1.4" '
               'stroke-linejoin="round"/>')
    s0, s1 = pt(6.5, ANGLE), pt(13.5, ANGLE)
    nx, ny = -math.sin(ANGLE), math.cos(ANGLE)
    out.append(f'  <line x1="{s0[0] - nx * 0.9:.2f}" y1="{s0[1] - ny * 0.9:.2f}" '
               f'x2="{s1[0] - nx * 0.6:.2f}" y2="{s1[1] - ny * 0.6:.2f}" '
               'stroke="#1d99f3" stroke-width="1.3" stroke-linecap="round"/>')

    # front pedal: centred on the crank eye, axle end as a silver dot
    out.append('  <!-- front pedal, centred on the arm end -->')
    out.append('  ' + pedal(ftip[0], ftip[1] - 0.2, 1.0, "#232629", "#bdc3c7", "#000000"))
    out.append(f'  <circle cx="{ftip[0]:.2f}" cy="{ftip[1]:.2f}" r="1.0" fill="#bdc3c7"/>')

    # Axle / crank bolt
    out.append('  <!-- axle -->')
    out.append(f'  <circle cx="{CX}" cy="{CY}" r="3.4" fill="#232629"/>')
    out.append(f'  <circle cx="{CX}" cy="{CY}" r="2.1" fill="none" stroke="#bdc3c7" stroke-width="0.8"/>')
    out.append('</svg>')
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    target = Path(__file__).resolve().parent.parent / "tretlager/data/icons/de.linuxundich.Tretlager.svg"
    target.write_text(build())
    print(target)
