#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# shellcheck disable=SC2016 # device-side commands in single quotes
# v1.1.1 T2: the manual online update (Task Toolkit -> Check for Online
# Update; /usr/libexec/muos-update check | fetch). A local release (the
# GitHub API's JSON with file:// assets) is served through
# /run/muos/update-test (root-only tmpfs, gone at the next start).
#   t2-online-update.sh unit    the task headless (the frontend's protocol on
#                               fd 3, answers on stdin) against a 24 MB fake
#                               v9.9.9: up to date, Cancel, Download + Later;
#                               plus GitHub's real latest seen from v1.1.1
#                               (must not be offered: no downgrade)
#   t2-online-update.sh serve GZ   serve GZ (NAME.p2.img.gz with its .sha256
#                               next to it, pushed to MUOS/t2/online) as the
#                               newer release v9.9.9, for a run from the menu
#   t2-online-update.sh clean   remove the test release and update files
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
dev=port/scripts/device.sh
r() { "$dev" run "$@" < /dev/null; }
d=/userdata/MUOS/t2/online
mock='
d=/userdata/MUOS/t2/online gz=$d/MustardOS-R36S-port-v9.9.9.p2.img.gz
sha=${gz%.gz}.sha256
cat > $d/latest.json <<J
{"tag_name": "v9.9.9", "assets": [
 {"name": "${sha##*/}", "size": $(stat -c %s $sha), "browser_download_url": "file://$sha"},
 {"name": "${gz##*/}", "size": $(stat -c %s $gz), "browser_download_url": "file://$gz"}]}
J
printf "MUOS_UPDATE_API=file://%s\n" $d/latest.json > /run/muos/update-test'
# run_task RELEASE ANSWER...: run the task as the frontend would, print its
# records (ui.sh sends fd 3 to stdout in native mode) as "TYPE FIELDS" lines
run_task() {
    local rel=$1; shift
    r "printf 'MUOS_UPDATE_RELEASE=%s\n' '$rel' >> /run/muos/update-test
       . /usr/share/muos-r35s/update-task.sh
       for a in $*; do printf 'MUOS:RESPONSE\tID=x\tVALUE=%s\n' \"\$(T \"\$(echo \$a | tr _ ' ')\")\"; done > $d/answers
       cd /tmp && MUOS_TASK_UI=1 sh '/opt/muos/share/task/Check for Online Update.sh' < $d/answers > $d/rec.txt 2> /dev/null
       echo \"exit \$?\"; awk -F '\t' '/^MUOS:/ && \$1 != \"MUOS:PROGRESS\" { sub(/^MUOS:/, \"\"); \$1 = \$1; print }' OFS=' ' $d/rec.txt
       echo \"progress \$(grep -c '^MUOS:PROGRESS' $d/rec.txt)\"
       sed -i '/^MUOS_UPDATE_RELEASE=/d' /run/muos/update-test"
}
fail=0
check() { if grep -q -- "$2" <<< "$3"; then echo "PASS $1"; else echo "FAIL $1 (want: $2)"; echo "$3" | sed 's/^/    /'; fail=1; fi; }
case ${1:-unit} in
unit)
    r 'ls /userdata/MUOS/update/*.p2.img.gz* 2>/dev/null' && { echo 'MUOS/update holds an update: not touched'; exit 1; }
    r "mkdir -p $d && cd $d && head -c 25165824 /dev/urandom > p2 &&
       echo \"\$(sha256sum p2 | cut -d' ' -f1)  MustardOS-R36S-port-v9.9.9.p2.img\" > MustardOS-R36S-port-v9.9.9.p2.img.sha256 &&
       gzip -1 -c p2 > MustardOS-R36S-port-v9.9.9.p2.img.gz && rm p2" || exit 1
    out=$(r 'rm -f /run/muos/update-test; MUOS_UPDATE_RELEASE=MustardOS-R36S-port-v1.1.1 /usr/libexec/muos-update check; echo rc=$?')
    check 'GitHub latest from v1.1.1: not offered (no downgrade)' 'rc=1' "$out"
    r "$mock" || exit 1
    out=$(run_task MustardOS-R36S-port-v9.9.9)
    check 'same version: latest' "COMPLETE TEXT=$(r '. /usr/share/muos-r35s/update-task.sh; T "You have the latest version"')" "$out"
    out=$(run_task MustardOS-R36S-port-v1.1.1 Cancel)
    check 'newer: asks with the version' 'PROMPT ID=update_available.*v9.9.9' "$out"
    check 'Cancel: nothing downloaded' "COMPLETE TEXT=$(r '. /usr/share/muos-r35s/update-task.sh; T "Not downloaded"')" "$out"
    out=$(r 'ls /userdata/MUOS/update/*.p2.img.gz* 2>/dev/null; echo n=$?')
    check 'Cancel: MUOS/update empty' 'n=[12]' "$out"
    out=$(run_task MustardOS-R36S-port-v1.1.1 Download Later)
    check 'Download: progress shown' 'progress [1-9]' "$out"
    check 'Download: asks to install' 'PROMPT ID=install_update' "$out"
    check 'Later: kept for Install Firmware Update' "COMPLETE TEXT=$(r '. /usr/share/muos-r35s/update-task.sh; T "Saved in MUOS/update. To install it later:"')" "$out"
    out=$(r "cd /userdata/MUOS/update && cmp MustardOS-R36S-port-v9.9.9.p2.img.gz $d/MustardOS-R36S-port-v9.9.9.p2.img.gz && cmp MustardOS-R36S-port-v9.9.9.p2.img.sha256 $d/MustardOS-R36S-port-v9.9.9.p2.img.sha256 && echo same")
    check 'Download: the files in MUOS/update' 'same' "$out"
    r "rm -f /userdata/MUOS/update/MustardOS-R36S-port-v9.9.9.* /run/muos/update-test; rm -rf $d"
    [ "$fail" = 0 ] && echo 'PASS t2-online-update unit' || exit 1 ;;
serve)
    gz=${2:?serve GZ}; [ -f "${gz%.gz}.sha256" ] || { echo "no ${gz%.gz}.sha256" >&2; exit 1; }
    r "mkdir -p $d" || exit 1
    "$dev" push "$gz" "$d" && "$dev" push "${gz%.gz}.sha256" "$d" || exit 1  # into the directory DST
    r "cd $d && mv -f '${gz##*/}' MustardOS-R36S-port-v9.9.9.p2.img.gz &&
       mv -f '$(basename "${gz%.gz}.sha256")' MustardOS-R36S-port-v9.9.9.p2.img.sha256" || exit 1
    r "$mock && echo MUOS_UPDATE_RELEASE=MustardOS-R36S-port-v1.1.1 >> /run/muos/update-test && /usr/libexec/muos-update check" ;;
clean) r "rm -f /userdata/MUOS/update/MustardOS-R36S-port-v9.9.9.* /run/muos/update-test; rm -rf $d" ;;
*) sed -n '7,18p' "$0"; exit 2 ;;
esac
