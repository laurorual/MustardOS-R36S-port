# Emulator survey (2026-11-28)

Candidates to analyse later (decision 53): other standalone builds for
the systems the port has, other emulators for them, and standalones for
systems it does not have yet. Nothing here is decided; each entry needs a
bench measurement before it replaces anything (AGENTS.md "Heavy
systems": performance first, dArkOSen the first reference).

Sources: the local references (`refs/darkosen` launchers in
`usr/local/bin`; ROCKNIX `packages/virtual/emulators/package.mk` on
`next`, the RK3326 lines), the emulators' own pages, and the R36S
compatibility lists. r/R36S itself could not be read (Reddit refuses the
agent's tools); threads the user finds can be added here.

## Planned

| System | Now | Candidate | Evidence | Notes |
|---|---|---|---|---|
| Saturn | YabaSanshiro (dArkOSen's retro_arena port, patched) | **yabasanshiro-pirry** 1.6.4 (github.com/pirrypirrypirry/yabasanshiro-pirry, GPL-2.0) | bench 2026-11-28, Sonic R same scene: 35.5 presented frames/s vs 22.3; its table: 140 games, Sonic R 50.9 emulated fps; **ROCKNIX's RK3326 default** (`yabasanshiro-pirry-sa`) | v1.1.3, built from source with our patches (input map, SIGTERM quit, fps log, state on exit); its binaries: the dArkOS one needs GCC 14 libstdc++, the ArkOS one ignored SIGTERM |

## Other builds or emulators for systems the port has

| System | Now | Candidate | Evidence | Assessment |
|---|---|---|---|---|
| NDS | DraStic (steward-fu's advanced) | **DSperate** (github.com/beebono/DSperate; clean-room DraStic-style JIT + melonDS features, DSi too) | in dArkOSen (`NDS.sh` "dsperate"), arkos4clone, spruceOS; ROCKNIX ships it on aarch64 (DraStic stays its RK3326 default); v3.5.0 notes: NSMB, Spirit Tracks, Phantom Hourglass, Mario Kart DS "well above 30 fps" on an RK3326 (G350) | worth a bench A/B against DraStic (same games, fps and heat); open source would also remove a closed component; needs the DS BIOS/firmware files; licence to check |
| N64 | mupen64plus standalone, Rice | the same mupen64plus with **GLideN64** or Glide64mk2 (dArkOSen `n64.sh` offers all three) | community lists: Rice the fastest on RK3326, GLideN64 more accurate and heavier; per-game (the R36S compatibility sheet has entries where only one plugin works) | offer GLideN64 as a per-game choice for games Rice draws wrongly; not a default change |
| PS1 | pcsx_rearmed (libretro) | **DuckStation standalone** (dArkOSen `standalone-duckstation`, ROCKNIX `duckstation-sa`) | more accurate (fixes games that crash on pcsx_rearmed); heavier; no RK3326 numbers found | optional per game for compatibility; pcsx_rearmed stays the default; DuckStation's licence (CC BY-NC-ND for new versions) to check before shipping |
| DC | Flycast 2022 libretro (+ `muos-flycast` standalone) | flycast2021 libretro (ROCKNIX's RK3326 default), newer Flycast standalone (`flycastsa` in dArkOSen) | ROCKNIX picks flycast2021-lr by default on RK3326 | A/B flycast2021 vs 2022 on the bench games (Power Stone 2 fight state) |
| PSP | PPSSPP 1.12.3 ("2021", frameskip 1) + newer libretro | a newer PPSSPP standalone (ROCKNIX `ppsspp-sa`) | guides: the 2021 build is the most stable on RK3326; no measured comparison found | A/B with God of War states (`MUOS/t2/state-v120`); keep 2021 unless a newer one wins |
| DOS | DOSBox Pure (libretro) | dosbox-staging / DOSBox-X standalone | none for RK3326 | low priority |
| Arcade | FBNeo | MAME 2003-Plus, AdvanceMAME | — | per-game alternative; low priority |

## Standalones for systems the port does not have

| System | Candidate | Used by | Assessment |
|---|---|---|---|
| Amiga | **Amiberry** (GPL-3.0, ARM64 JIT) | ROCKNIX (`amiberry`, RK3326 included), also uae4arm/puae libretro | good fit: light, open source; add ROMS/AMIGA with Kickstart in MUOS/bios |
| Atari ST | **Hatari** standalone | ROCKNIX (`hatarisa`) | light; open source |
| C64 / VIC-20 | **VICE** standalone | ROCKNIX (`vice-sa`); vice libretro | light; open source |
| Naomi / Atomiswave | Flycast (the one the port has) | dArkOSen (`naomi.sh`, `atomiswave.sh`), ROCKNIX | cheap: folders and BIOS for the emulator the port already ships |
| Laserdisc (Dragon's Lair) | **hypseus-singe** | dArkOSen (`daphne.sh`), ROCKNIX | niche; open source |
| Beat 'em up engine | **OpenBOR** | ROCKNIX (`openbor`) | popular on handhelds; open source |
| Doom engines | **GZDoom / LZDoom** | dArkOSen (`doom.sh`), ROCKNIX (`gzdoom-sa`) | LZDoom is the lighter one for the A35; PrBoom libretro is the other way |
| Atari Jaguar | **BigPEmu** (closed, free; Linux ARM64 builds) | dArkOSen (`bigpemu.sh`), ROCKNIX (not on RK3326) | Virtual Jaguar is too slow; BigPEmu on the A35 unmeasured; its terms to check |
| Apple II | LinApple / AppleWin (sa2) | dArkOSen (`apple2.sh`) | niche |
| Nintendo DSi | DSperate | dArkOSen, ROCKNIX (`ndsiware`) | comes with the DSperate trial |
| PC (x86 games) | box64 (+ Wine) | ROCKNIX (aarch64) | PortMaster already uses box64 for its ports; a general Wine setup is too heavy for 1 GB |

Not feasible on the RK3326 (1 GB, Cortex-A35, Mali-G31): PS2
(AetherSX2/NetherSX2/ARMSX2), GameCube/Wii (Dolphin), 3DS
(Azahar/Citra), PS Vita (Vita3K), Switch. ROCKNIX enables none of them
on RK3326.

## Order to analyse (suggestion)

1. Saturn pirry (v1.1.3, decided).
2. DSperate vs DraStic (bench A/B; also open source).
3. Flycast 2021 vs 2022 (cheap A/B, two cores already buildable).
4. Naomi/Atomiswave folders (no new emulator).
5. Amiberry, Hatari, VICE, OpenBOR (new systems, light, open source).
6. GLideN64 per game; DuckStation per game; newer PPSSPP A/B.
7. BigPEmu, hypseus-singe, Doom, Apple II (niche).
