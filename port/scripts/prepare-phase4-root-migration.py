#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C80 read-only live survey and private p2 migration plan; no secret contents."""
from pathlib import Path
import argparse, hashlib, ipaddress, json, os, re, subprocess, tempfile
from phase4_candidate import sha, sums
import phase4_installed_core_session as live
from phase4_root_migration import make_plan, PRIVATE_FILES, OPTIONAL_PRIVATE

repo = Path(__file__).resolve().parents[2]; work = repo / 'build/phase4'
area = work / 'root-migration'; area.mkdir(exist_ok=True)
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--host',type=ipaddress.IPv4Address,required=True)
p.add_argument('--boot',type=int,required=True)
args = p.parse_args()
os.umask(0o077)
parents = {}
for name in ['gambatte-card-image','installed-core-session']:
    proof = repo / 'dist/phase4' / name
    for n,h in sums(proof/'SHA256SUMS').items(): assert sha(proof/n)==h,(name,n)
    parents[name] = sha(proof/'SHA256SUMS')
factory = json.loads((repo/'dist/phase4/gambatte-card-image/analysis.json').read_text())
ctx, _, prior, _, _, _ = live.historical()
common = live.current_common(ctx['common'],prior['boot_sequence'],args.boot)
ssh = ['ssh','-p','2222','-i',str(work/'private/c07-client'),'-oIdentitiesOnly=yes',
       '-oStrictHostKeyChecking=yes','-oHostKeyAlias=[192.168.15.17]:2222',
       '-oUserKnownHostsFile='+str(work/'private/c07-known_hosts'),'-oBatchMode=yes',
       '-oConnectTimeout=6','root@'+str(args.host)]
stage = Path(tempfile.mkdtemp(prefix='plan.',dir=area))
(area/'latest-attempt').write_text(str(stage)+'\n')
def remote(label, code):
    (stage/(label+'.sh')).write_text(code)
    r = subprocess.run(ssh+['sh -s'],input=code.encode(),capture_output=True,timeout=45)
    for ext,data in [('stdout',r.stdout),('stderr',r.stderr),('exit',(str(r.returncode)+'\n').encode())]:
        (stage/(label+'.'+ext)).write_bytes(data)
    assert r.returncode==0,(label,stage)
    return r.stdout

before = remote('preflight',common+ctx['infra'])
boot_id = remote('boot-id',common+'cat /proc/sys/kernel/random/boot_id\n').decode().strip()
assert re.fullmatch('[0-9a-f-]{36}',boot_id)
common += '[ "$(cat /proc/sys/kernel/random/boot_id)" = '+boot_id+' ]\n'
prefix = remote('boot-prefix',common+'dd if=/dev/mmcblk0 bs=1048576 count=16 2>/dev/null\n')
assert len(prefix)==16*1024*1024
mbr = prefix[:512]; (stage/'mbr.bin').write_bytes(mbr)
factory_image = work/'gambatte-card-image/image.efszbcqw/muos-r35s-panel0-c79-private.img'
assert sha(factory_image) == factory['image_sha256']
with factory_image.open('rb') as stream: expected_prefix = bytearray(stream.read(len(prefix)))
expected_prefix[478:494] = mbr[478:494]
assert prefix == expected_prefix, 'Bootchain prefix differs beyond the existing p3 entry'
paths = sorted(PRIVATE_FILES | OPTIONAL_PRIVATE)
code = common+r'''for path in /var/lib/muos-network /var/lib/muos-seedrng /var/lib/muos-diagnostic;do
 [ -d "$path" ] && [ ! -L "$path" ] && [ "$(stat -c '%u:%g:%a' "$path")" = 0:0:700 ]
done
printf 'model|';tr -d '\000' < /proc/device-tree/model;printf '\n'
printf 'kernel|';uname -r
printf 'capacity_sectors|';cat /sys/class/block/mmcblk0/size
printf 'sector_bytes|';cat /sys/class/block/mmcblk0/queue/logical_block_size
printf 'cid_sha256|';printf %s "$(cat /sys/class/block/mmcblk0/device/cid)" | sha256sum | cut -d' ' -f1
printf 'root_partuuid|';blkid -s PARTUUID -o value /dev/mmcblk0p2
printf 'data_partuuid|';blkid -s PARTUUID -o value /dev/mmcblk0p3
'''
code += 'for name in '+' '.join('/'+n for n in paths)+r''';do
 if [ ! -e "$name" ] && [ ! -L "$name" ];then continue;fi
 [ -f "$name" ] && [ ! -L "$name" ]
 printf 'file|%s|' "${name#/}"
 stat -c '%u|%g|%a|%h|%s' "$name"
 printf 'hash|%s|' "${name#/}";sha256sum "$name" | cut -d' ' -f1
done
# Reject extra network/seed entries rather than silently discard their state.
find /var/lib/muos-network /var/lib/muos-seedrng -mindepth 1 -maxdepth 1 | while IFS= read -r path;do
 printf 'member|%s\n' "${path#/}"
done
'''
raw = remote('survey',code).decode()
observed = {'original_present':False,'root_ro':True,'quiet':True,'p3_mounted':False,
            'boot_sequence':args.boot,'boot_prefix_16MiB_sha256':hashlib.sha256(prefix).hexdigest(),
            'private_files':{},'kernel_boot_id':boot_id,'host':str(args.host)}
members = []
for line in raw.splitlines():
    fields = line.split('|'); key = fields[0]
    if key == 'file':
        assert len(fields)==7 and fields[1] not in observed['private_files']
        observed['private_files'][fields[1]] = dict(zip(['uid','gid','mode','links','bytes'],
            [int(fields[2]),int(fields[3]),int(fields[4],8),int(fields[5]),int(fields[6])]))
    elif key == 'hash':
        assert len(fields)==3
        observed['private_files'][fields[1]]['sha256'] = fields[2]
    elif key == 'member': members.append(fields[1])
    else:
        assert len(fields)==2 and key not in observed
        observed[key] = int(fields[1]) if key in ['capacity_sectors','sector_bytes'] else fields[1]
assert set(members) == {n for n in observed['private_files'] if n.startswith(('var/lib/muos-network/','var/lib/muos-seedrng/'))}
plan = make_plan(mbr,observed,factory)
# This is not a backup: only boot prefix/MBR and metadata hashes were read.
# No network config, key or seed content is exported by this survey.
assert remote('postflight',common+ctx['infra']) == before
assert remote('mbr-after',common+'dd if=/dev/mmcblk0 bs=512 count=1 2>/dev/null\n') == mbr
plan['source_sha256'] = {str(f.relative_to(repo)):sha(f) for f in [Path(__file__),repo/'port/scripts/phase4_root_migration.py']}
plan['parent_proofs_sha256'] = parents
(stage/'survey.json').write_text(json.dumps(observed,indent=2)+'\n')
(stage/'migration-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
(stage/'analysis.json').write_text(json.dumps({'passed':True,'experiment':'C80_LIVE_READONLY_ROOT_MIGRATION_PLAN',
    'boot_sequence':args.boot,'root_read_only':True,'installed40_and_preserved132_verified':True,
    'infrastructure_and_mbr_unchanged':True,'private_file_metadata_count':len(observed['private_files']),
    'bootchain_prefix_matches_C79_except_existing_p3_entry':True,
    'private_file_contents_exported':False,'offline_backup_created':False,'candidate_provisioned':False,
    'device_written':False,'device_writer_available':False,'execution_enabled':False,
    'parent_proofs_sha256':parents,'plan_sha256':sha(stage/'migration-plan.json'),
    'source_sha256':plan['source_sha256']},indent=2)+'\n')
(area/'latest-plan').write_text(str(stage)+'\n')
print('C80 read-only survey/plan passed; no backup, provisioning or device writer:',stage)
