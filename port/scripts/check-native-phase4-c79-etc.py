#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C99 test only private /etc creation/removal in the native mount namespace."""
from pathlib import Path
import argparse,base64,ipaddress,json,os,subprocess,tempfile
import phase4_c79_session as session
from phase4_backup_core import write_new,sync_dir


def main(host):
    os.umask(0o077);host=str(ipaddress.IPv4Address(host))
    qualified,boot=session.qualified();context,*_=session.historical()
    checks=Path((session.AREA/'latest-checks').read_text().strip())
    tested=json.loads((checks/'analysis.json').read_text());assert tested['passed']
    for n,h in tested['source_sha256'].items():assert session.sha(session.REPO/n)==h
    common=session.current_common('',0,boot['boot_sequence']);infra=context['infra']
    stage=Path(tempfile.mkdtemp(prefix='native-etc.',dir=session.AREA))
    ssh=['ssh','-p','2222','-i',str(session.WORK/'private/c07-client'),'-oIdentitiesOnly=yes',
        '-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222',
        '-oUserKnownHostsFile='+str(session.WORK/'private/c07-known_hosts'),'-oBatchMode=yes',
        '-oConnectTimeout=8','root@'+host,'sh -s']
    def remote(label,code):
        write_new(stage/(label+'.sh'),code.encode())
        r=subprocess.run(ssh,input=code,capture_output=True,text=True,timeout=40)
        for n,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]:write_new(stage/(label+'.'+n),v.encode())
        assert r.returncode==0,(label,stage);return r.stdout
    before=remote('preflight',common+infra)
    probe='''set -eu
dir=$1;state=$dir/state
[ "$(readlink /proc/self/ns/mnt)" != "$(readlink /proc/1/ns/mnt)" ]
. /usr/libexec/muos-session/runtime.sh
. "$dir/etc-view.sh"
mkdir -m 700 "$state";: > "$state/mounts"
finish() {
 rc=$?;trap - EXIT HUP INT TERM
 session_restore || rc=125
 [ ! -e /etc/asound.conf ] && [ ! -L /etc/asound.conf ] || rc=125
 [ ! -e /mnt/mmc ] && [ ! -L /mnt/mmc ] || rc=125
 exit "$rc"
}
trap finish EXIT
trap 'exit 143' HUP INT TERM
session_c79_etc_prepare
[ -f /etc/asound.conf ] && [ ! -L /etc/asound.conf ]
[ "$(stat -c '%u:%g:%a:%h:%s' /etc/asound.conf)" = 0:0:644:1:444 ]
cmp /etc/asound.conf /opt/muos/share/conf/rootfs/asound.conf
[ -d /mnt/mmc ] && [ ! -L /mnt/mmc ]
findmnt -rn -o OPTIONS / | tr ',' '\\n' | grep -qx ro
echo C99_PRIVATE_ETC_NATIVE_COPY_AND_BIND_VALID
'''
    helper=session.SESSION_NATIVE/'etc-view.sh'
    code=common+'''[ ! -e /etc/asound.conf ] && [ ! -L /etc/asound.conf ]
dir=$(mktemp -d /run/muos-c79-etc.XXXXXX)
before=$dir/global-before.txt
cat /proc/1/mountinfo > "$before"
cleanup() {
 rc=$?;trap - EXIT HUP INT TERM
 for info in /proc/[0-9]*/mountinfo;do
  [ -r "$info" ] || continue
  if awk -v prefix="$dir/" '$5 ~ "^"prefix {f=1} END{exit !f}' "$info" 2>/dev/null;then exit 125;fi
 done
 [ ! -e /etc/asound.conf ] && [ ! -L /etc/asound.conf ] || exit 125
 [ ! -e /mnt/mmc ] && [ ! -L /mnt/mmc ] || exit 125
 cmp /proc/1/mountinfo "$before" || exit 125
 rm -rf "$dir"
 exit "$rc"
}
trap cleanup EXIT
trap 'exit 143' HUP INT TERM
'''
    for name,data in [('etc-view.sh',helper.read_bytes()),('probe.sh',probe.encode())]:
        code+="printf '%s' '"+base64.b64encode(data).decode()+"' | base64 -d > \"$dir/"+name+"\"\n"
        code+='chmod 700 "$dir/'+name+'"\n'
    code+='''/usr/libexec/muos-session/bin/muos-run-bounded 15 /usr/libexec/muos-session/mount-namespace /bin/sh "$dir/probe.sh" "$dir"
'''
    assert remote('native',code)=='C99_PRIVATE_ETC_NATIVE_COPY_AND_BIND_VALID\n'
    assert remote('postflight',common+infra)==before
    report={'passed':True,'experiment':'C99_NATIVE_PRIVATE_ETC_CHECK','boot_sequence':boot['boot_sequence'],
        'C97_analysis_sha256':session.sha(qualified/'analysis.json'),'checks_analysis_sha256':session.sha(checks/'analysis.json'),
        'root_readonly_global_mounts_and_infrastructure_preserved':True,'original_asound_remains_absent':True,
        'original_mmc_mountpoint_remains_absent':True,'capsule_removed':True,'GUI_audio_core_or_ROM_started':False,
        'source_sha256':{str(p.relative_to(session.REPO)):session.sha(p) for p in [Path(__file__),helper,Path(session.__file__)]}}
    write_new(stage/'analysis.json',(json.dumps(report,indent=2)+'\n').encode());sync_dir(stage)
    (session.AREA/'latest-native-etc').write_text(str(stage)+'\n');sync_dir(session.AREA)
    print('C99 native private /etc copy/bind/restore passed without GUI:',stage)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True);main(p.parse_args().host)
