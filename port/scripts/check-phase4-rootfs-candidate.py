#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C23 refusal fixtures on disposable host trees; no mounts or device access."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
from phase4_candidate import inventory,sha,validate

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/rootfs-candidate'
base=Path((area/'latest-composition').read_text().strip());assert not (base/'superseded.json').exists()
meta=json.loads((base/'analysis.json').read_text());assert meta['passed'] and meta['boot_contract_checked_before_and_after_image']
for name,digest in meta['sources'].items():assert sha(repo/name)==digest,name
stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area));cases={}
before=inventory(base/'target');image_hash=sha(base/'images/rootfs.ext4')
def candidate(root):
 report=validate(root)
 if meta.get('C36_direct_zero_PCM_integrated'):
  eq=json.loads((base/'native-C36-equivalence.json').read_text());assert eq['passed']
  assert sha(base/'native-C36-equivalence.json')==meta['native_C36_equivalence_sha256']
  for name,digest in eq['public_file_sha256'].items():assert sha(root/name)==digest,name
 return report
assert candidate(base/'target')['passed'];cases['complete_readback_tree']=True

def write(root,name,text):
 p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)

def test(name,change):
 root=stage/'fixture';shutil.copytree(base/'target',root,symlinks=True)
 try:
  change(root);snapshot=inventory(root)
  try:candidate(root)
  except (AssertionError,ValueError,OSError):pass
  else:raise AssertionError('unexpected success: '+name)
  assert inventory(root)==snapshot,'validator wrote fixture'
  cases[name]=True
 finally:shutil.rmtree(root)

test('automatic_session_refused',lambda r:write(r,'etc/default/muos-session',(r/'etc/default/muos-session').read_text().replace('enabled=0\n','enabled=1\n',1)))
test('permanent_preferences_refused',lambda r:write(r,'etc/default/muos-session',(r/'etc/default/muos-session').read_text().replace('preferences_enabled=0','preferences_enabled=1')))
test('generic_rcS_dispatch_refused',lambda r:write(r,'etc/inittab',(r/'etc/inittab').read_text()+'::sysinit:/etc/init.d/rcS\n'))
test('seed_inclusion_refused',lambda r:write(r,'var/lib/muos-seedrng/seed','fixture only; not entropy\n'))
test('private_host_key_refused',lambda r:write(r,'etc/dropbear/dropbear_ed25519_host_key','fixture only; not a key\n'))
test('changed_runtime_helper_refused',lambda r:write(r,'usr/libexec/muos-session/data-functions.sh','changed\n'))
test('stale_post_overlay_foundation_refused',lambda r:write(r,'usr/libexec/muos-session/prerequisites.sha256','0'*64+'  /etc/inittab\n'))
test('manifest_escape_refused',lambda r:write(r,'usr/libexec/muos-session/payload.sha256',(r/'usr/libexec/muos-session/payload.sha256').read_text()+'0'*64+'  ../outside\n'))
test('missing_counter_refused',lambda r:(r/'var/lib/muos-diagnostic/boot-seq').unlink())
if meta.get('C25_and_C26_integrated'):
 def refresh(r):
  # Preserve valid nested hash tables so the tests exercise semantic guards,
  # not only the outer digest of an intentionally changed file.
  from phase4_candidate import sums
  profile=r/'usr/share/muos-r35s-profile';pm=profile/'manifest.json';data=json.loads(pm.read_text())
  data['profile_sha256']=sha(profile/'profile.json')
  for name,row in data['files'].items():row['sha256']=sha(r/name)
  pm.write_text(json.dumps(data,indent=2)+'\n')
  f=r/'usr/libexec/muos-session/profile-source.sha256';records=sums(f);f.write_text(''.join(sha(profile/n)+'  '+n+'\n' for n in records))
  f=r/'usr/libexec/muos-session/payload.sha256';records=sums(f);f.write_text(''.join(sha(r/'usr/libexec/muos-session'/n)+'  '+n+'\n' for n in records))
  f=r/'usr/libexec/muos-session/prerequisites.sha256';records=sums(f);f.write_text(''.join(sha(r/n.lstrip('/'))+'  '+n+'\n' for n in records))
 def dispatcher(r,mode):
  f=r/'etc/inittab';t=f.read_text()
  if mode=='missing':t=t.replace('::sysinit:/usr/libexec/muos-c25/select.sh\n','')
  elif mode=='duplicate':t+='::sysinit:/usr/libexec/muos-c25/session.sh start\n'
  else:t=t.replace('::sysinit:/usr/libexec/muos-c25/select.sh\n::sysinit:/usr/libexec/muos-c07-run','::sysinit:/usr/libexec/muos-c07-run\n::sysinit:/usr/libexec/muos-c25/select.sh')
  f.write_text(t);refresh(r)
 for mode in ['missing','duplicate','reordered']:test('C25_dispatch_'+mode+'_with_fresh_hashes',lambda r,mode=mode:dispatcher(r,mode))
 test('C25_once_dangling_symlink_refused',lambda r:(r/'var/lib/muos-diagnostic/c25.once').symlink_to('/missing'))
 test('factory_used_receipt_refused',lambda r:write(r,'var/lib/muos-diagnostic/c25.used.BOOT0050','MUOS-C25-ONCE\nBOOT=50\n'))
 test('factory_live_counter_refused',lambda r:write(r,'var/lib/muos-diagnostic/boot-seq','52\n'))
 test('private_ssh_dangling_symlink_refused',lambda r:(r/'root/.ssh').symlink_to('/missing'))
 def old_core(r):write(r,'etc/init.d/S95muos-core','#!/bin/sh\n# stale core without C26\n');refresh(r)
 test('C26_missing_core_hook_with_fresh_hashes',old_core)
 def old_quantum(r):
  for name in ['etc/default/muos-core','usr/share/muos-r35s-profile/overlay/etc/default/muos-core']:write(r,name,'audio=1\ninput=1\n')
  refresh(r)
 test('C26_missing_quantum_with_fresh_hashes',old_quantum)
 def old_gain(r):
  f=r/'usr/share/muos-r35s-profile/profile.json';d=json.loads(f.read_text());d['audio']['codec_gain']=157;f.write_text(json.dumps(d));refresh(r)
 test('C26_old_profile_metadata_with_fresh_hashes',old_gain)
 if meta.get('C36_direct_zero_PCM_integrated'):
  def missing_prime(r):
   f=r/'etc/init.d/S95muos-core';f.write_text(f.read_text().replace('if ! audio_prime_pcm;', 'if ! true;'));refresh(r)
  def missing_rw(r):
   f=r/'opt/muos/device/control/wireplumber.conf';f.write_text(f.read_text().replace('      api.alsa.disable-mmap = true\n',''));refresh(r)
  test('C36_missing_prime_with_fresh_hashes',missing_prime)
  test('C36_missing_RW_with_fresh_hashes',missing_rw)
 if (base/'target/usr/share/muos-r35s-profile/speaker-calibration.json').exists():
  def bad_calibration(r,kind):
   folder=r/'usr/share/muos-r35s-profile';f=folder/'speaker-calibration.json';c=json.loads(f.read_text())
   if kind=='unconfirmed':c['maximum_clean_and_adequate_user_confirmed']=False
   else:c['codec_gain']=205
   f.write_text(json.dumps(c));p=folder/'profile.json';d=json.loads(p.read_text());d['speaker_calibration_sha256']=sha(f);p.write_text(json.dumps(d));refresh(r)
  test('calibration_wrong_gain_with_fresh_hashes',lambda r:bad_calibration(r,'wrong-gain'))
  test('calibration_unconfirmed_with_fresh_hashes',lambda r:bad_calibration(r,'unconfirmed'))
# Exercise the actual read-only bootstrap gate, independently of the Python
# validator. Restore the counter after a corrupt value, then corrupt a checked
# file: the same function used by PID1 must refuse both.
root=stage/'fixture';shutil.copytree(base/'target',root,symlinks=True)
try:
 library=root/'usr/libexec/muos-candidate-boot-checks'
 def gate():return subprocess.run(['sh','-c','. "$1"; candidate_boot_check "$2"','fixture',str(library),str(root)],capture_output=True,text=True)
 assert gate().returncode==0;cases['native_gate_accepts_complete_tree']=True
 write(root,'var/lib/muos-diagnostic/boot-seq','44\n');assert gate().returncode==0;cases['native_gate_accepts_preserved_live_counter']=True
 write(root,'var/lib/muos-diagnostic/boot-seq','corrupt\n');assert gate().returncode!=0;cases['native_gate_rejects_bad_counter']=True
 write(root,'var/lib/muos-diagnostic/boot-seq','0\n')
 write(root,'etc/default/muos-core','audio=0\ninput=1\n');assert gate().returncode!=0;cases['native_gate_rejects_old_audio_template']=True
finally:shutil.rmtree(root)
assert inventory(base/'target')==before and sha(base/'images/rootfs.ext4')==image_hash
report={'passed':True,'cases':cases,'candidate_tree_and_image_unchanged':True,'hardware_accessed':False,'candidate_boot_tested':False,'source_sha256':{str(p.relative_to(repo)):sha(p) for p in [Path(__file__),repo/'port/scripts/phase4_candidate.py',repo/'port/device/rk-r35s-p0/candidate/boot-checks.sh']}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n');(area/'latest-checks').write_text(str(stage)+'\n')
print('C23 refusal/read-only cases passed:',len(cases),stage)
