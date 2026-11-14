# Project status

Current state only; update at the end of every milestone. How-tos
(flash, build, trial root, trial kernel, boot sequence) are in
[procedures.md](procedures.md); finished milestones with their results and
T3 checklists in [milestones.md](milestones.md). See also
[hardware-findings.md](hardware-findings.md), [roadmap.md](roadmap.md),
[compatibility-matrix.md](compatibility-matrix.md) and
[storage.md](storage.md). The C1–C122 history is in
[archive/phase4/](archive/phase4/README.md).

## Current phase

**Phase 5 (own-card firmware). M1–M4b done (M4b flashed by the user
2026-11-14, T3 items 1–5 passed, 6–7 pending). M4c (Wi-Fi toggle, Wi-Fi
after wake 18 → 9 s, warm-reboot dongle fix, Web Services = SSH/SFTP,
in-game Wi-Fi glyph) is T2-passed and installed on the card (2026-11-14
evening); its T3 is next.** A logged discharge (M4b T3 item 6, capacity
check) is running: `t2-discharge.sh log-start` + CTR, started at 96%.

## When you're back (user)

1. **M4b item 6 (as you planned):** when the battery is flat, plug in and
   power on at once; note the % (expected: low, not ~33%). Then tell the
   agent: it runs `t2-discharge.sh report` + `log-stop` (capacity check
   with FCC 2550), restores your volume (55; the run uses 10) and stops
   CTR's test state.
2. **M4c T3 checklist** (below). No flash needed: the card already has
   M4c (same files as `dist/firmware/test128-m4c-20261114`).
3. **Decision 2 (a):** send the revised Hardkernel request
   (`docs/archive/phase4/hardkernel-r13-license-request.md`, revised
   2026-11-14: to `odroid@hardkernel.com`, forum fallback; fill in the
   GitHub URL and your name).

## Evening of 2026-11-14 (M4c, details: milestones.md M4c)

- Frontend built from source for the first time since Phase 4
  (`build-frontend-libs.sh`, patches `port/patches/frontend/0001–0003`);
  muxretro patch 0004.
- T2 all PASS on the card: `t2-wifi-radio.sh`, menu toggle via button
  injection, Web Services rows, Wi-Fi off across a reboot,
  `t2-wake-wifi.sh` 6/6 (8.5–9.2 s wake → address), 5/5 warm reboots,
  `t2-wifi.sh`, `t2-wifi-robust.sh`.
- M4b promoted to recovery, M3d retired, M4c image added (5/5).

## Device and bench

- **Device:** R35S Panel 0 (DT model R36S-V12 2023-08-18 Panel 0),
  test128 in slot 1: the M4b developer image flashed by the user
  2026-11-14, plus the M4c files (`install-rootfs.sh`, originals in
  `/var/lib/muos-m1-backup`). On battery, CTR running, volume 10.
  - Boot records: main = `Image-4f866b8b4ad7` (patches 0001–0005, 200 mΩ)
    + `panel0-bc04b6f8e4d4.dtb` (capacity 2500/2550, FCC reads 2550);
    previous = the M2 kernel.
  - p3: ROMs from `port/roms` (incl. CTR + PSX BIOS, re-pushed), Wi-Fi
    profile `MUOS/network/Home.ini`; `MUOS/init/zz-discharge-log.sh` with
    `user_init=1` (removed by `log-stop`).
- **original32 (stock dArkOSen):** the flasher station (slot 1, target
  in slot 2). Never write it.
- Device access, identity and card layout: procedures.md.

## Recovery image

The developer images are **private** (Wi-Fi PSK, SSH host key,
authorized_keys): never commit or share them. Flashing any image rewrites
the whole card, bootloader included; steps in procedures.md.

| Image | Content | State |
|---|---|---|
| `dist/firmware/test128-m4c-20261114.img.zst` (raw `ab60ef13…`, p2 `70f7ae82…`) | M4c developer image: M4b + Wi-Fi toggle, wake 9 s, no 8821cu autoload, Web Services SSH/SFTP, in-game glyph | T2-passed; its files are on the card; never flashed |
| **`dist/firmware/test128-m4b-20261114.img.zst`** (raw `3737c893…`, p2 `a45a3c4a…`) | **Recovery image since 2026-11-14 (evening).** M4b developer image (Wi-Fi robustness, crash capture, kernel 200 mΩ, DTB 2500/2550) | Flashed by the user, T3 items 1–5 passed |
| `dist/firmware/test128-m4a-20261114.img.zst` (raw `deef0ab2…`) + `public-m4a-20261114` (raw `193c520f…`) | M4a developer + public variant | T3 passed (developer: except Wi-Fi after sleep) |
| `dist/firmware/test128-m3e-20261113.img.zst` (raw `7b7c4a66…`) | M3e | Flashed and T3-passed |
| `dist/recovery/test128-m2-20261111.img.zst` (raw `34beb417…`) | M2: the last image with the M2 U-Boot | **Base of every image build**; never retire while used |

5/5 firmware versions (`port/packaging/storage-retention.json`; retired
M1, M3a.1, M3b, M3c, M3d). After the M4c T3: promote M4c, retire M3e
(rule, user 2026-11-13).

## What works (T3-confirmed)

Display (60.0046 Hz), all controls, frontend and submenus; volume and
brightness with muxretro's in-game bar and hold-to-repeat; speaker audio;
Wi-Fi (power save, profiles, scan, connect, replug, sleep/wake) +
SSH/SFTP; prefs persistence; GB, NES, SNES, GBA, MD and PSX (CTR smooth,
user's BIOS) with saves and states; per-system governors, 408 MHz menu
idle; autostart, menu reboot/shutdown, hard power-cut recovery;
Power-key sleep/resume in menu and game, shutdown timer, charging fake
sleep; battery %, icons and low-battery poweroff from the RK817 gauge;
battery-empty splash; headphone path switching; flashing with the host
card reader; p3 auto-grow; `panic=10` reboots after a kernel panic.

## Open problems

- **Battery:** (a) FCC is now 2550 (DT clamp); the running discharge
  checks that the % tracks the real ~2530 mAh. (b) Patch 0005's estimate
  at 200 mΩ: M4b item 6 (after the run). (c) The BSP's `off=`
  underreports the time off and stays set across warm reboots.
- **Wi-Fi dongle (RTL8821CU):** a deaf dongle has no software recovery
  except another sleep (power cut); case (d) (deaf after a warm reboot)
  is most likely the udev autoload fixed in M4c (5/5 clean). The pstore
  dump of the afternoon's panic was lost with the reflash (unchecked).
  Inserting the dongle during boot is unqualified; Bluetooth blacklisted.
- **Wake:** a game resumes 0.6 s after wake; Wi-Fi returns ~9 s later with
  ~0.7 s of slow frames (M4b: worst 52 ms; not re-measured with the
  shorter settle). The user wants dips gone late in the project.
- **Power:** menu idle ~409 mA; Wi-Fi off saves ~76 mA (CTR). LEDs (the
  R35S LED node is disabled in stock too) and rumble not done.
- **Audio:** one unexplained no-sound report (M3d); WirePlumber "no
  profile" start failure retried, not explained; 3–8 underrun bursts per
  game.
- **Frame pacing:** one M3e run had one 29 ms frame; reruns clean.
- **Headphones (hardware, deprioritized):** jack not detected with the
  plug fully in (contact problem).
- **DDR devfreq** isn't synced to the display; **U-Boot log** goes to
  serial/LCD only.
- **Pinned, not rebuilt:** muxfrontend, libui/libmuxcom (lang/config
  structs), the cores, the kernel modules, the tuned `/opt/muos` config;
  idbloader and trust from the M2 image (vendor blobs).
- **Trial root:** p3 can't be unmounted at shutdown while it runs.
- **Menu:** the Wi-Fi row's help text is English only (no lang entry, to
  keep libmuxcom pinned); "Direct Link" and "Proxy Settings" in
  Connectivity are upstream screens not exercised on the port; static
  addresses untested; NTP not ported (no clock source).
- **SFTP** runs as root with the whole filesystem (decision 6: port
  upstream's jail before the public build).
- **Licences:** Mali r13p0 (decision 2 (a): request ready, not sent),
  BL31 (decision 3: replace with rkbin's, M4d), the dirty U-Boot, Gambatte and BT firmware are
  private-only (`port/packaging/pending-licenses.json`).

## Decisions

Answered by the user 2026-11-14 (evening):
1. **Name:** "muOS for R36S/R35S (unofficial port)"; the user contacts
   the MustardOS team before publication.
2. **Mali:** (a), request r13p0 terms from Hardkernel (user sends the
   revised request).
3. **Boot payloads:** rkbin files acceptable: keep DDR/miniloader/BL32
   (= rkbin) and replace BL31 with rkbin's v1.14 (confirmed; trust-image
   rebuild = bootloader write + one T3 cycle, M4d).
4. **GPL source offer:** on GitHub.
5. **Public root password:** as upstream (`root`).
6. **SFTP:** port upstream's jailed `muos` user later, before the final
   public build.
7. **Unported web services:** hidden now (M4c); port some before the
   final public build.
8. **Public p3:** empty.

Earlier: kernel base stays the rk351 4.4 BSP (mainline/Panfrost = M5
candidate); CPU overclock deferred to the end as an optional toggle;
recovery promotion after a passed T3 is automatic.

## M4c T3 checklist (user; the card already has M4c)

1. **Wi-Fi toggle:** Configuration → Connectivity: first row "Wi-Fi:
   Enabled". Left → "Disabled": the header Wi-Fi icon goes within ~2 s,
   "Wi-Fi Network" is dimmed and A on it gives the error sound. Right →
   "Enabled": icon back within ~15 s. A on the row also toggles.
2. **No dongle:** unplug the dongle while on Connectivity: within ~3 s
   the row reads "Unavailable", dimmed; left/right/A only give the error
   sound. Plug back: "Enabled" within ~5 s, Wi-Fi back within ~20 s.
3. **Off stays off:** with Wi-Fi disabled, sleep/wake once and reboot
   once: no Wi-Fi icon after either; enable it again afterwards.
4. **Wake 3× (menu and game):** Wi-Fi icon back ~9–12 s after waking
   (M4b: ~15–18 s). In a game, open the pause menu right after waking
   (no Wi-Fi glyph or disconnected) and again ~15 s later (connected).
5. **Web Services:** only SSH and SFTP listed; toggling one works.
6. **Back navigation:** Wi-Fi Network → B: the focus is on "Wi-Fi
   Network", not on the Wi-Fi toggle.
7. **Warm reboot 2× (menu Reboot):** Wi-Fi icon within ~10 s of the menu
   appearing, both times.
8. M4b leftovers: item 6 ("When you're back" 1) and item 7 (public image,
   optional; the M4c public variant isn't built yet).

## Next milestone (proposal)

**M4d — public-build prerequisites:** rkbin BL31 trust image (bootloader
write, T3), SFTP jail (`musftpjail` in the frontend build, decision 6),
NTP (clock), the M4c public variant, LEDs/rumble; then the publication
checklist (name, GPL bundle on GitHub, Mali answer).
