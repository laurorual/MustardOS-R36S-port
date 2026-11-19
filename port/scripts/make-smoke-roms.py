#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""M6 T2: minimal synthetic ROMs (an endless loop at the reset vector) for
the systems that need no BIOS, so a core can be loaded and timed by
t2-nes-fps.sh without game dumps. The fps is the emulator's cost on an idle
CPU, a lower bound; real games are the T3 verdict.
  make-smoke-roms.py OUTDIR   -> OUTDIR/<ROMS dir>/smoke.<ext>"""
import os
import struct
import sys


def a2600():  # 4K, 6507: JMP $F000; reset vector -> $F000
    rom = bytearray(b"\xea" * 4096)
    rom[0:3] = b"\x4c\x00\xf0"
    rom[0xFFC:0xFFE] = b"\x00\xf0"
    return rom, "a26"


def a7800():  # 32K, a78 header (no BIOS), 6502: JMP $8000; vector -> $8000
    body = bytearray(b"\xea" * 32768)
    body[0:3] = b"\x4c\x00\x80"
    body[0x7FFC:0x7FFE] = b"\x00\x80"
    hdr = bytearray(128)
    hdr[0] = 1
    hdr[1:10] = b"ATARI7800"
    hdr[17:49] = b"muOS smoke".ljust(32, b"\0")
    hdr[49:53] = struct.pack(">I", len(body))
    hdr[100:128] = b"ACTUAL CART DATA STARTS HERE"
    return hdr + body, "a78"


def pce():  # 8K HuCard, bank 0 at $E000 on reset: JMP $E000
    rom = bytearray(8192)
    rom[0:3] = b"\x4c\x00\xe0"
    rom[0x1FFE:0x2000] = b"\x00\xe0"
    return rom, "pce"


def ngp():  # SNK header, entry $200040: JR T,$ (TLCS-900H)
    rom = bytearray(0x80000)
    rom[0:28] = b"COPYRIGHT BY SNK CORPORATION"
    rom[0x1C:0x20] = struct.pack("<I", 0x200040)
    rom[0x23] = 0x10  # colour mode
    rom[0x24:0x30] = b"MUOS SMOKE  "
    rom[0x40:0x42] = b"\x68\xfe"
    return rom, "ngc"


def wswan():  # 64K, reset at FFFF:0000 -> JMP FAR F000:0000; JMP $ there
    rom = bytearray(0x10000)
    rom[0:2] = b"\xeb\xfe"
    rom[-16:-11] = b"\xea\x00\x00\x00\xf0"
    rom[-10] = 0  # developer
    rom[-6] = 0  # ROM size code, 1 = 4 Mbit (accepted for any image)
    return rom, "ws"


def sg1000():  # 8K, Z80: DI; JR $
    rom = bytearray(8192)
    rom[0:3] = b"\xf3\x18\xfe"
    return rom, "sg"


def pokemini():  # Free BIOS boots the cartridge at $2100 ("MN" header)
    rom = bytearray(0x10000)
    rom[0x2100:0x2102] = b"MN"
    rom[0x2102:0x2104] = b"\xf1\xfe"  # JRS $ (S1C88)
    rom[0x21A4:0x21AC] = b"NINTENDO"
    rom[0x21AC:0x21B0] = b"MUOS"
    return rom, "min"


def dos():  # .COM: JMP $
    return bytearray(b"\xeb\xfe"), "com"


ROMS = {"ATARI2600": a2600, "ATARI7800": a7800, "PCE": pce, "NGPC": ngp, "WS": wswan,
        "SG1000": sg1000, "POKEMINI": pokemini, "DOS": dos}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    for d, make in ROMS.items():
        data, ext = make()
        os.makedirs(os.path.join(sys.argv[1], d), exist_ok=True)
        with open(os.path.join(sys.argv[1], d, f"smoke.{ext}"), "wb") as f:
            f.write(data)
        print(f"{d}/smoke.{ext} {len(data)} bytes")
