"""Public offline checks: counts, exact colored cells, privacy and old seals."""
from collections import Counter
import csv
from decimal import Decimal
import json
import math
import re
from urllib.parse import urlsplit

import publish_opus5_reference as b
from validate_consolidated_release import privacy
from validate_direct_release import Page


def validate():
    s = json.loads((b.DEST/'statistics.json').read_text())
    old = json.loads((b.previous.DEST/'statistics.json').read_text())
    manifest = json.loads((b.DEST/'manifest.json').read_text())
    assert (s['model_count'],s['decision_model_count'],len(s['reference_model_ids']),s['primary_cases']) == (31,27,4,41602)
    assert all(s['models'][mid] == m for mid,m in old['models'].items()), 'An earlier measurement changed'
    assert s['ranked_model_ids'] == sorted(s['models'],key=lambda mid:(-s['models'][mid]['correct'],mid))
    assert s['ranked_model_ids'][:3] == ['fastino_glide','reference_sol','mammoth1']
    o = s['models'][b.MID]
    assert o['n'] == o['attempts'] == 1342 and o['correct'] == 1109 and o['answered'] == 1305
    assert o['first_statuses'] == {'ok':1305,'refusal':37} and o['recoveries'] == 0
    assert o['reasoning_token_counts'] == {'0':1307,'None':35}
    assert o['reasoning_text_responses'] == 0 and o['cost']['unknown_attempts'] == 35
    assert Decimal(o['cost']['known_decimal']) == Decimal('4.641065')
    assert o['matched_original_1136']['correct'] == 1001 and o['added_206']['correct'] == 108
    assert o['families']['F08']['correct'] == 66 and o['families']['F13']['correct'] == 18
    assert o['dates_toronto'] == {'2026-10-23':1342} and o['median_ms'] < 2000
    assert math.isclose(o['median_ms'],1537.6197495061206) and math.isclose(o['p95_ms'],2109.479128840758)
    assert manifest['prior_statistics_sha256'] == b.digest(b.previous.DEST/'statistics.json')
    assert manifest['bank_sha256'] == s['question_bank_sha256'] == b.digest(b.run.native.base.BANK)
    for m in s['models'].values():
        assert sum(v['n'] for v in m['families'].values()) == 1342
        assert sum(v['correct'] for v in m['families'].values()) == m['correct']
        assert math.isclose(m['correct']/1342,m['accuracy'])
    for name,h in manifest['artifacts'].items():
        path = b.DEST/name
        assert b.digest(path) == h,name
        assert path.read_bytes() == (b.ROOT/'docs'/b.NAME/name).read_bytes()
        if path.suffix != '.png':
            inspect = privacy(path.read_text())
            if path.suffix == '.json': inspect(json.loads(path.read_text()))
    for path in (b.DEST/'report.html',b.ROOT/'docs/report.html'):
        page = Page(); page.feed(path.read_text())
        assert page.summary == s['ranked_model_ids']
        assert len(page.cells) == 961 and len(page.ids) == len(set(page.ids))
        assert Counter(c['data-model'] for c in page.cells) == {m:31 for m in s['models']}
        for c in page.cells:
            value = s['models'][c['data-model']]['families'][c['data-category']]
            assert (int(c['data-correct']),int(c['data-n'])) == (value['correct'],value['n'])
            assert b.readable.color(value['accuracy'])[0] in c['style']
        visible = ' '.join(page.text)
        for phrase in ('41,602 first attempts','1109/1342','82.6%','35','refusals','JSON-choice','66/67'):
            assert phrase in visible,phrase
        assert 'without a prior' not in visible
        for label in b.readable.LABELS.values(): assert label in visible,label
        for target in page.links:
            url = urlsplit(target)
            if not url.scheme and not url.netloc:
                if url.path: assert (path.parent/url.path).exists(),target
                elif url.fragment: assert url.fragment in page.ids,target
    with (b.DEST/'category_scores.csv').open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 31
    for row in rows:
        for m in s['models'].values(): assert row[m['label']] == b.readable.score(m['families'][row['category_id']])
    with (b.DEST/'model_statistics.csv').open() as stream:
        rows = list(csv.DictReader(stream))
    assert [r['model_id'] for r in rows] == s['ranked_model_ids']
    for r in rows:
        m = s['models'][r['model_id']]
        assert int(r['correct']) == m['correct'] and float(r['median_ms']) == m['median_ms']
    for path in (b.ROOT/'README.md',b.repo_file('FUNCTIONS.md'),b.repo_file('OUTPUT_COMPLIANCE.md')):
        text = path.read_text();privacy(text)
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if not re.match(r'^(https?:|mailto:|#)',target): assert (path.parent/target.split('#')[0]).exists(),target
    from validate_fastino_2026_10_23 import validate as previous
    previous()
    print('PASS: Opus5 added,31 complete routes,961 exact category cells; all30 previous records and old seals unchanged.')
    return s


if __name__ == '__main__':
    validate()
