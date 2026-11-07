# SPDX-License-Identifier: MIT
"""C105 immutable caller package inputs; C104 remains untouched."""
from pathlib import Path
import importlib,json,re
import phase4_reboot_layout_session as parent
from phase4_candidate import sha,sums
from phase4_root_migration import require

REPO,WORK=parent.REPO,parent.WORK
AREA=WORK/'manual-caller';NATIVE=REPO/'port/device/rk-r35s-p0/manual-caller'
PREFIX='usr/libexec/muos-caller'
SCRIPTS=['adapter.sh','app-launch.sh','cycle.sh','frontend-libs.sh','installed-host.sh','installed-store.sh',
    'select.sh','store-base.sh','store.sh','worker.sh']
NAMES=SCRIPTS+['functions.sh','dependencies.tsv','assets.tsv','contract.json','LICENSE','payload.sha256','caller.sh']

def qualified():
    _,previous=parent.qualified();stage=Path((parent.AREA/'latest-load').read_text().strip())
    require(stage.resolve().is_relative_to(parent.AREA),'Known completed C104')
    public=json.loads((parent.proof('reboot-layout-session')/'analysis.json').read_text())
    r=json.loads((stage/'analysis.json').read_text());parent.transition(previous,r['boot_sequence'],r['kernel_boot_id'])
    require(public['passed'] is True and public['schema']==104 and public['boot_sequence']==r['boot_sequence'] and
        public['physical_image_input_audio_restore_return_confirmed'] is True and
        r['passed'] is True and r['C104_post_reboot_layout_runtime_validation'] is True and
        r['RAM_removed'] is True and r['cleanup_passed'] is True,'Qualified C104 cycle required')
    for n in ['technical-analysis.json','physical-observation.json']:
        receipt=json.loads((stage/n).read_text());require(receipt['passed'] is True and
            receipt['session_analysis_sha256']==sha(stage/'analysis.json'),'C104 physical/technical binding')
    final=json.loads((stage/'final-audit.json').read_text());require(final['passed'] is True,'C104 closure required')
    for n,h in final['recorded_receipts_sha256'].items():require(sha(stage/n)==h,'C104 receipt changed')
    for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'C104 source changed')
    return stage,r

def common():
    _,r=qualified()
    return parent.current_common('',r['prior_boot_sequence'],r['boot_sequence'])+\
        '[ "$(cat /proc/sys/kernel/random/boot_id)" = '+r['kernel_boot_id']+' ]\n'

def original_scripts():
    stage,_=qualified();intent=json.loads((stage/'intent.json').read_text())
    ctx,*_=parent.legacy.historical()
    files={n:ctx['files'][n] for n in ['adapter.sh','cycle.sh','store.sh']}
    files.update({n:parent.NATIVE/n for n in SCRIPTS if n not in files and n!='worker.sh'})
    files['worker.sh']=ctx['worker']
    for n,p in files.items():
        expected=intent['worker_sha256'] if n=='worker.sh' else intent['binary_sha256'][n]
        require(sha(p)==expected and p.read_text().startswith('#!/bin/sh\n# SPDX-License-Identifier: MIT'),
            'Only exact previously qualified MIT caller scripts')
    return files,intent

def public_dependencies():
    code=common()
    rows=re.findall(r"printf '[^']+' ([0-9a-f]{64}) /([A-Za-z0-9_./+-]+) \| sha256sum -c - >/dev/null",code)
    require(len(rows)==143 and len({n for _,n in rows})==143,'Complete C104 hash guard')
    composition=Path((WORK/'initial-migration/latest-complete').read_text().strip())
    tree=json.loads((composition/'tree.json').read_text())
    tree['etc/asound.conf']={**tree['opt/muos/share/conf/rootfs/asound.conf'],'mode':0o644}
    records=[]
    for h,n in sorted(rows,key=lambda row:row[1]):
        if n=='etc/muos-network-authorized_key':continue
        r=tree[n]
        require(r['type']=='regular' and r['sha256']==h and r['uid']==r['gid']==0 and r['links']==1,
            'Public C79/C102 dependency')
        for p in Path(n).parents:
            if str(p)=='.':continue
            d=tree[str(p)];require(d['type']=='directory' and d['mode']==0o755,'Qualified dependency parent modes')
        records.append(f'{h} {r["mode"]:o} {r["bytes"]} {n}\n')
    require(len(records)==142,'Exclude only the provisioned identity guard')
    return ''.join(records)

def source_files():
    return [Path(__file__),REPO/'port/scripts/prepare-phase4-manual-caller.py',
        REPO/'port/scripts/check-phase4-manual-caller.py',REPO/'port/diagnostics/phase4-manual-caller-fixture.py',
        REPO/'port/scripts/run-phase4-manual-caller-install.py',
        *sorted(NATIVE.glob('*.sh'))]
