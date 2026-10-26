"""Seal the local October 18 review without touching older release manifests."""
from repo_layout import logical_relative, repo_file
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEST=repo_file('overall_expanded_2026-10-18/review_checksums.json', root=ROOT)
SOURCES=['native_field_2026_10_18.py','test_native_field_2026_10_18.py',
         'native_expansion_analysis.py','test_native_expansion_analysis.py',
         'plot_native_expansion.py','build_native_expansion_report.py',
         'native_expansion_notes.md','NATIVE_DECISION_EXPANSION.md','freeze_native_review.py']


def paths():
    return sorted({*(repo_file(n, root=ROOT) for n in SOURCES),
        *(p for p in (repo_file('native_additions_2026-10-18', root=ROOT)).rglob('*') if p.is_file()),
        *(p for p in DEST.parent.rglob('*') if p.is_file() and p!=DEST)})


if __name__=='__main__':
    data={logical_relative(p, root=ROOT).as_posix():sha256(p.read_bytes()).hexdigest() for p in paths()}
    DEST.write_text(json.dumps(data,indent=2)+'\n')
    print('Sealed',len(data),'local-review files; all older release manifests unchanged')
