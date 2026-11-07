#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C52: actual p3 audit RO; transactions only in an owned RAM-backed ext4 image."""
from pathlib import Path
import argparse,gzip,io,ipaddress,json,re,struct,subprocess,tarfile,tempfile,zlib
from phase4_candidate import sha,sums
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True,type=ipaddress.IPv4Address);p.add_argument('--boot',required=True,type=int);args=p.parse_args()
repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'save-store'
build=Path((area/'latest-ext4-build').read_text().strip());br=json.loads((build/'analysis.json').read_text());assert br['passed']
checks=Path(br['checks_stage']);cr=json.loads((checks/'analysis.json').read_text());assert cr['passed'] and sha(checks/'analysis.json')==br['checks_analysis_sha256']
for report in [br,cr]:
 for n,h in report['source_sha256'].items():assert sha(repo/n)==h
for n,h in br['payload_sha256'].items():assert sha(build/n)==h
baseline=repo/'dist/phase4/muxretro-native-cpu'
for n,h in sums(baseline/'SHA256SUMS').items():assert sha(baseline/n)==h
common,infra=(baseline/'preflight.sh').read_text().split('for name in udevd',1);infra='for name in udevd'+infra
common=common.replace('= 65 ]','= '+str(args.boot)+' ]')
stage=Path(tempfile.mkdtemp(prefix='native.',dir=area));(area/'latest-native-attempt').write_text(str(stage)+'\n')
ssh=['ssh','-p','2222','-i',str(work/'private/c07-client'),'-oIdentitiesOnly=yes','-oStrictHostKeyChecking=yes',
     '-oHostKeyAlias=[192.168.15.17]:2222','-oUserKnownHostsFile='+str(work/'private/c07-known_hosts'),'-oBatchMode=yes','-oConnectTimeout=6','root@'+str(args.host)]
def remote(label,code,timeout=35,required=True):
 (stage/(label+'.sh')).write_text(code)
 r=subprocess.run(ssh+['sh -s'],input=code,text=True,capture_output=True,timeout=timeout)
 for n,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/(label+'.'+n)).write_text(v)
 if required:assert r.returncode==0,(stage,label,r.stdout[-2000:],r.stderr)
 return r
loops='for loop in /sys/class/block/loop[0-7];do [ ! -e "$loop/loop/backing_file" ] || exit 64;done\n'
before=remote('preflight',common+infra+loops).stdout
dirs=remote('allocate',common+'mktemp -d /run/muos-prefs-data.XXXXXX\nmktemp -d /run/muos-prefs-ext4.XXXXXX\n').stdout.splitlines();assert len(dirs)==2
audit,lab=dirs
assert re.fullmatch('/run/muos-prefs-data[.][a-zA-Z0-9]{6}',audit) and re.fullmatch('/run/muos-prefs-ext4[.][a-zA-Z0-9]{6}',lab)
(stage/'intent.json').write_text(json.dumps({'audit_directory':audit,'lab_directory':lab,'boot_sequence':args.boot,'real_p3':'ro,noload','lab_bytes':16777216,'commercial_content':False,'reboot':False,'installed_files_modified':False},indent=2)+'\n')
payload={n:(build/n).read_bytes() for n in ['muos-save-store','phase4-save-store-ext4','data.ext4','transaction.sh']}
for label in ['a','b']:
 core=label.encode()*1024
 data={'quicksave.state':b'PKST'+struct.pack('<HHIIII',1,0,len(core),0,zlib.crc32(core),0)+bytes(8)+core,
       'states.ini':b'[quicksave]\nname=synthetic\ncreated=1\ncrc=synthetic\ncore=synthetic\ncore_version=synthetic\n',
       'quicksave.png':b'\x89PNG\r\n\x1a\nsynthetic'}
 for n,b in data.items():payload[f'source-{label}/'+n]=b
def upload(directory,files):
 b=io.BytesIO()
 with tarfile.open(fileobj=b,mode='w') as archive:
  for d in sorted({str(Path(n).parent) for n in files if '/' in n}):
   item=tarfile.TarInfo(d);item.type=tarfile.DIRTYPE;item.mode=0o700;archive.addfile(item)
  for n,data in files.items():
   item=tarfile.TarInfo(n);item.size=len(data);item.mode=0o700 if n in {'muos-save-store','phase4-save-store-ext4','transaction.sh','audit-data.sh'} else 0o600
   archive.addfile(item,io.BytesIO(data))
 r=subprocess.run(ssh+['tar -xf - -C '+directory],input=b.getvalue(),capture_output=True,timeout=45);assert r.returncode==0,r.stderr
def verify(directory,files):
 import hashlib
 return ''.join(f"printf '%s  %s\\n' {hashlib.sha256(b).hexdigest()} {directory}/{n} | sha256sum -c -\n" for n,b in files.items())
native=None;cleanup_ok=False
try:
 upload(lab,payload);audit_payload={'audit-data.sh':(build/'audit-data.sh').read_bytes()};upload(audit,audit_payload)
 lock=repo/'port/device/rk-r35s-p0/muxretro-cpu/session-lock.sh'
 code=common+loops+lock.read_text()+verify(lab,payload)+verify(audit,audit_payload)+f'''
cat /proc/1/mountinfo > {lab}/global-before
/usr/libexec/muos-run-bounded 25 /usr/libexec/muos-session/mount-namespace /bin/sh {audit}/audit-data.sh {audit}
mkdir -m 700 {lab}/mnt
{lab}/phase4-save-store-ext4 {lab}
'''+loops+f'cmp /proc/1/mountinfo {lab}/global-before\necho C52_GLOBAL_MOUNTS_IDENTICAL\n'
 native=remote('native',code,timeout=85,required=False)
 after=remote('postflight',common+infra+loops).stdout;assert before==after
 if native.returncode==0:
  r=subprocess.run(ssh+['gzip -c '+lab+'/data.ext4'],capture_output=True,timeout=30);assert r.returncode==0
  image=gzip.decompress(r.stdout);assert len(image)==16777216;(stage/'after.ext4').write_bytes(image)
finally:
 cleanup=common+loops+f'''
for dir in {audit} {lab};do
 [ -d "$dir" ] && [ ! -L "$dir" ] && [ "$(stat -c '%u:%g:%a' "$dir")" = 0:0:700 ]
 for info in /proc/[0-9]*/mountinfo;do
  [ -r "$info" ] || continue
  if awk -v prefix="$dir/" '$5 ~ "^"prefix {{f=1}} END{{exit !f}}' "$info" 2>/dev/null;then exit 64;fi
 done
done
[ ! -f {lab}/global-before ] || cmp /proc/1/mountinfo {lab}/global-before
rm -rf {audit} {lab}
c25_ready
echo C52_RAM_REMOVED_REAL_DATA_UNMOUNTED_ROOT_RO_FOUNDATION97_NETWORK_OK
'''
 cleanup_ok=remote('cleanup',cleanup,required=False).returncode==0
assert cleanup_ok,'Inspect owned loop/mount evidence before removing anything'
assert native is not None and native.returncode==0,(stage,native.stderr if native else None)
text=native.stdout
for marker in ['C52_REAL_DATA_RO_NOLOAD_PREFS_UNCHANGED','C52_EXT4_LAB_OK_ROOT_RO_NO_CARD_WRITES','C52_GLOBAL_MOUNTS_IDENTICAL']:
 assert marker in text,marker
rel='/work/'+str(stage.relative_to(work))
code=f'''cd {rel}
e2fsck -fn after.ext4 > fsck-after.txt 2>&1
debugfs -R 'cat /store/HEAD' after.ext4 > head-after.txt 2> debugfs.stderr
'''
r=subprocess.run(['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id','--tmpfs','/tmp:rw,nosuid,nodev','-v',f'{work}:/work:rw,z',(work/'rootfs-container.iid').read_text().strip(),'sh','-eu','-c',code],capture_output=True,text=True,timeout=30)
(stage/'offline.stderr').write_text(r.stderr);assert r.returncode==0,(stage,r.stderr)
assert 'CURRENT=00000001\nPREVIOUS=00000000\nNEXT=00000003\n' in (stage/'head-after.txt').read_text()
report={'passed':True,'experiment':'C52_SAVE_STORE_NATIVE_LAB','boot_sequence':args.boot,
        'real_data_read_only_noload':True,'native_ext4_two_generations_remount_and_explicit_recovery':True,
        'ext4_readonly_write_refused':True,'non_RAM_source_refused':True,'corrupt_generation_preserved':True,
        'after_image_fsck_passed':True,'cleanup_passed':True,'RAM_removed':True,
        'root_ro_and_infrastructure_preserved':True,'global_mountinfo_unchanged':True,
        'private_ROM_states_or_audio_used':False,'real_card_saves_written':False,'rebooted':False,
        'ext4_build_stage':str(build),'ext4_build_analysis_sha256':sha(build/'analysis.json'),
        'after_image_sha256':sha(stage/'after.ext4'),
        'source_sha256':{str(f.relative_to(repo)):sha(f) for f in [Path(__file__),lock]}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-native').write_text(str(stage)+'\n')
print('C52 native RO audit and RAM-backed ext4 transaction/recovery passed:',stage)
