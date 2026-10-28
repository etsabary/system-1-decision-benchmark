"""Preserve the committed presentation before adding LLM reference points."""
from repo_layout import logical_relative, repo_file
from repo_layout import frozen_file
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=repo_file('frontier_archive_2026-10-19', root=ROOT)
FILES=('README.md','FUNCTIONS.md','OUTPUT_COMPLIANCE.md','LLM_EXPANSION.md',
       'docs/index.html','docs/functions.html','docs/output_compliance.html',
       'build_readable_report.py','validate_readable_report.py','validate_consolidated_release.py',
       'test_consolidated_publication.py','test_readable_report.py','.github/workflows/october18-validate.yml')


def historical_path(path):
    path=Path(path)
    manifest=ARCHIVE/'manifest.json'
    files=json.loads(manifest.read_text())['files'] if manifest.exists() else {}
    name=str(logical_relative(path, root=ROOT))
    if name not in files:return frozen_file(path)
    entry=files[name];saved=ARCHIVE/entry['archive_path']
    assert sha256(saved.read_bytes()).hexdigest()==entry['sha256'],name
    return saved


def archive():
    if (ARCHIVE/'manifest.json').exists():
        manifest=ARCHIVE/'manifest.json';original=manifest.read_bytes();info=json.loads(original)
        missing=[name for name in FILES if name not in info['files']]
        if missing:
            # Extend the archive from its pinned original commit, never from
            # the changed working copy. Retain the initial manifest as evidence.
            initial=ARCHIVE/'manifest_initial.json'
            assert not initial.exists()
            initial.write_bytes(original)
            for name in missing:
                data=subprocess.check_output(['git','show',info['source_commit']+':'+name],cwd=ROOT)
                saved=ARCHIVE/(name+'.snapshot');assert not saved.exists()
                saved.parent.mkdir(parents=True,exist_ok=True);saved.write_bytes(data)
                info['files'][name]={'archive_path':name+'.snapshot','sha256':sha256(data).hexdigest()}
            manifest.write_text(json.dumps(info,indent=2)+'\n')
        for name in FILES:historical_path(repo_file(name, root=ROOT))
        return
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    files={}
    for name in FILES:
        data=subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT)
        assert (repo_file(name, root=ROOT)).read_bytes()==data,'Uncommitted overlapping source: '+name
        saved=ARCHIVE/(name+'.snapshot');saved.parent.mkdir(parents=True,exist_ok=True)
        assert not saved.exists()
        saved.write_bytes(data)
        files[name]={'archive_path':name+'.snapshot','sha256':sha256(data).hexdigest()}
    (ARCHIVE/'manifest.json').write_text(json.dumps({'source_commit':commit,'files':files,
        'purpose':'Exact committed source/presentation before the separately measured full-bank LLM references; prior numerical evidence is unchanged.'},indent=2)+'\n')


if __name__=='__main__':
    archive();print('Archived exact committed presentation; no inference or Git mutation.')
