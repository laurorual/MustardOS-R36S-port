#!/usr/bin/env python3
"""Generate a deterministic diagnostic PNG using only the Python standard library."""
import binascii
from pathlib import Path
import struct
import sys
import zlib

width, height = 640, 480
pixels = bytearray(width * height * 3)
colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255)]
for y in range(height):
    for x in range(width):
        color = colors[(y >= 240) * 2 + (x >= 320)]
        if x in (0, 639) or y in (0, 479):
            color = (0, 0, 0)
        offset = (y * width + x) * 3
        pixels[offset:offset+3] = bytes(color)

glyphs = [
    ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
]
for quadrant, glyph in enumerate(glyphs):
    left, top = (quadrant % 2) * 320 + 120, (quadrant // 2) * 240 + 60
    for row, line in enumerate(glyph):
        for col, active in enumerate(line):
            if active == "1":
                for y in range(top + row * 16, top + (row + 1) * 16):
                    for x in range(left + col * 16, left + (col + 1) * 16):
                        offset = (y * width + x) * 3
                        pixels[offset:offset+3] = b"\0\0\0"

def chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", binascii.crc32(kind + data) & 0xffffffff)

rows = b"".join(b"\0" + pixels[y*width*3:(y+1)*width*3] for y in range(height))
png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b"")
Path(sys.argv[1]).write_bytes(png)
