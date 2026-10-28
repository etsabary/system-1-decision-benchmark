"""Offline public-export checks, not a substitute for the private scoring audit."""
from repo_layout import logical_relative, repo_file
from collections import Counter
import csv
from decimal import Decimal
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re

from publish_consolidated_report import ARTIFACTS, DEST, FOLDER, MARKER, ROOT, digest

SEAL = DEST / 'release_checksums.json'
SOURCES = ('README.md', 'FUNCTIONS.md', 'OUTPUT_COMPLIANCE.md', 'LLM_EXPANSION.md',
           'REFERENCE_1136.md', 'REFERENCE_1136_FUNCTIONS.md', 'REFERENCE_1136_OUTPUT_COMPLIANCE.md',
           'REFERENCE_1136_LLM_EXPANSION.md', 'archive_october19_publication.py',
           'publish_consolidated_report.py', 'validate_consolidated_release.py',
           'test_consolidated_publication.py', 'freeze_consolidated_release.py',
           'freeze_corrected_release.py', 'test_corrected_release.py',
           'docs/index.html', 'docs/functions.html', 'docs/output_compliance.html',
           'docs/reference_1136.html', 'docs/reference_1136_functions.html',
           'docs/reference_1136_output_compliance.html', '.github/workflows/october18-validate.yml')


def hashes():
    from archive_frontier_presentation import historical_path
    paths = {repo_file(name, root=ROOT) for name in SOURCES}
    for folder in (DEST, repo_file('docs', root=ROOT) / FOLDER, repo_file('publication_archive_2026-10-19', root=ROOT)):
        paths.update(p for p in folder.rglob('*') if p.is_file())
    paths.discard(SEAL)
    # A later layout reuses these same sealed measurements. Resolve only the
    # superseded presentation/source paths to their exact committed snapshots.
    archive = repo_file('presentation_archive_2026-10-19', root=ROOT)
    manifest = json.loads((archive / 'manifest.json').read_text())['files'] if archive.exists() else {}
    result = {}
    for path in sorted(paths):
        name = str(logical_relative(path, root=ROOT))
        selected = archive / manifest[name]['archive_path'] if name in manifest else historical_path(path)
        result[name] = digest(selected)
        if name in manifest:
            assert result[name] == manifest[name]['sha256'], name
    return result


def privacy(data):
    assert '/Users/' not in data
    assert not re.search(r'\bsk-(?:or-v1-)?[A-Za-z0-9_-]{24,}', data)
    forbidden = {'gold_option', 'gold_text', 'gold_canonical', 'correct_option_id', 'correct_first',
                 'correct_eventual', 'choice_first_correct', 'leading_id_correct_first',
                 'api_key', 'authorization', 'is_byok', 'user_id', 'solution_certificate',
                 'proposed_answer', 'verifier_responses'}
    def inspect(value):
        if isinstance(value, dict):
            assert not forbidden.intersection(value), forbidden.intersection(value)
            for v in value.values():
                inspect(v)
        elif isinstance(value, list):
            for v in value:
                inspect(v)
    return inspect


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.targets = []
    def handle_starttag(self, tag, attrs):
        self.targets.extend(v for k, v in attrs if k in ('href', 'src'))


def csv_rows(name):
    with (DEST / name).open(newline='') as f:
        return list(csv.DictReader(f))


def validate():
    manifest = json.loads((DEST / 'manifest.json').read_text())
    assert set(manifest['artifacts']) == set(ARTIFACTS) | {'audit_receipt.json'}
    expected_files = set(ARTIFACTS) | {'audit_receipt.json', 'manifest.json'}
    assert {p.name for p in DEST.iterdir()} == expected_files | ({SEAL.name} if SEAL.exists() else set())
    assert {p.name for p in (repo_file('docs', root=ROOT) / FOLDER).iterdir()} == expected_files
    assert manifest['question_export_without_key_access'] is True
    assert manifest['stage_comparison_in_graphs'] is False
    for name, expected in manifest['artifacts'].items():
        assert digest(DEST / name) == expected, name
    for path in DEST.iterdir():
        if path.suffix not in ('.json', '.jsonl', '.csv', '.txt', '.html', '.svg'):
            continue
        text = path.read_text(); inspect = privacy(text)
        if path.suffix == '.json':
            inspect(json.loads(text))
        elif path.suffix == '.jsonl':
            for line in text.splitlines():
                inspect(json.loads(line))
    s = json.loads((DEST / 'statistics.json').read_text())
    assert (s['question_count'], s['model_count'], s['family_count'], s['primary_cases']) == (1342, 20, 31, 26840)
    assert s['attempts'] == 26983 and s['recoveries'] == 143
    assert s['cost']['unknown_attempts'] == 218
    assert Decimal(s['cost']['known_decimal']) == Decimal('0.480883745')
    order = s['ranked_model_ids']
    assert len(order) == len(set(order)) == 20
    assert order == sorted(order, key=lambda mid: -s['models'][mid]['correct'])
    assert order[:3] == ['respan02', 'pplx_decider12', 'nimble_v4_max']
    rows = csv_rows('model_statistics.csv')
    assert len(rows) == 20
    plots = json.loads((DEST / 'plot_data.json').read_text())
    assert plots['questions_each'] == 1342 and plots['stage_comparison'] is False
    assert [v['model_id'] for v in plots['models']] == order
    for row, plot, mid in zip(rows, plots['models'], order):
        v = s['models'][mid]
        assert int(row['questions']) == plot['n'] == v['n'] == 1342
        assert int(row['correct']) == plot['correct'] == v['correct']
        assert float(row['accuracy']) == plot['accuracy'] == v['correct'] / 1342
        for key in ('median_ms', 'p95_ms'):
            assert float(row[key]) == plot[key] == v[key]
        assert float(row['known_run_cost_usd']) == v['cost']['known_usd']
        assert float(row['known_cost_per1000_usd']) == plot['cost']['known_usd_per_1000'] == v['cost']['known_usd_per_1000']
        assert int(row['unknown_attempt_costs']) == v['cost']['unknown_attempts']
        assert row['test_dates_toronto'] == ', '.join(v['dates_toronto'])
        assert v['n'] == v['correct'] + v['wrong_valid'] + v['failed']
        assert v['failed'] == v['provider_failures'] + v['model_output_failures']
        assert sum(f['correct'] for f in v['families'].values()) == v['correct']
        assert sum(f['n'] for f in v['families'].values()) == 1342
        assert v['release_exclusion_diagnostic']['n'] == 1305
    assert sum(v['attempts'] for v in s['models'].values()) == s['attempts']
    assert sum(v['recoveries'] for v in s['models'].values()) == s['recoveries']
    assert sum(v['cost']['unknown_attempts'] for v in s['models'].values()) == 218
    assert sum(Decimal(v['cost']['known_decimal']) for v in s['models'].values()) == Decimal(s['cost']['known_decimal'])
    family_rows = csv_rows('family_statistics.csv')
    assert len(family_rows) == 620
    families = {f['family_id']: f for f in s['families']}
    labels = {v['label']: v for v in s['models'].values()}
    for row in family_rows:
        f = families[row['family_id']]; v = labels[row['model']]['families'][row['family_id']]
        assert int(row['questions']) == f['n'] == v['n']
        assert int(row['correct']) == v['correct'] and float(row['accuracy']) == v['accuracy']
    questions = [json.loads(line) for line in (DEST / 'questions_1342.jsonl').read_text().splitlines()]
    assert len(questions) == len({q['id'] for q in questions}) == 1342
    assert not {'J001641', 'J001610'} & {q['id'] for q in questions}
    assert {'J001641-R1-cb2bba8d367c', 'J001610-R1-f23f98b3cb80'} <= {q['id'] for q in questions}
    counts = Counter(q['family_id'] for q in questions)
    assert counts == {f['family_id']: f['n'] for f in s['families']}
    assert questions == sorted(questions, key=lambda q: (q['family_id'], q['id']))
    qcsv = csv_rows('questions_1342.csv')
    assert len(qcsv) == 1342
    for q, row in zip(questions, qcsv):
        assert set(q) == {'id', 'family_id', 'family', 'instructions', 'context', 'question', 'options', 'native_input', 'native_input_sha256'}
        assert len(q['options']) == len(set(q['options'])) == 5
        packet = q['native_input']
        assert set(packet) == {'state', 'questions'} and set(packet['questions']) == {'decision'}
        decision = packet['questions']['decision']
        assert set(decision) == {'type', 'instructions', 'criteria'} and decision['type'] == 'choice'
        assert decision['criteria'] == dict(zip('12345', q['options']))
        encoded = json.dumps(packet, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
        assert sha256(encoded).hexdigest() == q['native_input_sha256']
        for key in ('id', 'family_id', 'family', 'instructions', 'context', 'question', 'native_input_sha256'):
            assert q[key] == row[key]
        assert q['options'] == [row['option_' + str(i)] for i in range(1, 6)]
    source = manifest['source_artifacts']
    for name in ARTIFACTS:
        if name not in ('report.html', 'report.txt', 'statistics.json'):
            assert digest(DEST / name) == source[name], name
    for path in DEST.iterdir():
        if path.name != 'release_checksums.json':
            assert path.read_bytes() == (repo_file('docs', root=ROOT) / FOLDER / path.name).read_bytes(), path.name
    for path in [*(repo_file('docs', root=ROOT)).glob('*.html'), repo_file('docs', root=ROOT) / FOLDER / 'report.html']:
        links = Links(); links.feed(path.read_text())
        for target in links.targets:
            if re.match(r'^(https?:|mailto:|#|data:)', target):
                continue
            assert (path.parent / target.split('#')[0]).exists(), (path, target)
    from archive_frontier_presentation import historical_path
    assert MARKER in historical_path(repo_file('docs/index.html', root=ROOT)).read_text()
    assert MARKER in (DEST / 'report.html').read_text()
    assert 'No publication occurred.' not in (DEST / 'report.html').read_text()
    receipt = json.loads((DEST / 'audit_receipt.json').read_text())
    assert receipt['active_summary_sha256'] == manifest['source_summary_sha256']
    assert receipt['answer_free_questions_exported'] == 1342
    assert receipt['answer_key_or_item_correctness_exported'] is False
    if SEAL.exists():
        assert hashes() == json.loads(SEAL.read_text()), 'Consolidated release changed after sealing'
    print('PASS: 20 complete routes, 1342 key-free questions, 620 category cells, CSV/plot parity and preserved release seals')
    return s


if __name__ == '__main__':
    validate()
