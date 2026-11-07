#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C25 real selection policy + isolated session orchestration and Kconfig."""
from pathlib import Path
import json, subprocess, tempfile
from phase4_candidate import sha

repo=Path(__file__).resolve().parents[2]; work=repo/'build/phase4'; area=work/'rootfs-candidate'
stage=Path(tempfile.mkdtemp(prefix='c25-checks.',dir=area))
fixture=r"""
from pathlib import Path
import os, shutil, subprocess
p=Path('/port/device/rk-r35s-p0/launcher-once'); root=Path('/tmp/c25')
def reset():
 if root.exists(): shutil.rmtree(root)
 root.mkdir(mode=0o700)
 store=root/'store'; state=root/'state'
 store.mkdir(mode=0o700); state.mkdir(mode=0o700)
 (store/'boot-seq').write_text('47\n'); (store/'boot-seq').chmod(0o600)
 return store,state
def token(store,body='MUOS-C25-ONCE\nBOOT=48\n'):
 f=store/'c25.once'; f.write_text(body); f.chmod(0o600); return f
def policy(store,state,sync='true'):
 code=f'''set -u; umask 077
. {p}/policy.sh
c25_store={store}; c25_state={state}
c25_durable() {{ [ ! -e "$c25_state/grant" ] || exit 99; {sync}; }}
c25_select
'''
 return subprocess.run(['sh','-c',code],capture_output=True,text=True)
def pass_(s): print('PASS_'+s,flush=True)
s,t=reset(); assert policy(s,t).returncode==0 and (t/'selected').read_text()=='c07\n'; pass_('absent_token_C07')
for name,body in [('wrong_boot','MUOS-C25-ONCE\nBOOT=47\n'),('extra_line','MUOS-C25-ONCE\nBOOT=48\nX=1\n'),('no_newline','MUOS-C25-ONCE\nBOOT=48')]:
 s,t=reset(); f=token(s,body); assert policy(s,t).returncode==64 and f.read_text()==body and not (t/'grant').exists(); pass_(name+'_preserved')
for mode in [0o644,0o400]:
 s,t=reset(); f=token(s); f.chmod(mode); assert policy(s,t).returncode==64 and f.exists(); pass_('mode_'+oct(mode)+'_refused')
s,t=reset(); f=token(s); os.link(f,s/'linked'); assert policy(s,t).returncode==64; pass_('hardlinked_token_refused')
s,t=reset(); f=token(s); f.rename(s/'other'); f.symlink_to(s/'other'); assert policy(s,t).returncode==64 and f.is_symlink(); pass_('symlink_token_refused')
s,t=reset(); f=token(s); used=s/'c25.used.BOOT0048'; used.write_text('existing'); assert policy(s,t).returncode==64 and used.read_text()=='existing' and f.exists(); pass_('used_collision_preserved')
s,t=reset(); token(s); assert policy(s,t,'false').returncode==1 and not (s/'c25.once').exists() and not (t/'grant').exists() and (t/'selected').read_text()=='c07\n'; pass_('sync_failure_consumed_no_grant_no_rearm')
s,t=reset(); token(s); assert policy(s,t).returncode==0 and (t/'selected').read_text()=='c25\n' and not (s/'c25.once').exists() and (t/'grant').read_text()=='MUOS-C25-GRANT\nBOOT=48\n'; pass_('consume_sync_before_grant')
(s/'boot-seq').write_text('48\n'); assert policy(s,t).returncode==0 and (t/'selected').read_text()=='c07\n' and (t/'fallback').read_text()=='1\n'; pass_('next_boot_C07_fallback')
(s/'boot-seq').write_text('49\n'); assert policy(s,t).returncode==0 and (t/'fallback').read_text()=='0\n'; pass_('later_boot_no_extra_archive')

# Test the actual session script with only native hardware adapters replaced.
# Fixed absolute paths are redirected to tmpfs. No profile, ELF or device used.
def session_fixture(mode='clean',init=True,selected='c25'):
 s,t=reset(); os.umask(0o077)
 pkg=root/'package'; pkg.mkdir(); sess=root/'session-package'; sess.mkdir(); base=root/'session'
 for f in ['policy.sh','card-guard.sh']:
  shutil.copyfile(p/f if f!='card-guard.sh' else Path('/port/device/rk-r35s-p0/linux-diagnostic/card-guard.sh'),pkg/f)
 native='''c25_init_child() { INIT; }
c25_ready() { [ ! -e STATE/reject ]; }
c25_publish() { echo PUBLISHED >> STATE/events; }
'''.replace('INIT','true' if init else 'false').replace('STATE',str(t))
 (pkg/'native.sh').write_text(native)
 shutil.copyfile('/port/device/rk-r35s-p0/session/control-functions.sh',sess/'control-functions.sh')
 data=(p/'session.sh').read_text()
 for old,new in [('/usr/libexec/muos-c25',str(pkg)),('/usr/libexec/muos-session',str(sess)),('/var/lib/muos-diagnostic',str(s)),('/run/muos/session',str(base)),('/run/muos/c25',str(t))]: data=data.replace(old,new)
 (root/'session.sh').write_text(data)
 (t/'selected').write_text(selected+'\n'); (t/'fallback').write_text('1\n')
 (s/'boot-seq').write_text('48\n'); (t/'grant').write_text('MUOS-C25-GRANT\nBOOT=48\n')
 script='''#!/bin/sh
set -eu
echo "$1" >> STATE/events
case "$1" in
start)
 mkdir -p BASE/run-0001
 echo run-0001 > BASE/current
 cp "$MUOS_SESSION_CONFIG" BASE/run-0001/run.conf
 for f in first-paint software-volume brightness-active; do echo fixture > BASE/run-0001/$f.txt; done
 echo 0 > BASE/run-0001/result
 touch BASE/run-0001/ready BASE/run-0001/done
 MODE
 ;;
stop) ;;
esac
'''.replace('STATE',str(t)).replace('BASE',str(base))
 script=script.replace('MODE',{'clean':':','failed':'echo 1 > '+str(base)+'/run-0001/result; exit 1','foreign':'echo enabled=0 > '+str(base)+'/run-0001/run.conf; exit 1'}[mode])
 (sess/'service.sh').write_text(script); (sess/'service.sh').chmod(0o755)
 for f in [*t.iterdir(),s/'boot-seq']: f.chmod(0o600)
 return s,t,base
def run(action='start'):
 return subprocess.run(['sh',str(root/'session.sh'),action],capture_output=True,text=True,timeout=5)
s,t,b=session_fixture(init=False); assert run().returncode==64 and not (t/'events').exists(); pass_('SSH_start_refused_before_attempt')
s,t,b=session_fixture(); (t/'grant').write_text('MUOS-C25-GRANT\nBOOT=49\n'); assert run().returncode==64 and not (t/'events').exists(); pass_('wrong_grant_no_session')
s,t,b=session_fixture(); (t/'session.once').mkdir(); assert run().returncode==64 and not (t/'events').exists(); pass_('duplicate_start_refused')
s,t,b=session_fixture(); (t/'reject').touch(); assert run().returncode==64 and not (t/'events').exists(); pass_('failed_ready_guard_no_session')
s,t,b=session_fixture(); r=run(); assert r.returncode==0,(r.stdout,r.stderr); assert (t/'result').read_text()=='0\n' and (t/'events').read_text()=='start\nstop\nPUBLISHED\n' and not (t/'ready').exists(); pass_('clean_lease_cleanup_before_publication')
s,t,b=session_fixture('failed'); assert run().returncode==1 and (t/'events').read_text()=='start\nstop\nPUBLISHED\n' and (t/'result').read_text()=='1\n'; pass_('failed_start_owned_cleanup')
s,t,b=session_fixture('foreign'); assert run().returncode==1 and (t/'events').read_text()=='start\nPUBLISHED\n'; pass_('foreign_generation_never_stopped')
s,t,b=session_fixture(); assert run().returncode==0; (t/'events').unlink(); assert run('stop').returncode==0 and (t/'events').read_text()=='stop\n'; pass_('shutdown_stops_owned_generation')
(b/'run-0001/run.conf').write_text('enabled=0\n'); (t/'events').unlink(); assert run('stop').returncode==0 and not (t/'events').exists(); pass_('shutdown_preserves_foreign_generation')
s,t,b=session_fixture(selected='c07'); assert run().returncode==0 and (t/'events').read_text()=='PUBLISHED\n' and not b.exists(); pass_('fallback_report_no_session')
s,t,b=session_fixture(selected='c07'); (t/'fallback').write_text('0\n'); assert run().returncode==0 and not (t/'events').exists(); pass_('normal_C07_no_session_or_archive')

# Actual FAT-report implementation, with mount syscalls replaced by a recorder.
# /boot is a separate disposable tmpfs supplied to this container.
def publish(ready=True,marker=True,rw=True,collision=False,oversize=False,copy_fail=False,unmount_fail=False):
 s,t=reset(); os.umask(0o077)
 (s/'boot-seq').write_text('48\n')
 (t/'FINAL.TXT').write_text('RESULT=0\n'); (t/'START.TXT').write_text('x'*65537 if oversize else 'START=1\n')
 (t/'private.raw').write_text('fixture never exported')
 for f in t.iterdir(): f.chmod(0o600)
 fat=Path('/boot')
 for x in fat.iterdir():
  if x.is_dir(): shutil.rmtree(x)
  else: x.unlink()
 (fat/'DIAG.ID').write_text('MUOS-R35S-EXT4-P4-B01\n' if marker else 'OTHER\n')
 if collision:
  (fat/'DIAG25/BOOT0048').mkdir(parents=True); (fat/'DIAG25/BOOT0048/FINAL.TXT').write_text('preserve')
 code=f'''. {p}/policy.sh
. {p}/native.sh
c25_state={t}; c25_store={s}
c25_ready() {{ {'true' if ready else 'false'}; }}
mount() {{
 echo "$*" >> {t}/mounts
 case "$*" in *remount,rw*) {'true' if rw else 'false'} ;; *) return 0 ;; esac
}}
umount() {{ echo "$*" >> {t}/unmounts; {'false' if unmount_fail else 'true'}; }}
{ 'cp() { return 1; }' if copy_fail else '' }
c25_publish
'''
 r=subprocess.run(['sh','-c',code],capture_output=True,text=True,timeout=5)
 return r,t,fat
r,t,f=publish(); assert r.returncode==0 and (t/'unmounts').exists() and sorted(x.name for x in (f/'DIAG25/BOOT0048').iterdir())==['FINAL.TXT','START.TXT']; pass_('public_whitelist_readback_and_unmount')
r,t,f=publish(ready=False); assert r.returncode==64 and not (t/'mounts').exists(); pass_('report_guard_before_mount')
r,t,f=publish(marker=False); assert r.returncode!=0 and (t/'unmounts').exists() and 'remount,rw' not in (t/'mounts').read_text(); pass_('wrong_FAT_marker_never_rw')
r,t,f=publish(oversize=True); assert r.returncode==64 and not (t/'mounts').exists(); pass_('oversized_report_before_mount')
r,t,f=publish(collision=True); assert r.returncode==1 and (f/'DIAG25/BOOT0048/FINAL.TXT').read_text()=='preserve' and (t/'unmounts').exists(); pass_('archive_collision_preserved')
r,t,f=publish(rw=False); assert r.returncode==1 and (t/'unmounts').exists(); pass_('report_rw_failure_unmount')
r,t,f=publish(copy_fail=True); assert r.returncode==1 and (t/'unmounts').exists(); pass_('report_copy_failure_unmount')
r,t,f=publish(unmount_fail=True); assert r.returncode==1 and len((t/'unmounts').read_text().splitlines())==2; pass_('report_unmount_failure_retry_and_failure')
"""
(stage/'fixtures.py').write_text(fixture)
common=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges','--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev','--tmpfs','/boot:rw,nosuid,nodev','-v',f'{repo}/port:/port:ro,z','-v',f'{work}:/work:ro,z',(work/'rootfs-container.iid').read_text().strip()]
rel=lambda x:'/work/'+str(x.relative_to(work))
r=subprocess.run(common+['python3','-B',rel(stage/'fixtures.py')],capture_output=True,text=True,timeout=40)
(stage/'stdout').write_text(r.stdout); (stage/'stderr').write_text(r.stderr); assert r.returncode==0,(stage,r.stdout,r.stderr)
cases=[x for x in r.stdout.splitlines() if x.startswith('PASS_')]; assert len(cases)==32,len(cases)
# Real Kconfig in separate O=, shared SDK configuration kept byte-for-byte.
baseline=work/'network-tools/baseline.config'; sdk=work/'graphics-config/output/.config'; assert sdk.read_bytes()==baseline.read_bytes()
out=stage/'output'; config=rel(out)+'/.config'
script=f'''set -eu
make -C /work/buildroot O={rel(out)} BR2_EXTERNAL=/port/buildroot BR2_DEFCONFIG=/work/network-tools/baseline.config defconfig
! grep -qx BR2_PACKAGE_MUOS_R35S_LAUNCHER_ONCE=y {config}
echo PASS_Kconfig_default_off
/work/buildroot/utils/config --file {config} --enable BR2_PACKAGE_MUOS_CORE --enable BR2_PACKAGE_MUOS_R35S_PROFILE --enable BR2_PACKAGE_MUOS_R35S_SESSION --enable BR2_PACKAGE_MUOS_R35S_LAUNCHER_ONCE --disable BR2_PACKAGE_MUOS_R35S_BOOT
make -C /work/buildroot O={rel(out)} BR2_EXTERNAL=/port/buildroot olddefconfig
grep -qx BR2_PACKAGE_MUOS_R35S_LAUNCHER_ONCE=y {config}
! grep -qx BR2_PACKAGE_MUOS_R35S_BOOT=y {config}
echo PASS_Kconfig_without_C12
/work/buildroot/utils/config --file {config} --disable BR2_PACKAGE_MUOS_R35S_SESSION --enable BR2_PACKAGE_MUOS_R35S_LAUNCHER_ONCE
make -C /work/buildroot O={rel(out)} BR2_EXTERNAL=/port/buildroot olddefconfig
! grep -qx BR2_PACKAGE_MUOS_R35S_LAUNCHER_ONCE=y {config}
echo PASS_Kconfig_missing_session_refused
'''
(stage/'kconfig.sh').write_text(script)
args=common.copy(); args[args.index(f'{work}:/work:ro,z')]=f'{work}:/work:rw,z'
r=subprocess.run(args+['sh','-c',script],capture_output=True,text=True,timeout=60)
(stage/'kconfig.stdout').write_text(r.stdout); (stage/'kconfig.stderr').write_text(r.stderr); assert r.returncode==0,(stage,r.stdout[-2000:],r.stderr)
assert sdk.read_bytes()==baseline.read_bytes()
cases += [x for x in r.stdout.splitlines() if x.startswith('PASS_')]; assert len(cases)==35
sources=[Path(__file__),repo/'port/buildroot/Config.in',*sorted((repo/'port/device/rk-r35s-p0/launcher-once').glob('*')),*sorted((repo/'port/buildroot/package/muos-r35s-launcher-once').glob('*')),repo/'port/device/rk-r35s-p0/session/control-functions.sh']
report={'passed':True,'cases':cases,'SDK_baseline_unchanged':True,'hardware_tested':False,'adapters_mocked_for_session_fixtures':True,'source_sha256':{str(s.relative_to(repo)):sha(s) for s in sources}}
(stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n'); (area/'latest-c25-checks').write_text(str(stage)+'\n')
print('C25 35 policy/session/report/Kconfig cases passed:',stage)
