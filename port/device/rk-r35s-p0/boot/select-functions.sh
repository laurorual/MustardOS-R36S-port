# SPDX-License-Identifier: MIT
# Pure selection policy; the caller supplies fixed directories and selector_exec.
c12_select_start() {
    mkdir -p "$selector_state" || return 1
    mkdir "$selector_state/once" 2>/dev/null || return 64
    printf 'c07\n' > "$selector_state/mode" || return 1
    pending=$selector_dir/c12.once
    if [ -f "$pending" ] && [ ! -L "$pending" ] &&
       [ "$(stat -c '%u:%g:%a:%h:%s' "$pending")" = 0:0:600:1:14 ] &&
       [ "$(cat "$pending")" = MUOS-C12-ONCE ] && selector_exec c12-config; then
        # Consume durably BEFORE starting anything that could touch RNG/network.
        [ ! -L "$selector_dir/c12.used" ] || return 64
        [ ! -e "$selector_dir/c12.used" ] || [ -f "$selector_dir/c12.used" ] || return 64
        rm -f "$selector_dir/c12.used" || return 1
        mv "$pending" "$selector_dir/c12.used" || return 1
        selector_exec sync || return 1
        [ ! -e "$pending" ] || return 1
        printf 'c12\n' > "$selector_state/mode" || return 1
        selector_exec c12
        # Never fall through to C07 in this boot after C12 consumed RNG.
        return $?
    fi
    selector_exec c07
}
c12_select_stop() {
    [ -f "$selector_state/mode" ] && [ ! -L "$selector_state/mode" ] || return 64
    case "$(cat "$selector_state/mode")" in
      c12) selector_exec c12-stop ;;
      c07) selector_exec c07-stop ;;
      *) return 64 ;;
    esac
}
