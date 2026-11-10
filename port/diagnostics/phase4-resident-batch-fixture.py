#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C122 real resident copy/adoption and nine-file transaction fault fixtures."""
import json,sys
from pathlib import Path
source=Path(sys.argv[1]);out=Path(sys.argv[2])
plan={'bundle':{n:(source/n).read_text() for n in ['functions.sh','host.sh','contract.json','LICENSE','payload.sha256','caller.sh']},
      'scripts':['adapter.sh','app-launch.sh','cycle.sh','frontend-libs.sh','installed-host.sh','installed-store.sh','select.sh','store-base.sh','store.sh','worker.sh']}
# Preserve the existing real legacy package/asset setup; replace only how the
# resident prefix and its callback are wired. No mock of rb_adopt/c120_adopt.
text=Path('/port/diagnostics/phase4-batch-caller-fixture.py').read_text()
text=text[:text.index('reset();assert invoke(')]
text=text.replace("plan=json.loads(Path(sys.argv[1]).read_text());out=Path(sys.argv[2]);",'')
text=text.replace('c119','c122').replace('v2','v3').replace('contract-v2','contract-v3')
text=text.replace("v3=cap/'contract-v3';cases=[];", "v3=cap/'contract-v3';resident=legacy.parent/'muos-batch-v1';cases=[];")
old="    v3.mkdir(mode=0o700)\n    for n,text in plan['bundle'].items():put(v3/n,text,0o644)"
new="    resident.mkdir(mode=0o755);resident.chmod(0o755)\n    for p in source.iterdir():put(resident/p.name,p.read_bytes(),0o644)"
assert text.count(old)==1;text=text.replace(old,new)
text=text.replace("v3_manifest_sha={sha(v3/'payload.sha256')}","v3_manifest_sha={sha(resident/'payload.sha256')}\nrb_system_root={root};rb_root={resident};rb_manifest_sha={sha(source/'resident.sha256')}")
text=text.replace('. /port/device/rk-r35s-p0/batch-caller/functions.sh','. {resident}/resident-functions.sh\n. {resident}/functions.sh')
text=text.replace(' staged) return 0;;',' staged) return 0;;\n adopt) [ "${{FAIL_ADOPT:-0}}" = 0 ] && c120_adopt "$2";;')
exec(compile(text,__file__+'-setup','exec'),globals())
hashof=sha

reset();assert invoke('rb_package;rb_adopt "$v3_cap";c120_staged "$v3_cap"').returncode==0
assert all((cap/'contract-v3'/n).read_bytes()==(source/n).read_bytes() for n in plan['bundle'])
cases.append('resident-copy-six-exact-files-and-real-C120-adoption')
before=snapshot();assert invoke('rb_adopt "$v3_cap"').returncode!=0 and snapshot()==before;cases.append('repeat-resident-adoption-refused-byte-exact')
for label,change in {
 'package-source':lambda:put(resident/'host.sh','bad',0o644),
 'package-extra':lambda:put(resident/'foreign','bad',0o644),
 'package-mode':lambda:resident.chmod(0o700),
 'file-mode':lambda:(resident/'host.sh').chmod(0o755),
 'file-hardlink':lambda:os.link(resident/'host.sh',base/'link'),
 'file-symlink':lambda:((resident/'host.sh').unlink(),(resident/'host.sh').symlink_to('functions.sh')),
 'manifest':lambda:put(resident/'resident.sha256','bad',0o644),
 'existing-bundle':lambda:(cap/'contract-v3').mkdir(),
 'dangling-bundle':lambda:(cap/'contract-v3').symlink_to('missing'),
 'old-run':lambda:(cap/'caller-stage/run.once').mkdir(),
 'old-script':lambda:put(cap/'installed-host.sh','bad',0o700),
 'old-boot':lambda:put(cap/'caller-stage/boot','wrong',0o600),
 'marker':lambda:put(cap/'preparation.once/resident','wrong',0o600),
 'marker-mode':lambda:(cap/'preparation.once/ready').chmod(0o644),
 'role':lambda:put(cap/'role','save\n',0o600),
 'asset':lambda:put(cap/'runner','bad',0o700),
}.items():
 reset();change();before=snapshot();assert invoke('rb_adopt "$v3_cap"').returncode!=0 and snapshot()==before,label
 cases.append('before-copy-refuses-'+label)
for extra in ['FAIL_PLATFORM=1','FIXTURE_BOOT=84']:
 reset();before=snapshot();assert invoke('rb_adopt "$v3_cap"',extra).returncode!=0 and snapshot()==before;cases.append('platform-or-boot-refusal-before-copy')
reset();before=snapshot();assert invoke('rb_adopt /run/muos-prefs-data.OTHER1').returncode!=0 and snapshot()==before;cases.append('cross-capsule-refused')
reset();fake=base/'bin';fake.mkdir();put(fake/'cat',f'#!/bin/sh\n[ "$1" != {resident}/host.sh ] || exit 74\nexec /bin/cat "$@"\n',0o755)
r=invoke('rb_adopt "$v3_cap"',f'PATH={fake}:$PATH');assert r.returncode!=0 and (v3/'functions.sh').exists() and not (cap/'caller-v3-stage').exists()
before=snapshot();assert invoke('rb_adopt "$v3_cap"').returncode!=0 and snapshot()==before;cases.append('partial-copy-retained-no-repeat-no-adoption')
reset();assert invoke('rb_adopt "$v3_cap"','FAIL_ADOPT=1').returncode!=0 and len(list(v3.iterdir()))==6
before=snapshot();assert invoke('rb_adopt "$v3_cap"').returncode!=0 and snapshot()==before;cases.append('adoption-failure-retains-copy-no-repeat')
# Reuse the real transaction fault harness, adapted to this exact nine-leaf scope.
old=Path('/port/diagnostics/phase4-manual-caller-fixture.py').read_text();start=old.index("install_base=Path(");end=old.index("install_case('install-new-17-leaf")
block=old[start:end].replace('c105','c122').replace('C105','C122').replace('usr/libexec/muos-caller','usr/libexec/muos-batch-v1')
a="names=scripts+['functions.sh','dependencies.tsv','assets.tsv','contract.json','LICENSE','payload.sha256','caller.sh']"
assert block.count(a)==1;block=block.replace(a,"names=[*plan['bundle'],'resident-functions.sh','resident.sha256','load.sh']")
block=block.replace('/worker.sh','/functions.sh')
exec(compile(block,__file__+'-transaction','exec'),globals())
install_case('nine-leaf-install-and-exact-rollback')
for hook in ['guard','rw','directory-created','verify','sync','ro']:install_case('install-failure-'+hook,hook)
for hook in ['file-staged','file-installed']:
 for at in [1,5,9]:install_case('install-failure-'+hook+'-'+str(at),hook,at)
install_case('rollback-preserves-foreign-neighbor',foreign=True)
# Exercise the actual recipe's install command against a disposable target.
recipe=Path('/port/buildroot-batch/package/muos-r35s-batch/muos-r35s-batch.mk')
for variant in ['valid','missing-input','wrong-manifest','changed-leaf','foreign-leaf']:
 work=Path('/tmp/c122-recipe')/variant;work.mkdir(parents=True)
 src=work/'public';shutil.copytree(source,src);manifest=work/'export.sha256'
 shutil.copyfile(source.parents[3]/'export.sha256',manifest);expected=sha(manifest)
 if variant=='wrong-manifest':manifest.write_text('wrong')
 if variant=='changed-leaf':(src/'host.sh').write_text('changed')
 if variant=='foreign-leaf':(src/'foreign').write_text('foreign')
 makefile=work/'Makefile';makefile.write_text('include '+str(recipe)+'\nall:\n\t$(MUOS_R35S_BATCH_INSTALL_TARGET_CMDS)\n')
 cmd=['make','--no-print-directory','-f',str(makefile),'all','INSTALL=install','TARGET_DIR='+str(work/'target'),
  'MUOS_R35S_BATCH_PAYLOAD='+('' if variant=='missing-input' else str(src)),'MUOS_R35S_BATCH_MANIFEST='+str(manifest),'MUOS_R35S_BATCH_MANIFEST_SHA256='+expected]
 result=subprocess.run(cmd,capture_output=True,text=True)
 assert (result.returncode==0)==(variant=='valid'),(variant,result.stdout,result.stderr)
 if variant=='valid':
  target=work/'target/usr/libexec/muos-batch-v1'
  assert len(list(target.iterdir()))==9 and all(sha(target/n)==sha(source/n) and (target/n).stat().st_mode&0o777==0o644 for n in [*plan['bundle'],'resident-functions.sh','resident.sha256','load.sh'])
 else:assert not (work/'target').exists()
 cases.append('recipe-'+variant)
(out/'fixture-results.json').write_text(json.dumps({'passed':True,'cases':cases,'case_count':len(cases),'real_resident_and_C120_functions':True,'device_or_GUI_executed':False},indent=2)+'\n')
print('C122',len(cases),'resident/transaction cases passed')
