"""Resolve the exact October 19 presentation for its unchanged release checks."""
from repo_layout import logical_relative, repo_file
from repo_layout import frozen_file
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=repo_file('direct_archive_2026-10-20', root=ROOT)


def previous_path(path):
    path=Path(path)
    manifest=ARCHIVE/'manifest.json'
    entries=json.loads(manifest.read_text())['files'] if manifest.exists() else {}
    entry=entries.get(str(logical_relative(path, root=ROOT)))
    if entry is None:return frozen_file(path)
    saved=ARCHIVE/entry['path']
    assert saved.resolve().is_relative_to(ARCHIVE.resolve())
    assert sha256(saved.read_bytes()).hexdigest()==entry['sha256'],path
    return saved
