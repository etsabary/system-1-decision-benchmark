"""Resolve the exact active presentation before the October 27 additions."""
from hashlib import sha256
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'results/archives/presentation_before_october27_2026'
def previous(path):
    path=Path(path)
    if not path.is_absolute():path=ROOT/path
    manifest=ARCHIVE/'manifest.json'
    if not manifest.exists():return path
    entry=json.loads(manifest.read_text())['files'].get(path.relative_to(ROOT).as_posix())
    if entry is None:return path
    saved=ARCHIVE/entry['path']
    assert sha256(saved.read_bytes()).hexdigest()==entry['sha256'],str(path)
    return saved
def archive():
    for path in json.loads((ARCHIVE/'manifest.json').read_text())['files']:previous(ROOT/path)
