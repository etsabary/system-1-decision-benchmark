"""Publish two audited incomplete local screens without changing full-bank data."""
import argparse, hashlib, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = 'system1_v4_local_screens_2026-11-02'
parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--audits', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
source, output = args.source.resolve(), args.output.resolve()
if output.exists() or output == source or source in output.parents:
    raise SystemExit('Output must be new and outside the previous release')
def read(folder):
    return json.loads((args.audits / folder / 'audit_summary_PRIVATE.json').read_text())
tt = read('this_that_1_2_fp16')
gl = read('gliner25_decide_fp32')
assert (tt['n'], tt['usable'], tt['correct'], tt['subq_correct_same_inputs']) == (100, 100, 32, 77)
assert (gl['n'], gl['usable'], gl['correct'], len(gl['invalid'])) == (20, 14, 4, 6)
assert tt['stop_reason'] == 'accuracy_below_50_percent'
assert gl['stop_reason'] == 'unusable_fraction_at_least_5_percent'
assert all(x['http_status'] == 422 and 'exceed 512 tokens' in x['body']['error'] for x in gl['invalid'])
shutil.copytree(source, output)
partial = json.loads((output / 'partial_models.json').read_text())
assert len(partial) == 1 and partial[0]['model'] == 'Hanzo Kai 1.9'
for x, label, precision, limit in [(tt, 'THIS/THAT 1.2', 'FP16 (source BF16)', 2048),
                                   (gl, 'GLiNER2.5-Decide', 'FP32', 512)]:
    partial.append({'status': 'incomplete_not_in_full_bank_rankings', 'model': label,
                    'local_model_id': x['model'], 'precision': precision, 'device': 'CUDA GPU',
                    'server_input_limit_tokens': limit, 'model_catalog_digest': x['catalog_digest'],
                    'source_revision': x['configuration']['local.source_revision'],
                    'sample_n': x['n'], 'sample_usable': x['usable'], 'sample_correct': x['correct'],
                    'subq_correct_on_same_inputs': x['subq_correct_same_inputs'],
                    'sage_correct_on_same_inputs': x['sage_correct_same_inputs'],
                    'median_usable_ms': x['median_usable_ms'], 'stopping_reason': x['stop_reason'],
                    'sample_method': 'Answer-blind seeded shuffle, sequential first responses; partial unstratified sample.',
                    'records_digest_sha256': x['source_records_digest'], 'cost': 'unmetered local'})
(output / 'partial_models.json').write_text(json.dumps(partial, indent=2) + '\n')
case = '''# Local model screens: incomplete results

Both models were tested sequentially on the same frozen System 1 v4 inputs, in an answer-blind seeded shuffle. The first returned model answer was retained. One non-benchmark readiness call warmed each model; the reported times include the LAN and client overhead. GPU use is local and electricity and hardware cost were not measured. These partial, unstratified screens are not 2,157-question results or 62% cutoff classifications.

## THIS/THAT 1.2

The local `this-that:1.2` deployment used FP16 (source BF16), a CUDA GPU and a 2,048-token input limit. It answered 32 of the first 100 questions correctly, with all 100 responses usable and a 281.88 ms median. SubQ answered 77/100 on those identical inputs; Sage 2 answered 74/100. The screen stopped at 100 because its accuracy was below the requested 50% threshold. Local model digest and source revision are recorded in `partial_models.json`.

## GLiNER2.5-Decide

The local `gliner2.5:decide` deployment used FP32, a CUDA GPU and a 512-token server limit. Among the first 20 attempts, 14 produced usable answers and 4 were correct. Six requests returned HTTP 422 because their full rendered inputs exceeded 512 tokens; their stated lengths were 723, 821, 930, 959, 1,129 and 1,999 tokens. The screen stopped at 20 because 30% of requests were unusable, exceeding the 5% stopping rule. SubQ answered 15/20 and Sage 2 14/20 on the same 20 inputs. Its median was 115.63 ms across the 14 usable answers only; this is not an all-input latency measure.

No rejected input was shortened or retried, and no partial result was put into the full-bank leaderboard. A future run with a different input limit must identify that configuration separately. `partial_models.json` records the local model identifiers, precision, revisions, digests and stopping reasons.
'''
(output / 'LOCAL_SCREEN_NOTES.md').write_text(case)
page = (output / 'report.html').read_text()
anchor = '<section id="legend">'
assert page.count(anchor) == 1
note = ('<section id="local-screens"><h2>Incomplete local screens</h2><p>These answer-blind partial screens stopped early and are not full-bank scores or cutoff classifications.</p>'
        '<ul><li><strong>THIS/THAT 1.2 · FP16:</strong> 32/100 correct; all 100 usable; median 282 ms. '
        'Stopped at the 50% accuracy screen. SubQ scored 77/100 on the same inputs.</li>'
        '<li><strong>GLiNER2.5-Decide · FP32, 512-token limit:</strong> 4 correct of 14 usable answers, '
        'with 6 of 20 requests rejected for length. Median 116 ms on usable answers only. '
        'Stopped after the 20-question unusable-response screen.</li></ul>'
        '<p><a href="LOCAL_SCREEN_NOTES.md">Screen methods and context limits</a> · '
        '<a href="partial_models.json">Partial-screen data</a></p></section>')
page = page.replace(anchor, note + anchor, 1)
(output / 'report.html').write_text(page)
readme = (output / 'README_V4.md').read_text().replace('results/releases/system1_v4_sage_2026-11-02/', 'results/releases/' + NAME + '/')
anchor = '## Question selection\n\n'
assert readme.count(anchor) == 1
note = (f'**Additional incomplete local screens:** THIS/THAT 1.2 (FP16) stopped at 32/100 correct, with a 282 ms median; '
        f'SubQ scored 77/100 on the same inputs. GLiNER2.5-Decide (FP32, 512-token limit) stopped after '
        f'4 correct of 14 usable answers and 6 length rejections in 20 attempts; its 116 ms median covers usable answers only. '
        f'These partial screens are not full-bank scores or cutoff classifications. '
        f'[Screen methods and limits](results/releases/{NAME}/LOCAL_SCREEN_NOTES.md).\n\n')
readme = readme.replace(anchor, note + anchor, 1)
(output / 'README_V4.md').write_text(readme)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest = json.loads((source / 'manifest.json').read_text())
manifest['prior_sage_manifest_sha256'] = digest(source / 'manifest.json')
manifest['presentation_note'] = 'Add two incomplete local screens; all full-bank statistics, evidence and graphics are unchanged.'
manifest['files_sha256'] = {str(p.relative_to(output)): digest(p) for p in sorted(output.rglob('*')) if p.is_file() and p.name != 'manifest.json'}
(output / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
print(json.dumps({'output': str(output), 'full_bank_models': 29, 'partial_screens_added': 2}))
