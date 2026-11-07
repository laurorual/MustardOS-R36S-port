#!/usr/bin/env python3
"""Archive/verify a completed temporary session, then optionally remove it."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import tarfile

parser = argparse.ArgumentParser()
parser.add_argument('host')
parser.add_argument('directory', type=Path)
parser.add_argument('--cleanup', action='store_true')
args = parser.parse_args()
repo = Path(__file__).resolve().parents[2]
work = args.directory.resolve()
assert work.is_relative_to(repo / 'build/phase4') and work != repo / 'build/phase4'
assert re.fullmatch(r'[a-zA-Z0-9_][a-zA-Z0-9_.@-]*', args.host)
remote = (work / 'remote-session').read_text().strip()
assert re.fullmatch(r'/tmp/muos-r35s-p4-core\.[a-zA-Z0-9]+', remote)
ssh = ['ssh', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=10']
if os.environ.get('MUOS_SSH_CONTROL'):
    ssh += ['-S', os.environ['MUOS_SSH_CONTROL'], '-o', 'BatchMode=yes']
ssh.append(args.host)
code = '''import pathlib,subprocess,json,os,sys,hashlib
os.environ['PATH']='/usr/sbin:/usr/bin:/sbin:/bin'
root=pathlib.Path(sys.argv[1]);state=json.loads((root/'session-state.json').read_text())
pid=state.get('worker_pid')
try:same=pathlib.Path(f'/proc/{pid}/stat').read_text().split()[21]==state.get('worker_starttime')
except FileNotFoundError:same=False
assert not same,'Session is still running'
if (root/'mixer-before.state').exists():
 subprocess.run(['alsactl','-U','-f',str(root/'mixer-after.state'),'store'],check=True)
r={'taint':pathlib.Path('/proc/sys/kernel/tainted').read_text().strip(),
   'Image_sha256':hashlib.sha256(pathlib.Path('/boot/Image').read_bytes()).hexdigest()}
if state.get('brightness'):
 r['backlight_brightness']=pathlib.Path(state['brightness']['path']).read_text().strip()
 r['backlight_expected']=str(state['brightness']['value'])
 assert r['backlight_brightness']==r['backlight_expected'],'Brightness differs from pre-test snapshot'
commands=[['findmnt','/'],['findmnt','/boot'],['btrfs','device','stats','/'],['dmesg']]
if state['active_services']:commands.append(['systemctl','is-active',*state['active_services']])
for c in commands:
 p=subprocess.run(c,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 r[' '.join(c)]={'exit':p.returncode,'output':p.stdout}
(root/'health-after.json').write_text(json.dumps(r,indent=2)+'\\n')
'''
subprocess.run(ssh + ['sudo -n python3 - ' + shlex.quote(remote)], input=code, text=True, check=True)
with (work / 'remote-evidence.tar.gz').open('wb') as output:
    subprocess.run(ssh + ['sudo -n tar -C ' + shlex.quote(remote)
                         + ' --exclude=./rootfs --exclude=./core-staging.tar.gz -czf - .'], stdout=output, check=True)
evidence = work / 'evidence'
evidence.mkdir(exist_ok=True)
with tarfile.open(work / 'remote-evidence.tar.gz') as archive:
    archive.extractall(evidence, filter='data')
health = json.loads((evidence / 'health-after.json').read_text())
assert health['taint'] == '0'
if 'backlight_expected' in health:
    assert health['backlight_brightness'] == health['backlight_expected']
assert health['Image_sha256'] == '31bdb671d640863448b59f79801277fe486fa6c78c326bd4ebb51a54559b0577'
for name, result in health.items():
    if isinstance(result, dict):
        assert result['exit'] == 0, (name, result)
assert not re.search(r'bad page|bad rss|mmc.*error|btrfs.*error|transaction aborted|forced readonly', health['dmesg']['output'], re.I)
counters = re.findall(r'\s(\d+)\n', health['btrfs device stats /']['output'])
assert len(counters) == 5 and all(int(v) == 0 for v in counters)
if (evidence / 'mixer-before.state').exists():
    assert (evidence / 'mixer-before.state').read_bytes() == (evidence / 'mixer-after.state').read_bytes()
with (work / 'evidence-SHA256SUMS').open('w') as sums:
    for path in sorted(evidence.rglob('*')):
        if path.is_file():
            with path.open('rb') as source:
                digest = hashlib.file_digest(source, 'sha256').hexdigest()
            sums.write(f'{digest}  evidence/{path.relative_to(evidence)}\n')
if args.cleanup:
    cleanup = '''import pathlib,shutil,json,sys
p=pathlib.Path(sys.argv[1]);assert p.parent==pathlib.Path('/tmp') and p.name.startswith('muos-r35s-p4-core.') and not p.is_symlink()
state=json.loads((p/'session-state.json').read_text());pid=state.get('worker_pid')
try:same=pathlib.Path(f'/proc/{pid}/stat').read_text().split()[21]==state.get('worker_starttime')
except FileNotFoundError:same=False
assert not same
assert not any(line.split()[4].startswith(str(p)) for line in pathlib.Path('/proc/self/mountinfo').read_text().splitlines())
shutil.rmtree(p)
'''
    subprocess.run(ssh + ['sudo -n python3 - ' + shlex.quote(remote)], input=cleanup, text=True, check=True)
print('Session evidence verified; unchanged mixer/kernel; health OK; cleanup=' + str(args.cleanup))
