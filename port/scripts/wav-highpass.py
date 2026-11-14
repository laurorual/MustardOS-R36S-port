#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""High-pass + peak-normalise a 16-bit PCM WAV for the R35S speaker (M4a).

    wav-highpass.py IN.wav OUT.wav [CUTOFF_HZ=400] [PEAK=30000]

The tiny speaker reproduces almost nothing below ~400 Hz, so a bass-heavy
UI sound (muOS info_open/info_close, a copy of back.wav) is inaudible: a
4th-order Butterworth high-pass (two RBJ biquads, Q 0.5412 and 1.3066)
removes the bass, then the peak is raised to PEAK like navigate.wav
(hardware-findings.md). Pure standard library (runs in the build container).
"""
import array
import math
import sys
import wave


def biquad_hp(x, fs, fc, q):
    w0 = 2 * math.pi * fc / fs
    alpha = math.sin(w0) / (2 * q)
    c = math.cos(w0)
    b0, b1, b2 = (1 + c) / 2, -(1 + c), (1 + c) / 2
    a0, a1, a2 = 1 + alpha, -2 * c, 1 - alpha
    b0, b1, b2, a1, a2 = b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0
    y, x1, x2, y1, y2 = [], 0.0, 0.0, 0.0, 0.0
    for v in x:
        o = b0 * v + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, v, y1, o
        y.append(o)
    return y


def main():
    src, dst = sys.argv[1], sys.argv[2]
    fc = float(sys.argv[3]) if len(sys.argv) > 3 else 400.0
    peak = int(sys.argv[4]) if len(sys.argv) > 4 else 30000
    with wave.open(src) as w:
        p = w.getparams()
        if p.sampwidth != 2 or p.comptype != 'NONE':
            sys.exit('need 16-bit PCM')
        a = array.array('h', w.readframes(p.nframes))
    ch = p.nchannels
    chans = []
    for c in range(ch):
        s = [float(v) for v in a[c::ch]]
        for q in (0.5412, 1.3066):
            s = biquad_hp(s, p.framerate, fc, q)
        chans.append(s)
    m = max(max(abs(v) for v in s) for s in chans) or 1.0
    g = peak / m
    out = array.array('h', [0] * len(a))
    for c in range(ch):
        out[c::ch] = array.array('h', [max(-32768, min(32767, round(v * g))) for v in chans[c]])
    with wave.open(dst, 'wb') as w:
        w.setparams(p)
        w.writeframes(out.tobytes())
    print(f'{dst}: high-pass {fc:.0f} Hz, gain {20 * math.log10(g):+.2f} dB, peak {peak}')


if __name__ == '__main__':
    main()
