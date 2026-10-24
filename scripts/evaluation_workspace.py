"""Repository-local evaluation workspaces and verified, ownership-scoped cleanup.

No Host, model, network, install or permission changes. Archive only synthetic,
reviewed evidence: this helper does not sanitize secrets for the caller.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import uuid
import zipfile

REPO = Path(__file__).resolve().parents[1]
MARKER = '.evaluation-owned.json'


def validate_root(root, repo=REPO):
    root, parent = Path(root).resolve(), (Path(repo) / '.eval-workspaces').resolve()
    if not parent.is_relative_to(Path(repo).resolve()) or root == parent or not root.is_relative_to(parent):
        raise ValueError('Use a dedicated directory below repository .eval-workspaces; no drive-root environments')
    return root


def claim_root(root, repo=REPO):
    root = validate_root(root, repo)
    if root.exists():
        verify_owner(root, repo)
        return root
    root.mkdir(parents=True)
    (root / MARKER).write_text(json.dumps(dict(repository=str(Path(repo).resolve()),
        root=str(root), owner=uuid.uuid4().hex)), encoding='utf-8')
    return root


def verify_owner(root, repo=REPO):
    root = validate_root(root, repo)
    data = json.loads((root / MARKER).read_text(encoding='utf-8'))
    owner = data.get('owner')
    valid_owner = isinstance(owner, str) and len(owner) == 32 and set(owner) <= set('0123456789abcdef')
    if data.get('repository') != str(Path(repo).resolve()) or data.get('root') != str(root) or not valid_owner:
        raise ValueError('Workspace ownership mismatch; preserve files')
    return data


def initialize_project(work):
    # A real nested Git boundary prevents ancestor skills/AGENTS contaminating
    # CLI discovery. No commits, hooks, remotes or user configuration changes.
    subprocess.run(['git', '-c', 'init.templateDir=', 'init', '--quiet', str(work)],
                   check=True, capture_output=True, timeout=15)


def archive_and_clean(root, repo=REPO):
    root = validate_root(root, repo)
    owner = verify_owner(root, repo)
    entries = []
    for path in root.rglob('*'):
        if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
            raise ValueError('Workspace contains a link; preserve it for review')
        if path.is_file():
            entries.append((path.relative_to(root).as_posix(), file_digest(path)))
    destination = Path(repo).resolve() / '.eval-runs' / ('archive-' + owner['owner'])
    if not destination.resolve().is_relative_to(Path(repo).resolve()):
        raise ValueError('Evidence destination escapes repository')
    destination.mkdir(parents=True, exist_ok=False)
    archive = destination / 'evidence.zip'
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as output:
        for name, _ in entries:
            output.write(root / name, name)
    with zipfile.ZipFile(archive) as saved:
        if saved.testzip() or len(saved.infolist()) != len(entries):
            raise ValueError('Archive integrity failed; no cleanup')
        for name, digest in entries:
            with saved.open(name) as stream:
                archived_digest = stream_digest(stream)
            if archived_digest != digest or file_digest(root / name) != digest:
                raise ValueError('Archive mismatch or concurrent change; no cleanup')
    if {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()} != {n for n, _ in entries}:
        raise ValueError('Workspace changed during archive; no cleanup')
    verify_owner(root, repo)
    report = dict(source=str(root), archive=str(archive), entries=len(entries),
                  sha256=file_digest(archive), cleaned=False)
    receipt = destination / 'summary.json'
    receipt.write_text(json.dumps(report, indent=2), encoding='utf-8')
    shutil.rmtree(root)  # Resolved descendant and ownership rechecked above.
    report['cleaned'] = not root.exists()
    receipt.write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


def stream_digest(stream):
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
        digest.update(chunk)
    return digest.hexdigest()


def file_digest(path):
    with path.open('rb') as stream:
        return stream_digest(stream)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-and-clean', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(archive_and_clean(args.archive_and_clean)))
        return 0
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print(json.dumps(dict(cleaned=False, error=str(error))))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
