"""Resolve the sealed61-configuration presentation after the current view advances."""
from pathlib import Path
from hashlib import sha256
import json
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'results/archives/presentation_before_october31_2026'
def previous(path):
 path=Path(path);path=path if path.is_absolute() else ROOT/path
 target=ARCHIVE/'manifest.json'
 if not target.exists():return path
 entry=json.loads(target.read_text())['files'].get(path.relative_to(ROOT).as_posix())
 if entry is None:return path
 saved=ARCHIVE/entry['path'];assert sha256(saved.read_bytes()).hexdigest()==entry['sha256']
 return saved
