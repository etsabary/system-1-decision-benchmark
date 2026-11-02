"""Check the stopped Kai note without changing frozen v4 evidence or visuals."""
import argparse,hashlib,json
from pathlib import Path

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def validate(dest,source):
 manifest=json.loads((dest/'manifest.json').read_text())
 assert manifest['frozen_hosted_manifest_sha256']==sha(source/'manifest.json')
 old={p.relative_to(source) for p in source.rglob('*') if p.is_file()}
 new={p.relative_to(dest) for p in dest.rglob('*') if p.is_file()}
 assert new==old|{Path('KAI_CASE_NOTE.md')}
 changes={Path('manifest.json'),Path('report.html'),Path('README_V4.md')}
 for name in old-changes:assert sha(source/name)==sha(dest/name),str(name)
 for name,digest in manifest['files_sha256'].items():assert sha(dest/name)==digest,name
 partial=json.loads((dest/'partial_models.json').read_text());assert len(partial)==1
 x=partial[0];assert x['sample_n']==244 and x['sample_correct']==46 and x['subq_correct_on_same_inputs']==190 and x['provider_extrapolated_count']==31
 stats=json.loads((dest/'statistics.json').read_text());assert len(stats['models'])==28 and 'hanzo_kai19' not in stats['models']
 html=(dest/'report.html').read_text();begin=html.index('<h3>Below the 62% cutoff</h3>');end=html.index('<section id="legend">',begin);section=html[begin:end]
 assert 'data-incomplete-model="hanzo-kai"' in section and '46/244' in section and '190/244' in section and 'not a full-bank score or a 62% cutoff classification' in section
 assert 'prepaid credits were purchased' in section and 'eight-hour usage limit' in section and 'user stopped testing' in section.lower()
 readme=(dest/'README_V4.md').read_text();begin=readme.index('## Below the cutoff');end=readme.index('## Download and reproducibility',begin);section=readme[begin:end]
 assert 'Hanzo Kai 1.9 — stopped partial test' in section and '46/244' in section and 'not a full-bank score or a 62% cutoff classification' in section
 case=(dest/'KAI_CASE_NOTE.md').read_text().lower();assert all(x in case for x in ['50 answers','purchased prepaid credits','eight-hour usage window','31 of the 244','user stopped','not a 2,157-question score'])
 print('PASS: Kai partial sample and usage-limit story appear beside the below-cutoff catalogue; all v4 data, model scores, cost evidence and graphics are unchanged.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('release',type=Path);p.add_argument('source_release',type=Path);a=p.parse_args();validate(a.release,a.source_release)
