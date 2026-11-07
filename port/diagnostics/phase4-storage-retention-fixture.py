#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Exercise real host cleanup guards using only disposable temporary files."""
from pathlib import Path
import importlib.util, json, os, tempfile, unittest

SOURCE = Path(__file__).resolve().parents[1]/'scripts/retain-phase4-builds.py'
spec = importlib.util.spec_from_file_location('retention', SOURCE)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


class Retention(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='muos-retention-')
        self.repo = Path(self.temp.name)
        m.REPO = self.repo; m.WORK = self.repo/'build/phase4'
        m.POLICY = self.repo/'policy.json'
        m.os.sync = lambda: None
        self.root = m.WORK/'rootfs-candidate/composition.test/target'
        self.root.mkdir(parents=True)
        self.pin = self.root/'required'; self.pin.write_bytes(b'required input')
        self.old = self.root/'old'; self.old.write_bytes(b'old reproducible copy')
        m.POLICY.write_text(json.dumps({'maximum_firmware_versions': 5, 'firmware_versions': {},
                                      'required_files': {}, 'exceptions': {}}))
        m.trace = lambda: {'read_paths': [str(self.pin.relative_to(self.repo))], 'metadata_paths': []}
        self.report = self.repo/'report.json'

    def tearDown(self): self.temp.cleanup()

    def plan(self): return m.make_plan()

    def test_removes_only_replica_and_preserves_required(self):
        outside = self.repo/'unrelated'; outside.write_bytes(b'keep')
        plan = self.plan(); m.apply(plan, self.report)
        self.assertFalse(self.old.exists()); self.assertEqual(self.pin.read_bytes(), b'required input')
        self.assertTrue(outside.exists()); self.assertTrue(plan['complete'])

    def test_changed_candidate_refused_before_delete(self):
        plan = self.plan(); self.old.write_bytes(b'changed')
        with self.assertRaises(AssertionError): m.apply(plan, self.report)
        self.assertTrue(self.old.exists()); self.assertTrue(self.pin.exists())

    def test_changed_required_refused_before_delete(self):
        plan = self.plan(); self.pin.write_bytes(b'changed')
        with self.assertRaises(AssertionError): m.apply(plan, self.report)
        self.assertTrue(self.old.exists())

    def test_open_candidate_refused(self):
        plan = self.plan()
        with self.old.open('rb') as opened:
            self.assertTrue(opened.readable())
            with self.assertRaises(AssertionError): m.apply(plan, self.report)
        self.assertTrue(self.old.exists())

    def test_hardlink_to_required_preserved(self):
        other = self.root/'alias'; os.link(self.pin, other)
        plan = self.plan(); m.apply(plan, self.report)
        self.assertTrue(other.exists()); self.assertEqual(self.pin.stat().st_nlink, 2)

    def test_symlink_target_untouched(self):
        external = self.repo/'external'; external.mkdir(); (external/'data').write_bytes(b'keep')
        link = self.root/'link'; link.symlink_to(external, target_is_directory=True)
        plan = self.plan(); m.apply(plan, self.report)
        self.assertFalse(link.exists()); self.assertEqual((external/'data').read_bytes(), b'keep')

    def test_alias_parent_refused(self):
        external = self.repo/'external'; external.mkdir(); (external/'target').mkdir()
        alias = self.root.parent.parent/'composition.alias'; alias.symlink_to(external, target_is_directory=True)
        with self.assertRaises(AssertionError): self.plan()
        self.assertTrue(self.old.exists())

    def test_policy_change_refused(self):
        plan = self.plan(); m.POLICY.write_text('{}')
        with self.assertRaises(AssertionError): m.apply(plan, self.report)
        self.assertTrue(self.old.exists())

    def test_six_firmware_versions_refused(self):
        p = json.loads(m.POLICY.read_text()); p['firmware_versions'] = {str(i): [] for i in range(6)}
        m.POLICY.write_text(json.dumps(p))
        with self.assertRaises(AssertionError): self.plan()


if __name__ == '__main__': unittest.main()
