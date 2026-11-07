#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C97 guard matching/render/decoder tests. No device, SSH or entropy actions."""
from pathlib import Path
from unittest.mock import patch
from copy import deepcopy
import importlib,json,os,subprocess,sys
sys.path.insert(0,'/port/scripts')
boot=importlib.import_module('collect-phase4-initial-boot');r=boot.recovery
os.umask(0o077);stage=Path(sys.argv[1]);cases=[]
def passed(name):cases.append(name);print('C97_PASS_'+name,flush=True)
def reject(name,fn):
    try:fn()
    except (ValueError,OSError,KeyError,TypeError):passed(name)
    else:raise AssertionError(name)
common=(stage/'common.sh').read_text();tree=json.loads((stage/'guard-tree.json').read_text())
code,matching=boot.matched_common(common,tree)
assert matching=={'guard_file_count':141,'C79_public_file_count':140,'stable_identity_guard_file_count':1}
assert "stat -c '%u:%g:%a' /" in code and '/proc/mounts' in code and '/proc/modules' in code
passed('all141-native-guard-files-match-current-C79-candidate-and-safe-metadata')
name=next(n for n in tree if n not in r.PRIVATE_FILES|r.OPTIONAL_PRIVATE)
for why,change in [('changed-file-bytes',lambda x:x[name].update(sha256='0'*64)),('missing-file',lambda x:x.pop(name)),
    ('symlink-substitute',lambda x:x[name].update(type='symlink')),('unsafe-public-mode',lambda x:x[name].update(mode=0o777)),
    ('wrong-owner',lambda x:x[name].update(uid=1000)),('hardlink-substitute',lambda x:x[name].update(links=2)),
    ('empty-file',lambda x:x[name].update(bytes=0))]:
    bad=deepcopy(tree);change(bad);reject(why,lambda bad=bad:boot.matched_common(common,bad))
lines=common.splitlines(keepends=True);index=next(i for i,line in enumerate(lines) if '| sha256sum -c - >/dev/null' in line)
reject('missing-guard-hash-line',lambda:boot.matched_common(''.join(lines[:index]+lines[index+1:]),tree))
reject('duplicate-guard-hash-line',lambda:boot.matched_common(common+lines[index],tree))
auth='etc/muos-network-authorized_key';bad=deepcopy(tree);bad[auth]['sha256']='0'*64
reject('authorized-key-must-also-match-candidate',lambda:boot.matched_common(common,bad))
stable={auth:{'mode':0o644,'bytes':80,'sha256':'a'*64}}
rendered=boot.entropy.render(code,78,stable,['b'*64,'c'*64])
script=stage/'rendered.sh';script.write_text(rendered)
result=subprocess.run(['/bin/sh','-n',str(script)],capture_output=True,timeout=10);assert result.returncode==0,result.stderr
assert 'Seeding 2048 bits without crediting' in rendered and 'stop-ready.txt' in rendered and 'seed.no-credit' in rendered
assert rendered.count('[ "$credit_hash" != ')==2
assert 'boot_sequence|78' in rendered and '[ "$(cat /var/lib/muos-diagnostic/boot-seq)" = 78 ]' in rendered
passed('read-only-shell-render-parses-and-requires-first-boot78-and-seedless-path')
reject('unsafe-identity-path',lambda:boot.entropy.render(code,78,{'etc/../unsafe':stable[auth]},['b'*64]))
reject('invalid-old-seed-digest',lambda:boot.entropy.render(code,78,stable,['bad']))
reject('invalid-first-boot-counter',lambda:boot.entropy.render(code,10000,stable,['b'*64]))
valid='boot_sequence|78\nboot_id|12345678-1234-1234-1234-123456789abc\ncredit_bytes|256\nno_credit_consumed_without_credit|1\n'
assert boot.entropy.decoded(valid,78)['credit_bytes']=='256';passed('strict-decoder-first-boot-identity-and-credit-size')
for why,text in [('wrong-counter',valid.replace('sequence|78','sequence|79')),('bad-boot-id',valid.replace('12345678-1234-1234-1234-123456789abc','bad')),
    ('duplicate-evidence',valid+'boot_sequence|78\n'),('missing-evidence',valid.replace('credit_bytes|256\n','')),
    ('unknown-evidence',valid+'other|value\n'),('too-short-credit',valid.replace('bytes|256','bytes|1')),
    ('entropy-credit-claim',valid.replace('without_credit|1','without_credit|0'))]:
    reject(why,lambda text=text:boot.entropy.decoded(text,78))
missing=stage/'uncollected';before=set(stage.iterdir())
with patch.object(boot.prep,'AREA',missing),patch.object(boot.subprocess,'run',side_effect=AssertionError('Unexpected SSH')):
    reject('native-migration-and-independent-fence-required-before-SSH-or-stage',lambda:boot.main('192.168.15.16'))
assert set(stage.iterdir())==before;passed('pending-C94-cannot-be-qualified-as-booted')
(stage/'fixture-results.json').write_text(json.dumps({'passed':True,'case_count':len(cases),'cases':cases,
    'current_candidate_guard_inventory_reverified_without_payload_export':True,
    'first_boot_shell_executed_on_console':False,'native_positive_lineage_or_SSH_main_executed':False})+'\n')
