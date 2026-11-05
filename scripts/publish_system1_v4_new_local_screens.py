"""Create a presentation-only successor containing three audited local screens."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--audits', type=Path, nargs=3, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
source, output = args.source.resolve(), args.output.resolve()
if output.exists() or output == source or source in output.parents:
    raise SystemExit('Output must be new and outside the prior release')
audits = [json.loads(p.read_text()) for p in args.audits]
assert [(a['sample_n'], a['usable'], a['correct']) for a in audits] == [(100, 100, 29), (799, 798, 452), (20, 16, 6)]
assert [a['model'] for a in audits] == ['hindsight:hs-decide-1-flash', 'lumma-fev:4b-v2-nf4', 'h2o-lightning:e4b-nf4']
assert len(audits[2]['invalid']) == 4 and all(x['http_status'] == 422 for x in audits[2]['invalid'])
assert [a['reference_correct_same_inputs'] for a in audits] == [{'sage': 74, 'subq': 77}, {'sage': 566, 'subq': 625}, {'sage': 14, 'subq': 15}]
shutil.copytree(source, output)
partial = json.loads((output / 'partial_models.json').read_text())
assert len(partial) == 4
for a, name in zip(audits, ['Hindsight HS-Decide-1 Flash FP16', 'Lumma FEV 4B v2 NF4', 'H2O Lightning E4B NF4']):
    partial.append({'status': 'incomplete_not_in_full_bank_rankings', 'model': name,
                    'provider_model_id': a['model'], 'sample_n': a['sample_n'],
                    'sample_usable': a['usable'], 'sample_correct': a['correct'],
                    'median_usable_ms': a['median_usable_ms'], 'p95_usable_ms': a['p95_usable_ms'],
                    'reference_correct_same_inputs': a['reference_correct_same_inputs'],
                    'stop_reason': a['stop_reason'], 'records_digest_sha256': a['source_records_digest'],
                    'catalog_digest': a['catalog_digest'], 'configuration': a['configuration'],
                    'cost_status': 'local_unmetered'})
(output / 'partial_models.json').write_text(json.dumps(partial, indent=2) + '\n')
notes = '''# Three incomplete local model screens

These sequential GPU screens use the first questions of the same seeded, answer-blind shuffle of the frozen v4 bank. The samples are not stratified, and the runs stopped early under the predetermined reliability or performance rules. They are not full-bank scores or 62% cutoff classifications. SubQ and Sage results below use precisely the same questions, but were collected in different sessions and conditions.

| Model and local precision | Attempts | Usable | Correct | Median usable latency | SubQ / Sage correct on same inputs |
|---|---:|---:|---:|---:|---:|
| Hindsight HS-Decide-1 Flash, FP16 | 100 | 100 | 29 | 273 ms | 77 / 74 |
| Lumma FEV 4B v2, NF4 | 799 | 798 | 452 | 549 ms | 625 / 566 |
| H2O Lightning E4B, NF4 | 20 | 16 | 6 | 930 ms | 15 / 14 |

Hindsight stopped at the 100-question screen because fewer than half were correct. Lumma stopped at 799 attempts when the predetermined Wilson upper-bound rule was met. One Lumma request was unavailable after a server disconnection; it was retained as an unsuccessful attempt and was not replayed. The remaining 798 usable answers were collected across two sessions using the same recorded model digest and configuration.

H2O stopped at the 20-question reliability screen: four inputs were rejected for exceeding the local configuration's 1,024-token limit. The 6/16 usable-answer result is too small to establish full-bank accuracy. No question was truncated or retried. Local NF4 quantization affects H2O's probabilities. Both NF4 configurations are specific local implementations.

All times are client-observed and cover usable answers after warm-up; p95 was 460 ms for Hindsight, 1,262 ms for Lumma, and 2,348 ms for H2O. Local compute and electricity costs were not metered. The local adapter's reported confidence differs from its top returned probability on all 100 Hindsight responses, 791 of 798 Lumma responses, and all 16 usable H2O responses. The selected option matched the highest returned probability for all usable responses; this observation concerns the local adapter and does not establish upstream model behavior.

The full bank has the question-selection and source-key limitations described in the report. Digests, local precision and audit aggregates are in [partial_models.json](partial_models.json).
'''
(output / 'NEW_LOCAL_SCREEN_NOTES.md').write_text(notes)
page = (output / 'report.html').read_text()
anchor = '<p><a href="LOCAL_SCREEN_NOTES.md">Screen methods and context limits</a>'
assert page.count(anchor) == 1
note = ('<p><strong>Additional local screens:</strong> Hindsight FP16: 29/100 correct, 273 ms median. '
        'Lumma v2 NF4: 452/799 attempts correct, one unavailable, 549 ms median on usable answers. '
        'H2O E4B NF4: 6/16 usable answers correct; 4/20 requests exceeded the local 1,024-token limit, '
        '930 ms median on usable answers. These are partial screens, not full-bank scores or cutoff classifications. '
        '<a href="NEW_LOCAL_SCREEN_NOTES.md">Methods and limitations</a>.</p>')
page = page.replace(anchor, note + anchor, 1)
(output / 'report.html').write_text(page)
oldname = source.name
readme = (output / 'README_V4.md').read_text().replace('results/releases/' + oldname + '/', 'results/releases/' + output.name + '/')
anchor = '## Question selection'
assert readme.count(anchor) == 1
note = ('**Further incomplete local screens:** Hindsight FP16: 29/100 correct, 273 ms median; '
        'Lumma v2 NF4: 452/799 attempts correct, including one unavailable request, 549 ms median on usable answers; '
        'H2O E4B NF4: 6/16 usable answers correct and 4/20 requests rejected for the 1,024-token limit, '
        '930 ms median on usable answers. These are partial screens, not full-bank scores or cutoff classifications. '
        f'[Methods and limitations](results/releases/{output.name}/NEW_LOCAL_SCREEN_NOTES.md).\n\n')
readme = readme.replace(anchor, note + anchor, 1)
(output / 'README_V4.md').write_text(readme)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = json.loads((source / 'manifest.json').read_text())
manifest['prior_strike_screen_manifest_sha256'] = sha(source / 'manifest.json')
manifest['presentation_note'] = 'Add three incomplete local screens; prior full-bank results, evidence and graphics remain unchanged.'
manifest['files_sha256'] = {str(p.relative_to(output)): sha(p) for p in sorted(output.rglob('*')) if p.is_file() and p.name != 'manifest.json'}
(output / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
print('Created presentation-only local-screen successor:', output)
