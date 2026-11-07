# SPDX-License-Identifier: MIT
"""C115 graphical integration ready for later supervised test; zero input uploads."""
from pathlib import Path
from unittest.mock import patch
import ast,importlib,json
import phase4_resident_runtime as resident
from phase4_candidate import sha
from phase4_root_migration import require
parent=resident.parent;store=resident.store;assets=resident.assets
REPO,WORK,NATIVE,NAMES=parent.REPO,parent.WORK,parent.NATIVE,parent.NAMES
AREA=WORK/'resident-session';proof=parent.proof;caller=parent.caller;prep=parent.prep

def qualified():
    result=resident.qualified_rom();root=proof('resident-preparation')
    stage=Path((resident.AREA/'latest-complete').read_text().strip())
    require(stage.resolve().is_relative_to(resident.AREA),'Known C114 preparation')
    r=json.loads((stage/'analysis.json').read_text());public=json.loads((root/'analysis.json').read_text())
    require(r['passed'] is public['passed'] is True and all(public[k]==v for k,v in r.items() if k!='kernel_boot_id'),'C114 native preparation')
    require(r['inputs_uploaded']==0 and r['local_ROM_reads_prohibited'] is True and
        r['GUI_core_input_audio_or_reboot_executed'] is False and r['C113_analysis_sha256']==sha(result[0]/'analysis.json'),'Exact internal ROM source')
    for n,h in r['source_sha256'].items():require(sha(REPO/n)==h,'Frozen C114 source')
    return result

def resident_offline(text):
    """Replace only the legacy HOST-ROM admission with the verified p3 receipt."""
    _,record,_,_=resident.qualified_rom()
    changes={
      'assert rom.is_file() and not rom.is_symlink() and rom.stat().st_size==65536':
       "assert resident_import['ROM_bytes']==65536 and resident_import['ROM_sha256']==ar['ROM_sha256']",
      "nr['ROM_sha256']=ar['ROM_sha256'];assert sha(rom)==nr['ROM_sha256']":
       "nr['ROM_sha256']=ar['ROM_sha256'];assert resident_import['ROM_sha256']==nr['ROM_sha256']",
      'for n,f in files.items():assert sha(f)==expected[n]':
       "for n,f in files.items():assert (resident_import['ROM_sha256'] if n=='private.gb' else sha(f))==expected[n]",
    }
    for a,b in changes.items():require(text.count(a)==1,'Finite resident ROM source boundary');text=text.replace(a,b)
    ast.parse(text);return text

def historical():
    qualified();binding=importlib.import_module('phase4_frontend_libs_session')
    path=Path(binding.__file__);frozen=proof('frontend-libs-session')/'source'/path.relative_to(REPO)
    require(path.read_bytes()==frozen.read_bytes(),'Frozen C66 offline adapter')
    source=path.read_text();tree=ast.parse(source)
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='historical'];require(len(nodes)==1,'One offline history function')
    text=ast.get_source_segment(source,nodes[0]);anchor="        exec(compile(offline, str(SOURCE), 'exec'), context)"
    require(text.count(anchor)==1,'Finite offline execution boundary')
    text=text.replace(anchor,"        offline=resident_offline(offline)\n        context['resident_import']=resident_import\n"+anchor)
    env={**vars(binding),'resident_offline':resident_offline,'resident_import':resident.qualified_rom()[1]}
    exec(compile(text,__file__+'-offline-history','exec'),env)
    # Temporary Python call binding only; never write a frozen source/proof.
    with patch.object(binding,'historical',env['historical']):return parent.historical()

def current_common(common,old_boot,new_boot):
    _,r,_,_=resident.qualified_rom();require(type(new_boot) is int and new_boot==r['boot_sequence'],'Observed C113/C114 boot')
    return resident.common()

def bind(prior,provider,observation,boot,boot_id):
    stage,r,meta,_=qualified()
    require(type(boot) is int and boot==r['boot_sequence'] and boot_id==meta['kernel_boot_id'],'Exact observed internal ROM boot')
    require(observation['C113_analysis_sha256']==sha(stage/'analysis.json') and
      observation['C113_proof_sha256']==sha(proof('internal-rom-imported')/'SHA256SUMS'),'C113 source binding')
    return parent.base.legacy.bind(prior,provider,observation,boot,boot_id)

watch_script=parent.watch_script

def render_online(online):
    text=parent.render_online(online)
    old="f'mkdir -m 700 {directory}/inputs\\n'"
    new="f'[ -z \"$(find {directory} -mindepth 1 -maxdepth 1 -print)\" ]\\n'"
    require(text.count(old)==1,'Resident empty capsule check');text=text.replace(old,new)
    start=text.index('code=common+f"chmod 700');end=text.index("remote('prepare',code,timeout=120)",start)
    text=text[:start]+'''code=common+f"sh /usr/libexec/muos-resident/load.sh prepare {directory}\\n"
'''+text[end:]
    require(text.count('C107_CAPSULE_PREPARED_RAM_ONLY')==1,'Resident prepare receipt')
    text=text.replace('C107_CAPSULE_PREPARED_RAM_ONLY','C112_RESIDENT_PREPARED_ZERO_UPLOADS')
    old='grep -qx C107_CAPSULE_READY {directory}/preparation.once/ready\\n'
    require(text.count(old)==1,'Resident ready provenance')
    text=text.replace(old,old+'grep -qx C112_RESIDENT_INPUTS_READY_ROM_P3 {directory}/preparation.once/resident\\n')
    ast.parse(text);return text

def rendered_runner():
    text=parent.rendered_runner()
    require(text.count('from phase4_prepared_capsule_session import ')==2,'Frozen C109 import boundaries')
    text=text.replace('from phase4_prepared_capsule_session import ','from phase4_resident_session import ')
    for a,b in [("REPO / 'port/scripts/phase4_prepared_capsule_session.py'","REPO / 'port/scripts/phase4_resident_session.py'"),
      ('prepared_inputs=prep.INPUTS','prepared_inputs={}'),
      ("'schema':109, 'C109_local_preparation_runtime_validation':True","'schema':115, 'C115_resident_runtime_validation':True, 'ROM_source_internal_p3':True, 'runtime_input_uploads':0"),
      ("'public_assets_copied_locally':7, 'public_assets_uploaded_by_host':4","'public_assets_copied_locally':11, 'public_assets_uploaded_by_host':0"),
      ('C109 local preparation observed boot','C115 resident source observed boot'),
      ('C109 local preparation session collected:','C115 resident source session collected:')]:
      require(text.count(a)==1,'Finite C115 runner anchor '+a);text=text.replace(a,b)
    require(text.count('C111_analysis_sha256')==2 and text.count('C111_proof_sha256')==2,'Two source receipt pairs')
    text=text.replace('C111_analysis_sha256','C113_analysis_sha256').replace('C111_proof_sha256','C113_proof_sha256')
    require(text.count("proof('capsule-preparer-v3-installed')")==2,'Two resident proof sources')
    text=text.replace("proof('capsule-preparer-v3-installed')","proof('internal-rom-imported')")
    ast.parse(text);return text
