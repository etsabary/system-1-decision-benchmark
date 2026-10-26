"""Public offline aggregate, privacy, presentation and historical-seal checks."""
from collections import Counter
import csv
from decimal import Decimal
import json
import math
from urllib.parse import urlsplit

import publish_fastino_2026_10_23 as b
from validate_direct_release import Page
from validate_consolidated_release import privacy
from archive_fastino_presentation import previous as presentation_source


def validate():
    root=b.ROOT;dest=b.DEST
    s=json.loads((dest/'statistics.json').read_text())
    old=json.loads((b.PREVIOUS_DEST/'statistics.json').read_text())
    manifest=json.loads((dest/'manifest.json').read_text())
    assert (s['model_count'],s['decision_model_count'],len(s['reference_model_ids']),s['primary_cases'])==(30,27,3,40260)
    assert all(s['models'][mid]==m for mid,m in old['models'].items()),'An earlier measurement changed'
    assert s['ranked_model_ids']==sorted(s['models'],key=lambda m:(-s['models'][m]['correct'],m))
    assert s['ranked_model_ids'][:3]==['fastino_glide','reference_sol','mammoth1']
    assert s['question_bank_sha256']==b.run.text_bank.BANK_HASH==b.digest(b.run.text_bank.BANK)
    assert manifest['prior_statistics_sha256']==b.digest(b.PREVIOUS_DEST/'statistics.json')
    f=s['models'][b.MID]
    assert f['correct']==1154 and f['n']==f['answered']==f['attempts']==1342
    assert f['recoveries']==f['failed']==f['probability_warnings']==0
    assert f['returned_identities']=={'glide_v2':1342} and f['output_token_values']=={'0':1342}
    assert f['dates_toronto']=={'2026-10-23':1342} and f['median_ms']<2000
    assert Decimal(f['cost']['known_decimal'])==Decimal('0.01739196')
    assert f['cost']['source']=='usage_times_published_tariff' and f['cost']['api_reported_usd'] is None
    assert f['original_1136']['correct']==1028 and f['added_206']['correct']==126
    for m in s['models'].values():
        assert sum(v['n'] for v in m['families'].values())==1342
        assert sum(v['correct'] for v in m['families'].values())==m['correct']
        assert math.isclose(m['correct']/1342,m['accuracy'])
    for name,h in manifest['artifacts'].items():
        path=dest/name;assert b.digest(path)==h,name
        assert path.read_bytes()==(root/'docs'/b.NAME/name).read_bytes()
        if path.suffix!='.png':
            inspect=privacy(path.read_text())
            if path.suffix=='.json':inspect(json.loads(path.read_text()))
    for path in (dest/'report.html',root/'docs/report.html'):
        page=Page();page.feed(presentation_source(path).read_text())
        assert page.summary==s['ranked_model_ids']
        assert len(page.cells)==930 and len(page.ids)==len(set(page.ids))
        assert Counter(v['data-model'] for v in page.cells)=={m:31 for m in s['models']}
        for cell in page.cells:
            value=s['models'][cell['data-model']]['families'][cell['data-category']]
            assert (int(cell['data-correct']),int(cell['data-n']))==(value['correct'],value['n'])
            assert b.readable.color(value['accuracy'])[0] in cell['style']
        visible=' '.join(page.text)
        for phrase in ('40,260 first attempts','1154/1342','158/200','second','glide_v2','37.5%'):
            assert phrase in visible,phrase
        assert 'without a prior' not in visible
        for label in b.readable.LABELS.values():assert label in visible,label
        for target in page.links:
            url=urlsplit(target)
            if not url.scheme and not url.netloc:
                if url.path:assert (path.parent/url.path).exists(),target
                elif url.fragment:assert url.fragment in page.ids,target
    with (dest/'category_scores.csv').open() as stream:
        rows=list(csv.DictReader(stream))
    assert len(rows)==31
    for row in rows:
        for model in s['models'].values():assert row[model['label']]==b.readable.score(model['families'][row['category_id']])
    seal=dest/'release_checksums.json'
    if seal.exists():
        values=json.loads(seal.read_text())
        for name,h in values.items():assert b.digest(presentation_source(root/name))==h,name
    from validate_october21_release import validate as previous
    previous()
    print('PASS: Fastino added; 30 complete text routes, 930 exact colored category cells; all 29 earlier records and historical seals unchanged.')
    return s


if __name__=='__main__':
    validate()
