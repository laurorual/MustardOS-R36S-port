#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Guarded C01/C02 transaction or two-file C02 revision on secondary p2 only."""
from pathlib import Path
import hashlib,json,os,signal,stat,subprocess,sys,tempfile

assert os.geteuid()==0
os.environ['PATH']='/usr/sbin:/usr/bin:/sbin:/bin'
if sys.argv[-1:]!=['--private']:
    os.execvp('unshare',['unshare','--mount','--propagation','private',sys.executable,__file__,*sys.argv[1:],'--private'])
assert Path('/proc/self/ns/mnt').stat().st_ino!=Path('/proc/1/ns/mnt').stat().st_ino
def command(*args):return subprocess.check_output(args,text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cid(n):return hashlib.sha256(Path('/sys/block',n,'device/cid').read_text().strip().lower().encode()).hexdigest()
plan_path=Path(sys.argv[1]);plan=json.loads(plan_path.read_text());folder=plan_path.parent
assert plan.get('experiment') in ['MUOS-R35S-INIT-P4-C01','MUOS-R35S-INIT-P4-C02','MUOS-R35S-GRAPHICS-P4-C03','MUOS-R35S-FRONTEND-P4-C04','MUOS-R35S-AUDIO-P4-C05','MUOS-R35S-FRONTEND-AUDIO-P4-C06']
audio_ui = plan.get('experiment') == 'MUOS-R35S-FRONTEND-AUDIO-P4-C06'
audio_ui_revision=plan.get('diagnostic_revision_update',0) if audio_ui else 0
assert audio_ui_revision in [0,1,2,3,4]
audio = plan.get('experiment') == 'MUOS-R35S-AUDIO-P4-C05'
audio_revision=plan.get('diagnostic_revision_update',0) if audio else 0
assert audio_revision in [0,1,2,3,4,5]
frontend = plan.get('experiment') == 'MUOS-R35S-FRONTEND-P4-C04'
graphics = plan.get('experiment') == 'MUOS-R35S-GRAPHICS-P4-C03'
entropy = plan.get('experiment') == 'MUOS-R35S-INIT-P4-C02'
revision = plan.get('policy_revision_update',0) if entropy else 0
assert revision in [0,1,2]
auth_key=('authorized_secondary_c05_revision' if audio_revision else ('authorized_secondary_c05_install' if audio else ('authorized_secondary_c04_install' if frontend else ('authorized_secondary_c03_install' if graphics else ('authorized_secondary_c02_revision' if revision else ('authorized_secondary_c02_install' if entropy else 'authorized_secondary_c01_install'))))))
if audio_ui:auth_key='authorized_secondary_c06_revision' if audio_ui_revision else 'authorized_secondary_c06_install'
assert plan[auth_key] is True
assert plan['installer_sha256']==sha(Path(__file__))
assert command('uname','-r')=='4.4.189'
assert command('findmnt','-rn','-o','SOURCE','/')=='/dev/mmcblk0p2'
assert command('findmnt','-rn','-o','SOURCE','/boot')=='/dev/mmcblk0p1'
assert cid('mmcblk0')=='9b4fc38015ae4a049ecd796ceceb2ef9473f4773c9b3a066ce59b567c516bbef'
assert cid('mmcblk1')=='12d2c78fbc14993fe2f8a00c413a5e3ef8d9659a3eba9a41a77b5c37029aa193'
assert int(Path('/sys/block/mmcblk1/size').read_text())*512==127934660608
assert command('blkid','-s','PARTUUID','-o','value','/dev/mmcblk1p2')=='4d554432-02'
assert command('sha256sum','/boot/Image').split()[0]=='31bdb671d640863448b59f79801277fe486fa6c78c326bd4ebb51a54559b0577'
assert Path('/proc/sys/kernel/tainted').read_text().strip()=='0'
assert all(x.rsplit(None,1)[1]=='0' for x in command('btrfs','device','stats','/').splitlines())
number=Path('/sys/class/block/mmcblk1p2/dev').read_text().strip()
assert not [x for x in Path('/proc/self/mountinfo').read_text().splitlines() if x.split()[2]==number]
allowed=['usr/libexec/muos-c01-chain','usr/libexec/muos-c01-run','usr/libexec/muos-run-bounded',
         'etc/default/muos-core','etc/inittab','etc/muos-services-diagnostic','sbin/muos-ext4-diag']
if entropy:
    allowed=['sbin/muos-ext4-diag','usr/libexec/muos-rng-ready','usr/libexec/muos-entropy-functions',
             'etc/init.d/S05muos-entropy','etc/default/seedrng','usr/libexec/muos-c01-chain',
             'usr/libexec/muos-c01-run','etc/muos-services-diagnostic']
if revision:
    allowed=['usr/libexec/muos-entropy-functions','usr/libexec/muos-c01-run']
    if revision==2:allowed=['usr/libexec/muos-entropy-functions']
if graphics:
    allowed=['sbin/muos-ext4-diag','usr/libexec/muos-egl-context','usr/libexec/muos-sdl-video-probe',
             'usr/libexec/muos-drm-mode-probe','usr/libexec/muos-c01-run','etc/muos-graphics-diagnostic']
if frontend:
    allowed=['sbin/muos-ext4-diag','usr/libexec/muos-c01-run','etc/muos-frontend-diagnostic']
if audio:
    allowed=['sbin/muos-ext4-diag','usr/libexec/muos-audio-functions','usr/libexec/muos-audio-probe',
             'usr/share/muos-diagnostic/c05-tone.wav','usr/libexec/muos-c01-run','etc/muos-audio-diagnostic']
    if audio_revision==1:allowed=['usr/libexec/muos-root-writers','usr/libexec/muos-c01-run']
    if audio_revision==2:allowed=['usr/libexec/muos-c01-run']
    if audio_revision==3:allowed=['usr/lib/udev/rules.d/79-muos-rk817-path.rules','usr/libexec/muos-c01-run']
    if audio_revision in [4,5]:allowed=['usr/libexec/muos-audio-functions','usr/libexec/muos-audio-probe','usr/libexec/muos-c01-run']
if audio_ui:
    allowed=['sbin/muos-ext4-diag','usr/libexec/muos-c01-run','usr/libexec/muos-c06-session','etc/muos-frontend-audio-diagnostic']
    if audio_ui_revision:allowed=['usr/libexec/muos-c06-session']
    if audio_ui_revision==2:allowed=['usr/share/muos-diagnostic/c06-control-tone.wav','usr/libexec/muos-c06-session','usr/libexec/muos-c01-run']
    if audio_ui_revision==4:allowed=['usr/share/muos-diagnostic/c06-navigate-normalized.wav','usr/libexec/muos-c06-session']
assert [e['path'] for e in plan['entries']]==allowed
for e in plan['entries']:
    p=folder/'assets'/e['asset']
    assert p.name==e['path'].replace('/','_')
    assert stat.S_ISREG(p.lstat().st_mode) and sha(p)==e['sha256']
    if audio and e['path']=='usr/share/muos-diagnostic/c05-tone.wav':
        assert p.stat().st_size==576044 and e['sha256']=='959fcac27fe4bb517ea946d3725857c7fa01b61008c1363d6fdda3dfa96c43e8' and e['mode']==0o644
    elif audio_ui and e['path']=='usr/share/muos-diagnostic/c06-navigate-normalized.wav':
        assert p.stat().st_size==152142 and e['sha256']=='adac78795e6810ce5d17effa5593e9de87051d3ef36231ba9d530921951bb3ee' and e['mode']==0o644
    else:assert p.stat().st_size<131072
    assert e['mode'] in [0o644,0o755]
result={'scope':('C05 audio' if audio else ('C04 frontend' if frontend else ('C03 graphics' if graphics else ('C02 entropy' if entropy else 'C01'))))+' guarded transaction on secondary p2; no bootloader/kernel/partition changes',
        'applied':[],'backup':{},'created_directories':[],'success':False,'rollback_attempted':False}
if audio_ui:result['scope']='C06 frontend audio guarded transaction on secondary p2; no bootloader/kernel/partition changes'
def save():
    p=folder/'install-result.tmp';p.write_text(json.dumps(result,indent=2)+'\n');p.replace(folder/'install-result.json')
def terminated(_signum,_frame):raise TimeoutError('installer terminated')
signal.signal(signal.SIGTERM,terminated)
save()
with tempfile.TemporaryDirectory(prefix='muos-c01-install-',dir='/tmp') as temporary:
    mounted=False
    try:
        subprocess.run(['mount','-t','ext4','-o','rw,nosuid,nodev,noexec','/dev/mmcblk1p2',temporary],check=True);mounted=True
        root=Path(temporary)
        assert command('findmnt','-rn','-o','MAJ:MIN','--target',temporary)==number
        assert (root/'etc/muos-ext4-diagnostic').read_text().strip()=='MUOS-R35S-EXT4-P4-B01'
        assert (root/'etc/default/muos-ui').read_text().startswith('enabled=0\nhotkeys=0\n')
        if revision or graphics or frontend or audio or audio_ui:
            assert (root/'etc/muos-services-diagnostic').read_text().strip()=='MUOS-R35S-INIT-P4-C02'
            # Check only directory metadata. Never traverse, read, hash or
            # back up the private files; preserve the live seed across boots.
            private=root/'var/lib/muos-seedrng'
            for parent in [root/'var',root/'var/lib']:
                assert not parent.is_symlink()
            info=private.lstat()
            assert stat.S_ISDIR(info.st_mode) and (info.st_uid,info.st_gid,stat.S_IMODE(info.st_mode))==(0,0,0o700)
            result['private_seed_directory_metadata_validated_only']=True
            result['policy_revision_update']=revision
            if audio_ui:
                assert (root/'etc/muos-audio-diagnostic').read_text().strip()=='MUOS-R35S-AUDIO-P4-C05'
                assert (root/'etc/muos-frontend-diagnostic').read_text().strip()=='MUOS-R35S-FRONTEND-P4-C04'
                if audio_ui_revision:assert (root/'etc/muos-frontend-audio-diagnostic').read_text().strip()=='MUOS-R35S-FRONTEND-AUDIO-P4-C06'
                else:assert not (root/'etc/muos-frontend-audio-diagnostic').exists()
                required={'usr/libexec/muos-entropy-functions','etc/init.d/S05muos-entropy','usr/libexec/muos-core-lifecycle','etc/init.d/S95muos-core','opt/muos/script/init/S80pipewire.sh','usr/lib/alsa-lib/libasound_module_pcm_pipewire.so','opt/muos/device/control/asound.state','opt/muos/frontend/mulog','usr/lib/udev/rules.d/79-muos-rk817-path.rules','usr/lib/libmali-bifrost-g31-rxp0-gbm.so','usr/lib/libSDL2-2.0.so.0.3000.12','usr/libexec/muos-ui-supervisor','etc/init.d/S99muos-ui','opt/muos/frontend/muxfrontend','usr/libexec/muos-drm-mode-probe','usr/libexec/muos-audio-functions'}
                required|={'opt/muos/share/theme/MustardOS/sound/'+name+'.wav' for name in ['confirm','info_open','info_close']}
                if audio_ui_revision==1:required|={'sbin/muos-ext4-diag','usr/libexec/muos-c01-run'}
                if audio_ui_revision==2:required|={'sbin/muos-ext4-diag','usr/share/muos-diagnostic/c05-tone.wav','opt/muos/share/theme/MustardOS/sound/back.wav','opt/muos/share/theme/MustardOS/sound/navigate.wav'}
                if audio_ui_revision in [3,4]:required|={'sbin/muos-ext4-diag','usr/libexec/muos-c01-run','usr/share/muos-diagnostic/c05-tone.wav','usr/share/muos-diagnostic/c06-control-tone.wav','opt/muos/share/theme/MustardOS/sound/back.wav','opt/muos/share/theme/MustardOS/sound/navigate.wav'}
                assert set(plan['unchanged_required'])==required
                for name,expected in plan['unchanged_required'].items():assert sha(root/name)==expected
            if audio:
                assert (root/'etc/muos-frontend-diagnostic').read_text().strip()=='MUOS-R35S-FRONTEND-P4-C04'
                if audio_revision:assert (root/'etc/muos-audio-diagnostic').read_text().strip()=='MUOS-R35S-AUDIO-P4-C05'
                else:assert not (root/'etc/muos-audio-diagnostic').exists()
                required={'usr/libexec/muos-entropy-functions','etc/init.d/S05muos-entropy','usr/libexec/muos-core-lifecycle','etc/init.d/S95muos-core','opt/muos/script/init/S80pipewire.sh','usr/lib/alsa-lib/libasound_module_pcm_pipewire.so','opt/muos/device/control/asound.state'}
                if audio_revision>=2:required.add('opt/muos/frontend/mulog')
                if audio_revision>=4:required.add('usr/lib/udev/rules.d/79-muos-rk817-path.rules')
                assert set(plan['unchanged_required'])==required
                for name,expected in plan['unchanged_required'].items():assert sha(root/name)==expected
            if graphics or frontend:
                required={'usr/libexec/muos-entropy-functions','etc/init.d/S05muos-entropy','usr/lib/libmali-bifrost-g31-rxp0-gbm.so','usr/lib/libSDL2-2.0.so.0.3000.12'}
                if frontend:
                    assert (root/'etc/muos-graphics-diagnostic').read_text().strip()=='MUOS-R35S-GRAPHICS-P4-C03'
                    assert not (root/'etc/muos-frontend-diagnostic').exists()
                    required|={'usr/libexec/muos-ui-supervisor','etc/init.d/S99muos-ui','opt/muos/frontend/muxfrontend','usr/libexec/muos-drm-mode-probe'}
                else:assert not (root/'etc/muos-graphics-diagnostic').exists()
                assert set(plan['unchanged_required'])==required
                for name,expected in plan['unchanged_required'].items():
                    assert sha(root/name)==expected
        elif entropy:
            assert (root/'etc/muos-services-diagnostic').read_text().strip()=='MUOS-R35S-INIT-P4-C01'
            # First C02 boot must start seedless. Never inspect, back up or
            # overwrite a live seed; repeat boots reuse it without reinstall.
            assert not (root/'var/lib/muos-seedrng').exists()
            result['seed_directory_absent_before_install']=True
        for e in plan['entries']:
            p=root/e['path']
            for parent in p.parents:
                if parent==root:break
                assert not parent.is_symlink()
            if e['old_sha256'] is None:assert not p.exists() and not p.is_symlink()
            else:
                assert stat.S_ISREG(p.lstat().st_mode) and sha(p)==e['old_sha256']
                if revision==2:
                    assert (folder/'assets'/e['asset']).read_bytes()==p.read_bytes().replace(b'"$rng_probe" 5 >',b'"$rng_probe" 60 >')
                result['backup'][e['path']]={'hex':p.read_bytes().hex(),'mode':stat.S_IMODE(p.stat().st_mode)}
        save()
        if audio:
            directory=root/'usr/share/muos-diagnostic'
            assert not directory.is_symlink()
            if not directory.exists():
                directory.mkdir(mode=0o755)
                result['created_directories'].append('usr/share/muos-diagnostic');save()
        for index,e in enumerate(plan['entries']):
            p=root/e['path'];pending=p.with_name('.muos-c01-'+str(index)+'.tmp')
            fd=os.open(pending,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,e['mode'])
            with os.fdopen(fd,'wb') as f:
                f.write((folder/'assets'/e['asset']).read_bytes());f.flush();os.fchmod(f.fileno(),e['mode']);os.fchown(f.fileno(),0,0);os.fsync(f.fileno())
            pending.replace(p);result['applied'].append(e['path'])
            fd=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY)
            try:os.fsync(fd)
            finally:os.close(fd)
            assert sha(p)==e['sha256'];save()
        result['success']=True
    except Exception as error:
        result['error']=repr(error);result['rollback_attempted']=True
        if mounted:
            for name in reversed(result['applied']):
                p=Path(temporary)/name;old=result['backup'].get(name)
                if old:
                    p.write_bytes(bytes.fromhex(old['hex']));p.chmod(old['mode'])
                else:p.unlink()
            for name in reversed(result['created_directories']):(Path(temporary)/name).rmdir()
        raise
    finally:
        if mounted:subprocess.run(['umount',temporary],check=True)
        save()
fsck=subprocess.run(['/usr/sbin/e2fsck','-fn','/dev/mmcblk1p2'],capture_output=True,text=True)
result['candidate_ext4_fsck']={'exit':fsck.returncode,'out':fsck.stdout,'err':fsck.stderr}
assert fsck.returncode==0
result['unmounted_and_fsck_passed']=True;save()
print(('C06' if audio_ui else ('C05' if audio else ('C04' if frontend else ('C03' if graphics else ('C02' if entropy else 'C01')))))+' payload installed and fsck passed')
