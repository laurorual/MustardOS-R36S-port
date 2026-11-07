#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C25: real package macro + reviewed dispatcher; survey only, no device writes."""
from pathlib import Path
import argparse, ipaddress, json, shutil, subprocess, tempfile
from phase4_candidate import sha, sums

repo=Path(__file__).resolve().parents[2]; work=repo/'build/phase4'; area=work/'rootfs-candidate'
p=argparse.ArgumentParser(description=__doc__); p.add_argument('--host',required=True,type=ipaddress.IPv4Address); p.add_argument('--base-stage',type=Path); a=p.parse_args()
old=a.base_stage.resolve() if a.base_stage else Path((area/'latest-update').read_text().strip())
assert old.is_relative_to(area)
op=json.loads((old/'plan.json').read_text())
assert json.loads((old/'reboot-return.json').read_text())['passed'], 'Start from approved C24r1 boot'
base=Path(op['candidate_stage']); candidate=Path(tempfile.mkdtemp(prefix='c25-source.',dir=area))
shutil.copytree(base/'target',candidate/'target',symlinks=True); root=candidate/'target'
stage=Path(tempfile.mkdtemp(prefix='c25-update.',dir=area))
rel=lambda x:'/work/'+str(x.relative_to(work))
makefile=stage/'install.mk'
makefile.write_text('''BR2_EXTERNAL_MUOS_R35S_PATH=/port/buildroot
TARGET_DIR='''+rel(root)+'''
INSTALL=install
include /port/buildroot/package/muos-r35s-launcher-once/muos-r35s-launcher-once.mk
.PHONY: /port/device/rk-r35s-p0/launcher-once/.install
/port/device/rk-r35s-p0/launcher-once/.install:
\t$(MUOS_R35S_LAUNCHER_ONCE_INSTALL_TARGET_CMDS)
''')
args=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z','-v',f'{repo}/port:/port:ro,z',(work/'rootfs-container.iid').read_text().strip(),'make','-f',rel(makefile)]
r=subprocess.run(args,capture_output=True,text=True,timeout=30)
(stage/'recipe.stdout').write_text(r.stdout); (stage/'recipe.stderr').write_text(r.stderr); assert r.returncode==0,(r.stdout,r.stderr)
inittab=root/'etc/inittab'; data=inittab.read_text(); assert 'muos-c25' not in data
data=data.replace('::sysinit:/usr/libexec/muos-c07-run\n','::sysinit:/usr/libexec/muos-c25/select.sh\n::sysinit:/usr/libexec/muos-c07-run\n::sysinit:/usr/libexec/muos-c25/session.sh start\n')
data=data.replace('::shutdown:/usr/libexec/muos-c07-run stop\n','::shutdown:/usr/libexec/muos-c25/session.sh stop\n::shutdown:/usr/libexec/muos-c07-run stop\n'); inittab.write_text(data)
paths=sorted(str(x.relative_to(root)) for x in (root/'usr/libexec/muos-c25').iterdir())+['usr/share/licenses/muos-r35s-launcher-once/LICENSE','usr/libexec/muos-session/prerequisites.sha256','etc/inittab']
foundation=root/'usr/libexec/muos-session/prerequisites.sha256'; records=sums(foundation); assert len(records)==89
for name in paths:
 if name!='usr/libexec/muos-session/prerequisites.sha256': records['/'+name]=sha(root/name)
foundation.write_text(''.join(d+'  '+n+'\n' for n,d in sorted(records.items())))
assert len(records)==96
dirs=['usr/libexec/muos-c25','usr/share/licenses/muos-r35s-launcher-once']
code='''set -eu
[ "$(readlink /proc/1/exe)" = /bin/busybox ]
findmnt -rn -o OPTIONS / | tr ',' '\\n' | grep -qx ro
. /usr/libexec/muos-diag-card-guard; [ "$(diag_card /sys)" = /dev/mmcblk0p1 ]
. /usr/libexec/muos-candidate-boot-checks; candidate_boot_check
/usr/libexec/muos-c07-network status
[ ! -e /var/lib/muos-diagnostic/c25.once ]; [ ! -L /var/lib/muos-diagnostic/c25.once ]
printf 'BOOT %s\\n' "$(cat /var/lib/muos-diagnostic/boot-seq)"
'''
for name in paths:
 code+=f'''if [ -e /{name} ] || [ -L /{name} ]; then
[ ! -L /{name} ]; [ -f /{name} ]; [ "$(stat -c '%u:%g:%h' /{name})" = 0:0:1 ]
printf 'F %s %s {name}\\n' "$(stat -c %a /{name})" "$(sha256sum /{name} | cut -d' ' -f1)"
else printf 'A 0 - {name}\\n'; fi
'''
for name in dirs: code+=f'[ ! -e /{name} ]; [ ! -L /{name} ]\n'
ssh=['ssh','-p','2222','-i',str(work/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(work/'private/c07-known_hosts'),'-oBatchMode=yes','-oConnectTimeout=8','root@'+str(a.host),'sh -s']
r=subprocess.run(ssh,input=code,capture_output=True,text=True,timeout=30)
for suffix,value in [('sh',code),('stdout',r.stdout),('stderr',r.stderr)]: (stage/('survey.'+suffix)).write_text(value)
assert r.returncode==0,(stage,r.stdout,r.stderr)
lines=r.stdout.splitlines(); boot=int(lines.pop(0).split()[1]); rows=[]
before=sums(base/'target/usr/libexec/muos-session/prerequisites.sha256')
for line in lines:
 kind,mode,digest,name=line.split()
 if kind=='F': assert digest==(sha(base/'target'/name)),('Drift from approved C24r1',name)
 rows.append({'path':name,'before':{'type':kind,'mode':int(mode,8),'sha256':digest},'after':{'type':'file','mode':(root/name).stat().st_mode&0o777,'sha256':sha(root/name)}})
sources=[Path(__file__),repo/'port/buildroot/Config.in',*sorted((repo/'port/buildroot/package/muos-r35s-launcher-once').glob('*')),*sorted((repo/'port/device/rk-r35s-p0/launcher-once').glob('*')),repo/'port/device/rk-r35s-p0/linux-diagnostic/card-guard.sh']
pins={str(s.relative_to(repo)):sha(s) for s in sources}
(candidate/'analysis.json').write_text(json.dumps({'passed':True,'revision':'C25','base_analysis_sha256':sha(base/'analysis.json'),'foundation_hashes':96,'recipe_actually_executed':True,'sources':pins,'image_built':False},indent=2)+'\n')
plan={'schema':1,'experiment':'C25_LAUNCHER_ONCE','candidate_stage':str(candidate),'candidate_analysis_sha256':sha(candidate/'analysis.json'),'boot_sequence':boot,'files':rows,'new_directories':[{'mode':0o755,'path':x} for x in dirs],'already_current_skipped':[],'factory_counter_excluded':True,'private_state_or_p3_in_payload':False,'reboot_requested':False,'previous_update_stage':str(old),'source_sha256':pins}
(stage/'plan.json').write_text(json.dumps(plan,indent=2)+'\n'); (stage/'foundation-before-source.sha256').write_bytes((base/'target/usr/libexec/muos-session/prerequisites.sha256').read_bytes())
(area/'latest-update').write_text(str(stage)+'\n'); print('C25 candidate + directed plan:',len(rows),'files, boot',boot,stage)
