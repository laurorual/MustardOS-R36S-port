#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C58 headless C53 read adapter through the C57 installed store, p3 RO only."""
from pathlib import Path
import argparse,hashlib,io,ipaddress,json,re,subprocess,tarfile,tempfile
from phase4_candidate import sha,sums
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'gb-installed'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True,type=ipaddress.IPv4Address);p.add_argument('--source-load',required=True,type=Path);a=p.parse_args()
source=a.source_load.resolve();assert source.is_relative_to(work/'gb-reboot')
for name in ['gameboy-after-boot','save-store-installed']:
 proof=repo/'dist/phase4'/name
 for n,h in sums(proof/'SHA256SUMS').items():assert sha(proof/n)==h
r=json.loads((source/'analysis.json').read_text());assert r['passed'] and r['cleanup_passed'] and r['RAM_removed']
sanitized={k:('private' if k in {'private_identity','ROM_sha256','kernel_boot_id'} else v) for k,v in r.items()}
assert sanitized==json.loads((repo/'dist/phase4/gameboy-after-boot/load/analysis.json').read_text())
for n,h in r['source_sha256'].items():assert sha(repo/n)==h
boot=r['boot_sequence'];assert boot==69
identity=r['private_identity'];assert re.fullmatch('[0-9a-f]{64}',identity)
checks=Path((area/'latest-checks').read_text().strip());cr=json.loads((checks/'analysis.json').read_text());assert cr['passed'] and cr['case_count']==34
for n,h in cr['source_sha256'].items():assert sha(repo/n)==h
assert sha(checks/'store-base.sh')==cr['read_only_backend_sha256']
metadata=Path((work/'gb-state/latest-checks').read_text().strip());mr=json.loads((metadata/'analysis.json').read_text());assert mr['passed']
assert sha(metadata/'state-metadata')==mr['binary_sha256']==r['state_inspector_sha256']
installed=repo/'dist/phase4/save-store-installed';plan=json.loads((installed/'plan.json').read_text())
assert plan['files'][0]['sha256']==r['save_store_binary_sha256']
for row in plan['files']:
 line=row['sha256']+' '+f"{row['mode']:o}"+' '+row['path']
 assert line in (checks/'installed-store.sh').read_text()
# C54's inventory is a hash list, not raw commercial state. Keep its identity
# source receipt pinned; never fetch ROM/core/snapshot/PNG/INI bytes to the host.
expected_store=source/'collected/store-readonly-after.sha256'
assert expected_store.read_bytes()==(source/'collected/store-readonly-before.sha256').read_bytes()
health=(installed/'final-health.sh').read_text();common,infra=health.split('for name in udevd',1);infra='for name in udevd'+infra
stage=Path(tempfile.mkdtemp(prefix='native.',dir=area));(area/'latest-native-attempt').write_text(str(stage)+'\n')
ssh=['ssh','-p','2222','-i',str(work/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(work/'private/c07-known_hosts'),'-oBatchMode=yes','-oConnectTimeout=6','root@'+str(a.host)]
def remote(label,code,required=True,timeout=35):
 (stage/(label+'.sh')).write_text(code)
 result=subprocess.run(ssh+['sh -s'],input=code,capture_output=True,text=True,timeout=timeout)
 for n,v in [('stdout',result.stdout),('stderr',result.stderr),('exit',str(result.returncode)+'\n')]: (stage/(label+'.'+n)).write_text(v)
 if required:assert result.returncode==0,(stage,label,result.stdout[-1000:],result.stderr[-1800:])
 return result
before=remote('preflight',common+infra).stdout
capsule=remote('allocate',common+'mktemp -d /run/muos-prefs-data.XXXXXX\n').stdout.strip();assert re.fullmatch('/run/muos-prefs-data[.][A-Za-z0-9]{6}',capsule)
(stage/'intent.json').write_text(json.dumps({'directory':capsule,'boot_sequence':boot,'private_identity':identity,'source_C54_analysis_sha256':sha(source/'analysis.json'),'p3_mode':'ro,noload','game_or_ROM_sent':False,'store_ELF_sent':False},indent=2)+'\n')
assets={n:checks/n for n in ['store-base.sh','store.sh','installed-store.sh']}
assets['headless.sh']=repo/'port/device/rk-r35s-p0/gb-installed/headless.sh';assets['state-metadata']=metadata/'state-metadata'
files={n:f.read_bytes() for n,f in assets.items()}
files.update({'identity':(identity+'\n').encode(),'role':b'load\n','expected-store.sha256':expected_store.read_bytes(),
 'store-base.sha256':(sha(checks/'store-base.sh')+'\n').encode(),'installed-store.sha256':(sha(checks/'installed-store.sh')+'\n').encode()})
# Only the existing metadata inspector ELF is transferred; no CLI/core/UI/ROM.
assert 'save-store' not in files
buffer=io.BytesIO()
with tarfile.open(fileobj=buffer,mode='w') as archive:
 for name,data in files.items():
  item=tarfile.TarInfo(name);item.mode=0o700 if name in assets else 0o600;item.size=len(data);archive.addfile(item,io.BytesIO(data))
raw=subprocess.run(ssh+['tar -xf - -C '+capsule],input=buffer.getvalue(),capture_output=True,timeout=30);assert raw.returncode==0
verify=''.join(f"printf '%s  %s\\n' {hashlib.sha256(data).hexdigest()} {capsule}/{name} | sha256sum -c - >/dev/null\n" for name,data in files.items())
remote('prepare',common+verify+f'mkdir -m 700 {capsule}/state\n')
lock=repo/'port/device/rk-r35s-p0/muxretro-cpu/session-lock.sh'
call=common+lock.read_text()+f'''cat /proc/1/mountinfo > {capsule}/global-before.txt
/usr/libexec/muos-run-bounded 45 /usr/libexec/muos-session/mount-namespace /bin/sh {capsule}/headless.sh {capsule}
'''
result=remote('native',call,required=False,timeout=60)
after=remote('postflight',common+infra).stdout;assert after==before
remote('mounts',common+f'cmp /proc/1/mountinfo {capsule}/global-before.txt\n')
# Whitelist metadata/logs only. No state, PNG or INI is ever collected.
names=['store-seed.log','store-verify.log','seed-metadata.txt','store-readonly-before.sha256','store-readonly-after.sha256','store-prefs-seed-before.sha256','store-prefs-seed-after.sha256','store-prefs-verify-before.sha256','store-prefs-verify-after.sha256']
collect=common+f'cd {capsule}/state\nset --\nfor name in '+' '.join(names)+';do [ ! -f "$name" ] || set -- "$@" "$name";done\ntar -cf - "$@"\n'
raw=subprocess.run(ssh+['sh -s'],input=collect.encode(),capture_output=True,timeout=30)
assert raw.returncode==0,('Inspect owned capsule; do not redispatch',stage)
collected=stage/'collected';collected.mkdir()
with tarfile.open(fileobj=io.BytesIO(raw.stdout)) as archive:
 for item in archive.getmembers():
  assert item.isfile() and item.name in names and item.size<65536
  (collected/item.name).write_bytes(archive.extractfile(item).read())
cleanup=common+f'''for info in /proc/[0-9]*/mountinfo; do
 [ -r "$info" ] || continue
 if awk -v prefix={capsule}/ '$5 ~ "^"prefix {{f=1}} END{{exit !f}}' "$info" 2>/dev/null;then exit 64;fi
done
[ ! -L {capsule} ];[ "$(stat -c '%u:%g:%a' {capsule})" = 0:0:700 ]
rm -rf {capsule}
echo C58_RAM_REMOVED_ROOT_RO_P3_UNMOUNTED
'''
remote('cleanup',cleanup)
assert result.returncode==0,(stage,result.stderr,result.stdout)
assert 'C58_INSTALLED_BACKEND_SEED_VERIFY_OK' in result.stdout and 'C58_HEADLESS_END status=0 cleanup=0' in result.stdout
assert re.search(r'C51_STATE_VALID version=1 core_bytes=26861 core_crc_valid=1 manifest_valid=1 thumbnail_signature_valid=1 tmpfs=1',result.stdout)
assert (collected/'store-readonly-before.sha256').read_bytes()==expected_store.read_bytes()==(collected/'store-readonly-after.sha256').read_bytes()
for op in ['seed','verify']:
 assert (collected/f'store-prefs-{op}-before.sha256').read_bytes()==(collected/f'store-prefs-{op}-after.sha256').read_bytes()
logs=''.join((collected/n).read_text() for n in ['store-seed.log','store-verify.log'])
assert logs.count('C58_INSTALLED_DISPATCH operation=status')==2 and logs.count('C58_INSTALLED_DISPATCH operation=export')==1
sources=[Path(__file__),lock,*assets.values()]
report={'passed':True,'experiment':'C58_INSTALLED_STORE_HEADLESS','boot_sequence':boot,'source_C54_analysis_sha256':sha(source/'analysis.json'),
 'private_identity':identity,'C57_proof_sha256':sha(installed/'SHA256SUMS'),'checks_analysis_sha256':sha(checks/'analysis.json'),
 'installed_CLI_used':True,'store_ELF_transferred':False,'source_snapshot_generation':1,'snapshot_matches_C54':True,
 'core_bytes':26861,'PKST_CRC_manifest_PNG_signature_valid':True,'native_dispatch_calls':{'status':2,'export':1},
 'real_p3_read_only_noload':True,'card_saves_written':False,'installed_files_modified':False,'root_read_only':True,
 'foundation_files':97,'infrastructure_unchanged':True,'global_mountinfo_unchanged':True,'cleanup_passed':True,'RAM_removed':True,
 'reboot_requested':False,'UI_core_ROM_or_audio_started':False,'original_32GB_or_Deck_accessed':False,
 'source_sha256':{str(f.relative_to(repo)):sha(f) for f in sources if f.is_relative_to(repo/'port')}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-native').write_text(str(stage)+'\n')
print('C58 installed CLI: native read-only seed/verify, no CLI/ROM transfer, cleanup OK:',stage)
