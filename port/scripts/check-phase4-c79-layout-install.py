#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C102 isolated transaction checks, including partial publication and recovery."""
from pathlib import Path
import ast,json,os,subprocess,tempfile
from phase4_candidate import sha

REPO=Path(__file__).resolve().parents[2];WORK=REPO/'build/phase4';AREA=WORK/'c79-layout-install'
NATIVE=REPO/'port/device/rk-r35s-p0/c79-layout-install'

def sources():
    return [Path(__file__),REPO/'port/diagnostics/phase4-c79-layout-install-fixture.py',
        REPO/'port/scripts/run-phase4-c79-layout-install.py',*sorted(NATIVE.glob('*.sh'))]

def main():
    os.umask(0o077);AREA.mkdir(mode=0o700,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='checks.',dir=AREA))
    template=WORK/'gambatte-image/image.zal39n7u/target/opt/muos/share/conf/rootfs/asound.conf'
    assert template.stat().st_size==444 and sha(template)=='58aa042723b6935ddf81d44b47e6e960279f257e2543e0ed2626c461f585e8cb'
    (stage/'template.dat').write_bytes(template.read_bytes())
    hashes={str(p.relative_to(REPO)):sha(p) for p in sources()}
    for p in sources():
        if p.suffix=='.py':ast.parse(p.read_text())
        else:subprocess.run(['sh','-n',str(p)],check=True)
    argv=['podman','run','--rm','--network=none','--read-only','--cap-drop=all','--security-opt=no-new-privileges',
        '--userns=keep-id:uid=0,gid=0','--user=0','--tmpfs','/tmp:rw,nosuid,nodev,size=32m',
        '-v',str(stage)+':/work:rw,z','-v',str(REPO/'port')+':/port:ro,z',
        (WORK/'rootfs-container.iid').read_text().strip(),'python3',
        '/port/diagnostics/phase4-c79-layout-install-fixture.py','/work']
    r=subprocess.run(argv,capture_output=True,text=True,timeout=120)
    for n,v in [('stdout',r.stdout),('stderr',r.stderr),('exit',str(r.returncode)+'\n')]: (stage/n).write_text(v)
    assert r.returncode==0,('C102 fixture failure, preserve stage',stage,r.stdout[-500:],r.stderr[-1500:])
    report=json.loads((stage/'fixture-results.json').read_text())
    assert len(set(report['cases']))==report['case_count']==35
    assert all(sha(REPO/n)==h for n,h in hashes.items())
    report.update(schema=102,source_sha256=hashes,device_or_block_writer_executed=False,
        root_remounts_mocked=True,native_media_guards_not_executed_in_fixture=True)
    (stage/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    (AREA/'latest-checks').write_text(str(stage)+'\n')
    print('C102',report['case_count'],'transaction checks passed:',stage)

if __name__=='__main__':main()
