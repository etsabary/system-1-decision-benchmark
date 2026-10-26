"""Seal current correction files without replacing any earlier measurement seal."""
from repo_layout import logical_relative, repo_file
from repo_layout import frozen_file
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DEST = repo_file('corrected_2026-10-18/release_checksums.json', root=ROOT)
SOURCES = ['README.md', 'FUNCTIONS.md', 'LLM_EXPANSION.md', 'OUTPUT_COMPLIANCE.md',
           'docs/index.html', 'docs/functions.html', 'docs/output_compliance.html',
           'archive_october18_publication.py', 'freeze_october18_release.py',
           'freeze_corrected_release.py', 'import_corrected_bundle.py',
           'validate_corrected_release.py', 'test_corrected_release.py',
           'build_corrected_report.py', 'plot_corrected_release.py', 'test_publication.py',
           '.github/workflows/october18-validate.yml']
FOLDERS = ['corrected_2026-10-18', 'publication_archive_2026-10-18', 'docs/figures/corrected']


def hashes():
    paths = {repo_file(name, root=ROOT) for name in SOURCES}
    paths.update(p for folder in FOLDERS for p in (repo_file(folder, root=ROOT)).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    paths.discard(DEST)
    assert all(frozen_file(p).is_file() for p in paths)
    # A later presentation may supersede these logical paths. Check the exact
    # archived bytes against the original seal, never regenerate that seal.
    archive = repo_file('publication_archive_2026-10-19', root=ROOT)
    manifest = json.loads((archive / 'manifest.json').read_text())['files'] if archive.exists() else {}
    result = {}
    for path in sorted(paths):
        name = str(logical_relative(path, root=ROOT))
        selected = archive / manifest[name]['archive_path'] if name in manifest else frozen_file(path)
        result[name] = sha256(selected.read_bytes()).hexdigest()
        if name in manifest:
            assert result[name] == manifest[name]['sha256'], name
    return result


def committed_seal():
    # Git addresses physical paths, unlike the logical names inside old seals.
    return subprocess.run(['git', 'cat-file', '-e', 'HEAD:' + str(DEST.relative_to(ROOT))],
                          cwd=ROOT, capture_output=True).returncode == 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--refresh-unpublished', action='store_true', help='Only before this seal exists in HEAD; never modifies a committed seal')
    args = parser.parse_args()
    value = hashes()
    if args.check:
        assert value == json.loads(DEST.read_text()), 'Corrected release files changed'
    else:
        if DEST.exists():
            committed = committed_seal()
            assert args.refresh_unpublished and not committed, 'A committed seal is immutable; create a later version instead'
        DEST.write_text(json.dumps(value, indent=2)+'\n')
    print('PASS:', len(value), 'current correction files; original measurement seals unchanged')
