"""Preserve the exact October18 presentation against its existing seal."""
from repo_layout import repo_file
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
COMMIT = '089c4326cfebf42d91402bb8abfa267a4236929a'
DEST = repo_file('publication_archive_2026-10-19', root=ROOT)


def main():
    from freeze_corrected_release import SOURCES
    seal = json.loads((repo_file('corrected_2026-10-18/release_checksums.json', root=ROOT)).read_text())
    files = {}
    for name in SOURCES:
        data = subprocess.run(['git', 'show', COMMIT + ':' + name], cwd=ROOT,
                              capture_output=True, check=True).stdout
        digest = sha256(data).hexdigest()
        assert digest == seal[name], name
        path = DEST / (name + '.snapshot')
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            assert path.read_bytes() == data, name
        else:
            path.write_bytes(data)
        files[name] = {'archive_path': name + '.snapshot', 'sha256': digest}
    manifest = {'source_commit': COMMIT, 'files': files,
                'purpose': 'Exact superseded 1136-question presentation and validation sources. Measurement evidence and its committed seals remain unchanged.'}
    path = DEST / 'manifest.json'
    data = json.dumps(manifest, indent=2) + '\n'
    if path.exists():
        assert path.read_text() == data
    else:
        path.write_text(data)
    print('Preserved', len(files), 'sealed October18 source blobs')


if __name__ == '__main__':
    main()
