"""Run the documented member blocks in PowerShell, including failure then continue."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile

REPO = Path(__file__).resolve().parents[1]
PWSH = shutil.which('pwsh')


@unittest.skipUnless(PWSH and os.name == 'nt', 'Manual member commands target Windows PowerShell 7')
class ManualWorkflowTests(unittest.TestCase):
    def setUp(self):
        parent = REPO / '.eval-workspaces'
        parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='manual-workflow-', dir=parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.delivery = self.root / '交付 空格目录'
        self.delivery.mkdir()
        self.project = self.root / '业务 空格目录'
        self.project.mkdir()
        self.sentinel = self.project / 'customer.txt'
        self.sentinel.write_text('synthetic user data', encoding='utf-8')
        self.archive = self.delivery / 'ecommerce-image-designer-v0.1.2.zip'
        self.skill = REPO / '.agents/skills/ecommerce-image-designer'
        self.files = sorted(p for p in self.skill.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
        self.assertEqual(len(self.files), 11)
        self.manifest = dict(skill='ecommerce-image-designer', version='v0.1.2', skill_tree='4d27005fabe36d5bf19eb4fccda336cc39569ffe', revision='94859bd49482a15858f1beaf3eb7453b178ec81b', archive=self.archive.name,
                             files=[dict(path=p.relative_to(self.skill).as_posix(), sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in self.files])
        self.write_zip()
        (self.delivery / 'MANUAL.md').write_text('Fixture only; runnable blocks read from repository manual.', encoding='utf-8')

    def write_zip(self, prefix='ecommerce-image-designer/', extra=False):
        with zipfile.ZipFile(self.archive, 'w', zipfile.ZIP_DEFLATED) as output:
            for p in self.files:
                output.writestr(prefix + p.relative_to(self.skill).as_posix(), p.read_bytes())
            if extra:
                output.writestr(prefix + 'extra.txt', 'not part of package')
        self.refresh_hash()

    def refresh_hash(self):
        self.digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        self.manifest['archive_sha256'] = self.digest
        self.write_manifest()
        (self.delivery / 'SHA256SUMS.txt').write_text(self.digest + '  ' + self.archive.name + '\n', encoding='utf-8')

    def write_manifest(self):
        (self.delivery / 'release.json').write_text(json.dumps(self.manifest), encoding='utf-8')

    def probe(self, verifications=None, installations=None, **extra):
        request = dict(manual=str(REPO / 'MANUAL.md'), project=str(self.project),
                       verifications=verifications if verifications is not None else [dict(answers=[str(self.delivery), self.digest])],
                       installations=installations if installations is not None else [dict(answers=[str(self.project)])], **extra)
        path = self.root / 'request.json'
        path.write_text(json.dumps(request, ensure_ascii=False), encoding='utf-8')
        result = subprocess.run([PWSH, '-NoProfile', '-NonInteractive', '-File', str(REPO / 'tests/manual_workflow_probe.ps1'), '-RequestPath', str(path)],
                                capture_output=True, encoding='utf-8', timeout=45)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.sentinel.read_text(encoding='utf-8'), 'synthetic user data')
        return json.loads(result.stdout)

    def assert_failed_and_blocked(self, result):
        verification = result['verifications'][-1]
        self.assertIsNotNone(verification['error'])
        self.assertFalse(verification['verified'])
        self.assertFalse(any('交付内容校验通过' in item for item in verification['output']))
        install = result['installations'][0]
        self.assertIn('尚未完成本轮验证', install['error'])
        self.assertEqual(install['output'], [])
        self.assertEqual(install['unread_answers'], 1)
        self.assertFalse((self.project / '.agents').exists())

    def test_plain_and_quoted_paths_verify_install_without_extract_directory(self):
        for quoted in (False, True):
            with self.subTest(quoted=quoted):
                project = self.project / str(quoted)
                project.mkdir()
                wrap = lambda p: '  "' + str(p) + '"  ' if quoted else str(p)
                result = self.probe([dict(answers=[wrap(self.delivery), self.digest])], [dict(answers=[wrap(project)])], task_directory=wrap(self.root))
                self.assertIsNone(result['verifications'][0]['error'])
                self.assertEqual(sum('交付内容校验通过' in x for x in result['verifications'][0]['output']), 1)
                self.assertIsNone(result['installations'][0]['error'])
                installed = project / '.agents/skills/ecommerce-image-designer'
                self.assertEqual(len(list(p for p in installed.rglob('*') if p.is_file())), 11)
                for row in self.manifest['files']:
                    self.assertEqual(hashlib.sha256((installed / row['path']).read_bytes()).hexdigest(), row['sha256'])
                self.assertEqual(Path(result['task_directory']), self.root)
                self.assertFalse(list(self.root.glob('ecommerce-verify-*')))

    def test_wrong_release_version_or_skill_tree_blocks_install(self):
        for field,value in [('version','v0.1.1'),('skill_tree','0'*40)]:
            original=self.manifest[field]
            self.manifest[field]=value
            self.write_manifest()
            self.assert_failed_and_blocked(self.probe([dict(answers=[str(self.delivery)])]))
            self.manifest[field]=original

    def test_missing_manifest_does_not_ask_for_hash_or_print_success(self):
        (self.delivery / 'release.json').unlink()
        result = self.probe([dict(answers=[str(self.delivery)])])
        self.assert_failed_and_blocked(result)
        self.assertEqual(len(result['prompts']), 1)
        self.assertIn('release.json', result['verifications'][0]['error'])

    def test_empty_directory_and_previous_success_cannot_leave_stale_receipt(self):
        empty = self.root / 'empty'
        empty.mkdir()
        result = self.probe([dict(answers=[str(self.delivery), self.digest]), dict(answers=[str(empty)])])
        self.assertTrue(result['verifications'][0]['verified'])
        self.assert_failed_and_blocked(result)

    def test_missing_zip_stops_before_hash_prompt(self):
        self.archive.unlink()
        result = self.probe([dict(answers=[str(self.delivery)])])
        self.assert_failed_and_blocked(result)
        self.assertEqual(len(result['prompts']), 1)

    def test_malformed_manifest_cannot_print_success(self):
        (self.delivery / 'release.json').write_text('{broken', encoding='utf-8')
        self.assert_failed_and_blocked(self.probe([dict(answers=[str(self.delivery)])]))

    def test_wrong_or_non_hash_input_blocks_install(self):
        for value in ('0' * 64, '0be00e0', 'sha256:' + self.digest):
            with self.subTest(value=value):
                self.assert_failed_and_blocked(self.probe([dict(answers=[str(self.delivery), value])]))

    def test_malformed_zip_with_matching_whole_archive_digest_is_rejected(self):
        self.archive.write_bytes(b'not a zip')
        self.refresh_hash()
        self.assert_failed_and_blocked(self.probe())

    def test_wrong_inner_file_digest_is_rejected(self):
        self.manifest['files'][0]['sha256'] = '0' * 64
        self.write_manifest()
        self.assert_failed_and_blocked(self.probe())

    def test_duplicate_and_escaping_manifest_paths_are_rejected(self):
        for value in (self.manifest['files'][1]['path'], '../outside.txt'):
            with self.subTest(value=value):
                self.manifest['files'][0]['path'] = value
                self.write_manifest()
                self.assert_failed_and_blocked(self.probe())

    def test_wrong_zip_root_and_extra_files_are_rejected(self):
        for prefix, extra in [('source-code/', False), ('ecommerce-image-designer/', True)]:
            with self.subTest(prefix=prefix, extra=extra):
                self.write_zip(prefix, extra)
                self.assert_failed_and_blocked(self.probe())

    def test_install_without_verification_is_blocked(self):
        result = self.probe(verifications=[])
        self.assertIn('尚未完成本轮验证', result['installations'][0]['error'])
        self.assertEqual(result['installations'][0]['unread_answers'], 1)
        self.assertFalse((self.project / '.agents').exists())

    def test_archive_changed_after_verification_is_blocked(self):
        result = self.probe(mutate_archive=True)
        self.assertTrue(result['verifications'][0]['verified'])
        self.assertIn('ZIP在验证后被更改', result['installations'][0]['error'])
        self.assertFalse((self.project / '.agents').exists())

    def test_existing_installation_is_not_overwritten(self):
        result = self.probe(installations=[dict(answers=[str(self.project)]), dict(answers=[str(self.project)])])
        self.assertIsNone(result['installations'][0]['error'])
        self.assertIn('存在同名技能', result['installations'][1]['error'])
        self.assertEqual(result['installations'][1]['output'], [])

    def test_same_snapshot_backup_reinstall_restore_and_uninstall_preserve_user_data(self):
        result = self.probe(backup_restore=True)
        self.assertIn('passed', result['backup_restore'])
        self.assertFalse((self.project / '.agents/skills/ecommerce-image-designer').exists())
        self.assertEqual(len(list((self.project / '.skill-backups').iterdir())), 3)

    def test_junction_parent_is_rejected_without_writing_target(self):
        target = self.root / 'junction-target'
        target.mkdir()
        self.addCleanup(lambda: os.rmdir(self.project / '.agents') if (self.project / '.agents').is_junction() else None)
        result = self.probe(junction_target=str(target))
        self.assertIn('安装父目录为链接', result['installations'][0]['error'])
        self.assertEqual(list(target.iterdir()), [])
