#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Meaningful no-device geometry and preservation checks for the C20 planner."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import copy,importlib.util,json,struct

repo=Path(__file__).resolve().parents[2];area=repo/'build/phase4/preferences'
spec=importlib.util.spec_from_file_location('layout',Path(__file__).with_name('phase4_userdata_layout.py'))
layout=importlib.util.module_from_spec(spec);spec.loader.exec_module(layout)
survey=Path((area/'latest-layout').read_text().strip());assert survey.is_relative_to(area)
original=(survey/'mbr.before').read_bytes();inventory=json.loads((survey/'inventory.json').read_text())
cases=[]
def passed(name):cases.append(name)
def refuse(mbr,inv):
    try:layout.propose(mbr,inv)
    except ValueError:return
    raise AssertionError('Unexpected layout accepted')
proposed,plan=layout.propose(original,inventory)
assert proposed[:478]==original[:478] and proposed[494:]==original[494:]
assert plan['mbr_change_range']=={'first_byte_inclusive':478,'last_byte_inclusive':493}
assert not plan['execution_enabled'];passed('actual-survey-only-p3-slot-changes')
entry=layout.ENTRY.unpack_from(proposed,478)
assert entry[2]==0x83 and entry[4]==1310720
assert entry[4]+entry[5]<=layout.SECTORS and (entry[4]+entry[5])%2048==0
assert entry[4]==layout.P2[2]+layout.P2[3];passed('aligned-data-boundary-no-overlap-no-overflow')
refuse(proposed,inventory);passed('existing-p3-refused-no-replan')
for offset in [440,446,450,454,458,462,466,470,474,494,510]:
    changed=bytearray(original);changed[offset]^=1;refuse(changed,inventory)
passed('diskid-signature-p1-p2-and-p4-drift-refused')
changed=bytearray(original);changed[450]=0xee;refuse(changed,inventory)
passed('protective-GPT-refused')
refuse(original[:511],inventory);passed('short-MBR-refused')
for key in ['mmcblk0_SIZE','LOGICAL_SECTOR','mmcblk0p1_START','mmcblk0p1_SIZE','mmcblk0p2_START','mmcblk0p2_SIZE','ROOT_PARTUUID']:
    inv=copy.deepcopy(inventory);inv[key]='wrong';refuse(original,inv)
passed('kernel-survey-disagreement-refused')
for digest in ['', 'X'*64, 'a'*63]:
    inv=copy.deepcopy(inventory);inv['PREFIX16M_SHA256']=digest;refuse(original,inv)
passed('missing-or-malformed-prefix-identity-refused')
assert (survey/'mbr.before').read_bytes()==original
result={'passed':True,'case_count':len(cases),'cases':cases,'block_devices_opened':False,
        'original_survey_unchanged':True,'execution_enabled':False}
assert not (survey/'layout-checks.json').exists()
(survey/'layout-checks.json').write_text(json.dumps(result,indent=2)+'\n')
for name in cases:print('PASS',name)
