#!/usr/bin/env python3
"""Generate KiCAD 9 PCB file for VorteX Line Follower Car — V2

Fixes:
- Write with Unix line endings (LF only) for KiCAD compatibility
- Proper escaped newlines in text strings
- Clean Edge.Cuts board outline matching chassis dimensions
"""
import uuid
import os
import math

def uid():
    return str(uuid.uuid4())

def gen_pcb():
    lines = []
    def add(text):
        lines.append(text)

    # ============================================================
    # PCB Header
    # ============================================================
    add('''(kicad_pcb
\t(version 20241229)
\t(generator "pcbnew")
\t(generator_version "9.0")
\t(general
\t\t(thickness 1.6)
\t\t(legacy_teardrops no)
\t)
\t(paper "A3")
\t(layers
\t\t(0 "F.Cu" signal)
\t\t(31 "B.Cu" signal)
\t\t(32 "B.Adhes" user "B.Adhesive")
\t\t(33 "F.Adhes" user "F.Adhesive")
\t\t(34 "B.Paste" user)
\t\t(35 "F.Paste" user)
\t\t(36 "B.SilkS" user "B.Silkscreen")
\t\t(37 "F.SilkS" user "F.Silkscreen")
\t\t(38 "B.Mask" user "B.Mask")
\t\t(39 "F.Mask" user "F.Mask")
\t\t(40 "Dwgs.User" user "User.Drawings")
\t\t(41 "Cmts.User" user "User.Comments")
\t\t(42 "B.CrtYd" user "B.Courtyard")
\t\t(43 "F.CrtYd" user "F.Courtyard")
\t\t(44 "B.Fab" user "B.Fab")
\t\t(45 "F.Fab" user "F.Fab")
\t\t(46 "User.1" user)
\t\t(47 "User.2" user)
\t)
\t(setup
\t\t(pad_to_mask_clearance 0)
\t\t(allow_soldermask_bridges_in_footprints no)
\t\t(pcbplotparams
\t\t\t(layerselection 0x00010fc_ffffffff)
\t\t\t(plot_on_all_layers_selection 0x0000000_00000000)
\t\t\t(disableapertmacros no)
\t\t\t(usegerberextensions no)
\t\t\t(usegerberattributes yes)
\t\t\t(usegerberadvancedattributes yes)
\t\t\t(creategerberjobfile yes)
\t\t\t(dashed_line_dash_ratio 12.000000)
\t\t\t(dashed_line_gap_ratio 3.000000)
\t\t\t(svgprecision 4)
\t\t\t(plotframeref no)
\t\t\t(viasonmask no)
\t\t\t(mode 1)
\t\t\t(useauxorigin no)
\t\t\t(hpglpennumber 1)
\t\t\t(hpglpenspeed 20)
\t\t\t(hpglpendiameter 15.000000)
\t\t\t(pdf_front_fp_property_popups yes)
\t\t\t(pdf_back_fp_property_popups yes)
\t\t\t(pdf_metadata yes)
\t\t\t(excludeedgelayer yes)
\t\t\t(linewidth 0.100000)
\t\t\t(plotgerberformat 1)
\t\t\t(subtractmaskfromsilk no)
\t\t\t(outputformat 1)
\t\t\t(mirror no)
\t\t\t(drillshape 1)
\t\t\t(scaleselection 1)
\t\t\t(outputdirectory "gerbers/")
\t\t)
\t)''')

    # ============================================================
    # NETS
    # ============================================================
    nets = [
        "",          # net 0 = unconnected
        "GND",
        "+3V3",
        "+5V",
        "+12V",
        "VBAT",
        "SDA",
        "SCL",
        "GPS_TX",
        "GPS_RX",
        "CAM_TX",
        "CAM_RX",
        "IN1",
        "IN2",
        "IN3",
        "IN4",
        "PWMA",
        "PWMB",
        "STBY",
        "IR1",
        "IR2",
        "IR3",
        "IR4",
        "IR5",
        "MOTOR_A+",
        "MOTOR_A-",
        "MOTOR_B+",
        "MOTOR_B-",
        "SOLAR+",
    ]

    for i, net_name in enumerate(nets):
        add(f'\t(net {i} "{net_name}")')

    # ============================================================
    # BOARD OUTLINE — Edge.Cuts
    # ============================================================
    # Chassis dimensions from reference image:
    notch_w = 14.07
    notch_h = 13.71
    top_w = 125.18
    total_h = 181.19
    bottom_w = 167.05
    left_mid_h = 65.32
    diag = 61.71
    step_w = 20.86
    step_h = 11.89
    bottom_left_h = 46.04

    # Computed values
    diag_vert = total_h - notch_h - left_mid_h - bottom_left_h  # 56.12
    lo = bottom_w - step_w - top_w  # left offset = 21.01

    # PCB origin offset
    ox, oy = 100, 50

    # Outline points (clockwise, KiCad Y-down)
    outline_pts = [
        (lo, 0),                           # Top of protrusion, left
        (lo + notch_w, 0),                 # Top of protrusion, right
        (lo + notch_w, notch_h),           # Bottom of protrusion
        (lo + top_w, notch_h),             # Top-right of main section
        (lo + top_w, notch_h + step_h),    # Step down
        (bottom_w, notch_h + step_h),      # Step right to full width
        (bottom_w, total_h),               # Bottom-right
        (0, total_h),                      # Bottom-left
        (0, total_h - bottom_left_h),      # Start of diagonal
        (lo, total_h - bottom_left_h - diag_vert),  # End of diagonal
        (lo, notch_h),                     # Top-left of main section
        (lo, 0),                           # Close loop
    ]

    for i in range(len(outline_pts) - 1):
        x1, y1 = outline_pts[i]
        x2, y2 = outline_pts[i + 1]
        add(f'''
\t(gr_line
\t\t(start {ox + x1:.2f} {oy + y1:.2f})
\t\t(end {ox + x2:.2f} {oy + y2:.2f})
\t\t(stroke (width 0.15) (type solid))
\t\t(layer "Edge.Cuts")
\t\t(uuid "{uid()}")
\t)''')

    # ============================================================
    # ZONE LABELS (on Cmts.User — single-line, no newlines)
    # ============================================================
    zone_labels = [
        ("POWER ZONE",   ox + 10,              oy + total_h - 25),
        ("CONTROL ZONE", ox + 70,              oy + 60),
        ("MOTOR ZONE",   ox + bottom_w - 40,   oy + total_h - 35),
        ("SENSOR ZONE",  ox + 70,              oy + total_h - 15),
    ]

    for text, x, y in zone_labels:
        add(f'''
\t(gr_text "{text}"
\t\t(at {x:.2f} {y:.2f})
\t\t(layer "Cmts.User")
\t\t(uuid "{uid()}")
\t\t(effects
\t\t\t(font (size 3 3) (thickness 0.3) (bold yes))
\t\t)
\t)''')

    # Title block
    add(f'''
\t(gr_text "VorteX LineFollower - Team VorteX - DJSCE - UNPLUGGED 2025 R2"
\t\t(at {ox + bottom_w / 2:.2f} {oy + total_h + 10:.2f})
\t\t(layer "Cmts.User")
\t\t(uuid "{uid()}")
\t\t(effects
\t\t\t(font (size 2 2) (thickness 0.2))
\t\t)
\t)''')

    # Design rules note
    add(f'''
\t(gr_text "Design Rules: Signal 0.3mm | Power 0.8mm | Motor 1.5mm | Clearance 0.2mm"
\t\t(at {ox + bottom_w / 2:.2f} {oy + total_h + 15:.2f})
\t\t(layer "Cmts.User")
\t\t(uuid "{uid()}")
\t\t(effects
\t\t\t(font (size 1.5 1.5) (thickness 0.15))
\t\t)
\t)''')

    # ============================================================
    # Close
    # ============================================================
    add(')')

    return '\n'.join(lines)


if __name__ == '__main__':
    pcb = gen_pcb()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "VorteX_LineFollower.kicad_pcb")
    # Write with Unix line endings (LF) — KiCAD is strict about this
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write(pcb)
    print(f"Generated PCB: {out}")
    print(f"File size: {os.path.getsize(out)} bytes")
