"""Seal only the reviewed public expansion, without changing original hashes."""
from repo_layout import logical_relative, repo_file
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPANSION=repo_file('expansion_2026-10-15', root=ROOT)
SOURCES=['README.md','FUNCTIONS.md','THREE_MODEL_REFERENCE.md','report_layout.md','report_sections.md',
         'task_examples.md','text_models.py','score_expansion.py','plot_expansion.py','build_report.py',
         'build_reference_report.py','test_text_models.py','test_publication.py','freeze_expansion_checksums.py',
         'docs/index.html','docs/functions.html','docs/three_model_reference.html','.github/workflows/validate.yml',
         'decision_refresh.py','matched_analysis.py','plot_matched.py','test_decision_refresh.py','test_matched.py',
         'added_decisions.py','test_added_decisions.py','overall_analysis.py','plot_overall.py','test_overall.py',
         'addition_analysis.md','image_compatibility.py','publish_capabilities.py',
         'text_additions.py','test_text_additions.py','regular_additions_analysis.md',
         'OUTPUT_COMPLIANCE.md','output_compliance_layout.md','docs/output_compliance.html']


def paths():
    return sorted({*(repo_file(name, root=ROOT) for name in SOURCES),
                   *(p for p in EXPANSION.iterdir() if p.is_file() and p.name!='release_checksums.json'),
                   *(repo_file('decision_refresh_2026-10-15', root=ROOT)).iterdir(),*(repo_file('matched_2026-10-15', root=ROOT)).iterdir(),
                   *(repo_file('figures', root=ROOT)).glob('eleven_*'),*(repo_file('docs/figures', root=ROOT)).glob('eleven_*'),
                   *(repo_file('figures', root=ROOT)).glob('matched_*'),*(repo_file('docs/figures', root=ROOT)).glob('matched_*'),
                   *(p for p in (repo_file('additions_2026-10-16', root=ROOT)).rglob('*') if p.is_file()),
                   *(p for p in (repo_file('overall_2026-10-16', root=ROOT)).rglob('*') if p.is_file()),
                   *(p for p in (repo_file('llm_additions_2026-10-16', root=ROOT)).rglob('*') if p.is_file()),
                   *(p for p in (repo_file('overall_expanded_2026-10-16', root=ROOT)).rglob('*') if p.is_file()),
                   *(repo_file('figures', root=ROOT)).glob('overall_*'),*(repo_file('docs/figures', root=ROOT)).glob('overall_*'),
                   *(repo_file('figures', root=ROOT)).glob('expanded_*'),*(repo_file('docs/figures', root=ROOT)).glob('expanded_*')})


def freeze():
    manifest={logical_relative(p, root=ROOT).as_posix():sha256(p.read_bytes()).hexdigest() for p in paths()}
    (EXPANSION/'release_checksums.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Recorded',len(manifest),'public expansion file hashes; original checksums unchanged')


if __name__=='__main__':freeze()
