"""Snapshot only superseded presentation/check sources, not benchmark evidence."""
from repo_layout import repo_file
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from publication_history import ROOT,ARCHIVE,previous_path

FILES=('README.md','FUNCTIONS.md','OUTPUT_COMPLIANCE.md','docs/report.html',
       'docs/index.html','docs/functions.html','docs/output_compliance.html',
       'repo_identity.py','validate_frontier_release.py','validate_consolidated_release.py',
       '.github/workflows/october18-validate.yml')


def archive():
    manifest=ARCHIVE/'manifest.json'
    if manifest.exists():
        info=json.loads(manifest.read_text())
        assert not (repo_file('direct_additions_2026-10-20/release_checksums.json', root=ROOT)).exists()
        for name in set(FILES)-set(info['files']):
            data=subprocess.check_output(['git','show',info['source_commit']+':'+name],cwd=ROOT)
            assert data==(repo_file(name, root=ROOT)).read_bytes(),'Overlapping changes: '+name
            saved=ARCHIVE/(name+'.snapshot');assert not saved.exists()
            saved.parent.mkdir(parents=True,exist_ok=True);saved.write_bytes(data)
            info['files'][name]={'path':name+'.snapshot','sha256':sha256(data).hexdigest()}
        manifest.write_text(json.dumps(info,indent=2)+'\n')
        assert set(info['files'])==set(FILES)
        for name in FILES:previous_path(repo_file(name, root=ROOT))
        return
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    entries={}
    for name in FILES:
        data=subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT)
        assert data==(repo_file(name, root=ROOT)).read_bytes(),'Overlapping changes: '+name
        saved=ARCHIVE/(name+'.snapshot')
        assert not saved.exists()
        saved.parent.mkdir(parents=True,exist_ok=True);saved.write_bytes(data)
        entries[name]={'path':name+'.snapshot','sha256':sha256(data).hexdigest()}
    manifest.write_text(json.dumps({'source_commit':commit,'files':entries,
        'purpose':'Exact previous 23-route presentation and checks; old measurements, data and release seals stay unchanged.'},indent=2)+'\n')


if __name__=='__main__':archive()
