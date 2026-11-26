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
- No on-screen volume/brightness bar in ports (the keys still work), except
  ports that run a libretro core, which get the in-game bar and menu.
- A port that hangs on its own exit is closed with Fn+Start (its
  process group is ended after 3 s); unsaved progress is lost then.
- Ports are not tested one by one: please report the ones that misbehave
  (name, what happens, and `MUOS/log/system/port.log` from the card).

## System

- **Sound:** rarely, sound stops in the menu until the next game starts
  (the system repairs it before each game). 200 % volume (overdrive)
  distorts, as in MustardOS.
- After waking from sleep inside a game, Wi-Fi returns when the game
  ends.
- Menus not yet tested on this port: Direct Link, Proxy Settings, static
  IP addresses.
- Updating through Wi-Fi or the Task Toolkit replaces only the system
  partition; a new kernel or boot loader (rare) needs a full reflash.
- English task names in the Task Toolkit, as in MustardOS.
