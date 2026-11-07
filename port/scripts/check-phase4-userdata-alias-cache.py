#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""No-device checks for alias flush ordering, identity and failure propagation."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import hashlib,importlib.util,json,os,stat,tempfile,types
from unittest.mock import patch

source=Path(__file__).with_name('audit-phase4-userdata-alias-cache.py')
spec=importlib.util.spec_from_file_location('audit',source);audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/preferences'
stage=Path(tempfile.mkdtemp(prefix='alias-cache-checks.',dir=area));cases=[]
aliases=[('/dev/mmcblk0p2',os.makedev(179,2)),('/dev/mmcblk0',os.makedev(179,0))]
events=[];numbers=iter([10,11])
def opened(path,flags):
    assert flags&(os.O_NOFOLLOW|os.O_CLOEXEC)==os.O_NOFOLLOW|os.O_CLOEXEC
    assert not flags&os.O_WRONLY and not flags&os.O_RDWR
    events.append(('open',path));return next(numbers)
def inode(fd):return types.SimpleNamespace(st_mode=stat.S_IFBLK|0o600,st_rdev=os.makedev(179,2 if fd==10 else 0))
with patch.object(audit.os,'open',opened),patch.object(audit.os,'fstat',inode),\
     patch.object(audit.os,'fsync',lambda fd:events.append(('sync',fd))),\
     patch.object(audit.fcntl,'ioctl',lambda fd,cmd,arg:events.append(('flush',fd,cmd,arg))),\
     patch.object(audit.os,'close',lambda fd:events.append(('close',fd))):
    assert audit.flush_aliases(aliases)==[p for p,_ in aliases]
assert events==[('open',aliases[0][0]),('sync',10),('flush',10,0x1261,0),('close',10),
                ('open',aliases[1][0]),('sync',11),('flush',11,0x1261,0),('close',11)]
cases.append('partition-sync-and-invalidate-before-whole-device-alias')
events=[]
with patch.object(audit.os,'open',return_value=10),\
     patch.object(audit.os,'fstat',return_value=types.SimpleNamespace(st_mode=stat.S_IFREG|0o600,st_rdev=0)),\
     patch.object(audit.os,'close',lambda fd:events.append(('close',fd))),\
     patch.object(audit.fcntl,'ioctl',side_effect=AssertionError('must not flush wrong node')):
    try:audit.flush_aliases(aliases)
    except RuntimeError:pass
    else:raise AssertionError('Wrong node accepted')
assert events==[('close',10)];cases.append('non-block-or-wrong-alias-refused-before-ioctl')
events=[]
with patch.object(audit.os,'open',return_value=10),patch.object(audit.os,'fstat',inode),\
     patch.object(audit.os,'fsync',return_value=None),\
     patch.object(audit.fcntl,'ioctl',side_effect=OSError('flush failed')),\
     patch.object(audit.os,'close',lambda fd:events.append(('close',fd))):
    try:audit.flush_aliases(aliases)
    except OSError:pass
    else:raise AssertionError('Flush error hidden')
assert events==[('close',10)];cases.append('flush-error-closes-fd-and-does-not-claim-readback')
shared_source=Path(__file__).with_name('phase4_userdata_io.py')
shared_spec=importlib.util.spec_from_file_location('shared',shared_source)
shared=importlib.util.module_from_spec(shared_spec);shared_spec.loader.exec_module(shared)
events=[];numbers=iter([10,11])
with patch.object(shared.os,'open',opened),patch.object(shared.os,'fstat',inode),\
     patch.object(shared.os,'fsync',lambda fd:events.append(('sync',fd))),\
     patch.object(shared.fcntl,'ioctl',lambda fd,cmd,arg:events.append(('flush',fd,cmd,arg))),\
     patch.object(shared.os,'close',lambda fd:events.append(('close',fd))):
    assert shared.flush_block_aliases(aliases)==[p for p,_ in aliases]
assert events==[('open',aliases[0][0]),('sync',10),('flush',10,0x1261,0),('close',10),
                ('open',aliases[1][0]),('sync',11),('flush',11,0x1261,0),('close',11)]
cases.append('shared-IO-keeps-partition-first-flush-order')
with patch.object(shared.os,'open',return_value=10),\
     patch.object(shared.os,'fstat',return_value=types.SimpleNamespace(st_mode=stat.S_IFBLK|0o600,st_rdev=os.makedev(259,0))),\
     patch.object(shared.os,'close',return_value=None),\
     patch.object(shared.fcntl,'ioctl',side_effect=AssertionError('must not flush foreign node')):
    try:shared.flush_block_aliases(aliases)
    except ValueError:pass
    else:raise AssertionError('Foreign block alias accepted')
cases.append('shared-IO-refuses-foreign-block-node-before-ioctl')
result={'passed':True,'cases':cases,'case_count':len(cases),'real_block_devices_opened':False,
        'audit_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'io_source_sha256':hashlib.sha256(shared_source.read_bytes()).hexdigest()}
(stage/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
(area/'latest-alias-cache-checks').write_text(str(stage)+'\n')
for case in cases:print('PASS',case)
print(stage)
