#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C115 analyze timing and native receipts after a supervised session."""
from pathlib import Path
from phase4_root_migration import require
if __name__=='__main__':
 repo=Path(__file__).resolve().parents[2];source=repo/'port/scripts/analyze-phase4-prepared-capsule-session.py'
 require(source.read_bytes()==(repo/'dist/phase4/prepared-capsule-session/source'/source.relative_to(repo)).read_bytes(),'Frozen C109 analyzer')
 text=source.read_text();require(text.count("repo/'build/phase4/prepared-capsule-session'")==1,'Finite C115 analyzer')
 text=text.replace("repo/'build/phase4/prepared-capsule-session'","repo/'build/phase4/resident-session'")
 text=text.replace('C109_local_preparation_analyzed','C115_resident_preparation_analyzed')
 exec(compile(text,__file__,'exec'),globals())
