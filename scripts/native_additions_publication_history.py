"""Resolve the exact committed 49-route presentation for historical validation."""
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'results/archives/presentation_local_additions_2026-10-25'


def previous(path):
    path=Path(path)
    if not path.is_absolute(): path=ROOT/path
    entry=json.loads((ARCHIVE/'manifest.json').read_text())['files'].get(path.relative_to(ROOT).as_posix())
    if entry is None: return path
    saved=ARCHIVE/entry['path']
    assert sha256(saved.read_bytes()).hexdigest()==entry['sha256'], path
    return saved


def archive():
    for name in json.loads((ARCHIVE/'manifest.json').read_text())['files']:
        previous(ROOT/name)
