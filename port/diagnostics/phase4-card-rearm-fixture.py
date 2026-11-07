#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C95 protection-only orchestration and collector refusal; no card/network."""
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from copy import deepcopy
import importlib,json,os,sys
sys.path.insert(0,'/port/scripts')
import phase4_backup_core as core
import phase4_root_migration as policy
h=importlib.import_module('phase4-card-rearm');prep=importlib.import_module('prepare-phase4-card-rearm')
os.umask(0o077);stage=Path(sys.argv[1]);cases=[]
def passed(name):cases.append(name);print('C95_PASS_'+name,flush=True)
def reject(name,fn):
    try:fn()
    except (ValueError,OSError,KeyError,TypeError):passed(name)
    else:raise AssertionError(name)
def folder(name):p=stage/name;p.mkdir(mode=0o700);return p
old={'schema':83,'scope':'inode2_mode0777_to0755_only','host_copy_verified':True,'metadata_repair_required_before_boot':True,
    'deck_backup':'/var/tmp/muos-r35s-c81-backup.12345678','backup_artifacts':{}}
for n in ['host_ack_sha256','backup_receipt_sha256','prefix_before_sha256','mbr_sha256','boot_prefix_16MiB_sha256','automount_rule_sha256']:old[n]='a'*64
ctx={'schema':95,'operation':'protect-and-capture','legacy_context':old,'runtime_guard_sha256':'b'*64,'expected_boot_sequence':76,'attempt_sha256':'c'*64}
h.validate_context(ctx,policy);passed('finite-protection-context-current-boot')
for name,change in [('no-repair-mode',lambda x:x.update(operation='apply')),('no-extra-context',lambda x:x.update(writer=True)),
    ('no-boolean-boot',lambda x:x.update(expected_boot_sequence=True)),('no-old-boot',lambda x:x.update(expected_boot_sequence=72)),
    ('no-invalid-fence',lambda x:x.update(attempt_sha256='bad')),('no-foreign-backup',lambda x:x['legacy_context'].update(deck_backup='/tmp/backup')),
    ('no-unqualified-backup',lambda x:x['legacy_context'].update(host_copy_verified=False)),
    ('no-unknown-legacy-scope',lambda x:x['legacy_context'].update(scope='write-anything'))]:
    bad=deepcopy(ctx);change(bad);reject(name,lambda bad=bad:h.validate_context(bad,policy))
root=folder('root');rule=stage/'runtime-rule';source=stage/'mock-card';source.write_bytes(b'current prefix bytes')
for n in h.SOURCES:(root/n).write_text('synthetic leaf '+n+'\n')
(root/'context.json').write_bytes(prep.recovery.encoded(ctx))
events=[];failure=None;capsules={n:{'sb':b'superblock','gd':b'group-descriptor','sector':b'inode-sector','patch':{'synthetic_partition':n}} for n in (2,3)}
def run(args):
    events.append(args[0])
    if failure=='fsck' and args[0]=='e2fsck':raise ValueError('unclean filesystem')
    return SimpleNamespace(stdout=('77\n' if failure=='boot' else '76\n') if args[0]=='debugfs' else '')
def backup():events.append('backup');return ['synthetic userdata']
def auto():events.append('guard');return '0'*64 if failure=='guard' else ctx['runtime_guard_sha256']
def readonly():events.append('RO1')
def userdata(mode,rows):assert mode==0o777 and rows==['synthetic userdata'];events.append('userdata')
def capsule(fd,n):
    events.append('capsule-'+str(n))
    if failure=='capsule' and events.count('capsule-'+str(n))==2:raise ValueError('capsule changed')
    return deepcopy(capsules[n])
def copy_region(fd,offset,size,dest):
    assert offset==0 and size==640*1024*1024;events.append('copy-prefix')
    dest.write_bytes(os.pread(fd,source.stat().st_size,0));return core.sha(dest)
def region_sha(fd,offset,size):
    assert offset==0 and size==640*1024*1024
    return '0'*64 if failure=='prefix' else core.sha(source)
guard=SimpleNamespace(identity=lambda:events.append('identity'))
legacy=SimpleNamespace(ROOT=root,backup_check=backup,automount_guard=auto,readonly_card=readonly,run=run,userdata_check=userdata,
    open_whole=lambda:os.open(source,os.O_RDONLY),capsule=capsule)
fakecore=SimpleNamespace(sha=core.sha,write_new=core.write_new,copy_region=copy_region,region_sha=region_sha)
def path(value):return rule if str(value)=='/run/udev/rules.d/99-holo-automount.rules' else Path(value)
def protect(where):
    with patch.object(h,'Path',path):return h.protect(where,ctx,legacy,guard,fakecore,policy)
where=folder('success');result=protect(where)
assert events.index('guard')<events.index('RO1')<events.index('e2fsck')<events.index('copy-prefix')
assert events.count('RO1')==2 and result['repair_applied'] is False and result['physical_payload_written'] is False
assert result['media_unlocked'] is False and result['boot_sequence']==76
assert core.sha(where/'current-prefix.backup')==core.sha(source);passed('runtime-guard-and-RO-before-capture-without-writable-open')
manifest={'files':{n:core.sha(root/n) for n in h.SOURCES}}
prep.validate_report(result,ctx,manifest);passed('native-protection-only-receipt-validated')
for why in ['guard','fsck','boot','prefix','capsule']:
    events.clear();failure=why;where=folder('failure-'+why)
    reject(why+'-failure-without-completion',lambda where=where:protect(where))
    assert not (where/'analysis.json').exists()
    if why in ['guard','fsck','boot']:assert 'copy-prefix' not in events
failure=None;events.clear();rule.write_bytes(b'unknown rule');rule.chmod(0o644)
reject('unknown-runtime-rule-preserved',lambda:protect(folder('unknown-rule')))
assert rule.read_bytes()==b'unknown rule' and 'guard' not in events
ctx['runtime_guard_sha256']=core.sha(rule);events.clear();protect(folder('existing-rule'))
assert 'guard' not in events and events.count('RO1')==2;passed('already-correct-runtime-rule-reused-without-rewrite')
ctx['runtime_guard_sha256']='b'*64;rule.unlink()
for name,change in [('no-native-repair-claim',lambda x:x.update(repair_applied=True)),
    ('no-native-media-unlock',lambda x:x.update(media_unlocked=True)),('no-native-payload-write',lambda x:x.update(physical_payload_written=True)),
    ('no-native-seed-generation',lambda x:x.update(seed_loaded_or_generated=True)),
    ('no-native-incomplete-RO',lambda x:x.update(all_four_aliases_kernel_readonly=False)),
    ('no-native-wrong-boot',lambda x:x.update(boot_sequence=77)),('no-native-wrong-source',lambda x:x.update(source_sha256={})),
    ('no-native-wrong-preimage-size',lambda x:x.update(prefix_bytes=512*1024*1024))]:
    bad=deepcopy(result);change(bad);reject(name,lambda bad=bad:prep.validate_report(bad,ctx,manifest))
# Context passed to a report is pinned by its hash too.
bad=deepcopy(ctx);bad['expected_boot_sequence']=77
reject('report-context-hash-binding',lambda:prep.validate_report(result,bad,manifest))
(stage/'fixture-results.json').write_text(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,
    'physical_IO_guard_and_metadata_utilities_stubbed':True,'protection_orchestration_and_report_validation_executed':True,
    'privileged_namespace_bootstrap_or_native_collector_executed':False})+'\n')
