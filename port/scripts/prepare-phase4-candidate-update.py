#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Survey only public candidate paths and stage a directed C24 update."""
from pathlib import Path
import argparse,json,re,subprocess,tempfile
from phase4_candidate import sha,sums

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/rootfs-candidate'
p=argparse.ArgumentParser();p.add_argument('--host',required=True);a=p.parse_args()
import ipaddress
ipaddress.IPv4Address(a.host)
candidate=Path((area/'latest-composition').read_text().strip());meta=json.loads((candidate/'analysis.json').read_text())
assert meta['passed'] and not meta['device_written']
for name,digest in meta['sources'].items():assert sha(repo/name)==digest
proof=repo/'dist/phase4/rootfs-candidate-composition'
for name,digest in sums(proof/'SHA256SUMS').items():assert sha(proof/name)==digest
assert (candidate/'analysis.json').read_bytes()==(proof/'analysis.json').read_bytes()
stage=Path(tempfile.mkdtemp(prefix='update.',dir=area));(area/'latest-update').write_text(str(stage)+'\n')
changes=json.loads((candidate/'changes.json').read_text());root=candidate/'target'
files={n:r for n,r in changes.items() if r['type']=='file' and n!='var/lib/muos-diagnostic/boot-seq'}
files['etc/inittab']={'type':'file','mode':0o644,'sha256':sha(root/'etc/inittab')}
for name,record in json.loads((root/'usr/share/muos-r35s-profile/manifest.json').read_text())['files'].items():
 files[name]={'type':'file','mode':record['mode'],'sha256':record['sha256']}
dirs={n:r for n,r in changes.items() if r['type']=='directory' and not n.startswith('var/')}
# All immutable foundation paths outside the directed write set must already
# match; the installed C12 selector is an expected before-state, not imported.
foundation=sums(root/'usr/libexec/muos-session/prerequisites.sha256')
requested=set(files)|set(dirs)|{n.lstrip('/') for n in foundation if n.lstrip('/') not in files}
assert all(re.fullmatch(r'[a-zA-Z0-9_./-]+',n) and '..' not in n for n in requested)
ssh=['ssh','-p','2222','-i',str(repo/'build/phase4/private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(repo/'build/phase4/private/c07-known_hosts'),'-oBatchMode=yes','-oConnectTimeout=8','root@'+a.host]
code='''set -eu
boot_package=/usr/libexec/muos-boot;. "$boot_package/native-functions.sh"
c12_guard;c12_read_config;c12_root_ro;c12_session_quiescent || exit 1
[ ! -e /var/lib/muos-diagnostic/c12.once ];[ ! -d /sys/module/btusb ]
sha256sum -c /usr/libexec/muos-session/prerequisites.sha256 >/dev/null
printf 'BOOT %s\\n' "$(cat /var/lib/muos-diagnostic/boot-seq)"
'''
code+='for name in '+' '.join(sorted(requested))+''';do
 p=/$name
 parent=$(dirname "$p")
 while [ "$parent" != / ] && [ "$parent" != // ];do [ ! -L "$parent" ];parent=$(dirname "$parent");done
 [ ! -L "$p" ]
 if [ -f "$p" ];then
  [ "$(stat -c '%u:%g:%h' "$p")" = 0:0:1 ]
  printf 'F %s %s %s\\n' "$(stat -c %a "$p")" "$(sha256sum "$p" | cut -d' ' -f1)" "$name"
 elif [ -d "$p" ];then
  [ "$(stat -c '%u:%g' "$p")" = 0:0 ]
  printf 'D %s - %s\\n' "$(stat -c %a "$p")" "$name"
 else [ ! -e "$p" ];printf 'N 0 - %s\\n' "$name";fi
done
'''
(stage/'survey.sh').write_text(code)
r=subprocess.run(ssh+['sh -s'],input=code,capture_output=True,text=True,timeout=40)
(stage/'survey.stdout').write_text(r.stdout);(stage/'survey.stderr').write_text(r.stderr);assert r.returncode==0,(r.stdout,r.stderr)
lines=r.stdout.splitlines();assert lines[0].startswith('BOOT ');boot=int(lines.pop(0).split()[1]);before={}
for line in lines:
 kind,mode,digest,name=line.split();before[name]={'type':kind,'mode':int(mode,8),'sha256':digest}
assert set(before)==requested
drift=[]
for name,digest in foundation.items():
 n=name.lstrip('/')
 if n not in files and (before[n]['type']!='F' or before[n]['sha256']!=digest):drift.append(n)
assert not drift,('foundation drift outside directed profile/runtime set',drift)
rows=[];skipped=[]
for n,rec in sorted(files.items()):
 b=before[n];assert b['type'] in ('F','N'),n
 if b['sha256']==rec['sha256'] and b['mode']==rec['mode']:skipped.append(n);continue
 rows.append({'path':n,'before':b,'after':rec})
rows.sort(key=lambda r:(r['path']=='etc/inittab',r['path']=='sbin/muos-ext4-diag',r['path']))
new_dirs=[]
for n,rec in sorted(dirs.items(),key=lambda item:(len(Path(item[0]).parts),item[0])):
 assert before[n]['type'] in ('D','N'),n
 if before[n]['type']=='N':new_dirs.append({'path':n,'mode':rec['mode']})
plan={'schema':1,'experiment':'C24_DIRECTED_ROOTFS_UPDATE','candidate_stage':str(candidate),'candidate_analysis_sha256':sha(candidate/'analysis.json'),'boot_sequence':boot,'files':rows,'new_directories':new_dirs,'already_current_skipped':skipped,'factory_counter_excluded':True,'private_state_or_p3_in_payload':False,'reboot_requested':False,'source_sha256':{str(Path(__file__).relative_to(repo)):sha(Path(__file__))}}
(stage/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print('C24 public-file plan prepared:',len(rows),'writes;',len(new_dirs),'new directories;',len(skipped),'already-current skipped; boot',boot,stage)
