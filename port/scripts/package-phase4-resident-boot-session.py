#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""C116 sanitized proof; requires authentic technical, physical and closure receipts."""
from phase4_resident_boot_session import REPO,change
if __name__=='__main__':
    source=REPO/'port/scripts/package-phase4-resident-session.py'
    text=change(source.read_text(),'import phase4_resident_session as session','import phase4_resident_boot_session as session')
    for old,new in [("'dist/phase4/resident-session'","'dist/phase4/resident-boot-session'"),
                    ("'docs/archive/phase4/phase4-resident-session.md'","'docs/archive/phase4/phase4-resident-boot-session.md'"),
                    ('C115_resident_runtime_validation','C116_resident_boot_runtime_validation'),
                    ('C115_resident_preparation_analyzed','C116_resident_preparation_analyzed')]:
        text=change(text,old,new)
    text=text.replace('C115','C116').replace("'schema':115","'schema':116").replace("r['schema']==115","r['schema']==116")
    exec(compile(text,__file__,'exec'),globals())
