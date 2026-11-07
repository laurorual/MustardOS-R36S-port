#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Freeze C88 redacted provisioning/staging evidence, never image contents."""
from pathlib import Path
import argparse,importlib,json,os,shutil,tempfile
from phase4_backup_core import sha,write_new
from phase4_candidate import sums
from phase4_root_migration import require

def main(host):
    os.umask(0o077);prep=importlib.import_module('prepare-phase4-initial-image');repo=prep.REPO;area=prep.AREA
    p=prep.prep.prep.latest(area,'latest-complete');host_report=json.loads((p/'host-analysis.json').read_text());r=json.loads((p/'analysis.json').read_text())
    require(host_report['passed'] is True and sha(p/'analysis.json')==host_report['consumer_analysis_sha256']
        and sha(p/'request.json')==host_report['request_sha256'],'Completed provisioning binding')
    require(r['passed'] is True and r['candidate_provisioned'] is True and r['root_fsck_exit']==0
        and r['boot_handoff_authorized'] is False and sha(p/'candidate.ext4')==r['candidate_sha256'],'Candidate private hash')
    staged=json.loads((p/'deck-stage.json').read_text())
    require(staged['passed'] is True and staged['candidate_sha256']==r['candidate_sha256'] and staged['physical_media_opened_or_written'] is False,'Private staged copy')
    checks=prep.prep.prep.latest(area,'latest-checks');c=json.loads((checks/'analysis.json').read_text())
    require(c['passed'] is True and c['case_count']==len(c['cases']) and sha(checks/'analysis.json')==host_report['checks_sha256'],'Tested provisioning')
    for n,h in host_report['source_sha256'].items():require(sha(repo/n)==h,'Tested source changed')
    t=prep.prep.prep.transport();survey=t.native(host,t.INSPECT);t.validate_inspection(survey)
    code="""from pathlib import Path
import hashlib,json,os,re,stat,sys
r=json.load(sys.stdin);root=Path(r['stage']);assert re.fullmatch(r'/home/deck/muos-r35s-c88-candidate\\.[a-z0-9_]{8}',str(root))
s=root.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o700
fd=os.open(root/'candidate.ext4',os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
try:
 s=os.fstat(fd);assert stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1 and s.st_size==512*1024*1024 and stat.S_IMODE(s.st_mode)==0o600
 h=hashlib.sha256()
 for pos in range(0,s.st_size,1024*1024):
  block=os.pread(fd,1024*1024,pos);assert len(block)==1024*1024;h.update(block)
 a=os.fstat(fd);assert (s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns) and h.hexdigest()==r['sha256']
finally:os.close(fd)
sys=Path('/sys/class/block');assert all((sys/n/'ro').read_text().strip()=='1' for n in ['mmcblk0','mmcblk0p1','mmcblk0p2','mmcblk0p3'])
print(json.dumps({'passed':True,'private_regular_copy_reverified':True,'all_card_aliases_RO':True,'device_opened_or_written':False}))
"""
    post=t.native(host,code,json.dumps({'stage':staged['stage'],'sha256':r['candidate_sha256']}).encode())
    require(post['passed'] is True,'Final staging verification')
    write_new(p/'deck-postflight.json',(json.dumps({'inspection':survey,'postflight':post},indent=2)+'\n').encode())
    parents={}
    for name in host_report['parent_proofs_sha256']:
        proof=repo/'dist/phase4'/name
        for n,h in sums(proof/'SHA256SUMS').items():require(sha(proof/n)==h,'Parent proof changed')
        parents[name]=sha(proof/'SHA256SUMS');require(parents[name]==host_report['parent_proofs_sha256'][name],'Parent binding changed')
    out=repo/'dist/phase4/initial-image';require(not out.exists(),'Do not replace a frozen proof')
    public=Path(tempfile.mkdtemp(prefix='public.',dir=area))
    report={k:v for k,v in r.items() if k!='candidate_sha256'}
    report.update({'experiment':'C88_PRIVATE_INITIAL_C79_PROVISION_AND_DECK_REGULAR_FILE_STAGING',
        'component_check_count':c['case_count'],'private_Deck_copy_sha256_and_fsync_and_re_read_verified':True,
        'all_card_aliases_RO_and_card_unmounted':True,'physical_media_written':False,
        'qualified_for_boot_or_initial_physical_migration':False,'parent_proofs_sha256':parents,
        'private_images_payloads_trees_or_hashes_included':False})
    write_new(public/'analysis.json',(json.dumps(report,indent=2)+'\n').encode())
    for name in ['analysis.json','fixtures.stdout','fixtures.stderr','fixtures.exit']:
        shutil.copyfile(checks/name,public/('component-checks.json' if name=='analysis.json' else name))
    sources={repo/n for n in host_report['source_sha256']};sources.update([Path(__file__),repo/'docs/analysis/phase4-initial-image.md'])
    for source in sources:
        target=public/'source'/source.relative_to(repo);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    request=json.loads((p/'request.json').read_text());forbidden=[r['candidate_sha256'],request['reference_sha256']]
    forbidden.extend(row['sha256'] for row in request['private_files'].values())
    for source in public.rglob('*'):
        require(not source.is_symlink(),'Public symlink')
        if source.is_file():
            require(source.suffix not in {'.img','.ext4','.raw','.dat','.tar','.gb'},'Public payload')
            require(not any(h.encode() in source.read_bytes() for h in forbidden),'Private hash in proof')
    write_new(public/'SHA256SUMS',''.join(sha(f)+'  '+str(f.relative_to(public))+'\n' for f in sorted(public.rglob('*')) if f.is_file()).encode())
    shutil.move(str(public),out);print('C88 provisioned private image/staging redacted proof:',out)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',required=True);a=p.parse_args();main(a.host)
