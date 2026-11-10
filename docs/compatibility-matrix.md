# Compatibility matrix: native muOS on the R35S (Panel 0)

This is a condensed version, written 2026-11-10. The original is in
[archive/phase4/compatibility-matrix.md](archive/phase4/compatibility-matrix.md).
It holds the static analysis from 23/10, the evidence list E1–E12, and the
per-milestone update paragraphs. Technical details for each row are in
[hardware-findings.md](hardware-findings.md).

## Legend

**Basis** says where the classification came from:

| Code | Meaning |
|---|---|
| **F** | Observed in local files or Git objects. This is not a device validation. |
| **U** | Stated by the user or AGENTS.md, and not re-collected. |
| **H** | Hypothesis. |

**State** says how far the item has been checked:

| State | Meaning |
|---|---|
| **T3** | Confirmed on the device by the user. |
| **T2** | Confirmed on the device over SSH only. |
| **—** | Untested. |

The reference commits are in [upstream-revisions.txt](upstream-revisions.txt).

| Layer | Basis | State | Current status | Latest evidence | Orig. evidence |
|---|---|---|---|---|---|
| ISA / CPU / ABI | F/U | T2 | A35, glibc 2.41, CPU capped at 1296 MHz | Phase 1, C48 | E6, E10 |
| Bootloader | F | T3 | Own U-Boot from RG351MP @5606e804, with destructive paths removed. Stock payloads (DDR/BL31/BL32). | C79/C97 | E1, E4, E10–11 |
| Kernel / DTB / modules | F | T3 | `4.4.189-muos-r35s-p4`, own Panel 0 DTB, 555 modules | C97 | E4–5, E10 |
| Root FS / init | F | T2 | ext4 RO root; BusyBox PID 1 → C07 init. Full rcS/rcK pending. | C97–C122 | E1–5 |
| Partitions | F | T3 | test128: MBR, p1 FAT, p2 ext4 512 MiB, p3 ext4 data | C94/C97 | E2, E10 |
| Panel 0 display | F | T3 | 640×480 @ 59.94 Hz: port DTB 29 MHz, 732×661 (measured M1). The stock dArkOSen DTB uses 50 MHz / ≈61.2 Hz. | M1 | E4, E7, E11 |
| Brightness / blank | F | T3 / — | Levels 0–160 work. Blank is untested; UI percentage mapping is not calibrated. | C09, C21 | E4, E7, E11 |
| GPU / graphics | F/U | T3 | Mali-G31 with r13p0 blob (private licence), SDL2 KMSDRM/GLES | C03 | E8, E10 |
| Audio (speaker) | F | T3 | SPK_HP, gain 215, quantum 1024, PCM prime. Half-rate root cause still open; underruns. | C27, C36, C39 | E4–5, E7, E9, E11 |
| Audio (headphones) | F | — | Jack node exists | — | E7 |
| Buttons / sticks | F | T3 | `rk-r35s-p0` muinput backend, SDL mapping | Phase 2, C01 | E4–7, E11 |
| Volume keys | F | T3 | gpio_keys module plus patch0006 | C09 | E7, E11 |
| Power key | F | — | Only the U-Boot monitor long-press poweroff is confirmed | — | E7, E11 |
| uinput / evdev | F | T3 | Legacy uinput setup (4.4 headers) | Phase 2 | E5–6, E11 |
| Battery / charging | F | — | RK817 gauge present | — | E4–5, E7, E11 |
| LEDs / rumble | F | — | GPIO77 battery LED | — | E3, E5, E7, E11 |
| Reboot | F | T2 | Controlled reboot via the C12 preflight | C12 | E3, E5, E7 |
| Poweroff / suspend | F | — | Untested | — | E3, E5, E7 |
| Wi-Fi | F | T3 | RTL8821CU, Wi-Fi-only policy; warm reboot OK. Fails if inserted during boot. | C18, C105 | E7, E10 |
| Bluetooth | F | — | Disabled (btusb blacklisted) | C18 | E7, E10 |
| RTC | F | — | Not covered | — | E7, E10 |
| Frontend / config | F | T3 | Full muOS frontend; C79/C102 layout installed | C102–C104 | E2–3, E5, E8, E11 |
| Preferences | F | T3 | Durable store on p3 (vol/brightness) | C20, C21 | — |
| Emulation: GB | F | T3 | muxretro + Gambatte, states, durable saves, resident ROM, batch host | C121 | — |
| Emulation: NES | F | T3 (function only) | FCEUmm at ~51.4 fps (too slow) | C47, C48 | — |
| Libraries / ABI | F/U | T2 | Own Buildroot sysroot, 308 ELF | C78 | E6, E8 |
| Reproducibility | F | — | Open; rebuilt binaries differ from the qualified bytes | C72 | E1–2, E6, E10–11 |
| Licences | F | — | Private use only; see pending-licenses.json | — | E12 |
| Other panels / clones | H | — | Out of scope until there is evidence and a physical test | — | — |

Top risks from the original analysis, all rated high:
1. Boot and card preservation.
2. ABI/GPU blob.
3. Panel identity.
4. Input and power.
5. Rootfs bootstrap.
6. Provenance.

Items 2–4 are now largely retired for Panel 0. Items 1, 5 and 6 remain.
