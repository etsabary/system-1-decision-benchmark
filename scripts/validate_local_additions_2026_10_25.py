"""Public offline reconstruction of local timing, coverage and displayed cells."""
from collections import Counter, defaultdict
import csv
from html.parser import HTMLParser
import json
import math
import random
import re
import statistics
from urllib.parse import urlsplit

import publish_local_additions_2026_10_25 as b
from validate_consolidated_release import privacy
from validate_direct_release import Page

EXPECTED = {'H2O-Lightning 4B':892,'Fovea 4B':841,'Jebadiah 4B':808,'JevK5 4B':780,
            'Lev 4B':749,'Credence E4B':741,'Strands Decider 2B':710,'Snap 2B':574,
            'Mapika Decider 2B':547,'Sura 2B':428,'GLiClass':393,'Von':331,
            'Laya Typed Decisions':322,'Decima Agent':313,'CLM 8B':304,
            'D3 Flash Artemis 9B':995,'Perplexity Flash v1.2 mixed4':971,'Jebadiah 9B v2.1':855}


class RowSettings(HTMLParser):
    def __init__(self):
        super().__init__();self.rows={}
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='tr' and 'data-summary-model' in a:self.rows[a['data-summary-model']]=a.get('class','')


def percentile(values,p):
    values=sorted(values);pos=(len(values)-1)*p;lo=int(pos)
    return values[lo]+(values[min(lo+1,len(values)-1)]-values[lo])*(pos-lo)


def validate():
    s=json.loads((b.DEST/'statistics.json').read_text());old=json.loads((b.PREVIOUS/'statistics.json').read_text())
    assert (s['model_count'],s['local_model_count'],s['hosted_decision_model_count'],s['primary_cases'])==(49,18,27,65758)
    assert len(s['reference_model_ids'])==4 and s['decision_model_count']==45
    assert all(s['models'][mid]==m for mid,m in old['models'].items()), 'Earlier measurement changed'
    assert s['ranked_model_ids']==sorted(s['models'],key=lambda mid:(-s['models'][mid]['correct'],mid))
    assert s['ranked_model_ids'][:3]==['fastino_glide','reference_sol','mammoth1']
    assert {s['models'][mid]['label']:s['models'][mid]['correct'] for mid in s['local_model_ids']}==EXPECTED
    bank=b.ROOT/'results/releases/consolidated_2026-10-19/questions_1342.jsonl'
    assert b.digest(bank)==s['question_bank_sha256']
    questions=[json.loads(line) for line in bank.read_text().splitlines()]
    indexed={q['id']:q for q in questions};order=list(indexed);random.Random(2026101906).shuffle(order)
    with (b.DEST/'local_timing_evidence.csv').open() as stream:timing=list(csv.DictReader(stream))
    assert len(timing)==24156
    grouped=defaultdict(list)
    for row in timing:
        grouped[row['model_id']].append(row)
        assert row['item_id']==order[int(row['request_index'])-1]
        assert row['native_input_sha256']==indexed[row['item_id']]['native_input_sha256']
        assert row['family_id']==indexed[row['item_id']]['family_id']
        assert all(math.isfinite(float(row[k])) and float(row[k])>=0 for k in ('latency_ms','server_eval_ms','server_load_ms'))
    assert set(grouped)==set(s['local_model_ids'])
    for mid,rows in grouped.items():
        m=s['models'][mid];assert len(rows)==len({r['item_id'] for r in rows})==1342
        assert m['execution_location']=='local' and m['hardware']=='NVIDIA RTX 2060' and m['vram_gb']==6
        assert m['dates_toronto']=={'2026-10-25':1342} and m['recoveries']==0
        values=[float(r['latency_ms']) for r in rows]
        for key,expected in [('mean_response_ms',statistics.mean(values)),('median_ms',statistics.median(values)),('p95_ms',percentile(values,.95))]:
            assert math.isclose(m[key],expected,rel_tol=1e-12), (mid,key)
        assert m['first_statuses']==dict(Counter(r['status'] for r in rows))
        assert m['answered']==m['first_statuses'].get('ok',0) and m['answered']+m['failed']==1342
        assert m['cost']['known_usd'] is None and m['cost']['known_usd_per_1000'] is None
        assert m['cost']['kind']=='local_unmetered' and m['cost']['hardware_electricity_measured'] is False
        assert sum(f['correct'] for f in m['families'].values())==m['correct']
        assert sum(f['n'] for f in m['families'].values())==1342
        assert m['release_exclusion_diagnostic']['n']==1305
    assert sum(s['models'][mid]['answered'] for mid in s['local_model_ids'])==24136
    # New evidence appends to the exact earlier public timing rows.
    assert (b.DEST/'local_timing_evidence.csv').read_bytes().startswith((b.PREVIOUS/'local_timing_evidence.csv').read_bytes())
    assert len(s['added_model_ids']) == 3 and set(s['added_model_ids']) == set(s['models'])-set(old['models'])
    assert s['models'][s['local_model_ids'][0]]['label'] == 'D3 Flash Artemis 9B'
    for mid, failures in [(b.mid('pplx-decider:flash-v1.2-mixed4'),3), (b.mid('d3:flash-artemis-iq3_m'),3), (b.mid('jeb:9b-v2.1-iq4_xs'),7)]:
        m=s['models'][mid]
        assert m['first_statuses'] == {'ok':1342-failures,'http_failure':failures}
        assert m['failed'] == failures and m['recoveries'] == 0 and m['attempts'] == 1342
    receipt=json.loads((b.DEST/'audit_receipt.json').read_text())
    assert (receipt['models'],receipt['first_attempts'],receipt['usable'],receipt['unusable']) == (18,24156,24136,20)
    assert (receipt['new_models'],receipt['new_first_attempts'],receipt['new_usable'],receipt['new_unusable']) == (3,4026,4013,13)
    manifest=json.loads((b.DEST/'manifest.json').read_text())
    assert manifest['prior_statistics_sha256']==b.digest(b.PREVIOUS/'statistics.json')
    for name,h in manifest['artifacts'].items():
        p=b.DEST/name;assert b.digest(p)==h,name
        assert p.read_bytes()==(b.ROOT/'docs'/b.NAME/name).read_bytes(),name
        if p.suffix!='.png':
            text=p.read_text();inspect=privacy(text)
            assert '192.168.' not in text and '/home/' not in text,name
            if p.suffix=='.json':inspect(json.loads(text))
    for path in (b.DEST/'report.html',b.ROOT/'docs/report.html'):
        text=path.read_text();page=Page();page.feed(text);settings=RowSettings();settings.feed(text)
        assert page.summary==s['ranked_model_ids'] and len(page.cells)==1519
        assert len(page.ids)==len(set(page.ids))
        assert Counter(c['data-model'] for c in page.cells)=={mid:31 for mid in s['models']}
        for cell in page.cells:
            value=s['models'][cell['data-model']]['families'][cell['data-category']]
            assert (int(cell['data-correct']),int(cell['data-n']))==(value['correct'],value['n'])
            assert b.readable.color(value['accuracy'])[0] in cell['style']
        assert all(settings.rows[mid]=='local-model' for mid in s['local_model_ids'])
        assert text.count('class="local-badge"')>=90
        visible=' '.join(page.text)
        for phrase in ('65,758 first attempts','RTX 2060','6 GB','20%','49 routes','operating cost','upstream weight revision','chosen deliberately','older, more accessible'):
            assert phrase in visible,phrase
        assert 'without a prior' not in visible
        for label in b.readable.LABELS.values():assert label in visible,label
        for target in page.links:
            url=urlsplit(target)
            if not url.scheme and not url.netloc:
                if url.path:assert (path.parent/url.path).exists(),target
                elif url.fragment:assert url.fragment in page.ids,target
    svg=(b.DEST/'accuracy_speed_cost.svg').read_text()
    assert '#7c3aed' in svg and '#16728c' in svg and 'fill-opacity: 0.6' in svg
    assert '20% uniform guessing' in svg and 'Local compute' in svg
    for mid in s['local_model_ids']:assert s['models'][mid]['label'] in svg
    with (b.DEST/'model_statistics.csv').open() as stream:rows=list(csv.DictReader(stream))
    assert [r['model_id'] for r in rows]==s['ranked_model_ids']
    for row in rows:
        m=s['models'][row['model_id']]
        assert int(row['correct'])==m['correct'] and float(row['median_ms'])==m['median_ms']
        if row['model_id'] in s['local_model_ids']:assert row['known_cost_usd']==row['known_cost_per1000_usd']==''
    for p in (b.ROOT/'README.md',b.repo_file('FUNCTIONS.md'),b.repo_file('OUTPUT_COMPLIANCE.md')):
        text=p.read_text();privacy(text)
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if not re.match(r'^(https?:|mailto:|#)',target):assert (p.parent/target.split('#')[0]).exists(),target
    screens=json.loads((b.DEST/'screened_routes.json').read_text())
    assert len(screens)==4 and all(not r['ranked'] for r in screens)
    from validate_local_2026_10_25 import validate as old_validate
    old_validate()
    print('PASS: 49 routes; 18 local configurations; 24,156 public timing rows; 1,519 exact category cells; earlier records unchanged.')
    return s


if __name__=='__main__':validate()
