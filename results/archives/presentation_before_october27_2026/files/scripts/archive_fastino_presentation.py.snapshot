"""Exact committed active Fastino presentation before adding the Opus reference."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'results/archives/presentation_fastino_2026-10-23'
NAMES = ('README.md', 'documents/FUNCTIONS.md', 'documents/OUTPUT_COMPLIANCE.md',
         'docs/report.html', 'docs/index.html', 'docs/functions.html', 'docs/output_compliance.html',
         '.github/workflows/october18-validate.yml', 'scripts/layout_manifest.json',
         'scripts/validate_fastino_2026_10_23.py')


def previous(path):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    manifest = ARCHIVE / 'manifest.json'
    entries = json.loads(manifest.read_text())['files'] if manifest.exists() else {}
    entry = entries.get(path.relative_to(ROOT).as_posix())
    if entry is None:
        return path
    saved = ARCHIVE / entry['path']
    assert saved.resolve().is_relative_to(ARCHIVE.resolve())
    assert sha256(saved.read_bytes()).hexdigest() == entry['sha256']
    return saved


def archive():
    target = ARCHIVE / 'manifest.json'
    if target.exists():
        for name in json.loads(target.read_text())['files']:
            previous(ROOT / name)
        return
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    entries = {}
    for name in NAMES:
        data = subprocess.check_output(['git', 'show', commit + ':' + name], cwd=ROOT)
        assert data == (ROOT / name).read_bytes(), 'Overlapping changes: ' + name
        saved = ARCHIVE / (name + '.snapshot')
        saved.parent.mkdir(parents=True, exist_ok=True)
        assert not saved.exists()
        saved.write_bytes(data)
        entries[name] = {'path': name + '.snapshot', 'sha256': sha256(data).hexdigest()}
    target.write_text(json.dumps({'source_commit': commit, 'files': entries,
        'purpose': 'Exact superseded active presentation; dated releases and original seals unchanged'}, indent=2) + '\n')


if __name__ == '__main__':
    archive()
