"""Import only a sealed, key-free portable report; no model calls or Git writes.

Usage: python3 publish_consolidated_report.py --bundle PATH --audit-receipt PATH
Repeat builds with no arguments use the imported public bundle.
"""
from repo_layout import repo_file
import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
FOLDER = 'consolidated_2026-10-19'
DEST = repo_file(FOLDER, root=ROOT)
ARTIFACTS = ('report.html', 'report.txt', 'model_statistics.csv', 'family_statistics.csv',
             'function_guide.csv', 'statistics.json', 'plot_data.json',
             'questions_1342.csv', 'questions_1342.jsonl', 'questions_1342.txt',
             'accuracy_speed_cost.png', 'accuracy_speed_cost.svg',
             'family_profile.png', 'family_profile.svg', 'decision_domains.png', 'decision_domains.svg')
MARKER = '<meta name="benchmark-cohort" content="october19-consolidated-1342">'
REPO = 'https://github.com/etsabary/jev-1.14-comparison-benchmark'
SITE = 'https://etsabary.github.io/jev-1.14-comparison-benchmark/'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def table(headers, rows):
    def line(row):
        return '| ' + ' | '.join(str(c).replace('|', '\\|').replace('\n', ' ') for c in row) + ' |\n'
    return line(headers) + line(['---'] * len(headers)) + ''.join(line(r) for r in rows)


def archive_references():
    manifest = json.loads((repo_file('publication_archive_2026-10-19/manifest.json', root=ROOT)).read_text())
    targets = {'README.md': 'REFERENCE_1136.md', 'FUNCTIONS.md': 'REFERENCE_1136_FUNCTIONS.md',
               'OUTPUT_COMPLIANCE.md': 'REFERENCE_1136_OUTPUT_COMPLIANCE.md',
               'LLM_EXPANSION.md': 'REFERENCE_1136_LLM_EXPANSION.md'}
    for original, target in targets.items():
        text = (repo_file('publication_archive_2026-10-19', root=ROOT) / manifest['files'][original]['archive_path']).read_text()
        for old, new in targets.items():
            text = text.replace('](' + old, '](' + new)
        write(repo_file(target, root=ROOT), '> Earlier 1,136-question reference, not the current 1,342-question ranking. [Current report](README.md).\n\n' + text)
    pages = {'index.html': 'reference_1136.html', 'functions.html': 'reference_1136_functions.html',
             'output_compliance.html': 'reference_1136_output_compliance.html'}
    for original, target in pages.items():
        text = (repo_file('publication_archive_2026-10-19', root=ROOT) / manifest['files']['docs/' + original]['archive_path']).read_text()
        for old, new in pages.items():
            text = text.replace('href="' + old, 'href="' + new)
        text = text.replace('<body>', '<body><p style="padding:16px;background:#fff5df">Earlier 1,136-question reference. These scores are not the expanded ranking. <a href="index.html">Current 1,342-question report</a>.</p>', 1)
        write(repo_file('docs', root=ROOT) / target, text)


def import_bundle(bundle, receipt):
    assert not DEST.exists(), 'Never overwrite a previously imported bundle'
    source = json.loads((bundle / 'manifest.json').read_text())
    assert set(source['artifacts']) == set(ARTIFACTS)
    assert source['question_count'] == 1342 and source['model_count'] == 20
    assert source['question_export_without_key_access'] is True
    for name in ARTIFACTS:
        assert digest(bundle / name) == source['artifacts'][name], name
    audit = json.loads(receipt.read_text())
    assert audit['status'] == 'PASS_FINAL_CONSOLIDATED_REPORT'
    assert audit['active_summary_sha256'] == source['source_summary_sha256']
    assert audit['report_manifest_sha256'] == digest(bundle / 'manifest.json')
    assert audit['csv_and_plot_payloads_match_summary'] is True
    assert audit['independently_audited_statistical_payload_unchanged'] is True
    assert audit['answer_key_or_item_correctness_exported'] is False
    DEST.mkdir()
    for name in ARTIFACTS:
        shutil.copyfile(bundle / name, DEST / name)
    old = 'The active graphics, aggregate exports, answer-free question downloads and source-bound evidence are local. No GitHub push, publication, image-benchmark modification or further inference occurred.'
    new = 'The public bundle contains the consolidated graphics, aggregate statistics and all answer-free question inputs. The separate image benchmark is unchanged. No new inference was performed for this consolidation.'
    for name in ('report.html', 'report.txt'):
        text = (DEST / name).read_text()
        assert text.count(old) == 1
        text = text.replace(old, new).replace('No publication occurred.', 'Answer keys and private verification material are not published.')
        if name.endswith('.html'):
            text = text.replace('<head>', '<head>' + MARKER, 1)
            text = text.replace('href="' + REPO + '">1,136-question comparison',
                                'href="' + SITE + 'reference_1136.html">1,136-question comparison')
        write(DEST / name, text)
    stats = json.loads((DEST / 'statistics.json').read_text())
    stats['limits'][-1] = 'No new model calls, unchanged question reruns or model removals. This is a public developmental overview, not a held-out release.'
    write(DEST / 'statistics.json', json.dumps(stats, indent=2) + '\n')
    audit.pop('publication')
    audit['scope'] = 'Sanitized receipt of the private independent raw-evidence audit; public aggregate checks do not reproduce answer-key scoring or raw-latency pooling.'
    write(DEST / 'audit_receipt.json', json.dumps(audit, indent=2) + '\n')
    manifest = {k: v for k, v in source.items() if k not in ('published', 'artifacts')}
    manifest.update(release_date='2026-10-19', publication_target=REPO, source_artifacts=source['artifacts'],
                    source_manifest_sha256=digest(bundle / 'manifest.json'),
                    source_receipt_sha256=digest(receipt),
                    transformations=['Publication wording and earlier-reference link updated.', 'Added cohort marker.',
                                     'Removed obsolete no-publication limit; all numerical statistics and question inputs unchanged.'],
                    artifacts={name: digest(DEST / name) for name in (*ARTIFACTS, 'audit_receipt.json')})
    write(DEST / 'manifest.json', json.dumps(manifest, indent=2) + '\n')


def build():
    from build_october18_report import format_speed, format_cost, legend_markdown
    archive_references()
    s = json.loads((DEST / 'statistics.json').read_text())
    order = s['ranked_model_ids']
    sections = (DEST / 'report.txt').read_text().split('\n\n')
    readme = '# 20 decision models on 1,342 text questions\n\nUpdated October 19, 2026. Tests October 15 to 19, 2026.\n\n'
    readme += '**Respan Span-02 leads with 1,127/1,342 (84.0%), followed by Perplexity Decider v1.2 at 1,120 (83.5%) and Nimble Max at 1,115 (83.1%).**\n\n'
    readme += 'One combined bank across 31 categories, with five choices per question. [Interactive report](' + SITE + ') · [Full plain-text analysis](' + FOLDER + '/report.txt) · [All function scores](FUNCTIONS.md).\n\n'
    readme += '![Combined accuracy, median/p95 and cost](' + FOLDER + '/accuracy_speed_cost.png)\n\n'
    readme += '## Results, speed and cost\n\nEvery row covers all 1,342 first attempts. Provider failures remain unsuccessful. Median and p95 pool the individual first-attempt times, not stage medians. Costs include permitted recoveries and retain their captured tariffs. `+ ?` means unreported additional charges; `~` marks tariff-based accounting. Costs per 1,000 are normalized, not the actual number of questions tested.\n\n'
    rows = []
    for mid in order:
        v = s['models'][mid]; c = v['cost']
        rows.append([v['label'], v['correct'], f"{100*v['accuracy']:.1f}%", format_speed(v['median_ms']),
                     f"{v['p95_ms']:.0f} ms", ('~' if mid == 'nimble_v4_max' else '') + format_cost(c['known_usd_per_1000'], c['unknown_attempts']),
                     ', '.join(v['dates_toronto'])])
    readme += table(['Model', 'Correct / 1,342', 'Accuracy', 'Median', 'p95', 'Cost per 1,000', 'Test dates'], rows)
    readme += '\n' + legend_markdown().replace('each actual 1,136-question run', 'each actual 1,342-question run') + '\n'
    for part in sections:
        title, sep, text = part.partition('\n')
        if title in ('WHAT THIS MEASURES', 'SPAN LEADS THE COMBINED BANK', 'TYPICAL SPEED AND TAIL SPEED TELL DIFFERENT STORIES',
                     'SEQUENTIAL STATE UPDATES AND TRUTH COUNTING REMAIN DISCRIMINATING', 'THE OVERALL LEADER IS NOT STRONGEST IN EVERY FUNCTION',
                     'UNCERTAINTY AND SYSTEM CONSTRAINTS CHANGE THE FUNCTIONAL PICTURE', 'JEV, LUNA AND A LOWER-COST NATIVE ALTERNATIVE'):
            heading = 'Jev, Luna and a lower-cost native alternative' if title.startswith('JEV, LUNA') else title.capitalize()
            readme += '## ' + heading + '\n\n' + text + '\n\n'
    readme += '![All 31 function profiles](' + FOLDER + '/family_profile.png)\n\n![Uncertainty, strategy and system decisions](' + FOLDER + '/decision_domains.png)\n\n'
    readme += '## Questions and statistics\n\n'
    readme += 'All **1,342 questions**, facts and five choices retain their tested order. The JSONL also preserves exact model-independent native input packets and hashes. No answer keys, item-level correctness, certificates, verifier responses or private author metadata are published.\n\n'
    readme += '- Questions: [CSV](' + FOLDER + '/questions_1342.csv), [JSONL](' + FOLDER + '/questions_1342.jsonl), [readable text](' + FOLDER + '/questions_1342.txt).\n'
    readme += '- Statistics: [model CSV](' + FOLDER + '/model_statistics.csv), [function CSV](' + FOLDER + '/family_statistics.csv), [aggregate JSON](' + FOLDER + '/statistics.json), [plot data](' + FOLDER + '/plot_data.json).\n'
    readme += '- [Request failures and output compliance](OUTPUT_COMPLIANCE.md), [release manifest](' + FOLDER + '/manifest.json), [sanitized audit receipt](' + FOLDER + '/audit_receipt.json).\n\n'
    readme += '## Method and construction note\n\n' + (DEST / 'report.txt').read_text().split('METHOD AND CONSTRUCTION NOTES\n', 1)[1].replace('\n', '\n\n') + '\n'
    readme += 'The 37 author-development cases remain permanently excluded from a future held-out scored release. This public developmental overview does not claim a held-out score. Publication checks validate exported consistency and privacy; the sanitized audit receipt records a separate private raw-evidence check. The public aggregates alone cannot reproduce answer-key scoring or raw-latency quantiles.\n\n'
    readme += '## Earlier LLM comparison and image benchmark\n\nThe [36-model, 1,136-question reference](REFERENCE_1136.md) remains available with its measurements, analysis, raw evidence and unchanged release seals. Sixteen regular LLM configurations have no complete expanded coverage, so they are not assigned a 1,342-question score or mixed into this ranking. The [image benchmark](https://github.com/etsabary/visual-decision-benchmark) is unchanged.\n\n'
    readme += '## Offline publication checks\n\nRun `python3 validate_consolidated_release.py` and `python3 -m unittest test_consolidated_publication test_corrected_release`. These make no model calls. `publish_consolidated_report.py` rebuilds the presentation from the imported key-free bundle. Earlier report builders describe superseded releases and must not overwrite the current presentation.\n'
    write(repo_file('README.md', root=ROOT), readme)
    with (DEST / 'function_guide.csv').open(newline='') as f:
        guide = list(csv.DictReader(f))
    definitions = [list(r.values()) for r in guide]
    funcs = '# All 31 text decision functions\n\nAll 20 rows in the current ranking cover all 1,342 questions. [Overall results](README.md). The six F26-F31 functions have eight questions each; one answer changes a category score by 12.5 percentage points.\n\n'
    funcs += table(['ID', 'Function', 'What it tests', 'Simple illustration', 'Questions'], definitions) + '\n'
    funcs += table(['Function', 'Questions'] + [s['models'][m]['label'] for m in order],
                   [[f['family_id'] + ' ' + f['family'], f['n']] + [f['models'][m]['correct'] for m in order] for f in s['families']])
    funcs += '\nCells are correct decisions, not percentages. [Machine-readable function statistics](' + FOLDER + '/family_statistics.csv). [Earlier 1,136-question LLM function comparison](REFERENCE_1136_FUNCTIONS.md).\n'
    write(repo_file('FUNCTIONS.md', root=ROOT), funcs)
    quality = '# Delivered decisions and request failures\n\n[Current overall comparison](README.md). All rates retain 1,342 first attempts per route. A failed request is not classified as a wrong reasoning answer. Only transport failures or HTTP 408/429/5xx permit one recovery; a valid wrong choice or explanatory output is not retried. Recoveries do not replace the primary score or timing.\n\n'
    quality += table(['Model', 'Usable first', 'Wrong valid', 'Provider failures', 'Output failures', 'Recoveries', 'Eventual correct'],
                     [[v['label'], v['answered'], v['wrong_valid'], v['provider_failures'], v['model_output_failures'], v['recoveries'], v['eventual']['correct']] for m in order for v in [s['models'][m]]])
    quality += '\nSolar Decide remains excluded for latency. The distinct Solar Decide Flash is included. The [earlier compliance report](REFERENCE_1136_OUTPUT_COMPLIANCE.md) retains noncompliant runs, stopped LLM screens and compatibility probes outside the matched full-bank ranking.\n'
    write(repo_file('OUTPUT_COMPLIANCE.md', root=ROOT), quality)
    write(repo_file('LLM_EXPANSION.md', root=ROOT), '# Regular LLM coverage\n\nThe current [1,342-question comparison](README.md) covers 20 complete decision configurations. Sixteen regular LLM configurations have only the earlier 1,136 questions and are not extrapolated. Read the [earlier complete LLM comparison](REFERENCE_1136.md) and [earlier LLM expansion analysis](REFERENCE_1136_LLM_EXPANSION.md).\n')
    pages = repo_file('docs', root=ROOT) / FOLDER
    pages.mkdir(parents=True, exist_ok=True)
    for path in DEST.iterdir():
        if path.is_file() and path.name != 'release_checksums.json':
            shutil.copyfile(path, pages / path.name)
    for name, anchor in (('index.html', ''), ('functions.html', '#functions'), ('output_compliance.html', '#quality')):
        target = FOLDER + '/report.html' + anchor
        write(repo_file('docs', root=ROOT) / name, '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' + MARKER + '<meta http-equiv="refresh" content="0;url=' + target + '"><title>Text decision benchmark: 1,342 questions</title></head><body><p><a href="' + target + '">Open the current 1,342-question benchmark</a></p><p><a href="reference_1136.html">Earlier 1,136-question LLM reference</a></p></body></html>\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path)
    parser.add_argument('--audit-receipt', type=Path)
    args = parser.parse_args()
    if args.bundle:
        assert args.audit_receipt
        import_bundle(args.bundle.resolve(), args.audit_receipt.resolve())
    build()
    print('Prepared public 1342-question presentation; no inference or Git operation')
