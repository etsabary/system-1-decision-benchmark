"""Offline consistency, privacy and preservation checks for the LLM addition."""
from repo_layout import repo_file
from collections import Counter
import csv
from html.parser import HTMLParser
import json
import math
import re

import publish_frontier_references as b


class Page(HTMLParser):
    def __init__(self):
        super().__init__();self.cells=[];self.summary=[];self.targets=[];self.ids=[];self.text=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='td' and 'data-category' in a:self.cells.append(a)
        if 'data-summary-model' in a:self.summary.append(a['data-summary-model'])
        if 'id' in a:self.ids.append(a['id'])
        self.targets += [v for k,v in attrs if k in ('src','href')]
    def handle_data(self,data):self.text.append(data)


def validate():
    from publication_history import previous_path
    from validate_consolidated_release import privacy
    from validate_readable_report import validate as validate_prior
    s=json.loads((b.DEST/'statistics.json').read_text());manifest=json.loads((b.DEST/'manifest.json').read_text())
    native=json.loads((repo_file('consolidated_2026-10-19/statistics.json', root=b.ROOT)).read_text())
    count=20+len(s['reference_model_ids'])
    assert (s['question_count'],s['model_count'],s['family_count'],s['primary_cases'])==(1342,count,31,count*1342)
    assert set(s['reference_model_ids'])==set(b.LABELS)
    assert len(s['ranked_model_ids'])==count and s['all_tested_primary_cases']==30866
    assert manifest['tested_llm_count']==s['tested_llm_reference_count']==3
    assert s['decision_model_ids']==native['ranked_model_ids']
    assert s['source_native_statistics_sha256']==b.digest(repo_file('consolidated_2026-10-19/statistics.json', root=b.ROOT))
    assert b.digest(repo_file('consolidated_2026-10-19/questions_1342.jsonl', root=b.ROOT))==b.BANK_HASH==manifest['bank_sha256']
    assert all(s['models'][mid]==value for mid,value in native['models'].items()),'A decision-model measurement changed'
    assert s['ranked_model_ids']==sorted(s['models'],key=lambda mid:(-s['models'][mid]['correct'],mid))
    for mid,m in s['models'].items():
        assert m['n']==1342 and sum(v['n'] for v in m['families'].values())==1342
        assert m['correct']+m['wrong_valid']+m['failed']==1342 and m['answered']+m['failed']==1342
        assert math.isclose(m['accuracy'],m['correct']/1342)
        assert math.isclose(m['cost']['known_usd_per_1000'],m['cost']['known_usd']/1342*1000)
        assert m['median_ms']>=0 and m['p95_ms']>=m['median_ms']
    for mid in s['reference_model_ids']:
        m=s['models'][mid]
        if mid=='reference_qwen':
            assert m['reasoning_token_counts'].get('None',0)>0
            assert 'not cash invoice' in m['cost']['scope']
            assert 'Unknown token counts are not treated as verified zeros' in m['reasoning_verification']
        else:
            assert set(m['reasoning_token_counts'])<={'0','None'}
            assert m['reasoning_text_responses']==0
        if m['cost']['unknown_attempts']:assert m['cost']['exact_usd'] is None
    page=Page();page.feed((b.DEST/'report.html').read_text())
    assert len(page.ids)==len(set(page.ids))
    assert page.summary==s['ranked_model_ids'] and len(page.cells)==count*31
    assert Counter(c['data-model'] for c in page.cells)=={mid:31 for mid in s['models']}
    assert Counter(c['data-category'] for c in page.cells)=={fid:count for fid in b.readable.LABELS}
    for cell in page.cells:
        value=s['models'][cell['data-model']]['families'][cell['data-category']]
        assert int(cell['data-correct'])==value['correct'] and int(cell['data-n'])==value['n']
        assert b.readable.color(value['accuracy'])[0] in cell['style']
    visible=' '.join(page.text)
    assert 'MiniMax M3' not in visible and 'MiniMax M3' not in previous_path(repo_file('LLM_REFERENCES.md', root=b.ROOT)).read_text()
    for name in b.readable.LABELS.values():assert name in visible
    assert 'without a prior' not in visible.lower()
    assert 'JSON-choice' in visible and 'not additional out-of-pocket billing' in visible
    assert 'not an exhaustive ranking' in visible
    for path in [b.DEST/'report.html',*(repo_file('docs', root=b.ROOT)).glob('*.html')]:
        doc=Page();doc.feed(previous_path(path).read_text())
        for link in doc.targets:
            if re.match(r'^(https?:|mailto:|data:)',link):continue
            local,_,anchor=link.partition('#')
            if local:assert (path.parent/local).exists(),(path,link)
            elif anchor:assert anchor in doc.ids,(path,link)
    with (b.DEST/'category_scores.csv').open(newline='') as f:rows=list(csv.DictReader(f))
    assert len(rows)==31 and len(rows[0])==3+count
    for row in rows:
        fid=row['category_id'];assert row['category']==b.readable.LABELS[fid]
        for mid in s['ranked_model_ids']:
            m=s['models'][mid];assert row[m['label']]==b.readable.score(m['families'][fid])
    with (b.DEST/'model_statistics.csv').open(newline='') as f:models=list(csv.DictReader(f))
    assert [r['model_id'] for r in models]==s['ranked_model_ids']
    for row in models:
        m=s['models'][row['model_id']]
        assert int(row['questions'])==1342 and int(row['correct'])==m['correct']
        assert float(row['median_ms'])==m['median_ms'] and float(row['known_cost_usd'])==m['cost']['known_usd']
    for name,h in manifest['artifacts'].items():assert b.digest(b.DEST/name)==h,name
    for path in b.DEST.iterdir():
        if path.name=='release_checksums.json':continue
        assert path.read_bytes()==(repo_file('docs', root=b.ROOT)/b.NAME/path.name).read_bytes()
        if path.suffix!='.png':privacy(path.read_text())
    readme=previous_path(repo_file('README.md', root=b.ROOT)).read_text();assert all(s['models'][mid]['label'] in readme for mid in s['reference_model_ids'])
    assert 'The full comparison is 23 routes' in readme and 'The full comparison is 23 routes' in visible
    assert '1342' in readme and 'not an exhaustive ranking' in readme
    for path in (repo_file('README.md', root=b.ROOT),repo_file('FUNCTIONS.md', root=b.ROOT)):
        for target in re.findall(r'\]\(([^)]+)\)',previous_path(path).read_text()):
            if not re.match(r'^(https?:|mailto:|#)',target):assert (repo_file(target.split('#')[0], root=b.ROOT)).exists(),target
    validate_prior()
    seal=b.DEST/'release_checksums.json'
    if seal.exists():assert b.hashes()==json.loads(seal.read_text()),'New publication seal changed'
    print(f'PASS: {count} complete ranked routes, {count*31} exact category cells, three LLM configurations, unchanged 20 decision results and all earlier seals.')
    return s


if __name__=='__main__':validate()
