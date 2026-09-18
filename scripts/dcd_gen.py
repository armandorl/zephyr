#!/usr/bin/env python3
import struct

# ------------------------------------------------------------
# DCD command builders
# ------------------------------------------------------------

def write_data(address, value, params=0x14):
    """
    Build a WriteData command (TAG = 0xCC)
    Length is always 0x000C for 1 address/value pair.
    """
    tag = 0xCC
    length = 0x000C
    return struct.pack(">BHB", tag, length, params) + \
           struct.pack(">I", address) + \
           struct.pack(">I", value)


def check_data(address, mask, params=0x14, counter=0):
    """
    Build a CheckData command (TAG = 0xCF)
    Length depends on the counter.
    """
    tag = 0xCF
    if counter != 0:
        length = 0x0010
    else:
        length = 0x000C
    pack = struct.pack(">BHB", tag, length, params) + \
           struct.pack(">I", address) + \
           struct.pack(">I", mask)

    if counter != 0:
        struct.pack(">I", counter)

    return pack



# ------------------------------------------------------------
# Build full DCD
# ------------------------------------------------------------

def build_dcd(commands):
    """
    Build full DCD binary:
    - Header (TAG=D2, length, version=0x60)
    - Commands
    - IV (12 bytes)
    - GMAC (16 bytes)
    """
    dcd_data = b"".join(commands)

    # Header length = header(4 bytes) + commands length
    header_length = 4 + len(dcd_data)

    header = struct.pack(">BHB", 0xD2, header_length, 0x60)

    # Dummy IV + GMAC (ROM will verify)
    #iv = b"\x00" * 12
    #gmac = b"\x00" * 16

    return header + dcd_data


# ------------------------------------------------------------
# Example: your commands
# ------------------------------------------------------------
commands = [

    # GPIO 6 (Blue LED)
    write_data(0x4009C258,0x0021C000),
    # 1 byte write
    write_data(0x4009D305,0x00000001,params=0x11),

    # GPIO 7 (Red LED)
    write_data(0x4009C25C,0x0021C000),
    # 1 byte write
    write_data(0x4009D304,0x00000001, params=0x11),

    # GPIO 95 (Green LED)
    write_data(0x4009C3BC,0x0021C000),
    # 1 byte write (Low will turn On the LED on the S32G274ARDB)
    write_data(0x4009D35C,0x00000000, params=0x11),

    # VDD EFUSE Disable
    write_data(0x4009C2A4, 0x0021C000, params=0x14),
    write_data(0x4009D31A, 0x00000000, params=0x11),

    # QSPI INT B Disable high
    write_data(0x4009CAFC, 0x00000000, params=0x14),
    
    # GPIO 49 disabled
    write_data(0x4009C304, 0x00010000, params=0x14),

    # QSPI Int A b disable high and MCSR GPIO94 disabled
    write_data(0x4009CAD4, 0x00000000, params=0x14),
    write_data(0x4009C3B8, 0x00000000, params=0x14),

    # SRAM init
    write_data(0x4019C00C, 0x00000001),
    write_data(0x4019C000, 0x00000001),
    check_data(0x4019C00C, 0x00000001),

    # 1 byte write (Turn Off green LED on the S32G274ARDB)
    write_data(0x4009D35C,0x00000001, params=0x11),
    # Turn ON red LED
    write_data(0x4009D304,0x00000000, params=0x11),
    # SRAM_1 init
    write_data(0x401A000C, 0x00000001),
    write_data(0x401A0000, 0x00000001),
    check_data(0x401A000C, 0x00000001),

    # Turn Off red LED
    write_data(0x4009D304,0x00000001, params=0x11),
    # Turn On blue LED
    write_data(0x4009D305,0x00000000,params=0x11),
    # STDBY SRAM init
    write_data(0x4402800C, 0x00000001),
    write_data(0x44028000, 0x00000001),
    check_data(0x4402800C, 0x00000001),
    # Turn ON red LED
    write_data(0x4009D304,0x00000000, params=0x11),
]

# ------------------------------------------------------------
# Write binary file
# ------------------------------------------------------------

dcd_bin = build_dcd(commands)

with open("dcd.bin", "wb") as f:
    f.write(dcd_bin)

print("Generated dcd.bin ({} bytes)".format(len(dcd_bin)))

