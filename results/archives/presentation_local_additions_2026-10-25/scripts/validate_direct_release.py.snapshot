"""Public consistency/privacy checks; no inference, credentials or correct keys."""
from repo_layout import repo_file
from collections import Counter
import csv
from decimal import Decimal
from html.parser import HTMLParser
import json
import math
import re
from urllib.parse import urlsplit

import publish_direct_decisions as b


class Page(HTMLParser):
    def __init__(self):
        super().__init__();self.cells=[];self.summary=[];self.additions=[];self.ids=[];self.links=[];self.text=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='td' and 'data-category' in a:self.cells.append(a)
        if 'data-summary-model' in a:self.summary.append(a['data-summary-model'])
        if 'data-addition-model' in a:self.additions.append(a['data-addition-model'])
        if 'id' in a:self.ids.append(a['id'])
        self.links.extend(v for k,v in attrs if k in ('href','src'))
    def handle_data(self,data):self.text.append(data)


def validate():
    from archive_october21_presentation import previous
    from validate_consolidated_release import privacy
    old=json.loads((b.BASE/'statistics.json').read_text());s=json.loads((b.DEST/'statistics.json').read_text())
    manifest=json.loads((b.DEST/'manifest.json').read_text())
    assert (s['question_count'],s['model_count'],s['family_count'],s['primary_cases'])==(1342,26,31,34892)
    assert len(s['decision_model_ids'])==23 and len(s['reference_model_ids'])==3
    assert set(s['models'])==set(old['models'])|set(b.NEW_IDS)
    assert all(s['models'][mid]==v for mid,v in old['models'].items()),'An earlier measurement changed'
    assert s['ranked_model_ids']==sorted(s['models'],key=lambda mid:(-s['models'][mid]['correct'],mid))
    assert s['decision_model_ids'][:4]==['respan02','pplx_decider12','nimble_v4_max','d3_turbo']
    assert s['ranked_model_ids'][0]=='reference_sol'
    assert b.digest(b.BASE/'statistics.json')==s['prior_statistics_sha256']==manifest['prior_statistics_sha256']
    assert b.digest(b.BASE/'release_checksums.json')==manifest['prior_release_seal_sha256']
    assert b.digest(repo_file('consolidated_2026-10-19/questions_1342.jsonl', root=b.ROOT))==manifest['bank_sha256']==b.prior.BANK_HASH
    for mid,m in s['models'].items():
        assert m['n']==1342 and m['correct']+m['wrong_valid']+m['failed']==1342
        assert m['answered']+m['failed']==1342 and sum(v['n'] for v in m['families'].values())==1342
        assert sum(v['correct'] for v in m['families'].values())==m['correct']
        assert math.isclose(m['accuracy'],m['correct']/1342)
        assert m['p95_ms']>=m['median_ms']>=0 and m['release_exclusion_diagnostic']['n']==1305
        c=m['cost']
        if c.get('public_free_access'):
            assert mid in ('d3_turbo','amos_large')
            assert c['known_usd'] is c['known_usd_per_1000'] is c['exact_usd'] is None
            assert c['unknown_attempts']==1342 and c['accounted_access_cost_usd']==0
        else:
            assert math.isclose(c['known_usd_per_1000'],c['known_usd']/1342*1000)
        if mid in b.NEW_IDS:
            assert m['attempts']==1342 and m['recoveries']==m['failed']==m['probability_warnings']==0
            assert m['dates_toronto']=={'2026-10-20':1342} and m['output_token_values']=={'0':1342}
    assert [s['models'][mid]['correct'] for mid in b.NEW_IDS]==[1106,1074,1066]
    assert Decimal(s['models']['kettei_fat']['cost']['known_decimal'])==Decimal('0.02071056')
    assert s['total_http_attempts']==sum(m['attempts'] for m in s['models'].values())
    assert s['total_recoveries']==sum(m['recoveries'] for m in s['models'].values())
    for name,h in manifest['artifacts'].items():assert b.digest(b.DEST/name)==h,name
    assert {p.name for p in b.DEST.iterdir()}==set(manifest['artifacts'])|{'manifest.json'}|({'release_checksums.json'} if (b.DEST/'release_checksums.json').exists() else set())
    for path in b.DEST.iterdir():
        if path.name=='release_checksums.json':continue
        assert path.read_bytes()==(repo_file('docs', root=b.ROOT)/b.NAME/path.name).read_bytes()
        if path.suffix!='.png':
            check=privacy(path.read_text())
            if path.suffix=='.json':check(json.loads(path.read_text()))
    pages=[b.DEST/'report.html',repo_file('docs/report.html', root=b.ROOT)]
    for path in pages:
        page=Page();page.feed(previous(path).read_text())
        assert len(page.ids)==len(set(page.ids))
        assert page.summary==s['ranked_model_ids'] and page.additions==list(b.NEW_IDS)
        assert len(page.cells)==806
        assert Counter(c['data-model'] for c in page.cells)=={mid:31 for mid in s['models']}
        for c in page.cells:
            v=s['models'][c['data-model']]['families'][c['data-category']]
            assert (int(c['data-correct']),int(c['data-n']))==(v['correct'],v['n'])
            assert b.readable.color(v['accuracy'])[0] in c['style']
        visible=' '.join(page.text)
        for label in b.readable.LABELS.values():assert label in visible
        assert 'without a prior' not in visible.lower()
        assert '34,892 first attempts' in visible and '16 of the 23 decision models' in visible
        assert 'not an API-reported $0' in visible and 'not a numeric point' in visible
        privacy(visible)
        for target in page.links:
            u=urlsplit(target)
            if not u.scheme and not u.netloc:
                if u.path:assert (path.parent/u.path).exists(),(path,target)
                elif u.fragment:assert u.fragment in page.ids,(path,target)
    with (b.DEST/'category_scores.csv').open(newline='') as f:rows=list(csv.DictReader(f))
    assert len(rows)==31 and len(rows[0])==29
    for row in rows:
        fid=row['category_id'];assert row['category']==b.readable.LABELS[fid]
        for mid,m in s['models'].items():assert row[m['label']]==b.readable.score(m['families'][fid])
    with (b.DEST/'model_statistics.csv').open(newline='') as f:rows=list(csv.DictReader(f))
    assert [r['model_id'] for r in rows]==s['ranked_model_ids']
    for row in rows:
        m=s['models'][row['model_id']]
        assert int(row['questions'])==1342 and int(row['correct'])==m['correct']
        assert float(row['median_ms'])==m['median_ms'] and float(row['p95_ms'])==m['p95_ms']
        if m['cost'].get('public_free_access'):assert row['known_metered_or_accounted_cost_usd']==row['known_cost_per_1000_usd']==''
        else:assert float(row['known_metered_or_accounted_cost_usd'])==m['cost']['known_usd']
    caps=json.loads((b.DEST/'image_capabilities.json').read_text())
    assert caps['image_inference_calls']==0 and set(caps['models'])==set(s['models'])
    assert sum(caps['models'][mid]['image_input'] for mid in s['decision_model_ids'])==16
    assert all(caps['models'][mid]['image_input'] for mid in b.NEW_IDS)
    assert all(re.fullmatch('[a-f0-9]{64}',v['source_sha256']) for v in caps['models'].values())
    for name in ('README.md','FUNCTIONS.md','IMAGE_CAPABILITIES.md','OUTPUT_COMPLIANCE.md'):
        text=previous(repo_file(name, root=b.ROOT)).read_text();privacy(text)
        assert 'jev-1.14-comparison-benchmark' not in text
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if not re.match(r'^(https?:|mailto:|#)',target):assert (repo_file(target.split('#')[0], root=b.ROOT)).exists(),target
    text=previous(repo_file('README.md', root=b.ROOT)).read_text()
    for m in s['models'].values():assert m['label'] in text
    assert '34,892' in text and 'Free public access' in text and '23 specialized' in text
    from repo_identity import validate as old_release
    old_release()
    seal=b.DEST/'release_checksums.json'
    if seal.exists():assert b.hashes()==json.loads(seal.read_text()),'Current publication seal changed'
    print('PASS: 26 complete routes, 806 exact colored cells, free/metered cost separation, 16 declared image-capable decision models; all earlier measurements and seals unchanged.')
    return s


if __name__=='__main__':validate()
