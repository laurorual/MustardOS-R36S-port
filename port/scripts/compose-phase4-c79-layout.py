#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C100 compose a derived factory on this host; never provision or deploy it."""
from pathlib import Path
import json,os,stat,subprocess,tempfile
from phase4_backup_core import sha,write_new,sync_dir
from phase4_candidate import sums
from phase4_root_migration import require,ROOT_BYTES
import phase4_c79_layout as layout

REPO=Path(__file__).resolve().parents[2];WORK=REPO/'build/phase4';AREA=WORK/'c79-layout'


def main():
    os.umask(0o077);AREA.mkdir(mode=0o700,exist_ok=True)
    require(not (AREA/'compose.claim').exists(),'Inspect existing C100 composition before another copy')
    checks=Path((AREA/'latest-checks').read_text().strip());require(checks.resolve().is_relative_to(AREA),'Known C100 checks')
    tested=json.loads((checks/'analysis.json').read_text());require(tested['passed'] is True,'C100 checks required')
    for n,h in tested['source_sha256'].items():require(sha(REPO/n)==h,'Tested layout source changed')
    parents={}
    for name in ['gambatte-card-image','c79-session','initial-boot-native']:
        p=REPO/'dist/phase4'/name
        for n,h in sums(p/'SHA256SUMS').items():require(sha(p/n)==h,'Frozen source proof changed')
        parents[name]=sha(p/'SHA256SUMS')
    previous=json.loads((REPO/'dist/phase4/gambatte-card-image/analysis.json').read_text())
    require(previous['C78_rootfs_sha256']==layout.C79_SHA,'Pinned C79 source factory proof')
    source=WORK/'initial-image/provision.evbj4tey/factory.ext4';s=source.lstat()
    require(stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1 and
        stat.S_IMODE(s.st_mode) in (0o400,0o600) and s.st_size==ROOT_BYTES and sha(source)==layout.C79_SHA,
        'Reuse the independent private regular C79 factory; never the provisioned candidate')
    write_new(AREA/'compose.claim',b'C100 composition started; inspect stage before repeating\n');sync_dir(AREA)
    stage=Path(tempfile.mkdtemp(prefix='compose.',dir=AREA));output=stage/'output';output.mkdir(mode=0o700)
    (AREA/'latest-attempt').write_text(str(stage)+'\n');sync_dir(AREA)
    request={'factory_image':'/work/'+str(source.relative_to(WORK)),'factory_sha256':layout.C79_SHA}
    write_new(stage/'request.json',(json.dumps(request,indent=2)+'\n').encode())
    argv=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
        '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=64m',
        '-v',str(WORK)+':/work:rw,z','-v',str(REPO/'port')+':/port:ro,z',
        (WORK/'rootfs-container.iid').read_text().strip(),'python3','/port/scripts/phase4-c79-layout.py',
        '--request','/work/'+str((stage/'request.json').relative_to(WORK)),
        '--stage','/work/'+str(output.relative_to(WORK))]
    result=subprocess.run(argv,capture_output=True,timeout=900)
    for n,data in [('stdout',result.stdout),('stderr',result.stderr),('exit',(str(result.returncode)+'\n').encode())]:
        write_new(stage/('compose.'+n),data)
    require(result.returncode==0,'C100 composition failed; preserve stage, never deploy a partial')
    r=json.loads((output/'analysis.json').read_text());before=json.loads((output/'before-tree.json').read_text())
    after=json.loads((output/'tree.json').read_text());image=output/'factory.ext4';s=image.lstat()
    require(r['passed'] is True and r['schema']==100 and r['root_bytes']==ROOT_BYTES and
        r['source_factory_sha256']==layout.C79_SHA and r['fsck_exit']==0 and
        r['full_tree_and_metadata_readback_matched'] is True and r['factory_counter_preserved']==0 and
        r['filesystem_identity_features_and_geometry_preserved'] is True,'Full positive C100 composition required')
    require(stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode)==0o600 and s.st_nlink==1 and s.st_size==ROOT_BYTES and
        sha(image)==r['factory_sha256'] and after==layout.expected_tree(before),'Independent image hash and tree delta')
    require(sha(source)==layout.C79_SHA,'Original factory changed')
    for n,h in tested['source_sha256'].items():require(sha(REPO/n)==h,'Source changed during production composition')
    host={'passed':True,'schema':100,'analysis_sha256':sha(output/'analysis.json'),'factory_sha256':sha(image),
        'source_factory_unchanged':True,'checks_sha256':sha(checks/'analysis.json'),'parent_proofs_sha256':parents,
        'source_sha256':tested['source_sha256'],'network_or_device_accessed':False,'seed_provisioned':False,
        'root_tree_entry_count':len(after),'new_paths':sorted(layout.ADDED),'full_card_image_created':False,
        'hardware_boot_or_installed_layout_qualified':False}
    write_new(stage/'host-analysis.json',(json.dumps(host,indent=2)+'\n').encode());sync_dir(output);sync_dir(stage)
    (AREA/'latest-complete').write_text(str(stage)+'\n');sync_dir(AREA)
    print('C100 derived factory full readback/fsck passed; no device action:',stage)


if __name__=='__main__':main()
