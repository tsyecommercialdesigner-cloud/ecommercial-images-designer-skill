import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('workspace', REPO / 'scripts/evaluation_workspace.py')
workspace = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workspace)


class EvaluationWorkspaceTests(unittest.TestCase):
    def setUp(self):
        parent = REPO / '.eval-workspaces'
        parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='workspace-contract-', dir=parent)
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.root = self.repo / '.eval-workspaces/synthetic-test'

    def test_archive_verified_before_owned_workspace_is_removed(self):
        workspace.claim_root(self.root, self.repo)
        (self.root / 'failure.log').write_text('synthetic failure retained', encoding='utf-8')
        report = workspace.archive_and_clean(self.root, self.repo)
        self.assertTrue(report['cleaned'])
        self.assertFalse(self.root.exists())
        archive = Path(report['archive'])
        self.assertEqual(workspace.file_digest(archive), report['sha256'])
        with zipfile.ZipFile(archive) as saved:
            self.assertEqual(saved.read('failure.log'), b'synthetic failure retained')
        self.assertTrue(json.loads(archive.with_name('summary.json').read_text())['cleaned'])

    def test_parent_external_and_unowned_paths_are_never_deleted(self):
        for path in (self.repo / '.eval-workspaces', self.repo / 'user-files'):
            path.mkdir(exist_ok=True)
            with self.assertRaises(ValueError):
                workspace.archive_and_clean(path, self.repo)
            self.assertTrue(path.exists())
        self.root.mkdir()
        with self.assertRaises(FileNotFoundError):
            workspace.archive_and_clean(self.root, self.repo)
        self.assertTrue(self.root.exists())

    def test_owner_mismatch_preserves_files(self):
        workspace.claim_root(self.root, self.repo)
        marker = self.root / workspace.MARKER
        owner = json.loads(marker.read_text())
        owner['root'] = str(self.repo)
        marker.write_text(json.dumps(owner))
        with self.assertRaisesRegex(ValueError, 'ownership'):
            workspace.archive_and_clean(self.root, self.repo)
        self.assertTrue(self.root.exists())

    def test_owner_cannot_inject_an_archive_destination(self):
        workspace.claim_root(self.root, self.repo)
        marker = self.root / workspace.MARKER
        owner = json.loads(marker.read_text())
        owner['owner'] = '../../outside'
        marker.write_text(json.dumps(owner))
        with self.assertRaisesRegex(ValueError, 'ownership'):
            workspace.archive_and_clean(self.root, self.repo)
        self.assertTrue(self.root.exists())
        self.assertFalse((self.repo / '.eval-runs').exists())

    def test_corrupt_archive_blocks_cleanup(self):
        workspace.claim_root(self.root, self.repo)
        with patch.object(zipfile.ZipFile, 'testzip', return_value='corrupt.txt'):
            with self.assertRaisesRegex(ValueError, 'integrity'):
                workspace.archive_and_clean(self.root, self.repo)
        self.assertTrue(self.root.exists())

    def test_cleanup_failure_keeps_verified_archive_and_failed_receipt(self):
        workspace.claim_root(self.root, self.repo)
        with patch.object(workspace.shutil, 'rmtree', side_effect=PermissionError('synthetic lock')):
            with self.assertRaises(PermissionError):
                workspace.archive_and_clean(self.root, self.repo)
        receipt = next((self.repo / '.eval-runs').glob('*/summary.json'))
        report = json.loads(receipt.read_text())
        self.assertFalse(report['cleaned'])
        self.assertTrue(Path(report['archive']).is_file())
        self.assertTrue(self.root.exists())

    def test_links_are_preserved_for_review(self):
        workspace.claim_root(self.root, self.repo)
        outside = self.repo / 'private.txt'
        outside.write_text('synthetic private input')
        try:
            (self.root / 'linked.txt').symlink_to(outside)
        except OSError:
            self.skipTest('Symlink creation unavailable')
        with self.assertRaisesRegex(ValueError, 'link'):
            workspace.archive_and_clean(self.root, self.repo)
        self.assertEqual(outside.read_text(), 'synthetic private input')

    def test_nested_git_boundary_does_not_use_parent_repository(self):
        workspace.claim_root(self.root, self.repo)
        trial = self.root / 'trial'
        trial.mkdir()
        workspace.initialize_project(trial)
        result = subprocess.run(['git', '-C', str(trial), 'rev-parse', '--show-toplevel'],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()).resolve(), trial.resolve())
        self.assertFalse((trial / '.git/hooks').exists())

    def test_dsh_preparation_uses_local_boundaries_and_preserves_synthetic_config(self):
        home = self.repo / 'synthetic-dsh'
        profile = home / 'profiles/desktop'
        profile.mkdir(parents=True)
        for name in ('cordis.patch.yml', 'cordis.yml', 'package.json', 'pnpm-lock.yaml'):
            (profile / name).write_text('synthetic config', encoding='utf-8')
        (home / '.credentials.yaml').write_text('synthetic test only', encoding='utf-8')
        root = self.repo / 'dsh-skill-host-76d8-preparation'
        result = subprocess.run([sys.executable, '-X', 'utf8', '-B',
                                 str(REPO / 'scripts/prepare_dsh_desktop_smoke.py'), '--output', str(root)],
                                capture_output=True, text=True, timeout=30,
                                env={**os.environ, 'DSH_HOME': str(home)})
        self.assertEqual(result.returncode, 0, result.stderr)
        before = json.loads((root / 'before.json').read_text())
        self.assertEqual(len(before['skill_manifest']), 11)
        self.assertTrue(any('/references/' in path for path in before['skill_manifest']))
        self.assertTrue((root / workspace.MARKER).is_file())
        for path, digest in before['configuration_sha256'].items():
            self.assertEqual(workspace.file_digest(Path(path)), digest)
        self.assertEqual(len(list(root.glob('*-r1/.git/HEAD'))), 8)


if __name__ == '__main__':
    unittest.main()
