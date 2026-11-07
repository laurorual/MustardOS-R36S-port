#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Exercise bounded MBR commit/recovery on real regular files; no block devices."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import hashlib,importlib.util,json,os,tempfile
from unittest.mock import patch

def module(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
io=module('phase4_userdata_io')
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/preferences'
survey=Path((area/'latest-layout').read_text().strip());assert survey.is_relative_to(area)
before=(survey/'mbr.before').read_bytes();after=(survey/'mbr.proposed').read_bytes()
stage=Path(tempfile.mkdtemp(prefix='offline-io.',dir=area))
fixture=stage/'regular-fixture';tail=bytes(range(256))*256
original=before+tail;cases=[]
def passed(name):cases.append(name)
def reset():fixture.write_bytes(original)
def refuse(call):
    try:call()
    except (ValueError,io.CommitError):return
    raise AssertionError('Unexpected operation accepted')
reset();fd=os.open(fixture,os.O_RDWR|os.O_NOFOLLOW)
try:
    io.commit_mbr(fd,before,after)
    assert fixture.read_bytes()==after+tail
    assert io.canonical_prefix_sha256(fd,len(original),before)==hashlib.sha256(original).hexdigest()
    passed('commit-changes-only-approved-slot-and-preserves-whole-prefix')
    io.restore_mbr_slot(fd,before,after);assert fixture.read_bytes()==original
    passed('explicit-recovery-restores-exact-prefix')
    wrong=bytearray(after);wrong[440]^=1
    refuse(lambda:io.commit_mbr(fd,before,wrong));assert fixture.read_bytes()==original
    passed('non-p3-change-refused-before-write')
    os.pwrite(fd,b'X',10);snapshot=fixture.read_bytes()
    refuse(lambda:io.commit_mbr(fd,before,after));assert fixture.read_bytes()==snapshot
    passed('media-drift-refused-before-write')
    refuse(lambda:io.restore_mbr_slot(fd,before,after));assert fixture.read_bytes()==snapshot
    passed('recovery-refuses-changed-protected-bytes')
    reset();real_pwrite=os.pwrite
    def short(fd,data,offset):return real_pwrite(fd,data[:17],offset)
    with patch.object(io.os,'pwrite',short):io.commit_mbr(fd,before,after)
    assert fixture.read_bytes()==after+tail;passed('short-writes-complete-within-one-sector')
    reset()
    with patch.object(io.os,'fsync',side_effect=OSError('injected sync failure')):
        try:io.commit_mbr(fd,before,after)
        except io.CommitError as error:assert error.phase=='fsync' and error.may_have_changed
        else:raise AssertionError('Sync error hidden')
    assert fixture.read_bytes()==after+tail
    io.restore_mbr_slot(fd,before,after);assert fixture.read_bytes()==original
    passed('sync-failure-reports-uncertainty-no-auto-rollback-explicit-recovery')
    def torn(fd,data,offset):
        if offset>=480:raise OSError('injected torn slot write')
        return real_pwrite(fd,data[:min(16,480-offset)],offset)
    with patch.object(io.os,'pwrite',torn):refuse(lambda:io.commit_mbr(fd,before,after))
    partial=fixture.read_bytes();assert partial[:478]==original[:478] and partial[494:]==original[494:]
    io.restore_mbr_slot(fd,before,after);assert fixture.read_bytes()==original
    passed('partial-slot-write-explicit-recovery-keeps-protected-regions')
    baseline=stage/'baseline';baseline.write_bytes(original)
    old=os.open(baseline,os.O_RDONLY)
    try:
        os.pwrite(fd,b'X',2048)
        result=io.compare_metadata_change(fd,old,len(original),before,[(2048,2050)])
        assert result['changed_offsets']==[2048]
        passed('bounded-metadata-comparison-hashes-every-protected-byte')
        os.pwrite(fd,b'Y',4096)
        refuse(lambda:io.compare_metadata_change(fd,old,len(original),before,[(2048,2050)]))
        passed('root-permission-repair-cannot-hide-changed-file-data')
        refuse(lambda:io.compare_metadata_change(fd,old,len(original),before,[(0,512)]))
        passed('metadata-exemption-cannot-cover-MBR-or-invalid-bounds')
    finally:os.close(old);baseline.unlink()
finally:os.close(fd)
fixture.unlink()
result={'passed':True,'case_count':len(cases),'cases':cases,'block_devices_opened':False,
 'real_block_writer_or_formatter_enabled':False,
 'sources':{n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest()
            for n in ['phase4_userdata_io.py','check-phase4-userdata-io.py']}}
(stage/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
(area/'latest-offline-io').write_text(str(stage)+'\n')
for name in cases:print('PASS',name)
print(stage)
