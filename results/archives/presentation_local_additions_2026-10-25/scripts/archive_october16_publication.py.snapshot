"""Preserve superseded presentation bytes without changing their release seal."""
from repo_layout import repo_file
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DEST = repo_file('publication_archive_2026-10-16', root=ROOT)
COMMIT = '83dfec83825a39c55a225b9e567c0fc0513597e4'
PATHS = ('README.md', 'FUNCTIONS.md', 'OUTPUT_COMPLIANCE.md', 'docs/index.html',
         'docs/functions.html', 'docs/output_compliance.html', 'test_overall.py', 'test_publication.py')


def main():
    previous = json.loads((repo_file('expansion_2026-10-15/release_checksums.json', root=ROOT)).read_text())
    files = {}
    for name in PATHS:
        data = subprocess.run(['git', 'show', COMMIT + ':' + name], cwd=ROOT, check=True, capture_output=True).stdout
        digest = sha256(data).hexdigest()
        assert digest == previous[name], 'Old presentation blob differs from the original release seal'
        archived = name + '.snapshot'
        target = DEST / archived
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            assert target.read_bytes() == data, 'Never replace a different archived blob'
        else:
            target.write_bytes(data)
        files[name] = {'archive_path': archived, 'sha256': digest}
    manifest = {'source_commit': COMMIT, 'files': files,
                'purpose': 'Exact superseded presentation and publication-test bytes. Measurement evidence and original release_checksums.json stay in place unchanged. The current publication is sealed separately.',
                'snapshot_note': 'Snapshot suffix preserves source bytes at their original logical paths without presenting relocated HTML/Markdown as a separately rendered site.'}
    text = json.dumps(manifest, indent=2) + '\n'
    target = DEST / 'manifest.json'
    if target.exists():
        assert target.read_text() == text
    else:
        target.write_text(text)
    print('Archived eight exact October16 presentation/test blobs; old release seal unchanged')


if __name__ == '__main__':
    main()
