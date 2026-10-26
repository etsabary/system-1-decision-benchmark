"""Archive exact superseded publication blobs before the two-item correction."""
from repo_layout import repo_file
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DEST = repo_file('publication_archive_2026-10-18', root=ROOT)
COMMIT = '0ec4bd0caaea6048dc2f3366ae7b49cfffe9eb2c'
PATHS = ('README.md', 'FUNCTIONS.md', 'OUTPUT_COMPLIANCE.md', 'LLM_EXPANSION.md',
         'docs/index.html', 'docs/functions.html', 'docs/output_compliance.html',
         'freeze_october18_release.py', 'test_publication.py',
         '.github/workflows/october18-validate.yml')


def main():
    seal = json.loads((repo_file('overall_llm_expanded_2026-10-18/release_checksums.json', root=ROOT)).read_text())
    files = {}
    for name in PATHS:
        data = subprocess.run(['git', 'show', COMMIT + ':' + name], cwd=ROOT,
                              check=True, capture_output=True).stdout
        digest = sha256(data).hexdigest()
        assert digest == seal[name], 'Original blob must match the original release seal'
        target = DEST / (name + '.snapshot')
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            assert target.read_bytes() == data, 'Never replace different archived bytes'
        else:
            target.write_bytes(data)
        files[name] = {'archive_path': name + '.snapshot', 'sha256': digest}
    manifest = {'source_commit': COMMIT, 'files': files,
                'purpose': 'Superseded presentation and validation-source bytes only. The active bank and scores use the corrected release; original measurement captures retain their original seals.',
                'snapshot_note': 'Logical source paths retain exact bytes without presenting the snapshots as a second active site.'}
    target = DEST / 'manifest.json'
    text = json.dumps(manifest, indent=2) + '\n'
    if target.exists():
        assert target.read_text() == text
    else:
        target.write_text(text)
    print('Archived ten October18 publication/source blobs; original evidence seal unchanged')


if __name__ == '__main__':
    main()
