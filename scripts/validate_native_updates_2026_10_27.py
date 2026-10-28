"""Public checks of October27 coverage, timing, costs, cells and preservation."""
from collections import Counter,defaultdict
from decimal import Decimal
import csv,json,math,random,statistics
from pathlib import Path
import publish_native_updates_2026_10_27 as b
from october27_text_evidence import payload,packet
from validate_direct_release import Page
from validate_consolidated_release import privacy

def validate():
    s=json.loads((b.DEST/'statistics.json').read_text());old=json.loads((b.PREVIOUS/'statistics.json').read_text())
    assert (s['model_count'],s['primary_cases'],s['hosted_decision_model_count'],s['local_model_count'])==(54,72468,30,20)
    assert len(s['reference_model_ids'])==4 and s['decision_model_count']==50
    assert all(s['models'][m]==v for m,v in old['models'].items())
    assert set(s['models'])-set(old['models'])=={'d3_ultra','liquid11_decision'}
    assert s['ranked_model_ids']==sorted(s['models'],key=lambda m:(-s['models'][m]['correct'],m))
    qq={q['id']:q for q in [json.loads(x) for x in (b.ROOT/'results/releases/consolidated_2026-10-19/questions_1342.jsonl').read_text().splitlines()]}
    order=list(qq);random.Random(2026101906).shuffle(order)
    rr=list(csv.DictReader((b.DEST/'october27_timing_evidence.csv').open()));assert len(rr)==2684
    grouped=defaultdict(list)
    for r in rr:
        grouped[r['model_id']].append(r);q=qq[r['item_id']]
        assert r['status']=='ok' and r['attempt']=='1' and r['output_tokens']=='0'
        assert r['native_input_sha256']==q['native_input_sha256'] and r['family_id']==q['family_id']
        assert r['request_payload_sha256']==packet(payload(q,'d3_ultra' if r['model_id']=='d3_ultra' else 'liquid11'))
    for mid,correct in [('d3_ultra',1124),('liquid11_decision',1044)]:
        m=s['models'][mid];aa=grouped[mid];assert len(aa)==1342 and [r['item_id'] for r in aa]==order
        assert len({r['item_id'] for r in aa})==1342 and m['correct']==correct and m['answered']==1342 and m['recoveries']==0
        xx=sorted(float(r['latency_ms']) for r in aa);pos=1341*.95;lo=int(pos)
        assert math.isclose(m['mean_response_ms'],statistics.mean(xx),rel_tol=1e-12)
        assert m['median_ms']==statistics.median(xx) and math.isclose(m['p95_ms'],xx[lo]+(xx[lo+1]-xx[lo])*(pos-lo),rel_tol=1e-12)
        assert sum(f['n'] for f in m['families'].values())==1342 and sum(f['correct'] for f in m['families'].values())==correct
        assert m['dates_toronto']=={'2026-10-27':1342} and m['release_exclusion_diagnostic']['n']==1305
    assert s['models']['d3_ultra']['cost']['public_free_access'] and s['models']['d3_ultra']['cost']['known_usd'] is None
    total=sum((Decimal(r['reported_cost_usd']) for r in grouped['liquid11_decision']),Decimal(0))
    assert total==Decimal('.00774762')==Decimal(s['models']['liquid11_decision']['cost']['known_decimal'])
    assert s['models']['liquid11_decision']['admission_cost_usd']=='0.0000024'
    for name in ('local_models.json','local_model_metadata.json','local_timing_evidence.csv','screened_routes.json','historical_admission_resolutions.json','hosted_addition_timing_evidence.csv'):
        assert (b.DEST/name).read_bytes()==(b.PREVIOUS/name).read_bytes()
    # The live page advances; the dated report remains the validation authority.
    for path in (b.DEST/'report.html',):
        text=path.read_text();page=Page();page.feed(text)
        assert page.summary==s['ranked_model_ids'] and len(page.cells)==1674
        for c in page.cells:
            f=s['models'][c['data-model']]['families'][c['data-category']]
            assert (int(c['data-correct']),int(c['data-n']))==(f['correct'],f['n'])
            assert b.readable.color(f['accuracy'])[0] in c['style']
        assert 'without a prior' not in ' '.join(page.text)
        for phrase in ('54 routes','30 hosted','72,468','D3 Ultra','Liquid d1.1','1124/1342','1044/1342','chosen deliberately'):
            assert phrase in text,phrase
    svg=(b.DEST/'accuracy_speed_cost.svg').read_text()
    assert all(x in svg for x in ('D3 Ultra','Liquid d1.1','#7c3aed','#16728c','fill-opacity: 0.6','54 routes'))
    for p in b.DEST.iterdir():
        if p.is_file():assert p.read_bytes()==(b.ROOT/'docs'/b.NAME/p.name).read_bytes(),p.name
        if p.suffix in ('.json','.csv','.md','.html','.svg','.txt'):
            t=p.read_text();privacy(t)
            for token in ('192.168.','/Users/','"choice":','"correct_option_id":','"probabilities":'):assert token not in t,(p.name,token)
    manifest=json.loads((b.DEST/'manifest.json').read_text())
    for name,h in manifest['artifacts'].items():assert b.digest(b.DEST/name)==h,name
    from validate_native_additions_2026_10_25 import validate as historical
    historical()
    print('PASS:54 text routes;2684 new first attempts;1674 category cells;52 old model records exact')
    return s

if __name__=='__main__':validate()
