#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Pure C105 boot binding tests; no SSH, seed, device or firmware action."""
from pathlib import Path
import copy,json,sys,unittest
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import phase4_manual_caller as m

class Binding(unittest.TestCase):
    def setUp(self):
        self.previous={'boot_sequence':79,'kernel_boot_id':'11111111-1111-1111-1111-111111111111'}
        self.obs={'schema':105,'boot_sequence':81,'kernel_boot_id':'22222222-2222-2222-2222-222222222222',
            'passed':True,'C07_ready_without_recovery':True,'C104_analysis_sha256':'a'*64,'module_sha256':'b'*64}
    def test_explicit_later_identity_allowed(self):m.observation_binding(self.obs,self.previous,'a'*64,'b'*64)
    def test_bad_observation_refused(self):
        for k,values in {'boot_sequence':[True,79,78,'81',9999],
                         'kernel_boot_id':[self.previous['kernel_boot_id'],'bad',None],
                         'passed':[False], 'C07_ready_without_recovery':[False],
                         'C104_analysis_sha256':['wrong'],'module_sha256':['wrong']}.items():
            for v in values:
                with self.subTest(field=k,value=v):
                    changed={**self.obs,k:v}
                    with self.assertRaises(ValueError):m.observation_binding(changed,self.previous,'a'*64,'b'*64)
    def test_recovered_guard_does_not_change_install_gate(self):
        original='set -eu\nc25_ready\n# retained foundation checks\n'
        code=m.recovered_reboot_guard(original)
        self.assertIn('\nc25_ready\n',original);self.assertNotIn('\nc25_ready\n',code)
        for condition in ['c25_media && c25_root_mode ro && c25_quiet && c25_foundation',
                          'STATUS=1 ROOT_RO=1','FAILED_STEP=usb-mode FAILED_RC=1',
                          'RECOVERY=physical-removal-observed','RECOVERY_RC=0',
                          'RECOVERY=ssh-process-ready ROOT_RO=1','muos-c07-network status']:
            self.assertIn(condition,code)
        for mutation in ['mount -o remount','/sbin/reboot','c25.once','rm -rf']:
            self.assertNotIn(mutation,code)
    def test_guard_anchor_fails_closed(self):
        for code in ['set -eu\n','\nc25_ready\nc25_ready\n']:
            with self.assertRaises(ValueError):m.recovered_reboot_guard(code)

if __name__=='__main__':unittest.main()
