#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Analyze C02 public logs only. Never read seed bytes or compute seed hashes."""
from pathlib import Path
import hashlib,json,re,sys

folder=Path(sys.argv[1]).resolve();expected=sys.argv[2]
assert expected in ['seedless','persisted']
d=json.loads((folder/'log-collection.json').read_text())
assert d['experiment'] in ['MUOS-R35S-INIT-P4-C02','MUOS-R35S-GRAPHICS-P4-C03','MUOS-R35S-FRONTEND-P4-C04','MUOS-R35S-AUDIO-P4-C05','MUOS-R35S-FRONTEND-AUDIO-P4-C06'] and d['base_media_marker']=='MUOS-R35S-EXT4-P4-B01'
tag=d['experiment'].rsplit('-',1)[1]
r=d['files']['REPORT.TXT']['text'];log=d['files']['DMESG.TXT']['text']
assert d['files']['RESULT.TXT']['text'].strip()==tag+'_DIAGNOSTIC_STATUS=0'
assert r.startswith(d['experiment']+'\n') and '4.4.189-muos-r35s-p4' in r
assert 'PID1\n/bin/busybox\n' in r
assert 'ACTIVE STATUS\n0\n' in r and 'FINAL STATUS\n0\n' in r and 'TAINT\n0\n' in r
start=r.split('ENTROPY START\n',1)[1].split('MAPPING\n',1)[0]
stop=r.split('ENTROPY STOP\n',1)[1].split('FINAL STATUS\n',1)[0]
assert 'mode\n'+expected+'\n' in start
before=re.search(r'before.txt\nrng_ready=([01]) wait_ms=(\d+)',start)
after=re.search(r'after.txt\nrng_ready=1 wait_ms=(\d+)',start)
assert before and after and 'rng_ready=1' in stop
assert re.search(r'^Saving \d+ bits of creditable seed for next boot$',start,re.M)
assert re.search(r'^Saving \d+ bits of creditable seed for next boot$',stop,re.M)
if expected=='persisted':assert re.search(r'^Seeding \d+ bits and crediting$',start,re.M)
else:assert not re.search(r'^Seeding \d+ bits and crediting$',start,re.M)
for text in [start,stop]:
    m=re.search(r'seed_owner=0:0 seed_mode=400 seed_bytes=(\d+)',text)
    assert m and 32<=int(m[1])<=256
assert 'Name="muOS-Keys"' in r.split('ACTIVE INPUT\n',1)[1].split('ACTIVE MODULES\n',1)[0]
assert 'Name="muOS-Keys"' not in r.split('FINAL INPUT\n',1)[1].split('TAINT\n',1)[0]
mapping=r.split('MAPPING\n',1)[1].splitlines()[0]
assert re.fullmatch(r'[0-9a-f]{32},muOS-Keys,.*platform:Linux,',mapping)
assert 'org.freedesktop.DBus' in r
mounts=r.split('FINAL MOUNTS\n',1)[1]
root=[x for x in mounts.splitlines() if len(x.split())>=4 and x.split()[1]=='/']
assert len(root)==1 and root[0].split()[2]=='ext4' and 'ro' in root[0].split()[3].split(',')
assert d['candidate_ext4_fsck']['exit_code']==0 and d['taint']=='0'
assert d['services']['stdout']=='active\nactive\nactive'
assert d['stock_image']['stdout'].split()[0]=='31bdb671d640863448b59f79801277fe486fa6c78c326bd4ebb51a54559b0577'
stats=d['btrfs']['stdout'].splitlines();assert len(stats)==5 and all(x.rsplit(None,1)[1]=='0' for x in stats)
assert d['mount_namespace_private'] and d['secondary_mounted_readonly'] and d['secondary_unmounted_after_collection']
pattern=r'\bOops:|\bBUG:|Kernel panic|Call trace:|Internal error|I/O error|Buffer I/O|mmc.*(?:error|timeout|timed out)|EXT4-fs error'
faults=[x for x in log.splitlines() if re.search(pattern,x,re.I)];assert not faults,faults
early=[x for x in log.splitlines() if 'uninitialized urandom read' in x]
legacy_refresh='Legacy refresh after RNG readiness' in start
if legacy_refresh:
    assert expected=='persisted' and 'POLICY_REVISION\n1\n' in r
    assert re.search(r'^Saving \d+ bits of non-creditable seed for next boot$',start,re.M)
    assert re.search(r'^Seeding \d+ bits without crediting$',start,re.M)
    # Preserve the old-kernel SeedRNG fallback warning; consumers must never
    # run before readiness. Do not reclassify warnings from other processes.
    assert len(early)<=1 and all(re.search(r'random: seedrng: uninitialized urandom read',x) for x in early),early
else:assert not early,early
initialized=re.search(r'\[\s*([0-9.]+)\] random: nonblocking pool is initialized',log)
udev_start=re.search(r'\[\s*([0-9.]+)\] udevd\[\d+\]: starting',log)
assert initialized and udev_start and float(initialized[1])<=float(udev_start[1])
if 'POLICY_REVISION\n1\n' in r:
    seq=re.search(r'BOOT_SEQ\n(\d+)\n',r);assert seq
    archived=d['archived_logs'][f'BOOT{int(seq[1]):04d}']
    assert all(archived[name]==d['files'][name] for name in ['REPORT.TXT','DMESG.TXT','RESULT.TXT'])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
result={'scope':'one '+tag+' native cold boot, native SeedRNG and readiness before selected services',
 'passed':True,'mode':expected,'rng_ready_before_service':bool(int(before[1])),
 'readiness_wait_ms':int(after[1]),'native_seedrng_start_and_stop_verified':True,
 'creditable_seed_metadata_verified':True,'persisted_seed_consumed':expected=='persisted',
 'early_urandom_warnings':early,'legacy_native_seedrng_refresh':legacy_refresh,
 'premature_consumer_urandom_warnings':[],'candidate_taint':0,'kernel_fault_matches':faults,
 'rng_initialization_preceded_udev':True,
 'archived_statuses':{name:files.get('RESULT.TXT',{}).get('text','').strip() for name,files in d.get('archived_logs',{}).items()},
 'core_input_mapping_still_passed':True,'root_returned_readonly':True,'offline_ext4_fsck_passed':True,
 'stock_health_passed':True,'seed_bytes_or_seed_hashes_collected':False,
 'kernel_hwrng_validated':False,'complete_rcs_tested':False,'entropy_before_pid1_tested':False,
 'ui_audio_gles_network_tested':False,'software_shutdown_tested':False,'other_panels_tested':False,
 'report_uptime_seconds':float(r.split('UPTIME\n',1)[1].split()[0]),
 'collection_sha256':sha(folder/'log-collection.json'),'analyzer_source_sha256':sha(Path(__file__))}
(folder/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
