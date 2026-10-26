"""Physical repository locations and exact pre-layout bytes for dated evidence.

Live runners must use ``source_file`` for dependencies in scripts/. Only checks
against already-published provenance use ``frozen_file``. No release manifest,
measurement, question, or dated report is rewritten by this path migration.
"""
from hashlib import sha256
from functools import lru_cache
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'
ARCHIVE = SCRIPTS / 'legacy_layout'
MANIFEST = SCRIPTS / 'layout_manifest.json'


@lru_cache(maxsize=4)
def _manifest(path, modified_ns):
    return json.loads(path.read_text())


def layout_manifest():
    return _manifest(MANIFEST, MANIFEST.stat().st_mtime_ns)


def repo_file(path, *, root=None):
    """Resolve a logical evidence path into the current physical organization.

    Dated evidence keeps its original names in checksum manifests. Only the
    on-disk prefix changes. Explicit external/test roots are never redirected.
    """
    root = ROOT if root is None else Path(root)
    path = Path(path)
    if root != ROOT:
        return root / path
    if path.is_absolute():
        try:
            path = path.relative_to(ROOT)
        except ValueError:
            return path
    if not path.parts:
        return ROOT
    first, *tail = path.parts
    manifest = layout_manifest()
    if len(path.parts) == 1 and first in manifest['moved_sources']:
        return ROOT / manifest['moved_sources'][first]
    prefix = manifest.get('directory_layout', {}).get('prefixes', {}).get(first, first)
    return ROOT / prefix / Path(*tail)


def logical_relative(path, *, root=None):
    """Return the stable pre-layout name used by frozen evidence manifests."""
    root = ROOT if root is None else Path(root)
    relative = Path(path).relative_to(root)
    if root != ROOT:
        return relative
    name = relative.as_posix()
    manifest = layout_manifest()
    for old, new in manifest.get('directory_layout', {}).get('prefixes', {}).items():
        if name == new or name.startswith(new + '/'):
            return Path(old + name[len(new):])
    for old, new in manifest['moved_sources'].items():
        if name == new:
            return Path(old)
    return relative


def evidence_source_map(names):
    """Supply a sealed external validator's supported physical-path mapping."""
    return {name: repo_file(name).relative_to(ROOT).as_posix() for name in names}


def source_file(path):
    """Resolve a legacy filename to its active file, never an archived source."""
    return repo_file(path)


def frozen_file(path):
    """Resolve only registered superseded files to checksum-checked snapshots."""
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    try:
        name = path.relative_to(ROOT).as_posix()
    except ValueError:
        return path
    manifest = layout_manifest()
    if name in manifest['moved_sources'].values():
        name = path.name
    else:
        name = logical_relative(path).as_posix()
    entries = manifest['preserved_sources']
    entry = entries.get(name)
    if entry is None:
        return repo_file(path)
    saved = ROOT / entry['archive_path']
    assert saved.resolve().is_relative_to(ARCHIVE.resolve()), name
    assert sha256(saved.read_bytes()).hexdigest() == entry['sha256'], name
    return saved


def verify_software(saved, current, *, historical=False):
    """Offline audits may check archived code; live resume remains current-only."""
    if saved == current:
        return
    assert historical, 'Frozen execution software changed'
    assert set(saved) == set(current), 'Frozen execution dependency set changed'
    for name, expected in saved.items():
        path = frozen_file(ROOT / name)
        assert path.is_relative_to(ARCHIVE), 'No archived execution source: ' + name
        assert sha256(path.read_bytes()).hexdigest() == expected, name
