#!/usr/bin/env python3
"""Generate KiCAD 9 schematic for VorteX Line Follower Car — V3

Key improvements:
- BIG symbols matching ESP32 style (3.81mm pin spacing, wide body, 2.54mm pin length)
- Proper power symbols at every power pin
- NO wires drawn to no-connect pins (fixes dangling wire warnings)
- A0 paper with generous spacing
- All passives: decoupling caps, pull-up resistors, PWR_FLAGs
"""
import uuid
import os
import re

def uid():
    return str(uuid.uuid4())


def gen_schematic():
    lines = []
    root_uuid = uid()

    def add(text):
        lines.append(text)

    # ================================================================
    # HEADER
    # ================================================================
    add(f'''(kicad_sch
\t(version 20241209)
\t(generator "eeschema")
\t(generator_version "9.0")
\t(uuid "{root_uuid}")
\t(paper "A0")
\t(lib_symbols''')

    # ================================================================
    # CONNECTOR SYMBOL — ESP32-style big symbols
    # ================================================================
    PIN_SPACE = 3.81     # mm between pins (matching ESP32)
    PIN_LEN = 2.54       # pin stub length
    BODY_W = 25.4        # body width (half on each side = ±12.7)
    PIN_X = -(BODY_W / 2 + PIN_LEN)  # pin connection x = -15.24

    def add_connector_symbol(name, pin_names_list, ref_prefix="J"):
        n = len(pin_names_list)
        body_half_h = (n - 1) * PIN_SPACE / 2 + 2.54  # body extends beyond pins
        ref_y = body_half_h + 3.81
        val_y = -(body_half_h + 2.54)

        add(f'''
\t\t(symbol "{name}"
\t\t\t(pin_names (offset 1.016))
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "{ref_prefix}"
\t\t\t\t(at 0 {ref_y:.2f} 0)
\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t)
\t\t\t(property "Value" "{name}"
\t\t\t\t(at 0 {val_y:.2f} 0)
\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t)
\t\t\t(property "Footprint" ""
\t\t\t\t(at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(property "Datasheet" ""
\t\t\t\t(at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(property "Description" ""
\t\t\t\t(at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(symbol "{name}_0_1"
\t\t\t\t(rectangle
\t\t\t\t\t(start {-BODY_W / 2:.2f} {body_half_h:.2f})
\t\t\t\t\t(end {BODY_W / 2:.2f} {-body_half_h:.2f})
\t\t\t\t\t(stroke (width 0) (type default))
\t\t\t\t\t(fill (type background))
\t\t\t\t)
\t\t\t)
\t\t\t(symbol "{name}_1_1"''')
        for i, pname in enumerate(pin_names_list):
            y = (n - 1) * PIN_SPACE / 2 - i * PIN_SPACE
            add(f'''
\t\t\t\t(pin passive line
\t\t\t\t\t(at {PIN_X:.2f} {y:.2f} 0)
\t\t\t\t\t(length {PIN_LEN:.2f})
\t\t\t\t\t(name "{pname}"
\t\t\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t\t\t)
\t\t\t\t\t(number "{i + 1}"
\t\t\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t\t\t)
\t\t\t\t)''')
        add('''
\t\t\t)
\t\t)''')

    # ================================================================
    # PASSIVE SYMBOLS: Capacitor, Resistor
    # ================================================================
    add('''
\t\t(symbol "Device:C"
\t\t\t(pin_names (offset 0.254))
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "C"
\t\t\t\t(at 0.635 2.54 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (justify left))
\t\t\t)
\t\t\t(property "Value" "C"
\t\t\t\t(at 0.635 -2.54 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (justify left))
\t\t\t)
\t\t\t(property "Footprint" ""
\t\t\t\t(at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(property "Datasheet" "~"
\t\t\t\t(at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(property "Description" "Unpolarized capacitor"
\t\t\t\t(at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(symbol "C_0_1"
\t\t\t\t(polyline
\t\t\t\t\t(pts (xy -2.032 -0.762) (xy 2.032 -0.762))
\t\t\t\t\t(stroke (width 0.508) (type default))
\t\t\t\t\t(fill (type none))
\t\t\t\t)
\t\t\t\t(polyline
\t\t\t\t\t(pts (xy -2.032 0.762) (xy 2.032 0.762))
\t\t\t\t\t(stroke (width 0.508) (type default))
\t\t\t\t\t(fill (type none))
\t\t\t\t)
\t\t\t)
\t\t\t(symbol "C_1_1"
\t\t\t\t(pin passive line
\t\t\t\t\t(at 0 3.81 270)
\t\t\t\t\t(length 2.794)
\t\t\t\t\t(name "~"
\t\t\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t\t\t)
\t\t\t\t\t(number "1"
\t\t\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t\t\t)
\t\t\t\t)
\t\t\t\t(pin passive line
\t\t\t\t\t(at 0 -3.81 90)
\t\t\t\t\t(length 2.794)
\t\t\t\t\t(name "~"
\t\t\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t\t\t)
\t\t\t\t\t(number "2"
\t\t\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t\t\t)
\t\t\t\t)
\t\t\t)
\t\t)''')

    add('''
\t\t(symbol "Device:R"
\t\t\t(pin_names (offset 0))
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "R"
\t\t\t\t(at 2.032 0 90)
\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t)
\t\t\t(property "Value" "R"
\t\t\t\t(at -1.524 0 90)
\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t)
\t\t\t(property "Footprint" ""
\t\t\t\t(at -1.778 0 90)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(property "Datasheet" "~"
\t\t\t\t(at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(property "Description" "Resistor"
\t\t\t\t(at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(symbol "R_0_1"
\t\t\t\t(rectangle
\t\t\t\t\t(start -1.016 -2.54)
\t\t\t\t\t(end 1.016 2.54)
\t\t\t\t\t(stroke (width 0.254) (type default))
\t\t\t\t\t(fill (type none))
\t\t\t\t)
\t\t\t)
\t\t\t(symbol "R_1_1"
\t\t\t\t(pin passive line
\t\t\t\t\t(at 0 3.81 270)
\t\t\t\t\t(length 1.27)
\t\t\t\t\t(name "~"
\t\t\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t\t\t)
\t\t\t\t\t(number "1"
\t\t\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t\t\t)
\t\t\t\t)
\t\t\t\t(pin passive line
\t\t\t\t\t(at 0 -3.81 90)
\t\t\t\t\t(length 1.27)
\t\t\t\t\t(name "~"
\t\t\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t\t\t)
\t\t\t\t\t(number "2"
\t\t\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t\t\t)
\t\t\t\t)
\t\t\t)
\t\t)''')

    # ================================================================
    # POWER SYMBOLS: PWR_FLAG, GND, +3V3, +5V, +12V, VBAT
    # ================================================================
    add('''
\t\t(symbol "power:PWR_FLAG"
\t\t\t(power)
\t\t\t(pin_names (offset 0))
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "#FLG"
\t\t\t\t(at 0 1.905 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(property "Value" "PWR_FLAG"
\t\t\t\t(at 0 3.81 0)
\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t)
\t\t\t(property "Footprint" ""
\t\t\t\t(at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(property "Datasheet" "~"
\t\t\t\t(at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(property "Description" "Special symbol for power flag"
\t\t\t\t(at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(symbol "PWR_FLAG_0_0"
\t\t\t\t(pin power_in line
\t\t\t\t\t(at 0 0 90)
\t\t\t\t\t(length 0)
\t\t\t\t\t(name "pwr"
\t\t\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t\t\t)
\t\t\t\t\t(number "1"
\t\t\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t\t\t)
\t\t\t\t)
\t\t\t)
\t\t\t(symbol "PWR_FLAG_0_1"
\t\t\t\t(polyline
\t\t\t\t\t(pts (xy 0 0) (xy 0 1.27) (xy -1.016 1.905) (xy 0 2.54) (xy 1.016 1.905) (xy 0 1.27))
\t\t\t\t\t(stroke (width 0) (type default))
\t\t\t\t\t(fill (type none))
\t\t\t\t)
\t\t\t)
\t\t)''')

    def add_vcc_symbol(name):
        add(f'''
\t\t(symbol "power:{name}"
\t\t\t(power)
\t\t\t(pin_names (offset 0))
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "#PWR"
\t\t\t\t(at 0 -3.81 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(property "Value" "{name}"
\t\t\t\t(at 0 3.81 0)
\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t)
\t\t\t(property "Footprint" ""
\t\t\t\t(at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(property "Datasheet" ""
\t\t\t\t(at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(property "Description" "Power symbol {name}"
\t\t\t\t(at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(symbol "{name}_0_1"
\t\t\t\t(polyline
\t\t\t\t\t(pts (xy -0.762 1.27) (xy 0 2.54))
\t\t\t\t\t(stroke (width 0) (type default))
\t\t\t\t\t(fill (type none))
\t\t\t\t)
\t\t\t\t(polyline
\t\t\t\t\t(pts (xy 0 0) (xy 0 1.27))
\t\t\t\t\t(stroke (width 0) (type default))
\t\t\t\t\t(fill (type none))
\t\t\t\t)
\t\t\t\t(polyline
\t\t\t\t\t(pts (xy 0.762 1.27) (xy 0 2.54))
\t\t\t\t\t(stroke (width 0) (type default))
\t\t\t\t\t(fill (type none))
\t\t\t\t)
\t\t\t)
\t\t\t(symbol "{name}_1_1"
\t\t\t\t(pin power_in line
\t\t\t\t\t(at 0 0 90)
\t\t\t\t\t(length 0)
\t\t\t\t\t(name "{name}"
\t\t\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t\t\t)
\t\t\t\t\t(number "1"
\t\t\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t\t\t)
\t\t\t\t)
\t\t\t)
\t\t)''')

    add('''
\t\t(symbol "power:GND"
\t\t\t(power)
\t\t\t(pin_names (offset 0))
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "#PWR"
\t\t\t\t(at 0 -6.35 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(property "Value" "GND"
\t\t\t\t(at 0 -3.81 0)
\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t)
\t\t\t(property "Footprint" ""
\t\t\t\t(at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(property "Datasheet" ""
\t\t\t\t(at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(property "Description" "Power symbol GND"
\t\t\t\t(at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t\t)
\t\t\t(symbol "GND_0_1"
\t\t\t\t(polyline
\t\t\t\t\t(pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27))
\t\t\t\t\t(stroke (width 0) (type default))
\t\t\t\t\t(fill (type none))
\t\t\t\t)
\t\t\t)
\t\t\t(symbol "GND_1_1"
\t\t\t\t(pin power_in line
\t\t\t\t\t(at 0 0 270)
\t\t\t\t\t(length 0)
\t\t\t\t\t(name "GND"
\t\t\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t\t\t)
\t\t\t\t\t(number "1"
\t\t\t\t\t\t(effects (font (size 1.27 1.27)))
\t\t\t\t\t)
\t\t\t\t)
\t\t\t)
\t\t)''')

    add_vcc_symbol("+3V3")
    add_vcc_symbol("+5V")
    add_vcc_symbol("+12V")
    add_vcc_symbol("VBAT")

    # ================================================================
    # ADD ALL LIB SYMBOLS
    # ================================================================

    # --- ESP32 from file ---
    esp32_sym_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "libs", "ESP32_DEVKITV1.kicad_sym")
    with open(esp32_sym_path, 'r') as f:
        esp_content = f.read()
    sym_match = re.search(
        r'(\(symbol "ESP32_DEVKITV1".*?\n\t\))\s*\)', esp_content, re.DOTALL)
    if sym_match:
        esp_sym = sym_match.group(1)
        for line in esp_sym.split('\n'):
            add('\t\t' + line.rstrip('\r'))

    # Connector symbols with named pins
    add_connector_symbol("TP4056_Module",
                         ["IN+", "IN-", "BAT+", "BAT-", "STDBY", "CHRG"], "U")
    add_connector_symbol("LM2596_Module",
                         ["IN+", "IN-", "OUT+", "OUT-", "EN"], "U")
    add_connector_symbol("TB6612_Module",
                         ["VM", "VCC", "GND", "AO1", "AO2", "BO1", "BO2",
                          "PWMA", "AIN1", "AIN2", "STBY", "BIN1", "BIN2",
                          "PWMB", "GND2", "GND3"], "U")
    add_connector_symbol("NEO6M_GPS",
                         ["VCC", "GND", "TX", "RX", "SDA", "SCL"], "J")
    add_connector_symbol("OLED_I2C",
                         ["GND", "VCC", "SCL", "SDA"], "J")
    add_connector_symbol("ESP32_CAM",
                         ["5V", "GND", "TX", "RX", "IO0", "IO2", "IO4",
                          "IO12", "IO13", "IO14", "IO15", "IO16",
                          "GND2", "3V3", "VCC", "GND3"], "U")
    add_connector_symbol("Conn_2Pin",
                         ["Pin_1", "Pin_2"], "J")
    add_connector_symbol("IR_Sensor",
                         ["VCC", "GND", "OUT"], "J")

    add('\t)')  # close lib_symbols

    # ================================================================
    # PLACEMENT HELPERS
    # ================================================================

    pwr_n = [0]

    def next_pwr():
        pwr_n[0] += 1
        return f"#PWR{pwr_n[0]:03d}"

    flg_n = [0]

    def next_flg():
        flg_n[0] += 1
        return f"#FLG{flg_n[0]:02d}"

    def place_symbol(lib_id, ref, value, x, y, footprint="", rotation=0):
        u = uid()
        is_power = lib_id.startswith("power:")
        fp_prop = ""
        if footprint:
            fp_prop = f'''
\t\t(property "Footprint" "{footprint}"
\t\t\t(at {x:.2f} {y:.2f} 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)'''

        add(f'''
\t(symbol
\t\t(lib_id "{lib_id}")
\t\t(at {x:.2f} {y:.2f} {rotation})
\t\t(uuid "{u}")
\t\t(property "Reference" "{ref}"
\t\t\t(at {x + 3:.2f} {y - 3:.2f} 0)
\t\t\t(effects (font (size 1.27 1.27)){" (hide yes)" if is_power else ""})
\t\t)
\t\t(property "Value" "{value}"
\t\t\t(at {x + 3:.2f} {y + 3:.2f} 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t){fp_prop}
\t\t(instances
\t\t\t(project "VorteX_LineFollower"
\t\t\t\t(path "/{root_uuid}"
\t\t\t\t\t(reference "{ref}")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)''')
        return u

    def wire(x1, y1, x2, y2):
        add(f'''
\t(wire
\t\t(pts (xy {x1:.2f} {y1:.2f}) (xy {x2:.2f} {y2:.2f}))
\t\t(stroke (width 0) (type default))
\t\t(uuid "{uid()}")
\t)''')

    def label(name, x, y, angle=0):
        add(f'''
\t(label "{name}"
\t\t(at {x:.2f} {y:.2f} {angle})
\t\t(effects
\t\t\t(font (size 1.27 1.27))
\t\t\t(justify left)
\t\t)
\t\t(uuid "{uid()}")
\t)''')

    def no_connect(x, y):
        add(f'''
\t(no_connect
\t\t(at {x:.2f} {y:.2f})
\t\t(uuid "{uid()}")
\t)''')

    def text_note(text, x, y, size=3.5):
        add(f'''
\t(text "{text}"
\t\t(at {x:.2f} {y:.2f} 0)
\t\t(effects
\t\t\t(font (size {size} {size}) (bold yes))
\t\t\t(justify left)
\t\t)
\t\t(uuid "{uid()}")
\t)''')

    # ================================================================
    # CONNECTOR PIN CALCULATOR
    # ================================================================

    def conn_pin_xy(sx, sy, pin_idx, num_pins):
        """Pin connection point for our custom connector symbols.
        pin_idx is 0-based. Symbol placed at (sx, sy).
        In symbol coords: pin at (PIN_X, y_off) where y_off = (N-1)*PIN_SPACE/2 - i*PIN_SPACE
        In schematic: (sx + PIN_X, sy - y_off)  [Y inverted]
        """
        y_off = (num_pins - 1) * PIN_SPACE / 2 - pin_idx * PIN_SPACE
        return (sx + PIN_X, sy - y_off)

    # ================================================================
    # ESP32 PIN CALCULATOR (from actual .kicad_sym)
    # ================================================================

    ESP32_PINS = {
        # pin_num: (x_off, y_off, name, side)
        # Left side (direction 0)
        1:  (-19.05,  19.05, "EN",  "L"),
        2:  (-19.05,  15.24, "VP",  "L"),
        3:  (-19.05,  11.43, "VN",  "L"),
        4:  (-19.05,   7.62, "D34", "L"),
        5:  (-19.05,   3.81, "D35", "L"),
        6:  (-19.05,   0.00, "D32", "L"),
        7:  (-19.05,  -3.81, "D33", "L"),
        8:  (-19.05,  -7.62, "D25", "L"),
        9:  (-19.05, -11.43, "D26", "L"),
        10: (-19.05, -15.24, "D27", "L"),
        11: (-19.05, -19.05, "D14", "L"),
        12: (-19.05, -22.86, "D12", "L"),
        13: (-19.05, -26.67, "D13", "L"),
        # Bottom (direction 90)
        14: (-7.62, -36.83, "GND", "B"),
        15: (-2.54, -36.83, "VIN", "B"),
        16: ( 3.81, -36.83, "3V3", "B"),
        17: ( 8.89, -36.83, "GND", "B"),
        # Right side (direction 180)
        30: (20.32,  19.05, "D23", "R"),
        29: (20.32,  15.24, "D22", "R"),
        28: (20.32,  11.43, "TX0", "R"),
        27: (20.32,   7.62, "RX0", "R"),
        26: (20.32,   3.81, "D21", "R"),
        25: (20.32,   0.00, "D19", "R"),
        24: (20.32,  -3.81, "D18", "R"),
        23: (20.32,  -7.62, "D5",  "R"),
        22: (20.32, -11.43, "TX2", "R"),
        21: (20.32, -15.24, "RX2", "R"),
        20: (20.32, -19.05, "D4",  "R"),
        19: (20.32, -22.86, "D2",  "R"),
        18: (20.32, -26.67, "D15", "R"),
    }

    def esp_pin(sx, sy, pin_num):
        xo, yo, _, _ = ESP32_PINS[pin_num]
        return (sx + xo, sy - yo)

    # ================================================================
    # HELPER: connect a connector pin to a power symbol or label
    # ================================================================

    def connect_power(px, py, net_name, wire_len=15.24):
        """Draw wire from pin and place power symbol at end."""
        wx = px - wire_len
        wire(px, py, wx, py)
        ref = next_pwr()
        if net_name == "GND":
            place_symbol("power:GND", ref, "GND", wx, py)
        else:
            place_symbol(f"power:{net_name}", ref, net_name, wx, py)

    def connect_label(px, py, net_name, wire_len=15.24):
        """Draw wire from pin and place net label at end."""
        wx = px - wire_len
        wire(px, py, wx, py)
        label(net_name, wx, py, 180)

    def connect_nc(px, py):
        """Place no-connect directly on pin. NO wire drawn."""
        no_connect(px, py)

    # ================================================================
    # DECOUPLING CAP HELPER
    # ================================================================

    cap_n = [0]

    def decap(x, y, value, pwr_name):
        cap_n[0] += 1
        place_symbol("Device:C", f"C{cap_n[0]}", value, x, y,
                     "Capacitor_SMD:C_0805_2012Metric")
        # Pin 1 (top, y-3.81) → power
        wire(x, y - 3.81, x, y - 7.62)
        place_symbol(f"power:{pwr_name}", next_pwr(), pwr_name, x, y - 7.62)
        # Pin 2 (bottom, y+3.81) → GND
        wire(x, y + 3.81, x, y + 7.62)
        place_symbol("power:GND", next_pwr(), "GND", x, y + 7.62)

    # ================================================================
    #
    #                    S C H E M A T I C   L A Y O U T
    #
    #  A0 paper = 1189 × 841 mm
    #  Layout:
    #    ┌────────────────┬──────────────────┬──────────────────┐
    #    │  POWER SUPPLY  │  ESP32 CONTROL   │  MOTOR DRIVER    │
    #    │  (50-340)      │  (400-700)       │  (750-1100)      │
    #    │  y: 60-420     │  y: 60-420       │  y: 60-420       │
    #    ├────────────────┴──────────────────┴──────────────────┤
    #    │              PERIPHERALS + IR SENSORS                │
    #    │              y: 450-800                              │
    #    └─────────────────────────────────────────────────────┘
    #
    # ================================================================

    # =============================================
    #  ZONE 1: POWER SUPPLY (50-340, 60-420)
    # =============================================
    text_note("═══ POWER SUPPLY ═══", 50, 55, 5)

    # --- Solar Panel ---
    sol_x, sol_y = 120, 130
    text_note("Solar Panel", sol_x - 15, sol_y - 20)
    place_symbol("Conn_2Pin", "J1", "Solar_Panel", sol_x, sol_y,
                 "TerminalBlock:TerminalBlock_bornier-2_P5.08mm")
    # 2 pins: Pin_1 → SOLAR+, Pin_2 → GND
    px, py = conn_pin_xy(sol_x, sol_y, 0, 2)  # Pin_1
    connect_label(px, py, "SOLAR+")
    px, py = conn_pin_xy(sol_x, sol_y, 1, 2)  # Pin_2
    connect_power(px, py, "GND")

    # --- TP4056 Charger ---
    tp_x, tp_y = 280, 140
    text_note("TP4056 Charger", tp_x - 15, tp_y - 30)
    place_symbol("TP4056_Module", "U2", "TP4056", tp_x, tp_y,
                 "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical")
    # 6 pins: IN+, IN-, BAT+, BAT-, STDBY, CHRG
    tp_connections = [
        ("SOLAR+", "label"),   # IN+
        ("GND", "power"),      # IN-
        ("VBAT", "power"),     # BAT+
        ("GND", "power"),      # BAT-
        (None, "nc"),          # STDBY
        (None, "nc"),          # CHRG
    ]
    for i, (net, ntype) in enumerate(tp_connections):
        px, py = conn_pin_xy(tp_x, tp_y, i, 6)
        if ntype == "power":
            connect_power(px, py, net)
        elif ntype == "label":
            connect_label(px, py, net)
        else:
            connect_nc(px, py)

    # --- Battery Holder ---
    bat_x, bat_y = 120, 280
    text_note("18650 Battery", bat_x - 15, bat_y - 20)
    place_symbol("Conn_2Pin", "BT1", "18650", bat_x, bat_y,
                 "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical")
    px, py = conn_pin_xy(bat_x, bat_y, 0, 2)  # Pin_1 → VBAT
    connect_power(px, py, "VBAT")
    px, py = conn_pin_xy(bat_x, bat_y, 1, 2)  # Pin_2 → GND
    connect_power(px, py, "GND")

    # --- LM2596 Buck #1 → 5V ---
    bk1_x, bk1_y = 280, 280
    text_note("LM2596 → 5V", bk1_x - 15, bk1_y - 28)
    place_symbol("LM2596_Module", "U3", "LM2596_5V", bk1_x, bk1_y,
                 "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical")
    bk1_conns = [
        ("VBAT", "power"),   # IN+
        ("GND", "power"),    # IN-
        ("+5V", "power"),    # OUT+
        ("GND", "power"),    # OUT-
        (None, "nc"),        # EN (tie high internally on module)
    ]
    for i, (net, ntype) in enumerate(bk1_conns):
        px, py = conn_pin_xy(bk1_x, bk1_y, i, 5)
        if ntype == "power":
            connect_power(px, py, net)
        else:
            connect_nc(px, py)

    # --- LM2596 Buck #2 → 3.3V ---
    bk2_x, bk2_y = 280, 400
    text_note("LM2596 → 3.3V", bk2_x - 15, bk2_y - 28)
    place_symbol("LM2596_Module", "U4", "LM2596_3V3", bk2_x, bk2_y,
                 "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical")
    bk2_conns = [
        ("VBAT", "power"),   # IN+
        ("GND", "power"),    # IN-
        ("+3V3", "power"),   # OUT+
        ("GND", "power"),    # OUT-
        (None, "nc"),        # EN
    ]
    for i, (net, ntype) in enumerate(bk2_conns):
        px, py = conn_pin_xy(bk2_x, bk2_y, i, 5)
        if ntype == "power":
            connect_power(px, py, net)
        else:
            connect_nc(px, py)

    # --- Bulk Decoupling Caps ---
    text_note("Bulk Caps", 90, 455)
    decap(100, 490, "10uF", "+5V")
    decap(140, 490, "10uF", "+3V3")
    decap(180, 490, "10uF", "VBAT")

    # --- PWR_FLAGs ---
    text_note("Power Flags", 80, 545)
    flag_nets = ["+5V", "+3V3", "GND", "VBAT", "+12V"]
    for fi, fn in enumerate(flag_nets):
        fx = 100 + fi * 50
        fy = 580
        if fn == "GND":
            # GND: place GND symbol below, PWR_FLAG above, wire between
            place_symbol("power:GND", next_pwr(), "GND", fx, fy + 7.62)
            wire(fx, fy, fx, fy + 7.62)
            place_symbol("power:PWR_FLAG", next_flg(), "PWR_FLAG", fx, fy)
        else:
            # VCC types: place VCC above, PWR_FLAG below, wire between
            place_symbol(f"power:{fn}", next_pwr(), fn, fx, fy)
            wire(fx, fy, fx, fy + 7.62)
            place_symbol("power:PWR_FLAG", next_flg(), "PWR_FLAG", fx, fy + 7.62)

    # =============================================
    #  ZONE 2: ESP32 CONTROL (400-700, 60-420)
    # =============================================
    text_note("═══ MAIN CONTROLLER — ESP32 ═══", 400, 55, 5)

    esp_x, esp_y = 550, 230
    place_symbol("ESP32_DEVKITV1", "U1", "ESP32_DEVKITV1", esp_x, esp_y,
                 "esp32devkitv1:ESP32DEVIKITV1")

    WIRE_L = 15.24  # wire length from pin

    # --- LEFT SIDE ---
    for pnum, assignment in [
        (1,  ("nc", None)),
        (2,  ("nc", None)),
        (3,  ("nc", None)),
        (4,  ("label", "IR1")),
        (5,  ("label", "IR2")),
        (6,  ("label", "IR3")),
        (7,  ("label", "STBY")),
        (8,  ("label", "IN1")),
        (9,  ("label", "IN2")),
        (10, ("label", "PWMA")),
        (11, ("label", "IN3")),
        (12, ("label", "IN4")),
        (13, ("label", "PWMB")),
    ]:
        px, py = esp_pin(esp_x, esp_y, pnum)
        atype, anet = assignment
        if atype == "nc":
            no_connect(px, py)
        elif atype == "label":
            wire(px, py, px - WIRE_L, py)
            label(anet, px - WIRE_L, py, 180)

    # --- BOTTOM ---
    # Pin 14: GND
    px, py = esp_pin(esp_x, esp_y, 14)
    wire(px, py, px, py + 7.62)
    place_symbol("power:GND", next_pwr(), "GND", px, py + 7.62)

    # Pin 15: VIN → +5V
    px, py = esp_pin(esp_x, esp_y, 15)
    wire(px, py, px, py + 7.62)
    # +5V symbol: pin at (0,0,90) pointing up. Place below wire, arrow points up.
    # We need the connection at (px, py+7.62). The +5V pin is at origin, so place at that point.
    # Use rotation=180 so the arrow points downward visually (into the ESP32).
    # Actually, let's just place it, connection point is always at placed coords.
    place_symbol("power:+5V", next_pwr(), "+5V", px, py + 7.62)

    # Pin 16: 3V3 → +3V3
    px, py = esp_pin(esp_x, esp_y, 16)
    wire(px, py, px, py + 7.62)
    place_symbol("power:+3V3", next_pwr(), "+3V3", px, py + 7.62)

    # Pin 17: GND
    px, py = esp_pin(esp_x, esp_y, 17)
    wire(px, py, px, py + 7.62)
    place_symbol("power:GND", next_pwr(), "GND", px, py + 7.62)

    # --- RIGHT SIDE ---
    for pnum, assignment in [
        (30, ("nc", None)),          # D23 spare
        (29, ("label", "SCL")),      # D22 → SCL
        (28, ("label", "CAM_RX")),   # TX0 → CAM_RX (cross)
        (27, ("label", "CAM_TX")),   # RX0 → CAM_TX (cross)
        (26, ("label", "SDA")),      # D21 → SDA
        (25, ("label", "IR4")),      # D19 → IR4
        (24, ("label", "IR5")),      # D18 → IR5
        (23, ("nc", None)),          # D5 spare
        (22, ("label", "GPS_RX")),   # TX2 → GPS module RX
        (21, ("label", "GPS_TX")),   # RX2 ← GPS module TX
        (20, ("nc", None)),          # D4 spare
        (19, ("nc", None)),          # D2 spare
        (18, ("nc", None)),          # D15 spare
    ]:
        px, py = esp_pin(esp_x, esp_y, pnum)
        atype, anet = assignment
        if atype == "nc":
            no_connect(px, py)
        elif atype == "label":
            wire(px, py, px + WIRE_L, py)
            label(anet, px + WIRE_L, py)

    # --- Decoupling caps near ESP32 ---
    decap(esp_x - 45, esp_y + 55, "100nF", "+3V3")
    decap(esp_x - 25, esp_y + 55, "100nF", "+5V")

    # --- I2C Pull-ups ---
    text_note("I2C Pull-ups", esp_x + 48, esp_y - 65)

    rx1, ry1 = esp_x + 55, esp_y - 45
    place_symbol("Device:R", "R1", "4.7k", rx1, ry1,
                 "Resistor_SMD:R_0805_2012Metric")
    wire(rx1, ry1 - 3.81, rx1, ry1 - 10.16)
    place_symbol("power:+3V3", next_pwr(), "+3V3", rx1, ry1 - 10.16)
    wire(rx1, ry1 + 3.81, rx1, ry1 + 10.16)
    label("SCL", rx1, ry1 + 10.16)

    rx2, ry2 = esp_x + 75, esp_y - 45
    place_symbol("Device:R", "R2", "4.7k", rx2, ry2,
                 "Resistor_SMD:R_0805_2012Metric")
    wire(rx2, ry2 - 3.81, rx2, ry2 - 10.16)
    place_symbol("power:+3V3", next_pwr(), "+3V3", rx2, ry2 - 10.16)
    wire(rx2, ry2 + 3.81, rx2, ry2 + 10.16)
    label("SDA", rx2, ry2 + 10.16)

    # --- STBY Pull-up ---
    text_note("STBY Pull-up", esp_x - 75, esp_y - 45)

    rx3, ry3 = esp_x - 60, esp_y - 25
    place_symbol("Device:R", "R3", "10k", rx3, ry3,
                 "Resistor_SMD:R_0805_2012Metric")
    wire(rx3, ry3 - 3.81, rx3, ry3 - 10.16)
    place_symbol("power:+5V", next_pwr(), "+5V", rx3, ry3 - 10.16)
    wire(rx3, ry3 + 3.81, rx3, ry3 + 10.16)
    label("STBY", rx3, ry3 + 10.16)

    # =============================================
    #  ZONE 3: MOTOR DRIVER (750-1100, 60-420)
    # =============================================
    text_note("═══ MOTOR DRIVER — TB6612FNG ═══", 750, 55, 5)

    tb_x, tb_y = 900, 230
    place_symbol("TB6612_Module", "U5", "TB6612FNG", tb_x, tb_y,
                 "Connector_PinHeader_2.54mm:PinHeader_2x08_P2.54mm_Vertical")

    tb_pin_defs = [
        ("+12V", "power"),   # VM
        ("+5V",  "power"),   # VCC
        ("GND",  "power"),   # GND
        ("MOTOR_A+", "label"),  # AO1
        ("MOTOR_A-", "label"),  # AO2
        ("MOTOR_B+", "label"),  # BO1
        ("MOTOR_B-", "label"),  # BO2
        ("PWMA",  "label"),  # PWMA
        ("IN1",   "label"),  # AIN1
        ("IN2",   "label"),  # AIN2
        ("STBY",  "label"),  # STBY
        ("IN3",   "label"),  # BIN1
        ("IN4",   "label"),  # BIN2
        ("PWMB",  "label"),  # PWMB
        ("GND",   "power"),  # GND2
        ("GND",   "power"),  # GND3
    ]

    for i, (net, ntype) in enumerate(tb_pin_defs):
        px, py = conn_pin_xy(tb_x, tb_y, i, 16)
        if ntype == "power":
            connect_power(px, py, net)
        else:
            connect_label(px, py, net)

    # TB6612 decoupling caps
    decap(tb_x + 30, tb_y - 40, "100nF", "+5V")
    decap(tb_x + 55, tb_y - 40, "100nF", "+12V")

    # --- 12V Input connector ---
    v12_x, v12_y = 1060, 110
    text_note("12V Motor Supply", v12_x - 20, v12_y - 20)
    place_symbol("Conn_2Pin", "J2", "12V_Input", v12_x, v12_y,
                 "TerminalBlock:TerminalBlock_bornier-2_P5.08mm")
    px, py = conn_pin_xy(v12_x, v12_y, 0, 2)
    connect_power(px, py, "+12V")
    px, py = conn_pin_xy(v12_x, v12_y, 1, 2)
    connect_power(px, py, "GND")

    # --- Motor A connector ---
    ma_x, ma_y = 1060, 230
    text_note("Motor A", ma_x - 10, ma_y - 18)
    place_symbol("Conn_2Pin", "J3", "Motor_A", ma_x, ma_y,
                 "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical")
    px, py = conn_pin_xy(ma_x, ma_y, 0, 2)
    connect_label(px, py, "MOTOR_A+")
    px, py = conn_pin_xy(ma_x, ma_y, 1, 2)
    connect_label(px, py, "MOTOR_A-")

    # --- Motor B connector ---
    mb_x, mb_y = 1060, 340
    text_note("Motor B", mb_x - 10, mb_y - 18)
    place_symbol("Conn_2Pin", "J4", "Motor_B", mb_x, mb_y,
                 "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical")
    px, py = conn_pin_xy(mb_x, mb_y, 0, 2)
    connect_label(px, py, "MOTOR_B+")
    px, py = conn_pin_xy(mb_x, mb_y, 1, 2)
    connect_label(px, py, "MOTOR_B-")

    # =============================================
    #  ZONE 4: PERIPHERALS (50-700, 450-800)
    # =============================================
    text_note("═══ PERIPHERALS ═══", 50, 640, 5)

    # --- OLED Display ---
    oled_x, oled_y = 180, 730
    text_note("OLED I2C Display", oled_x - 15, oled_y - 28)
    place_symbol("OLED_I2C", "J5", "OLED_0.96", oled_x, oled_y,
                 "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical")
    oled_conns = [
        ("GND",  "power"),   # GND
        ("+3V3", "power"),   # VCC
        ("SCL",  "label"),   # SCL
        ("SDA",  "label"),   # SDA
    ]
    for i, (net, ntype) in enumerate(oled_conns):
        px, py = conn_pin_xy(oled_x, oled_y, i, 4)
        if ntype == "power":
            connect_power(px, py, net)
        else:
            connect_label(px, py, net)
    decap(oled_x + 20, oled_y, "100nF", "+3V3")

    # --- GPS NEO-6M ---
    gps_x, gps_y = 400, 730
    text_note("NEO-6M GPS", gps_x - 15, gps_y - 30)
    place_symbol("NEO6M_GPS", "J6", "NEO-6M", gps_x, gps_y,
                 "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical")
    gps_conns = [
        ("+3V3", "power"),    # VCC
        ("GND",  "power"),    # GND
        ("GPS_TX", "label"),  # TX
        ("GPS_RX", "label"),  # RX
        (None, "nc"),         # SDA (unused)
        (None, "nc"),         # SCL (unused)
    ]
    for i, (net, ntype) in enumerate(gps_conns):
        px, py = conn_pin_xy(gps_x, gps_y, i, 6)
        if ntype == "power":
            connect_power(px, py, net)
        elif ntype == "label":
            connect_label(px, py, net)
        else:
            connect_nc(px, py)
    decap(gps_x + 20, gps_y, "100nF", "+3V3")

    # --- ESP32-CAM ---
    cam_x, cam_y = 650, 730
    text_note("ESP32-CAM Module", cam_x - 15, cam_y - 42)
    place_symbol("ESP32_CAM", "U6", "ESP32-CAM", cam_x, cam_y,
                 "Connector_PinHeader_2.54mm:PinHeader_2x08_P2.54mm_Vertical")
    # 16 pins
    cam_conns = [
        ("+5V",    "power"),   # 5V
        ("GND",    "power"),   # GND
        ("CAM_TX", "label"),   # TX
        ("CAM_RX", "label"),   # RX
        (None, "nc"),  # IO0
        (None, "nc"),  # IO2
        (None, "nc"),  # IO4
        (None, "nc"),  # IO12
        (None, "nc"),  # IO13
        (None, "nc"),  # IO14
        (None, "nc"),  # IO15
        (None, "nc"),  # IO16
        ("GND",  "power"),  # GND2
        ("+3V3", "power"),  # 3V3
        ("+5V",  "power"),  # VCC
        ("GND",  "power"),  # GND3
    ]
    for i, (net, ntype) in enumerate(cam_conns):
        px, py = conn_pin_xy(cam_x, cam_y, i, 16)
        if ntype == "power":
            connect_power(px, py, net)
        elif ntype == "label":
            connect_label(px, py, net)
        else:
            connect_nc(px, py)
    decap(cam_x + 25, cam_y - 25, "100nF", "+5V")

    # =============================================
    #  ZONE 5: IR SENSOR ARRAY (750-1100, 500-800)
    # =============================================
    text_note("═══ IR SENSOR ARRAY (5x) ═══", 750, 640, 5)

    ir_signals = ["IR1", "IR2", "IR3", "IR4", "IR5"]
    for idx, sig in enumerate(ir_signals):
        ix = 830 + idx * 65
        iy = 730
        ref = f"J{7 + idx}"
        place_symbol("IR_Sensor", ref, f"IR_{idx + 1}", ix, iy,
                     "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical")
        # 3 pins: VCC, GND, OUT
        ir_conns = [
            ("+5V", "power"),
            ("GND", "power"),
            (sig,   "label"),
        ]
        for i, (net, ntype) in enumerate(ir_conns):
            px, py = conn_pin_xy(ix, iy, i, 3)
            if ntype == "power":
                connect_power(px, py, net)
            else:
                connect_label(px, py, net)

    # ================================================================
    # CLOSE SCHEMATIC
    # ================================================================
    add(f'''
\t(sheet_instances
\t\t(path "/"
\t\t\t(page "1")
\t\t)
\t)
)''')

    return '\n'.join(lines)


if __name__ == '__main__':
    sch = gen_schematic()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "VorteX_LineFollower.kicad_sch")
    with open(out, 'w', encoding='utf-8') as f:
        f.write(sch)
    print(f"Generated schematic: {out}")
    print(f"File size: {os.path.getsize(out)} bytes")
