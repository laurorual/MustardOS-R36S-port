# Decisions

Answered decisions, numbered in the order they were asked. Open ones are
in [STATUS.md](STATUS.md) "Decisions for the user". A later decision
overrides an earlier one where they conflict (noted inline).

## 2026-11-14

1. Name: "muOS for R36S/R35S (unofficial port)". Superseded 2026-11-25
   (34): "MustardOS for R36S/R35S (unofficial port)", following
   muos.dev/press.
2. Mali: (a) ask Hardkernel for the r13p0 terms (sent 2026-11-14,
   follow-up later; no answer). Superseded for the public image by 35.
3. Boot payloads from rkbin (done, M4d).
4. GPL source on GitHub.
5. Public root password `root` (as upstream).
6. SFTP jail before the final public build (done, M4g).
7. Unported web services hidden.
8. Public p3 empty.

## 2026-11-17

9. shellcheck download allowed (done).
10. The R35S has no rumble motor: keep the option, detect the motor, show
    "Unavailable" without one (done).
11. No public-image test yet (superseded by the rc1 plan, M9).

## 2026-11-18 (recommendations accepted)

12. Upstream themes in the developer image now, in the public image after
    the MustardOS team answers (answered 2026-11-25: allowed, see 34).
13. CPU 1512 MHz as an opt-in, off by default (M7).
14. Bluetooth, PortMaster, standalone emulators after v1.0 (exceptions:
    19, 20, 23).
15. Spare card in slot 2 (it fails there; swap test closed it, M8).
16. `root=` by the slot-1 device with the clean U-Boot in M8 (done).

## 2026-11-19

17. p2 grown to 1 GiB in the M8 card layout, then ScummVM and the CJK
    fonts (done).
18. The user provides game dumps: after every T3 check `port/roms/` on the
    PC and use any ROM of a not yet tested system for its core's T2.
19. Standalone Mupen64Plus for N64 in M7 (exception to 14).
20. Dreamcast, PSP, NDS and Saturn (lowest priority) in v1.0; Atari 5200,
    Virtual Boy, Jaguar, Jaguar CD and CD-i out of v1.0.
21. Sega CD and PC Engine CD BIOS provided in `port/roms/bios`.
22. N64 defaults to "Mupen64Plus - Standalone - Rice" (done).

## 2026-11-20

23. The emulator with the most FPS for every system, closed source
    allowed (PSP v1.12.3, NDS DraStic, DC Flycast 2022 + v2.7 standalone).
24. DC/Saturn BIOS provided.
25. Layout session (done: m8b flashed, p3 restored).
26. Slot-2 swap test: the spare card may be erased (done).
27. DraStic and every other closed component stay in the developer and
    the public image. Its condition "published only after explicit
    licence answers" is replaced by 35 (2026-11-25).

## 2026-11-21 / 2026-11-22

28. Undervolt as an opt-in, stock voltages by default: a row in
    Configuração → Configurações perigosas below "Máximo do processador"
    (done, m9a). Manual CPU/GPU values in two rows below it, 25 mV steps,
    16 DTBs in the image (done, m9b).
29. The ScummVM standalone is the SCUMMVM default (done, m9a).
30. Keep the Flycast v2.7 standalone in the DC list.
31. OpenCC allowed (`build/tools/opencc-venv`): Traditional Chinese
    overlay (done).

## 2026-11-23

32. (a) GitHub repository plus the full source bundle as v1.0 release
    assets.

## 2026-11-25

33. Public repository: https://github.com/laurorual/MustardOS-R36S-port
    (updates: `/etc/muos-update.conf`, docs and scripts point there).
    Release assets include NAME.p2.img.gz and NAME.p2.img.sha256 (public
    builds make them) next to the card image and the source bundle.
34. MustardOS team answer (permission): the port and the bundled themes
    are allowed if the port follows https://muos.dev/press (the name
    "MustardOS", short form "muOS"; never "Mustard OS", "MUOS" or "Muos";
    logos unmodified; assets under CC BY-NC 4.0) and states very clearly
    that the MustardOS team does not support devices outside their list:
    all support is the port's (its GitHub). Project name: "MustardOS for
    R36S/R35S (unofficial port)".
35. The public image is **complete**: the user only writes the card.
    Closed components without an answer (Mali r13p0 userspace, DraStic,
    steward-fu's 640x480 DraStic layouts) are **bundled**, following
    community practice (dArkOS/ArkOS do the same), with credits and the
    known licence or terms in THIRD-PARTY.txt. A removal request from an
    author is honoured. Layouts by other authors (the other resolutions of
    drastic_layout) are not shipped.
36. Plan B, ready but not used: `prepare-image.sh` on the PC downloads a
    component from its official source, checks the SHA256 and injects it
    into the image before flashing. No download on first boot.
37. Priority from 2026-11-25: licences and publication come first in every
    session, v1.0 polish after them.
38. Bluetooth firmware (rtl8821c) is left out of the public image.
39. Commit e-mail: the history is rewritten to the GitHub no-reply
    address `755915+laurorual@users.noreply.github.com` (2026-11-25,
    fast-export/fast-import, trees unchanged; local repo config uses it);
    the user force-pushes it.
40. AGENTS.md and CLAUDE.md are not in the public repository (removed by
    the user on GitHub); they stay local, ignored by Git.
41. rc builds are published as GitHub pre-releases after their T3,
    v1.0.0 as a normal release (auto-update reads `releases/latest`).
42. (rc1 T3, 2026-11-25) A fresh card starts in English at 50 % volume.
    The boot screen follows the press kit: MustardOS's own boot screen
    (badge as supplied) with the port's "R36S / R35S" and "unofficial
    port" text below.

43. (2026-11-25) Other R36S variants after v1.0: the dArkOSen DTBs of
    the same resolution (640x480) in a folder of the image, and a basic
    selector in the card's root (Windows, Linux, macOS) that puts the
    chosen DTB in place of the system's, like dArkOSen. README: untested
    by the port, feedback wanted.
44. (2026-11-25) Other Wi-Fi dongles after v1.0, with dArkOSen as the
    reference (no guessing: the port can't test them). README: untested,
    feedback wanted.
45. (2026-11-25) MustardOS updates: v1.0 stays on 2606.0 Andromeda, the
    latest official release (parity); the next official release is
    ported after v1.0 (upstream main is unreleased work, 81 frontend + 90
    internal commits on 2026-11-25).
46. (2026-11-25, rc2 T3 ok) test128 is wiped by the user and becomes an
    ext4 slot-2 test card; the public rc2 goes on the old original32
    card in slot 1 (no developer access while it runs). test128 returns
    to a developer image later by `flash-card.sh` + `card-p3.sh restore`.

## 2026-11-26

47. (2026-11-26) Hardkernel's forum answer (it gets the drivers from
    Rockchip and can't speak to redistribution) changes nothing: the
    publication strategy stays (Mali userspace shipped unmodified as
    community practice, LICENSING.md).
48. (2026-11-26) Versions: the next release is v1.1.1 (PortMaster from
    M11 and Pico-8 from M12, one build, one T3); the minor number goes
    up (v1.2.0) only for a big change. The user tests M11 and M12
    together.

Standing rules (AGENTS.md): heavy systems = maximum performance first;
recovery promotion after a clean T3 without asking.
