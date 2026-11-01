"""Resolve exact pre-v2 presentation bytes for historical release checks."""
from hashlib import sha256
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'results/archives/presentation_before_system1_v2_2026-11-01'
def previous(path):
 path=Path(path);path=path if path.is_absolute() else ROOT/path
 manifest=ARCHIVE/'manifest.json'
 if not manifest.exists():return path
 entry=json.loads(manifest.read_text())['files'].get(path.relative_to(ROOT).as_posix())
 if entry is None:return path
 saved=ARCHIVE/entry['path'];assert sha256(saved.read_bytes()).hexdigest()==entry['sha256']
 return saved
