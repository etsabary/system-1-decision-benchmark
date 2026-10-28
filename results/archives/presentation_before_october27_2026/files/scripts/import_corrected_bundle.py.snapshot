"""Install a validated, public-safe offline correction export exactly once."""
from repo_layout import repo_file
import argparse
from collections import Counter
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DEST = repo_file('corrected_2026-10-18', root=ROOT)


def load_validator(path):
    spec = importlib.util.spec_from_file_location('corrected_validator_import', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True, type=Path)
    args = parser.parse_args()
    assert not DEST.exists(), 'Never overwrite an existing imported evidence bundle'
    validator = load_validator(args.bundle / 'source/validate_corrected_public.py')
    result = validator.validate(args.bundle, ROOT)
    assert result['status'] == 'PASS_KEY_FREE_EVIDENCE_CHECKS'
    shutil.copytree(args.bundle, DEST)
    summary = json.loads((DEST / 'summary.json').read_text())
    records = []
    for mid in summary['models']:
        path = DEST / 'replacement_evidence/models' / mid.replace('/', '__') / 'attempts.jsonl'
        records.extend(json.loads(line) for line in path.read_text().splitlines() if line.strip())
    assert len(records) == 72 and all(r['attempt'] == 1 for r in records)
    attempts = ''.join(json.dumps(r, ensure_ascii=False, allow_nan=False) + '\n' for r in records)
    (DEST / 'replacement_attempts.jsonl').write_text(attempts)
    source = json.loads((DEST / 'source_manifest.json').read_text())
    routes = {'scope': 'Only the two corrected-question calls changed provider for these models. The other1134 results per model retain their original route.',
              'changes': source['route_changes']}
    receipt = {'date_toronto': '2026-10-18', 'status': 'COMPLETE_CORRECTED_ACTIVE_BANK',
        'active_models': 36, 'questions_each': 1136, 'core_questions_each': 640,
        'retained_original_primary_cases': 36*1134, 'fresh_primary_cases': 72, 'fresh_recoveries': 0,
        'repair_scope': 'Two dependent procedure variants changed only ambiguous final-state wording; all facts, operations, options and intended keys retained. New prompt IDs/hashes identify the replacements. Original prompts and results are excluded from active scores/timing/cost.',
        'audit': {'selected_difficult_items': 182, 'selection': 'At most30% of37 previously ranked configurations correct',
                  'two_independent_verifiers_support_original_answer': 181, 'wording_ambiguities_in_selected_set': 1,
                  'additional_matching_wording_defects_found_by_full_bank_search': 1,
                  'blind_verification_pool': ['Opus5.5 through Claude Code bridge', 'Argon through Antigravity bridge', 'GPT6.1 Sol xhigh through Codex bridge'],
                  'replacement_verification': 'Both corrected questions freshly solved independently by Opus and Argon, plus exact step-by-step simulation',
                  'scope_limit': 'Targeted difficult-item audit, not independent external verification of all1136 items'},
        'deltas_histogram': dict(Counter(str(v['correct_delta']) for v in summary['deltas'].values())),
        'retired_original_attempts_overhead': summary['retirement_overhead'],
        'unavailable_original_model': summary['partial_models']['nimble_v4'],
        'key_policy': 'External frozen answer key used offline only; no key or item-level correctness published',
        'input_export_checksums_sha256': sha256((DEST / 'checksums.json').read_bytes()).hexdigest(),
        'corrected_question_bank_sha256': sha256((DEST / 'questions_1136.csv').read_bytes()).hexdigest()}
    for name, value in [('routes.json', routes), ('correction_receipt.json', receipt)]:
        data = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode()
        validator.privacy_guard(data)
        (DEST / name).write_bytes(data)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
