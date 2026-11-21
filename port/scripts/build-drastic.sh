#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# M8 (decision 23, the user 2026-11-20: the fastest emulator, closed source
# allowed): DraStic r2.5.2.2 (NDS, closed source, free to use; the aarch64
# binary dArkOS ships) staged for the image. m8b shipped it plain (dArkOS
# RG351MP drastic.cfg with muOS-Keys controls); since M8 T3 6 it runs with
# the advanced hook:
#
# M8 (M8 T3 6: the two-screen layout dArkOSen/ROCKNIX users install,
# auto save state): trngaje's advanced_drastic, the LD_PRELOAD hook of
# the same DraStic r2.5.2.2 binary that upstream muOS ships as
# "drastic-trngaje" (layouts with background art, its own menu, auto save
# state on exit and load on start, SIGTERM saves and quits), with
# steward-fu's 640x480 layout art (trngaje/drastic_layout). Clones
# build/advdrastic-src and build/drastic-layout-src at pinned commits:
#   tree  build/m8/advdrastic/tree/opt/muos/share/emulator/drastic/ (the
#         m8b path: the frontend, coredb and migrations look for it)
#         (drastic, libs/ = the dArkOS build of libadvdrastic.so +
#         libjson-c.so.5, resources/ font lang menu pen bg/640x480,
#         system/, game_database.xml, microphone/)
#   cfg   port/device/rk-r35s-p0/rootfs/usr/share/muos-r35s/drastic-trngaje/
#         drastic.cfg = upstream muOS's drastic-trngaje drastic.cfg
#         (MustardOS/internal device/rg35xx-h, 640x480) with the controls
#         its control/drastic.sh derives from the board sdl_map, here the
#         muOS-Keys map (b0 B, b1 A, b2 X, b3 Y, b4/b5 L1/R1, b6/b7 L2/R2,
#         b8 Select, b9 Start, b10 Fn = HOT, b11/b12 L3/R3), touch press on
#         L3, and dArkOS's performance settings (auto frameskip 1, threaded
#         3D); layout_index 8 ("vh_s0": top screen 480x360 top left, touch
#         screen 160x120 bottom right), auto save state on.
#   build-drastic.sh stage-adv
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
case "${1:-}" in
stage-adv)
    adv=$repo/build/advdrastic-src adv_commit=d445a56349cce68f5337d02c9fe890de9d390f3f
    lay=$repo/build/drastic-layout-src lay_commit=e8dc3eb5bb51351bf3e93229e388ae9e5fea9adc
    up=$repo/build/upstream/internal up_commit=550cc58f9cd3449a17f53ca55efcdc6c473b5a89
    [ "$(git -C "$adv" rev-parse HEAD)" = "$adv_commit" ] || { echo "advdrastic-src is not at $adv_commit" >&2; exit 1; }
    [ "$(git -C "$lay" rev-parse HEAD)" = "$lay_commit" ] || { echo "drastic-layout-src is not at $lay_commit" >&2; exit 1; }
    git -C "$adv" diff --quiet && git -C "$lay" diff --quiet || { echo "dirty clone" >&2; exit 1; }
    atree=$repo/build/m8/advdrastic/tree adest=opt/muos/share/emulator/drastic
    acfg=$repo/port/device/rk-r35s-p0/rootfs/usr/share/muos-r35s/drastic-trngaje
    rm -rf "$atree"; mkdir -p "$atree/$adest/libs" "$atree/$adest/resources/bg" "$acfg"
    a=$atree/$adest
    [ "$(md5sum < "$adv/drastic_v2522" | cut -d' ' -f1)" = 17550db727f3b59d36b57746ad1944be ] || { echo "drastic_v2522 md5" >&2; exit 1; }
    cp "$adv/drastic_v2522" "$a/drastic"; chmod 755 "$a/drastic"
    cp "$adv/libs/arkos/libadvdrastic.so" "$adv/libs/arkos/libjson-c.so.5" "$a/libs/"
    cp -r "$adv/resources/font" "$adv/resources/lang" "$adv/resources/menu" "$adv/resources/pen" "$a/resources/"
    cp -r "$lay/bg/640x480" "$a/resources/bg/"
    cp -r "$adv/system" "$adv/microphone" "$a/"; cp "$adv/game_database.xml" "$a/"
    find "$a" -type d -exec chmod 755 {} +; find "$a" -type f ! -name drastic -exec chmod 644 {} +
    # muOS-Keys codes (DraStic: 1024 + SDL button)
    git -C "$up" show "$up_commit:device/rg35xx-h/control/drastic-trngaje/drastic.cfg" | tr -d '\r' | awk '
        BEGIN {
            b["A"]=1025; b["B"]=1024; b["X"]=1026; b["Y"]=1027; b["L"]=1028; b["R"]=1029
            b["START"]=1033; b["SELECT"]=1032; b["SWAP_SCREENS"]=1031; b["FAKE_MICROPHONE"]=1036
            b["UI_SELECT"]=1025; b["UI_BACK"]=1026; b["UI_EXIT"]=1024; b["UI_PAGE_UP"]=1028
            b["UI_PAGE_DOWN"]=1029; b["UI_SWITCH"]=1027; b["HOT"]=1034; b["HOT_TOGGLE_DPAD_MOUSE"]=1028
            b["HOT_TOGGLE_BLUR_PIXEL"]=1024; b["HOT_CHANGE_THEME"]=1027; b["HOT_ENTER_MENU"]=1026
            b["HOT_TOGGLE_FAST_FORWARD"]=1029; b["HOT_SAVE_STATE"]=1031; b["HOT_LOAD_STATE"]=1030
            b["HOT_QUIT"]=1033; b["TOUCH_CURSOR_PRESS"]=1035
            v["frameskip_type"]=2; v["frameskip_value"]=1; v["safe_frameskip"]=0; v["threaded_3d"]=1
            v["screen_swap"]=0; v["unzip_roms"]=1
        }
        match($0, /^controls_b\[CONTROL_INDEX_[A-Z0-9_]+\]/) {
            k = substr($0, 26, RLENGTH - 26)
            if (k in b) { print "controls_b[CONTROL_INDEX_" k "] = " b[k]; next }
        }
        { split($0, kv, " = "); if (kv[1] in v) { print kv[1] " = " v[kv[1]]; next } }
        { print }
        END { print "enable_autosavestate = 1"; print "layout_index = 8"; print "theme_index = 0" }' > "$acfg/drastic.cfg"
    grep -q "^controls_b\[CONTROL_INDEX_HOT\] = 1034$" "$acfg/drastic.cfg" || { echo "control mapping failed" >&2; exit 1; }
    cat > "$acfg/settings.json" <<'JSON'
{
  "pen":5,
  "theme":0,
  "mode":8,
  "alpha":2,
  "position":2,
  "border":3,
  "overlay":1,
  "lang":"english",
  "menu_c0":"0xffffff",
  "menu_c1":"0x404040",
  "menu_c2":"0x004000",
  "states":"",
  "menu_bg":0,
  "menu_cursor":1,
  "pixel_filter":1
}
JSON
    (cd "$a" && find . -type f | sort | xargs -d '\n' sha256sum) > "$repo/build/m8/advdrastic/SHA256SUMS"
    du -sh "$a" ;;
*) sed -n '3,29p' "$0"; exit 2 ;;
esac
