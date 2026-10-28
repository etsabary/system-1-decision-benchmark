"""Check the high-level folder layout without network calls or private data."""
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit

from repo_layout import ARCHIVE, MANIFEST, ROOT, SCRIPTS, frozen_file, repo_file, source_file


def validate():
    manifest = json.loads(MANIFEST.read_text())
    assert manifest['version'] == 'scripts-layout-2026-10-22-v1'
    assert len(manifest['moved_sources']) == 110
    assert not list(ROOT.glob('*.py')), 'Python sources remain in the repository root'
    for old, new in manifest['moved_sources'].items():
        assert '/' not in old and old.endswith('.py')
        assert new == 'scripts/' + old and not (ROOT / old).exists()
        assert source_file(ROOT / old) == ROOT / new
        assert (ROOT / new).is_file()
        preserved = frozen_file(ROOT / old)
        assert preserved.is_relative_to(ARCHIVE)
    for old, entry in manifest['preserved_sources'].items():
        assert frozen_file(ROOT / old) == ROOT / entry['archive_path']
    for name, expected in manifest['protected_files'].items():
        path = frozen_file(ROOT / name)
        assert path.resolve().is_relative_to(ROOT.resolve()), name
        assert sha256(path.read_bytes()).hexdigest() == expected, 'Published evidence changed: ' + name
    assert manifest['current_files'], 'Active sources have not been bound'
    for name, expected in manifest['current_files'].items():
        assert sha256((ROOT / name).read_bytes()).hexdigest() == expected, 'Active source changed: ' + name
    actual = {p.relative_to(ROOT).as_posix() for p in SCRIPTS.glob('*.py')}
    assert actual <= manifest['current_files'].keys(), 'Unbound active Python source'
    for path in SCRIPTS.glob('*.py'):
        compile(path.read_text(), str(path), 'exec')
    for name in ('README.md', '.github/workflows/validate.yml', '.github/workflows/october18-validate.yml'):
        assert name in manifest['current_files']
    readme = (ROOT / 'README.md').read_text()
    assert '[scripts/](scripts/README.md)' in readme
    assert 'python3 scripts/validate_october21_release.py' in readme
    directory = manifest['directory_layout']
    assert directory['version'] == 'high-level-layout-2026-10-22-v1'
    tracked = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0')
    entries = {name.split('/')[0] for name in tracked if name and (ROOT / name).exists()}
    assert entries == set(directory['root_entries']), ('Unexpected root clutter', entries)
    assert len(entries) == 10 and {p.name for p in ROOT.glob('*.md')} == {'README.md'}
    for old, new in directory['prefixes'].items():
        assert not (ROOT / old).exists(), old
        assert repo_file(old) == ROOT / new and (ROOT / new).exists(), new
    for document in [ROOT / 'README.md', SCRIPTS / 'README.md', ROOT / 'results/README.md', ROOT / 'data/README.md', *sorted((ROOT / 'documents').glob('*.md'))]:
        for target in re.findall(r'\]\(([^\s)]+)\)', document.read_text()):
            url = urlsplit(target)
            if not url.scheme and not url.netloc and url.path:
                assert (document.parent / url.path).exists(), (document, target)
    print(f"PASS: 10 high-level root entries; 110 relocated sources; {len(manifest['protected_files'])} preserved artifacts; "
          f"{len(manifest['current_files'])} active files, documentation links and historical snapshots checked.")
    return manifest


if __name__ == '__main__':
    validate()
