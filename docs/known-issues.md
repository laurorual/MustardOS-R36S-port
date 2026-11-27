# Known issues

For MustardOS for R36S/R35S (unofficial port). Report new problems at
https://github.com/laurorual/MustardOS-R36S-port/issues, not to the
MustardOS team.

## Hardware support

- Only the R35S/R36S **Panel 0** (R36S-V12 board) and the Realtek
  **RTL8821CU** Wi-Fi adapter are tested (since v1.1 also a TP-Link
  RTL8822BU, 2357:0115, by the user). The other models and Wi-Fi
  chips in the README are experimental (since v1.1): untested by the
  port. On another model the undervolt rows (Danger Settings) are
  unavailable, the boot logo before the menu may look wrong, and the
  battery figures come from dArkOSen's device tree for that model. No
  Bluetooth.
- After a warm reboot the RTL8821CU occasionally fails to start (about 1
  in 7): unplug and plug it again.
- At power-on the first Wi-Fi scan sometimes hangs; the system resets the
  adapter after 20 s, so Wi-Fi can take up to ~40 s to connect.
- No HDMI output, no rumble (the R35S has no motor), no controllable LEDs.

## Systems

- **Heavy systems are limited by heat, not settings:** PSP (God of War
  playable with frame skip 1), Dreamcast (most games full speed, some
  heavy scenes slow down), Saturn (Sonic R 20–25 fps: only light games
  are playable). Play them on battery; charging while playing heats the
  SoC and slows the CPU.
- Standalone N64 (Mupen64Plus): no on-screen volume/brightness bar (the
  keys still work); screenshots are saved without a visual confirmation.
- In-game screenshots work in the menu and the standalone N64 only.
- Many new systems were checked only with test content; please report
  games that misbehave.

## PortMaster (since v1.1.1)

- Ports that exist only for 32-bit (armhf) systems do not run: the
  firmware is 64-bit only. PortMaster lists them; about 200 of 1500.
- The volume/brightness bar shows when the port draws its next frame: in
  a still screen that waits for a key (a title screen, PortMaster's menu)
  it appears with the next button press. Ports that bring their own SDL
  library or draw without SDL/EGL show no bar (the keys still work).
- A port that hangs on its own exit is closed with Fn+Start (its
  process group is ended after 3 s); unsaved progress is lost then.
- If the console is switched off while PortMaster updates its port list,
  it can lose the list ("Unable to find a source"): delete the folder
  `MUOS/PortMaster` on the card and open Applications → PortMaster again
  (installed ports stay).
- Ports are not tested one by one: please report the ones that misbehave
  (name, what happens, and `MUOS/log/system/port.log` from the card).

## PICO-8 (since v1.1.1)

- The official PICO-8 is not included: bring your own Raspberry Pi
  download. Splore (BBS) needs it; with the free cores, play carts you
  copied to `ROMS/PICO-8`.
- Without the official PICO-8, choosing the "PICO-8 - Standalone" cores
  only returns to the menu.

## Card storage (since v1.1.2)

- exFAT and FAT32 have no journal: a power cut while the system writes
  (a save, a setting, an update) can damage files on the card. Shut down
  from the menu and keep the battery charged; choose EXT4 at Install if
  you copy games over Wi-Fi anyway.
- FAT32 can't hold a file larger than 4 GB (some PSP and Dreamcast
  games): use exFAT for those.
- Install formats the storage only on a fresh card: a card that already
  has games or saves keeps its format (choose EXT4 there, or flash again).
- A card updated from v1.1.1 or older stays EXT4 (Windows can't open it
  without extra software).

## System

- **Sound:** rarely, sound stops in the menu until the next game starts
  (the system repairs it before each game). 200 % volume (overdrive)
  distorts, as in MustardOS.
- After waking from sleep inside a game, Wi-Fi returns when the game
  ends.
- Menus not yet tested on this port: Direct Link, Proxy Settings, static
  IP addresses.
- Updating through Wi-Fi or the Task Toolkit replaces the system
  partition and the kernel; a new boot loader (rare) needs a full reflash.
- **On v1.1.0 only:** its automatic updater runs in the background with
  Wi-Fi on. Don't start Install Firmware Update while it is downloading
  (the first minutes after a start with Wi-Fi, when a new release is out):
  both unpack into the same file and the update falls back to the old
  system at the restart. Turn Wi-Fi off first, or let the automatic
  update finish. From v1.1.1 on, updates over Wi-Fi only start from
  Task Toolkit → Check for Online Update.
