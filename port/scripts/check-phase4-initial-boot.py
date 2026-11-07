#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C97 isolated guard matcher/entropy renderer/decoder tests, no SSH/media."""
from pathlib import Path
import ast,importlib,json,os,re,subprocess,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_root_migration import require
from phase4_candidate import sums

def main():
    os.umask(0o077);repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'initial-boot';area.mkdir(exist_ok=True)
    boot=importlib.import_module('collect-phase4-initial-boot');composed=boot.prep.initial.latest(work/'initial-migration','latest-complete')
    report=json.loads((composed/'analysis.json').read_text());require(report['passed'] is True,'Completed C93 composition required')
    common=boot.installed.current_common('',report['migration_counter'],report['expected_first_C07_counter'])
    tree=json.loads((composed/'tree.json').read_text());boot.matched_common(common,tree)
    names=re.findall(r"printf '[^']+' [0-9a-f]{64} /([A-Za-z0-9_./+-]+) \| sha256sum -c - >/dev/null",common)
    stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area));write_new(stage/'common.sh',common.encode())
    # This includes one stable authorized-public-key hash and stays private;
    # neither this map nor the generated shell is exported in a public proof.
    write_new(stage/'guard-tree.json',(json.dumps({n:tree[n] for n in names},indent=2)+'\n').encode())
    sources={Path(__file__),repo/'port/diagnostics/phase4-initial-boot-fixture.py',
        *[repo/'port/scripts'/n for n in ['collect-phase4-initial-boot.py','collect-phase4-recovery-boot.py',
            'phase4_installed_core_session.py','phase4_gambatte_install.py','phase4_installed_provider_session.py',
            'phase4_frontend_libs_session.py','collect-phase4-p2-initial.py','prepare-phase4-p2-initial.py']]}
    hashes={str(p.relative_to(repo)):sha(p) for p in sources};parents={}
    for name in ['p2-initial-prepared','initial-preparer','initial-migration','p2-recovery-boot']:
        root=repo/'dist/phase4'/name
        for n,d in sums(root/'SHA256SUMS').items():require(sha(root/n)==d,'Frozen parent changed')
        parents[name]=sha(root/'SHA256SUMS')
    container=(work/'rootfs-container.iid').read_text().strip()
    argv=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
        '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=64m',
        '-v',str(work)+':/work:rw,z','-v',str(repo/'port')+':/port:ro,z',container,'python3',
        '/port/diagnostics/phase4-initial-boot-fixture.py','/work/'+str(stage.relative_to(work))]
    result=subprocess.run(argv,capture_output=True,timeout=120)
    for n,data in [('stdout',result.stdout),('stderr',result.stderr),('exit',(str(result.returncode)+'\n').encode())]:write_new(stage/('fixtures.'+n),data)
    require(result.returncode==0,'C97 fixture failed; inspect '+str(stage))
    r=json.loads((stage/'fixture-results.json').read_text());require(r['passed'] is True and r['case_count']==len(set(r['cases'])),'Unique complete checks')
    for p in sources:ast.parse(p.read_text())
    require(all(sha(repo/n)==d for n,d in hashes.items()),'Tested source changed')
    r.update(source_sha256=hashes,parent_proofs_sha256=parents,network_or_physical_media_contacted=False,
        composition_receipt_sha256=sha(composed/'analysis.json'),common_sha256=sha(stage/'common.sh'),guard_tree_sha256=sha(stage/'guard-tree.json'))
    write_new(stage/'analysis.json',(json.dumps(r,indent=2)+'\n').encode());sync_dir(stage)
    (area/'latest-checks').write_text(str(stage)+'\n');sync_dir(area);print('C97',r['case_count'],'offline checks passed:',stage)

if __name__=='__main__':main()
