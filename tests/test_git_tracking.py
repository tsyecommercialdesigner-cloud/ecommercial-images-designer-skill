"""Exercise the project ignore template in a fresh, repository-local Git index."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]


class GitTrackingTests(unittest.TestCase):
    def test_generated_and_shared_assets_have_distinct_tracking_rules(self):
        parent = REPO / '.eval-workspaces'
        parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='ignore-contract-', dir=parent) as name:
            root = Path(name)
            shutil.copyfile(REPO / '.gitignore', root / '.gitignore')

            def git(*args):
                return subprocess.run(['git', '-C', str(root), *args], capture_output=True,
                                      encoding='utf-8', timeout=15)

            self.assertEqual(git('init', '--quiet').returncode, 0)
            ignored = ['.env', 'sub/.env.production', 'sub/.venv/pyvenv.cfg',
                       'sub/__pycache__/a.pyc', 'sub/node_modules/a.js',
                       'sub/test-results/a.json', 'sub/coverage/x.xml', '.eval-runs/raw.json',
                       '.eval-cache/data', '.eval-workspaces/run/data', 'eval-traces/raw.json',
                       '.codex/auth.json', '.claude/settings.local.json', 'dist/package.zip']
            tracked = ['.env.example', 'tests/test_package.py', 'tests/fixtures/safe.json',
                       'tests/golden/answer.md', 'evals/scenarios.json', 'uv.lock',
                       'sub/package-lock.json', '.github/workflows/windows-ci.yml',
                       '.agents/skills/example/SKILL.md', '.agents/skills/example/reference/rules.md',
                       '.agents/skills/example/agents/openai.yaml', '.claude/skills/example/SKILL.md',
                       'outputs/approved-design.md', 'sub/scripts/check.py']
            for path in ignored + tracked:
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('synthetic fixture\n', encoding='utf-8')
                result = git('check-ignore', '-v', '--no-index', '--', path)
                if path in ignored:
                    self.assertEqual(result.returncode, 0, path + result.stderr)
                    self.assertTrue(result.stdout.strip(), path)
                else:
                    # Negated rules may return 0 with -v, so query the decision too.
                    self.assertEqual(git('check-ignore', '--no-index', '--', path).returncode, 1, path)
            staged = git('add', '.')
            self.assertEqual(staged.returncode, 0, staged.stderr)
            listing = git('diff', '--cached', '--name-only', '-z')
            self.assertEqual(listing.returncode, 0, listing.stderr)
            self.assertEqual(set(listing.stdout.rstrip('\0').split('\0')), set(tracked) | {'.gitignore'})


if __name__ == '__main__':
    unittest.main()
