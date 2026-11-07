#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C24r1 two-file plan: own C07 umask + refreshed foundation; counter untouched."""
from pathlib import Path
import argparse,ipaddress,json,shutil,subprocess,tempfile
from phase4_candidate import sha,sums

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/rootfs-candidate'
p=argparse.ArgumentParser();p.add_argument('--host',required=True,type=ipaddress.IPv4Address);a=p.parse_args()
old=Path((area/'latest-update').read_text().strip());oldplan=json.loads((old/'plan.json').read_text());assert json.loads((old/'counter-mode-repair.json').read_text())['passed']
source=repo/'port/device/rk-r35s-p0/network-diagnostic/run.sh';base=Path(oldplan['candidate_stage'])
candidate=Path(tempfile.mkdtemp(prefix='umask-source.',dir=area));shutil.copytree(base/'target',candidate/'target',symlinks=True)
root=candidate/'target';shutil.copyfile(source,root/'usr/libexec/muos-c07-run');(root/'usr/libexec/muos-c07-run').chmod(0o755)
f= root/'usr/libexec/muos-session/prerequisites.sha256';records=sums(f);assert '/usr/libexec/muos-c07-run' in records;records['/usr/libexec/muos-c07-run']=sha(source)
f.write_text(''.join(d+'  '+n+'\n' for n,d in records.items()))
cm={'passed':True,'revision':'C24r1','base_C23_analysis_sha256':sha(base/'analysis.json'),'source':{'path':str(source.relative_to(repo)),'sha256':sha(source)},'counter_bytes_in_payload':False,'image_built':False};(candidate/'analysis.json').write_text(json.dumps(cm,indent=2)+'\n')
stage=Path(tempfile.mkdtemp(prefix='update-r1.',dir=area))
paths=['usr/libexec/muos-c07-run','usr/libexec/muos-session/prerequisites.sha256']
code='''set -eu
[ "$(readlink /proc/1/exe)" = /bin/busybox ];findmnt -rn -o OPTIONS / | tr ',' '\\n' | grep -qx ro
. /usr/libexec/muos-diag-card-guard;[ "$(diag_card /sys)" = /dev/mmcblk0p1 ]
. /usr/libexec/muos-candidate-boot-checks;candidate_boot_check
/usr/libexec/muos-c07-network status
printf 'BOOT %s\\n' "$(cat /var/lib/muos-diagnostic/boot-seq)"
'''
for name in paths:code+=f'''[ ! -L /{name} ];[ "$(stat -c '%u:%g:%h' /{name})" = 0:0:1 ];printf 'F %s %s {name}\\n' "$(stat -c %a /{name})" "$(sha256sum /{name} | cut -d' ' -f1)"\n'''
ssh=['ssh','-p','2222','-i',str(repo/'build/phase4/private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(repo/'build/phase4/private/c07-known_hosts'),'-oBatchMode=yes','root@'+str(a.host),'sh -s']
r=subprocess.run(ssh,input=code,capture_output=True,text=True,timeout=30);(stage/'survey.sh').write_text(code);(stage/'survey.stdout').write_text(r.stdout);(stage/'survey.stderr').write_text(r.stderr);assert r.returncode==0,(r.stdout,r.stderr)
lines=r.stdout.splitlines();boot=int(lines.pop(0).split()[1]);rows=[]
for line in lines:
 kind,mode,digest,name=line.split();rows.append({'path':name,'before':{'type':kind,'mode':int(mode,8),'sha256':digest},'after':{'type':'file','mode':(root/name).stat().st_mode&0o777,'sha256':sha(root/name)}})
plan={'schema':1,'experiment':'C24_R1_COUNTER_UMASK','candidate_stage':str(candidate),'candidate_analysis_sha256':sha(candidate/'analysis.json'),'boot_sequence':boot,'files':rows,'new_directories':[],'already_current_skipped':[],'factory_counter_excluded':True,'private_state_or_p3_in_payload':False,'reboot_requested':False,'previous_update_stage':str(old),'source_sha256':{str(Path(__file__).relative_to(repo)):sha(Path(__file__)),str(source.relative_to(repo)):sha(source)}}
(stage/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
(stage/'foundation-before-source.sha256').write_bytes((base/'target/usr/libexec/muos-session/prerequisites.sha256').read_bytes())
(area/'latest-update').write_text(str(stage)+'\n');print('C24r1 two-file plan; counter stays',boot,stage)
