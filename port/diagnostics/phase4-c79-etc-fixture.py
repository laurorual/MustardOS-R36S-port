#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Real disposable /etc copies; mount is recorded, never performed."""
from pathlib import Path
import hashlib,json,os,shutil,stat,subprocess,sys

os.umask(0o077)
area=Path('/tmp/c99-etc');cases=[]
source=Path('/port/device/rk-r35s-p0/c79-session/etc-view.sh').read_text()
payload=b'# private audio template\n'
def inventory(path):
    result={}
    for f in [path,*sorted(path.rglob('*'))]:
        s=f.lstat();kind=stat.S_IFMT(s.st_mode)
        result[str(f.relative_to(path))]=(kind,stat.S_IMODE(s.st_mode),s.st_uid,s.st_gid,
            os.readlink(f) if f.is_symlink() else hashlib.sha256(f.read_bytes()).hexdigest() if f.is_file() else '')
    return result

def run(name,ok=False,change=None,extra=''):
    if area.exists():shutil.rmtree(area)
    area.mkdir(mode=0o700);etc=area/'etc';etc.mkdir(mode=0o755);etc.chmod(0o755)
    (etc/'default').mkdir(mode=0o755);(etc/'default/test').write_text('unchanged\n')
    (etc/'local-link').symlink_to('default/test');(etc/'identity').write_text('dummy identity\n');(etc/'identity').chmod(0o600)
    template=area/'asound-source';template.write_bytes(payload);template.chmod(0o755)
    cap=area/'capsule';cap.mkdir(mode=0o700)
    mnt=area/'mnt';mnt.mkdir(mode=0o755);mnt.chmod(0o755)
    if change:change(etc,template,cap)
    # Test relocation is limited to the two fixed path assignments and the
    # expected public template fingerprint/length in the disposable copy.
    code=source.replace('c79_etc=/etc','c79_etc='+str(etc)).replace(
        'c79_template=/opt/muos/share/conf/rootfs/asound.conf','c79_template='+str(template))
    code=code.replace('c79_mnt=/mnt','c79_mnt='+str(mnt))
    code=code.replace('0:0:755:1:444','0:0:755:1:'+str(len(payload))).replace(
        '58aa042723b6935ddf81d44b47e6e960279f257e2543e0ed2626c461f585e8cb',hashlib.sha256(payload).hexdigest())
    code+='\ndir='+str(cap)+'''\nfindmnt() { echo tmpfs; }
session_bind() {
 case "$1:$2" in
 "$dir/etc-view:'''+str(etc)+'''"|"$dir/mnt-view:'''+str(mnt)+'''") ;;
 *) return 1 ;;
 esac
 printf 'bound\n' >> "$dir/bound"
}
'''+extra+'\nsession_c79_etc_prepare\n'
    before=inventory(etc);before_mnt=inventory(mnt)
    r=subprocess.run(['sh','-c',code],capture_output=True,text=True,timeout=10)
    assert (r.returncode==0)==ok,(name,r.returncode,r.stdout,r.stderr)
    assert inventory(etc)==before,(name,'original /etc changed')
    assert inventory(mnt)==before_mnt,(name,'original /mnt changed')
    if ok:
        view=cap/'etc-view'
        assert (view/'asound.conf').read_bytes()==payload and stat.S_IMODE((view/'asound.conf').stat().st_mode)==0o644
        assert (view/'local-link').is_symlink() and os.readlink(view/'local-link')=='default/test'
        assert (view/'identity').read_bytes()==b'dummy identity\n' and stat.S_IMODE((view/'identity').stat().st_mode)==0o600
        assert (cap/'bound').read_text()=='bound\nbound\n' and (cap/'mnt-view/mmc').is_dir()
    else:assert not (cap/'bound').exists(),name
    cases.append(name);print('C99_ETC_PASS_'+name,flush=True)

run('copy-preserves-modes-links-and-identity-only-in-private-RAM',True)
run('reject-existing-asound',change=lambda e,t,c:(e/'asound.conf').write_text('existing'))
run('reject-dangling-asound-symlink',change=lambda e,t,c:(e/'asound.conf').symlink_to('absent'))
def etc_link(e,t,c):
    target=e.with_name('real-etc');e.rename(target);e.symlink_to(target)
run('reject-etc-alias',change=etc_link)
run('reject-unsafe-etc-mode',change=lambda e,t,c:e.chmod(0o777))
run('reject-template-hash-change',change=lambda e,t,c:t.write_bytes(b'x'*len(payload)))
run('reject-template-mode-change',change=lambda e,t,c:t.chmod(0o777))
run('reject-template-hardlink',change=lambda e,t,c:os.link(t,t.with_name('hardlink')))
def template_link(e,t,c):
    target=t.with_name('real-template');t.rename(target);t.symlink_to(target)
run('reject-template-symlink',change=template_link)
run('reject-non-tmpfs-capsule',extra='findmnt() { echo ext4; }')
run('reject-existing-view',change=lambda e,t,c:(c/'etc-view').mkdir())
run('reject-view-alias',change=lambda e,t,c:(c/'etc-view').symlink_to(e))
run('copy-error-never-binds-or-touches-original',extra='cp() { return 1; }')
run('template-copy-error-preserves-original',extra='cp() { [ "$1" != -p ] || return 1; command cp "$@"; }')
run('bind-error-preserves-original',extra='session_bind() { return 1; }')
run('reject-nonempty-original-mnt',change=lambda e,t,c:(e.parent/'mnt/unowned').touch())
def mnt_link(e,t,c):
    p=e.parent/'mnt';p.rename(e.parent/'real-mnt');p.symlink_to('real-mnt')
run('reject-original-mnt-alias',change=mnt_link)
run('reject-original-mnt-mode',change=lambda e,t,c:(e.parent/'mnt').chmod(0o777))
run('reject-existing-mnt-view',change=lambda e,t,c:(c/'mnt-view').mkdir())
Path(sys.argv[1]).write_text(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,
    'real_copies_and_original_inventories_checked':True,'mounts_stubbed':True})+'\n')
