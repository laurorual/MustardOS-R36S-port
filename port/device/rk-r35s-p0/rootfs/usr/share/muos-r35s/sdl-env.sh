# SPDX-License-Identifier: MIT
# M11: the SDL controller environment for applications and ports, as
# upstream SETUP_SDL_ENVIRONMENT (internal script/var/display.sh): the
# content's control scheme (/run/muos/controller: retro, modern, or system
# = Remap layout setting) picks the muOS-Keys mapping from the
# gamecontrollerdb store; /usr/lib/gamecontrollerdb.txt (a link to
# /run/muos/gamecontrollerdb.txt) gets that file plus the same mapping
# under PortMaster's name for muOS devices, "Deeplay-keys" (upstream
# script/control/gamecontrollerdb.sh), which PortMaster's control.txt
# greps. Sourced by muos-frontend before it clears the request files.
sdl_env() {
    _store=/opt/muos/share/info/gamecontrollerdb
    _sel=$(head -n 1 /run/muos/controller 2>/dev/null || :)
    case $_sel in
        '' | system)
            case $(cat /opt/muos/config/settings/remap/layout 2>/dev/null) in
                1) _sel=modern ;;
                *) _sel=retro ;;
            esac ;;
    esac
    _f=$_store/$_sel.txt
    [ -f "$_f" ] || _f=$_store/retro.txt
    _line=$(grep -v '^#' "$_f" 2>/dev/null | grep -m 1 ',muOS-Keys,' || :)
    {
        cat "$_f" 2>/dev/null
        [ -z "$_line" ] || printf '%s\n' "$_line" | awk -F, -v OFS=, '{ $2 = "Deeplay-keys"; print }'
    } > /run/muos/gamecontrollerdb.txt.tmp && mv -f /run/muos/gamecontrollerdb.txt.tmp /run/muos/gamecontrollerdb.txt
    SDL_GAMECONTROLLERCONFIG_FILE=/usr/lib/gamecontrollerdb.txt
    SDL_GAMECONTROLLERCONFIG=$_line
    export SDL_GAMECONTROLLERCONFIG_FILE SDL_GAMECONTROLLERCONFIG
    unset _store _sel _f _line
}
