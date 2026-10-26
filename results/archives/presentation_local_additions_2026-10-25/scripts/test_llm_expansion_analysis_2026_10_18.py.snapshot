"""Offline export integrity, screening and aggregate regressions; no API calls."""
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import llm_expansion_analysis_2026_10_18 as a


class LlmExpansionAnalysis(unittest.TestCase):
    def test_policy_exact_boundaries(self):
        primary = {'attempted': 100, 'accuracy_attempted': .5}
        compliance = {'model_output_failures': 4}
        self.assertEqual(a.gate_reasons(primary, compliance, {'median_ms': 2000}), [])
        self.assertEqual(a.gate_reasons(primary, {'model_output_failures': 5}, {'median_ms': 2000}), ['model_output_failures_at_least_5_percent'])
        self.assertEqual(a.gate_reasons({**primary, 'accuracy_attempted': .49}, compliance, {'median_ms': 2000}), ['accuracy_below_50_percent'])
        self.assertEqual(a.gate_reasons(primary, compliance, {'median_ms': 2000.01}), ['median_above_2000_ms'])

    def test_compliance_actual_partial_denominator_and_error_separation(self):
        records = [{'status': 'ok', 'http_status': 200, 'error': '', 'raw_response': {}} for _ in range(94)]
        records += [{'status': 'invalid_output', 'http_status': 200, 'error': '', 'raw_response': {}} for _ in range(5)]
        records += [{'status': 'provider_error', 'http_status': 200, 'error': '', 'raw_response': {'error': {'code': 502}}}]
        value = a.compliance(records)
        self.assertEqual(value['planned'], 100)
        self.assertEqual(value['model_output_failures'], 5)
        self.assertEqual(value['provider_transport_failures'], 1)
        self.assertEqual(value['model_output_failure_fraction'], .05)
        self.assertFalse(value['passes_output_format_screen'])
        self.assertNotIn('eligible_for_main_comparison', value)

    def test_privacy_gate_rejects_instead_of_rewriting_bound_bytes(self):
        for value in ({'user_id': 'private'}, {'nested': {'gold_option': '2'}},
                      {'path': '/Users/person/private'}, {'Authorization': 'secret'},
                      {'value': 'sk-or-v1-' + 'a' * 48}):
            with self.assertRaises(AssertionError):
                a.privacy_guard(json.dumps(value).encode(), 'test.json')
        a.privacy_guard(b'{"primary":{"correct":50,"attempted":100}}\n', 'aggregate.json')

    def test_unknown_cost_is_not_zero(self):
        rows = [{'accounted_cost_usd': .001, 'reported_cost_usd': .001, 'cost_source': 'api_reported'},
                {'accounted_cost_usd': None, 'reported_cost_usd': None, 'cost_source': 'unreported'}]
        value = a.prior.native16.accounted_money(rows)
        self.assertEqual(value['known_usd'], .001)
        self.assertEqual(value['missing_attempts'], 1)
        self.assertEqual(value['accounted_attempts'], 1)

    def test_active_run_is_never_exported(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            self.assertIn('ACTIVE', a.classify('qwen3_235b', out))
            with patch.object(a, 'source_dir', return_value=out):
                with self.assertRaisesRegex(AssertionError, 'Never export'):
                    a.export('qwen3_235b')
            (out / 'completion.json').write_text('{"status":"COMPLETE_1136"}')
            self.assertEqual(a.classify('qwen3_235b', out), 'ACTIVE_OR_CONTROLLER_SETTLING')

    def test_blocked_probe_has_no_fake_full_bank_score(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            (out / 'compatibility_probe.json').write_text('{"status":"http_failure"}')
            self.assertEqual(a.classify('xing4_free', out), 'COMPATIBILITY_BLOCKED')
            self.assertEqual(a.validate_screen_decisions('xing4_free', out), [])

    def test_no_inference_call_or_credentials_in_analysis(self):
        source = Path(a.__file__).read_text()
        self.assertNotIn('.send(', source)
        self.assertNotIn('.api_key(', source)
        self.assertNotIn('urlopen(', source)

    def test_export_validation_uses_frozen_runners_and_prefixes(self):
        count = 0
        for m in a.MODELS:
            folder = a.PUBLIC / m
            if not (folder / 'checksums.json').exists():
                continue
            first, eventual, attempts, receipts = a.validate_export(m)
            state = a.classify(m, folder)
            if state == 'COMPLETE_1136':
                self.assertEqual(len(first), 1136)
                self.assertEqual(len(eventual), 1136)
                self.assertTrue(all(r['decision'] == 'continue' for r in receipts))
            elif state == 'COMPATIBILITY_BLOCKED':
                self.assertFalse(first)
                self.assertFalse(attempts)
            else:
                self.assertLessEqual(len(first), 1136)
                self.assertEqual(receipts[-1]['decision'], 'stop')
            count += 1
        if not count:
            self.skipTest('Settled public exports not generated yet')

    def test_public_evidence_byte_identical_to_captured_source(self):
        for m in a.MODELS:
            folder = a.PUBLIC / m
            if not (folder / 'checksums.json').exists():
                continue
            audit = json.loads((folder / 'source_audit.json').read_text())
            for name, expected in audit['source_evidence_sha256'].items():
                # Every public clone checks original captured-byte hashes. The
                # owner can additionally compare private local source files;
                # those private runtime directories are deliberately not Git data.
                self.assertEqual(a.digest_file(folder / name), expected)
                source=a.source_dir(m)/name
                if source.exists():
                    self.assertEqual((folder/name).read_bytes(),source.read_bytes())
            manifest = json.loads((folder / 'manifest.json').read_text())
            self.assertEqual(len(manifest['request_plan']), 1136)
            self.assertFalse((folder / 'run_manifest.json').exists())

    def test_all_old_rows_families_costs_and_partial_preserved(self):
        path = a.OVERALL / 'summary.json'
        if not path.exists(): self.skipTest('Aggregate not generated yet')
        value, base = json.loads(path.read_text()), json.loads(a.BASE.read_text())
        for m, old in base['models'].items(): self.assertEqual(value['models'][m], old)
        for before, after in zip(base['by_family'], value['by_family']):
            for m, old in before['models'].items(): self.assertEqual(after['models'][m], old)
        self.assertEqual(value['partial_runs'], base['partial_runs'])
        self.assertEqual(value['publication']['excluded_model_ids'], base['publication']['excluded_model_ids'])
        self.assertEqual(value['model_count'], 36 + len(value['llm_added_october_18_model_ids']))
        self.assertEqual(value['publication']['ranked_model_count'], 33 + len(value['llm_added_october_18_model_ids']))
        self.assertEqual(value['total_scored_model_questions'], value['model_count'] * 1136)

    def test_selected_complete_and_partial_never_mixed(self):
        path = a.OVERALL / 'summary.json'
        if not path.exists(): self.skipTest('Aggregate not generated yet')
        value = json.loads(path.read_text())
        for m in value['llm_added_october_18_model_ids']:
            row = value['models'][m]
            self.assertEqual(row['primary']['attempted'], 1136)
            self.assertEqual(sum(f['models'][m]['correct'] for f in value['by_family']), row['primary']['correct'])
            self.assertIn(m, value['publication']['eligible_model_ids'])
        for m, row in value['partial_samples'].items():
            self.assertNotIn(m, value['models'])
            self.assertNotIn(m, value['publication']['eligible_model_ids'])
            self.assertFalse(row['full_bank_extrapolation'])
            self.assertEqual(row['primary_on_completed_only']['attempted'], row['completed_first_attempts'])
        for m, row in value['compatibility_only'].items():
            self.assertFalse(row['benchmark_accuracy_available'])
            self.assertNotIn('primary', row)
            self.assertNotIn(m, value['models'])

    def test_experiment_cost_buckets_and_sources_reconcile(self):
        path = a.OVERALL / 'summary.json'
        if not path.exists(): self.skipTest('Aggregate not generated yet')
        value = json.loads(path.read_text())
        self.assertTrue(set(a.ANALYSIS_SOURCES) <= set(value['source_files_sha256']))
        costs = value['llm_october_18_experiment_costs']
        pieces = [costs[k] for k in ('selected_full_runs', 'stopped_samples', 'compatibility_probes')]
        self.assertEqual(sum((Decimal(p['exact_usd']) for p in pieces), Decimal(0)), Decimal(costs['total_new_experiment']['exact_usd']))
        self.assertEqual(sum(p['missing_attempts'] for p in pieces), costs['total_new_experiment']['missing_attempts'])
        base = json.loads(a.BASE.read_text())
        self.assertEqual(Decimal(value['total_selected_accounted_cost']['exact_usd']),
                         Decimal(base['total_selected_accounted_cost']['exact_usd']) + Decimal(costs['selected_full_runs']['exact_usd']))
        a.validate_summary()

    def test_tev_not_misclassified_as_non_generative(self):
        path = a.OVERALL / 'summary.json'
        if not path.exists(): self.skipTest('Aggregate not generated yet')
        value = json.loads(path.read_text())
        if 'tev1_4b_native' not in value['models']: self.skipTest('Tev export pending')
        row = value['models']['tev1_4b_native']
        self.assertIn('generative', row['classification'])
        self.assertIn('native adapter', row['classification'])
        self.assertIn('architecture_limit', row)

    def test_no_private_data_in_owned_exports(self):
        for folder in (a.PUBLIC, a.OVERALL):
            for path in folder.rglob('*'):
                if path.is_file() and path.suffix in ('.json', '.jsonl', '.csv'):
                    a.privacy_guard(path.read_bytes(), path.name)


if __name__ == '__main__': unittest.main()
