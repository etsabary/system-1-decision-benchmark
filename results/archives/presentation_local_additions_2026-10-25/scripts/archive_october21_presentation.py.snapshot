"""Preserve the exact committed 26-route presentation before the next additions."""
from repo_layout import logical_relative, repo_file
from repo_layout import frozen_file, source_file
from hashlib import sha256
import ast
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = repo_file('presentation_archive_2026-10-21', root=ROOT)


def previous(path):
    path = Path(path)
    manifest = ARCHIVE/'manifest.json'
    entries = json.loads(manifest.read_text())['files'] if manifest.exists() else {}
    entry = entries.get(str(logical_relative(path, root=ROOT)))
    if entry is None:
        return frozen_file(path)
    saved = ARCHIVE/entry['path']
    assert saved.resolve().is_relative_to(ARCHIVE.resolve())
    assert sha256(saved.read_bytes()).hexdigest()==entry['sha256']
    return saved


def archive():
    tree = ast.parse((source_file(repo_file('publish_direct_decisions.py', root=ROOT))).read_text())
    files = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=='ACTIVE' for t in node.targets))
    target = ARCHIVE/'manifest.json'
    if target.exists():
        for name in json.loads(target.read_text())['files']:
            previous(repo_file(name, root=ROOT))
        return
    commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    entries = {}
    for name in files:
        data = subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT)
        assert data==(repo_file(name, root=ROOT)).read_bytes(),'Overlapping changes: '+name
        saved = ARCHIVE/(name+'.snapshot')
        saved.parent.mkdir(parents=True,exist_ok=True)
        assert not saved.exists()
        saved.write_bytes(data)
        entries[name] = dict(path=name+'.snapshot',sha256=sha256(data).hexdigest())
    target.write_text(json.dumps(dict(source_commit=commit,files=entries,
        purpose='Exact October20 presentation and checks; measurements and dated release seals remain unchanged'),indent=2)+'\n')


if __name__=='__main__':
    archive()
