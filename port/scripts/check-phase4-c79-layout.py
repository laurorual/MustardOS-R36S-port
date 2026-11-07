#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C100 isolated real-ext4 layout tests; no console, Deck or block device."""
from pathlib import Path
import ast,importlib,json,os,subprocess,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_root_migration import require
import phase4_c79_layout as layout


def main():
    os.umask(0o077);repo=Path(__file__).resolve().parents[2];work=repo/'build/phase4';area=work/'c79-layout'
    area.mkdir(mode=0o700,exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='checks.',dir=area))
    template=work/'gambatte-image/image.zal39n7u/target'/layout.TEMPLATE
    require(sha(template)==layout.TEMPLATE_SHA and template.stat().st_size==444,'Reviewed C79 public template')
    write_new(stage/'template.dat',template.read_bytes())
    sources=[Path(__file__),repo/'port/scripts/phase4_c79_layout.py',repo/'port/scripts/phase4-c79-layout.py',
        repo/'port/diagnostics/phase4-c79-layout-fixture.py',repo/'port/scripts/compose-phase4-c79-layout.py',
        *[repo/'port/scripts'/n for n in ['phase4_initial_image.py','phase4_recovery_image.py','phase4_root_recovery.py',
            'phase4_backup_core.py','phase4_root_migration.py']]]
    hashes={str(p.relative_to(repo)):sha(p) for p in sources}
    argv=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
        '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=64m',
        '-v',str(work)+':/work:rw,z','-v',str(repo/'port')+':/port:ro,z',
        (work/'rootfs-container.iid').read_text().strip(),'python3','/port/diagnostics/phase4-c79-layout-fixture.py',
        '/work/'+str(stage.relative_to(work))]
    result=subprocess.run(argv,capture_output=True,timeout=240)
    for n,data in [('stdout',result.stdout),('stderr',result.stderr),('exit',(str(result.returncode)+'\n').encode())]:
        write_new(stage/('fixtures.'+n),data)
    require(result.returncode==0,'C100 fixtures failed; inspect '+str(stage))
    r=json.loads((stage/'fixture-results.json').read_text())
    entry=importlib.import_module('phase4-c79-layout')
    for value in ['/dev/mmcblk0','/tmp/factory.ext4','/work/../dev/mmcblk0']:
        try:entry.work_path(value)
        except ValueError:r['cases'].append('entry-refuses-'+value)
        else:raise AssertionError(value)
    r['case_count']=len(r['cases']);require(len(set(r['cases']))==r['case_count'],'Unique tests')
    for p in sources:ast.parse(p.read_text())
    require(all(sha(repo/n)==h for n,h in hashes.items()),'C100 source changed during checks')
    r.update(source_sha256=hashes,production_factory_or_device_written=False)
    # Only synthetic regular image fixtures in this newly-created stage.
    for p in stage.rglob('*.ext4'):
        require(p.is_file() and not p.is_symlink(),'Unexpected fixture image alias');p.unlink()
    write_new(stage/'analysis.json',(json.dumps(r,indent=2)+'\n').encode());sync_dir(stage)
    (area/'latest-checks').write_text(str(stage)+'\n');sync_dir(area)
    print('C100',r['case_count'],'offline layout checks passed:',stage)


if __name__=='__main__':main()
