#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C100 publish source/checks and public factory evidence, never image payloads."""
from pathlib import Path
import json,os,shutil,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_candidate import sums
from phase4_root_migration import require,ROOT_BYTES
import phase4_c79_layout as layout
from importlib import import_module


def main():
    os.umask(0o077);builder=import_module('compose-phase4-c79-layout');repo,area=builder.REPO,builder.AREA
    out=repo/'dist/phase4/c79-layout';require(not out.exists(),'Frozen C100 proof must not be replaced')
    stage=Path((area/'latest-complete').read_text().strip());require(stage.resolve().is_relative_to(area),'Known completed composition')
    host=json.loads((stage/'host-analysis.json').read_text());output=stage/'output'
    report=json.loads((output/'analysis.json').read_text());checks=Path((area/'latest-checks').read_text().strip())
    require(checks.resolve().is_relative_to(area),'Known C100 check stage');tested=json.loads((checks/'analysis.json').read_text())
    require(host['passed'] is report['passed'] is tested['passed'] is True and host['schema']==report['schema']==100 and
        host['analysis_sha256']==sha(output/'analysis.json') and host['checks_sha256']==sha(checks/'analysis.json') and
        host['source_sha256']==tested['source_sha256'],'Complete tested production lineage')
    require(report['root_bytes']==ROOT_BYTES and report['source_factory_sha256']==layout.C79_SHA and
        host['factory_sha256']==report['factory_sha256']==sha(output/'factory.ext4') and
        json.loads((output/'tree.json').read_text())==layout.expected_tree(json.loads((output/'before-tree.json').read_text())),
        'Derived factory image/hash/full-tree delta binding')
    for name,h in host['parent_proofs_sha256'].items():
        p=repo/'dist/phase4'/name;require(sha(p/'SHA256SUMS')==h,'Parent proof binding')
        for n,d in sums(p/'SHA256SUMS').items():require(sha(p/n)==d,'Frozen parent changed')
    for n,h in tested['source_sha256'].items():require(sha(repo/n)==h,'Tested source changed')
    public=Path(tempfile.mkdtemp(prefix='public.',dir=area))
    summary={**report,'production_container_and_host_main_executed':True,'checks':tested['case_count'],
        'new_regular_file_payload_bytes':444,'new_directory_count':1,'parent_proofs_sha256':host['parent_proofs_sha256'],
        'network_console_or_Deck_accessed':False,'full_card_image_created':False,'provisioning_required_before_network_boot':True,
        'native_installation_or_reboot_performed':False,'raw_ELF_ROM_state_image_or_runtime_identity_included':False,
        'private_only':True,'redistribution_approved':False}
    write_new(public/'analysis.json',(json.dumps(summary,indent=2)+'\n').encode())
    write_new(public/'checks.json',(json.dumps({n:tested[n] for n in ['passed','case_count','cases','real_ext4_32MiB',
        'full_scan_fsck_and_regular_writes_executed','physical_media_or_network_accessed','source_sha256']},indent=2)+'\n').encode())
    sources={Path(__file__),repo/'docs/archive/phase4/phase4-c79-layout.md',*[repo/n for n in tested['source_sha256']]}
    for source in sources:
        target=public/'source'/source.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    for p in public.rglob('*'):
        require(not p.is_symlink(),'Public proof symlink')
        if p.is_file():require(p.suffix in {'.py','.md','.json'} and not p.read_bytes().startswith(b'\x7fELF'),'Unexpected public payload')
    write_new(public/'SHA256SUMS',''.join(sha(p)+'  '+str(p.relative_to(public))+'\n' for p in sorted(public.rglob('*')) if p.is_file()).encode())
    for p in public.rglob('*'):
        if p.is_file():
            fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
            try:os.fsync(fd)
            finally:os.close(fd)
    for d in sorted((p for p in public.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):sync_dir(d)
    sync_dir(public);os.rename(public,out);sync_dir(out.parent)
    print('C100 factory layout proof:',out)


if __name__=='__main__':main()
