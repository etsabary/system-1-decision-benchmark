"""Add the audited Strike partial screen beside the below-cutoff catalogue."""
import argparse, hashlib, json, shutil
from pathlib import Path

NAME = 'system1_v4_strike_screen_2026-11-04'
parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--audit', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
source, output = args.source.resolve(), args.output.resolve()
if output.exists() or output == source or source in output.parents:
    raise SystemExit('Output must be new and outside the prior release')
audit = json.loads(args.audit.read_text())
assert audit['model'] == 'strike-1' and audit['complete_100']
assert (audit['sample_n'], audit['valid'], audit['correct']) == (100, 100, 57)
assert audit['reference_same_inputs'] == {'subq': 77, 'sage': 74, 'this_that': 32}
assert audit['probability_choice_mismatch_count'] == 0
assert audit['reported_charge_count'] == 100 and float(audit['reported_charges_eur']) == 0
plan = [json.loads(line) for line in (args.audit.parent / 'plan.jsonl').read_text().splitlines() if line]
assert len(plan) == 100
record_hashes = [hashlib.sha256((args.audit.parent / 'jobs' / row['id'] / 'result.json').read_bytes()).hexdigest()
                 for row in plan]
records_digest = hashlib.sha256(json.dumps(record_hashes, sort_keys=True, ensure_ascii=False,
                                          separators=(',', ':'), allow_nan=False).encode()).hexdigest()
shutil.copytree(source, output)
partial = json.loads((output / 'partial_models.json').read_text())
assert len(partial) == 3
partial.append({'status': 'incomplete_not_in_full_bank_rankings', 'model': 'Strike 1',
                'provider_model_id': 'strike-1', 'catalogue_revision_at_start': audit['catalogue_weights_revision'],
                'identity_limit': 'Provider-reported catalogue revision; no immutable weights hash in responses.',
                'sample_n': 100, 'sample_usable': 100, 'sample_correct': 57,
                'subq_correct_on_same_inputs': 77, 'sage_correct_on_same_inputs': 74,
                'median_ms': audit['median_ms'], 'p95_ms': audit['p95_ms'],
                'input_tokens': audit['input_tokens'], 'reported_charge_eur': audit['reported_charges_eur'],
                'reported_charge_count': audit['reported_charge_count'],
                'records_digest_sha256': records_digest,
                'sample_method': audit['selection'],
                'post_screen_catalogue_http_status': 402,
                'post_screen_catalogue_note': 'After the screen, a read-only catalogue request returned payment_required; whether the free allowance resets was not established.'})
(output / 'partial_models.json').write_text(json.dumps(partial, indent=2) + '\n')
case = '''# Strike 1: incomplete free-tier screen

Strike 1 answered **57 of 100 questions correctly**. All 100 responses were usable. On the same inputs, SubQ Snap 1.1 answered **77/100** correctly and Levanto Sage 2 answered **74/100** correctly. These are paired, answer-blind results on the first 100 questions of a seeded shuffle of the frozen v4 bank; the sample is not stratified. It is a partial screen, not a 2,157-question result or a 62% cutoff classification. The user's instruction was to stop after these 100 questions.

The median client-observed response time was **626.22 ms**, with a **1,423.54 ms p95**. All 100 responses reported a zero EUR charge; they used 105,360 input tokens. Responses were collected sequentially through Strike's direct API. The compared models were tested in different sessions and conditions, so the timings are not a controlled head-to-head measurement.

At the start, the provider's catalogue identified `strike-1` as revision `v20261102`; responses identified `strike-1` without an independently verifiable weights hash. After the screen, a read-only catalogue request returned HTTP 402 and `payment_required` with a no-credits message. This observation does not establish whether the advertised free allowance will reset. No extra model answers were requested after the screen.

The full bank has known question-selection and source-key limitations described in the main report. Aggregate screen information is in [partial_models.json](partial_models.json).
'''
(output / 'STRIKE_SCREEN_NOTES.md').write_text(case)
page = (output / 'report.html').read_text()
anchor = '<div class="note" data-incomplete-model="hanzo-kai">'
assert page.count(anchor) == 1
note = ('<div class="note" data-incomplete-model="strike-1"><strong>Strike 1 — incomplete 100-question screen:</strong> '
        '57/100 correct (57%); SubQ scored 77/100 and Sage 2 scored 74/100 on the same inputs. '
        'Median response time was 626 ms. <strong>This is not a full-bank score or a 62% cutoff classification.</strong> '
        'All 100 responses reported zero EUR charges. '
        '<a href="STRIKE_SCREEN_NOTES.md">Screen method and details</a> · <a href="partial_models.json">Partial-test data</a>.</div>')
page = page.replace(anchor, note + anchor, 1)
(output / 'report.html').write_text(page)
readme = (output / 'README_V4.md').read_text().replace('results/releases/system1_v4_local_screens_2026-11-02/', 'results/releases/' + NAME + '/')
anchor = '**Hanzo Kai 1.9 — stopped partial test:**'
assert readme.count(anchor) == 1
note = (f'**Strike 1 — incomplete 100-question screen:** 57/100 correct (57%); SubQ scored 77/100 and '
        f'Sage 2 scored 74/100 on the same inputs. Median response time was 626 ms; all responses reported zero EUR charges. '
        f'This is not a full-bank score or a 62% cutoff classification. '
        f'[Screen method and details](results/releases/{NAME}/STRIKE_SCREEN_NOTES.md).\n\n')
readme = readme.replace(anchor, note + anchor, 1)
(output / 'README_V4.md').write_text(readme)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest = json.loads((source / 'manifest.json').read_text())
manifest['prior_local_screens_manifest_sha256'] = digest(source / 'manifest.json')
manifest['presentation_note'] = 'Add incomplete Strike screen; prior full-bank results, evidence and graphics remain unchanged.'
manifest['files_sha256'] = {str(p.relative_to(output)): digest(p) for p in sorted(output.rglob('*')) if p.is_file() and p.name != 'manifest.json'}
(output / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
print(json.dumps({'output': str(output), 'strike_sample': '57/100', 'full_bank_models': 29}))
