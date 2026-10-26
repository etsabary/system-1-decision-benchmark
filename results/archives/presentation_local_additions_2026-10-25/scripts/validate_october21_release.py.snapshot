"""Offline aggregate, privacy, link and seal checks for the 29-route release."""
from repo_layout import repo_file, frozen_file
from collections import Counter
import csv
from decimal import Decimal
import json
import math
import re
from urllib.parse import urlsplit

import publish_october21_additions as b
from validate_direct_release import Page


def validate():
    from validate_consolidated_release import privacy
    s = json.loads((b.DEST/'statistics.json').read_text())
    old = json.loads((b.prior.DEST/'statistics.json').read_text())
    manifest = json.loads((b.DEST/'manifest.json').read_text())
    assert (s['model_count'],s['question_count'],s['family_count'],s['primary_cases'])==(29,1342,31,38918)
    assert len(s['decision_model_ids'])==26 and len(s['reference_model_ids'])==3
    assert set(s['models'])==set(old['models'])|set(b.NEW)
    assert all(s['models'][mid]==m for mid,m in old['models'].items()),'Earlier measurement changed'
    assert s['ranked_model_ids']==sorted(s['models'],key=lambda mid:(-s['models'][mid]['correct'],mid))
    assert s['ranked_model_ids'][:4]==['reference_sol','mammoth1','drex_max','respan02']
    assert [s['models'][mid]['correct'] for mid in b.NEW]==[1139,1004,1127]
    assert Decimal(s['models']['drex_max']['cost']['known_decimal'])==Decimal('0.02842302')
    assert manifest['prior_statistics_sha256']==b.digest(b.prior.DEST/'statistics.json')
    assert manifest['bank_sha256']==b.analysis.router.bank.BANK_HASH
    assert b.digest(b.analysis.router.bank.BANK)==manifest['bank_sha256']
    for mid,m in s['models'].items():
        assert m['n']==1342 and m['correct']+m['wrong_valid']+m['failed']==1342
        assert m['answered']+m['failed']==1342
        assert sum(v['n'] for v in m['families'].values())==1342
        assert sum(v['correct'] for v in m['families'].values())==m['correct']
        assert math.isclose(m['accuracy'],m['correct']/1342)
        assert m['p95_ms']>=m['median_ms']>0
        assert m['release_exclusion_diagnostic']['n']==1305
        c=m['cost']
        if c.get('public_free_access'):
            assert c['known_usd'] is c['known_usd_per_1000'] is None
        else:
            assert math.isclose(c['known_usd']/1342*1000,c['known_usd_per_1000'])
        if mid in b.NEW:
            assert m['first_statuses']=={'ok':1342} and m['recoveries']==m['failed']==m['probability_warnings']==0
            assert m['median_ms']<=2000 and m['dates_toronto']=={'2026-10-21':1342}
    for name,h in manifest['artifacts'].items():
        assert b.digest(b.DEST/name)==h,name
    assert {p.name for p in b.DEST.iterdir()}==set(manifest['artifacts'])|{'manifest.json'}|({'release_checksums.json'} if (b.DEST/'release_checksums.json').exists() else set())
    for path in b.DEST.iterdir():
        if path.name=='release_checksums.json':continue
        assert path.read_bytes()==(repo_file('docs', root=b.ROOT)/b.NAME/path.name).read_bytes()
        if path.suffix!='.png':
            check=privacy(path.read_text())
            if path.suffix=='.json':check(json.loads(path.read_text()))
    for path in (b.DEST/'report.html',repo_file('docs/report.html', root=b.ROOT)):
        page=Page();page.feed(frozen_file(path).read_text())
        assert page.summary==s['ranked_model_ids'] and page.additions==list(b.NEW)
        assert len(page.cells)==899 and len(page.ids)==len(set(page.ids))
        assert Counter(c['data-model'] for c in page.cells)=={mid:31 for mid in s['models']}
        for c in page.cells:
            v=s['models'][c['data-model']]['families'][c['data-category']]
            assert (int(c['data-correct']),int(c['data-n']))==(v['correct'],v['n'])
            assert b.readable.color(v['accuracy'])[0] in c['style']
        text=' '.join(page.text)
        assert '38,918 first attempts' in text and 'Promotional free access' in text
        assert 'without a prior' not in text.lower()
        assert '18/48' in text and '33/48' in text and '206/2157' in text
        for label in b.readable.LABELS.values():assert label in text,label
        privacy(text)
        for target in page.links:
            url=urlsplit(target)
            if not url.scheme and not url.netloc:
                if url.path:assert (path.parent/url.path).exists(),(path,target)
                elif url.fragment:assert url.fragment in page.ids,(path,target)
    with (b.DEST/'model_statistics.csv').open(newline='') as stream:
        rows=list(csv.DictReader(stream))
    assert [r['model_id'] for r in rows]==s['ranked_model_ids']
    for row in rows:
        m=s['models'][row['model_id']]
        assert int(row['questions'])==1342 and int(row['correct'])==m['correct']
        assert float(row['median_ms'])==m['median_ms'] and float(row['p95_ms'])==m['p95_ms']
        if m['cost'].get('public_free_access'):assert row['known_cost_usd']==row['known_cost_per1000_usd']==''
        else:assert float(row['known_cost_usd'])==m['cost']['known_usd']
    with (b.DEST/'category_scores.csv').open(newline='') as stream:
        rows=list(csv.DictReader(stream))
    assert len(rows)==31
    for row in rows:
        for m in s['models'].values():assert row[m['label']]==b.readable.score(m['families'][row['category_id']])
    for name in ('README.md','FUNCTIONS.md','OUTPUT_COMPLIANCE.md','IMAGE_CAPABILITIES.md'):
        document=repo_file(name, root=b.ROOT)
        text=document.read_text();privacy(text)
        assert 'jev-1.14-comparison-benchmark' not in text
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if not re.match(r'^(https?:|mailto:|#)',target):assert (document.parent/target.split('#')[0]).exists(),target
    receipt=json.loads((b.DEST/'audit_receipt.json').read_text())
    assert receipt['primary_attempts']==4026 and receipt['recoveries']==receipt['unusable_responses']==0
    assert all(v['n']==v['same_choice']==20 for v in receipt['controls'].values())
    from validate_direct_release import validate as previous
    previous()
    seal=b.DEST/'release_checksums.json'
    if seal.exists():assert b.hashes()==json.loads(seal.read_text()),'Current publication seal changed'
    print('PASS:29 full-bank routes,899 exact colored cells; earlier26 records and all prior seals unchanged.')
    return s


if __name__=='__main__':
    validate()
