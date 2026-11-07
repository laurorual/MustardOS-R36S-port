#!/usr/bin/env python3
"""Private chroot mounts and native uinput, followed by an unprivileged menu."""
import ctypes
import fcntl
import json
import os
from pathlib import Path
import pwd
import re
import signal
import stat
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
if os.geteuid() or ROOT.parent != Path('/tmp') or not ROOT.name.startswith('muos-r35s-phase3.'):
    raise SystemExit('Expected sudo in the temporary Phase 3 directory')
state = json.loads((ROOT/'session-state.json').read_text())
if os.readlink('/proc/self/ns/mnt') == state['mount_namespace']:
    raise SystemExit('Refusing mounts in the original mount namespace')
if len(sys.argv) != 2 or sys.argv[1] not in ('inspect','menu','audio'): raise SystemExit('Unknown mode')
mode = sys.argv[1]
jail = ROOT / 'staging'
assert jail.is_dir() and not jail.is_symlink()
account = pwd.getpwnam('ark')
groups = os.getgrouplist('ark', account.pw_gid)
nodes = [Path('/dev')/name for name in ('null','zero','random','urandom','tty','fb0','uinput','mali0','rga')]
nodes += list(Path('/dev/input').glob('event*')) + list(Path('/dev/input').glob('js*'))
nodes += list(Path('/dev/dri').glob('*'))
if mode == 'audio': nodes += list(Path('/dev/snd').glob('*'))
devices = [(str(p),p.stat().st_rdev) for p in nodes if p.exists() and stat.S_ISCHR(p.stat().st_mode)]

def run(*args): subprocess.run(args, check=True)
run('mount','--make-rprivate','/')
for name in ('usr','etc','sys'):
    target = jail / name
    target.mkdir(exist_ok=True)
    run('mount','--bind','/'+name,str(target))
    run('mount','-o','remount,bind,ro',str(target))
for name in ('bin','sbin','lib','lib64'):
    if Path('/'+name).exists() and not (jail/name).exists(): (jail/name).symlink_to('usr/'+name)
for name in ('dev','proc','tmp','run','home/ark'):
    (jail/name).mkdir(parents=True,exist_ok=True)
run('mount','-t','proc','-o','ro,nosuid,nodev,noexec','proc',str(jail/'proc'))
run('mount','-t','tmpfs','-o','mode=0755,nosuid','tmpfs',str(jail/'dev'))
for name,device in devices:
    target = jail / name.lstrip('/')
    target.parent.mkdir(parents=True, exist_ok=True)
    os.mknod(target,stat.S_IFCHR|0o660,device)
    os.chown(target,account.pw_uid,account.pw_gid)
os.chown(jail/'home/ark',account.pw_uid,account.pw_gid)
# Only the staging tree is writable. No host home, boot, ROMs, storage, or system scripts.
for name in ['opt/muos/config','opt/muos/device/config','opt/muos/kiosk','run','tmp']:
    path = jail/name
    path.mkdir(parents=True,exist_ok=True)
    for item in [path,*path.rglob('*')]: os.chown(item,account.pw_uid,account.pw_gid)
env = {'PATH':'/usr/bin:/bin','LC_ALL':'C.UTF-8','HOME':'/home/ark','SDL_VIDEODRIVER':'KMSDRM',
       'SDL_VIDEO_EGL_DRIVER':'libEGL.so','SDL_VIDEO_GL_DRIVER':'libGLESv2.so',
       'SDL_JOYSTICK_HIDAPI':'0','MUOS_RUN_DIR':'/run/muos'}
if mode == 'audio':
    env['SDL_AUDIODRIVER'] = 'alsa'
    (jail/'home/ark/.asoundrc').write_text('pcm.!default { type plug slave.pcm "hw:0,0" }\nctl.!default { type hw card 0 }\n')
    os.chown(jail/'home/ark/.asoundrc',account.pw_uid,account.pw_gid)

def enter():
    os.chroot(jail)
    os.chdir('/')
    os.setgroups(groups)
    os.setgid(account.pw_gid)
    os.setuid(account.pw_uid)
    if ctypes.CDLL(None,use_errno=True).prctl(38,1,0,0,0): raise OSError(ctypes.get_errno(),'PR_SET_NO_NEW_PRIVS')

def interrupted(sig,frame): raise SystemExit(128+sig)
for sig in [signal.SIGHUP,signal.SIGINT,signal.SIGTERM]: signal.signal(sig,interrupted)
(jail/'run/muos/storage').mkdir(parents=True,exist_ok=True)
os.chown(jail/'run/muos',account.pw_uid,account.pw_gid)
os.chown(jail/'run/muos/storage',account.pw_uid,account.pw_gid)
log = (ROOT/'muinput.log').open('w')
daemon = subprocess.Popen(['/usr/sbin/chroot',str(jail),'/opt/muos/frontend/muinput','--device','rk-r35s-p0','--foreground','--verbose','--rumble-strength','0'],stdout=log,stderr=log,env=dict(os.environ,MUOS_RUMBLE_STRENGTH='0'))
menu = None
try:
    deadline = time.monotonic()+10
    virtual = None
    while time.monotonic()<deadline:
        if daemon.poll() is not None: raise RuntimeError('muinput exited during setup')
        for p in Path('/sys/class/input').glob('event*/device/name'):
            if p.read_text().strip()=='muOS-Keys' and (p.parent/'id/product').read_text().strip()=='3504':
                virtual = p
                break
        if virtual and (jail/'dev/muinput/rk-r35s-p0-source').exists(): break
        time.sleep(.05)
    if not virtual or not (jail/'dev/muinput/rk-r35s-p0-source').exists(): raise RuntimeError('No isolated source and virtual controller')
    major,minor = map(int,(virtual.parents[1]/'dev').read_text().split(':'))
    node = jail/'dev/input'/virtual.parents[1].name
    os.mknod(node,stat.S_IFCHR|0o660,os.makedev(major,minor))
    os.chown(node,account.pw_uid,account.pw_gid)
    identity = bytearray(8)
    with node.open('rb',buffering=0) as controller: fcntl.ioctl(controller,0x80084502,identity)
    if identity.hex() != '06006d7504356f73': raise RuntimeError('Unexpected virtual controller identity')
    output = subprocess.check_output(['/opt/muos/frontend/phase3-menu','--inspect-input'],preexec_fn=enter,env=env,text=True)
    print(output,flush=True)
    match = re.search(r'SDL_JOYSTICK name=muOS-Keys guid=([0-9a-f]{32}) buttons=15 axes=4 hats=1',output)
    if not match: raise RuntimeError('Unexpected SDL descriptor; do not guess mapping')
    # Query joydev's actual index order: BTN_* first, then non-BTN keys. Do not
    # reuse an upstream profile's indices or sort all evdev key codes together.
    js_paths = [p for p in Path('/sys/class/input').glob('js*/device/id/product') if p.read_text().strip()=='3504']
    if len(js_paths)!=1: raise RuntimeError('Expected one matching virtual joydev node')
    js_sys = js_paths[0].parents[2]
    js_major,js_minor=map(int,(js_sys/'dev').read_text().split(':'))
    js_node=jail/'dev/input'/js_sys.name
    os.mknod(js_node,stat.S_IFCHR|0o660,os.makedev(js_major,js_minor))
    os.chown(js_node,account.pw_uid,account.pw_gid)
    button_map=bytearray(1024)
    button_count=bytearray(1)
    with js_node.open('rb',buffering=0) as joystick:
        fcntl.ioctl(joystick,0x80016a12,button_count)
        fcntl.ioctl(joystick,0x84006a34,button_map)
    codes=list(struct.unpack('512H',button_map)[:button_count[0]])
    print('PHASE3_JOYDEV_BUTTON_CODES='+json.dumps(codes),flush=True)
    expected={'a':305,'b':304,'x':307,'y':308,'leftshoulder':310,'rightshoulder':311,
              'lefttrigger':312,'righttrigger':313,'back':314,'start':315,'guide':316,
              'leftstick':317,'rightstick':318,'volumedown':114,'volumeup':115}
    # joydev exposes the thirteen BTN_* buttons. This SDL evdev backend also
    # exposes the two KEY_VOLUME* buttons; verify their positions interactively.
    btn_codes={code for code in expected.values() if code>=256}
    if len(codes)!=13 or set(codes)!=btn_codes: raise RuntimeError('Unexpected joydev buttons')
    codes += [114,115]
    mapping=match[1]+',muOS-Keys,'+','.join(f'{name}:b{codes.index(code)}' for name,code in expected.items())
    mapping+=',leftx:a0,lefty:a1,rightx:a2,righty:a3,dpup:h0.1,dpdown:h0.4,dpleft:h0.8,dpright:h0.2,platform:Linux,'
    (jail/'opt/muos/device/config/board/sdl_map').write_text(mapping+'\n')
    print('PHASE3_SDL_MAPPING='+mapping,flush=True)
    if mode != 'inspect':
        subprocess.run(['/opt/muos/frontend/muvarctl','build'],preexec_fn=enter,env=env,check=True)
        args = ['/opt/muos/frontend/phase3-menu']
        if mode == 'audio': args.append('--audio')
        menu = subprocess.Popen(args,preexec_fn=enter,env=env)
        status = menu.wait(timeout=145)
        print('PHASE3_MENU_EXIT_STATUS='+str(status),flush=True)
        if status: raise SystemExit(status)
finally:
    if menu and menu.poll() is None:
        menu.terminate()
        try: menu.wait(timeout=4)
        except subprocess.TimeoutExpired:
            menu.kill()
            menu.wait()
    daemon.terminate()
    try: code=daemon.wait(timeout=5)
    except subprocess.TimeoutExpired:
        daemon.kill()
        code=daemon.wait()
    log.close()
    print('PHASE3_MUINPUT_EXIT_STATUS='+str(code),flush=True)
