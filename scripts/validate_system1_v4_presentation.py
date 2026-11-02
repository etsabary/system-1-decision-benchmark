"""Check v3 presentation parity, cost visibility and colour bands offline."""
import argparse,hashlib,html,json,re,struct
from decimal import Decimal
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'results/releases/system1_v3_presentation_2026-11-01'
BANDS=['#d8f1e8','#fff4c2','#ffe4ca','#fbdedd']
GRAY='#edf0f2'
MARKS=['🟩','🟨','🟧','🟥']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def band(value,bounds):return next((i for i,x in enumerate(bounds) if Decimal(str(value))<=Decimal(str(x))),3)
def money_cost(c):
 if c['local_unmeasured_count'] or c['known_usd_per_1000'] is None:return None
 v=Decimal(c['known_usd_per_1000'])
 if not v and c['free_access_tariff_count'] and not c['reported_count'] and not c['tariff_estimate_count']:return None
 return band(v,['.01','.025','.05'])
def total(c):
 if c['local_unmeasured_count']:return 'Unmetered local'
 if c['known_subtotal_usd'] is None:return 'Unknown'
 value=Decimal(c['known_subtotal_usd'])
 if not value and c['free_access_tariff_count'] and c['unknown_count']:return 'Free access + ?'
 if not value and c['free_access_tariff_count'] and not c['reported_count'] and not c['tariff_estimate_count']:return 'Free access*'
 return '$'+f'{value:.5f}'+(' + ?' if c['unknown_count'] else '')
def normalized(c):
 if c['local_unmeasured_count']:return 'Unmetered local'
 if c['known_usd_per_1000'] is None:return 'Unknown'
 value=Decimal(c['known_usd_per_1000'])
 if not value and c['free_access_tariff_count'] and c['unknown_count']:return 'Free access + ?'
 return '$'+f'{value:.5f}'+(' + ?' if c['unknown_count'] else '')

def validate(dest):
 manifest=json.loads((dest/'manifest.json').read_text());assert manifest['version']=='v4' and manifest['frozen_v3_manifest_sha256']==sha(SOURCE/'manifest.json')
 actual={str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file() and p.name!='manifest.json'};assert actual==set(manifest['files_sha256'])
 for name,digest in manifest['files_sha256'].items():assert sha(dest/name)==digest,name
 assert len(manifest['unchanged_files_sha256'])>=14
 for name,digest in manifest['unchanged_files_sha256'].items():assert sha(dest/name)==digest,name
 stats=json.loads((dest/'statistics.json').read_text());models=stats['models'];mids=stats['ranked_model_ids'];cost=json.loads((dest/'cost_statistics.json').read_text())['models'];assert len(mids)>0
 page=(dest/'report.html').read_text();readme=(dest/'README_V4.md').read_text()
 assert 'Total known USD' in page and 'USD / 1,000' in page and 'Total known cost' in readme and 'Cost / 1,000' in readme
 assert 'selection bias' in page.lower() and 'original rights holders' in page.lower() and 'mobile-cards' in page
 rows=re.findall(r'<tr data-overall-model="([^"]+)">(.*?)</tr>',page,re.S)
 primary={mid:body for mid,body in rows if 'data-cost-band=' in body};assert set(primary)==set(mids) and len(primary)==len(mids)
 cards=dict(re.findall(r'<article class="mobile-card" data-overall-model="([^"]+)">(.*?)</article>',page,re.S));assert set(cards)==set(mids)
 for mid in mids:
  m=models[mid];c=cost[mid];row=primary[mid];card=cards[mid];sb=[band(m['median_ms'],[250,500,1000]),band(m['p95_ms'],[250,500,1000])];cb=money_cost(c);expected='unknown' if cb is None else str(cb)
  assert re.findall(r'data-speed-band="([^"]+)"',row)==[str(x) for x in sb]
  assert re.findall(r'data-cost-band="([^"]+)"',row)==[expected,expected]
  assert re.findall(r'data-mobile-speed-band="([^"]+)"',card)==[str(x) for x in sb]
  assert re.findall(r'data-mobile-cost-band="([^"]+)"',card)==[expected,expected]
  assert re.findall(r'<td class="cost [^"]*" style="background:([^"]+)"',row)==[GRAY if cb is None else BANDS[cb]]*2
  assert html.escape(total(c)) in row and html.escape(normalized(c)) in row
  lines=[line for line in readme.splitlines() if line.startswith('| '+m['label']+' |')];assert len(lines)==1
  line=lines[0];mark='⬜' if cb is None else MARKS[cb]
  assert MARKS[sb[0]] in line and MARKS[sb[1]] in line and mark+' '+total(c) in line and mark+' '+normalized(c) in line
 for kind in ['accuracy','latency','cost']:
  name='comparison_'+kind+'.png';data=(dest/name).read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n';width,height=struct.unpack('>II',data[16:24]);assert width>=1300 and height>=1600
  assert f'src="comparison_{kind}.png"' in page and name in readme
 print('PASS: v4 input hashes valid; qualifying table rows and mobile cards show correct coloured speed and cost bands; three readable graphs and selection/rights disclosures present.')

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('release',type=Path);args=parser.parse_args();validate(args.release)
