"""Offline integration regressions for the fourteen-model comparison."""
from repo_layout import repo_file
from repo_layout import frozen_file, source_file
from hashlib import sha256
import json
import unittest

import overall_analysis as a


class Overall(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads((a.OVERALL / 'summary.json').read_text())
        cls.base = json.loads((a.prior.MATCHED / 'summary.json').read_text())

    def test_complete_counts_and_dates(self):
        s = self.summary
        self.assertEqual(s['model_count'], 14)
        self.assertEqual(s['total_scored_model_questions'], 15904)
        self.assertEqual(s['pending_model_ids'], [])
        for model, score in [('microsoft_decision', 841), ('nimble_v4', 902), ('nimble_v4_max', 997)]:
            result = s['models'][model]
            self.assertEqual(result['primary']['correct'], score)
            self.assertEqual(result['primary']['answered'], 1136)
            self.assertEqual(result['latency_first_all']['n'], 1136)
            self.assertEqual(set(result['dates_toronto']), {'2026-10-16'})

    def test_original_eleven_are_identical(self):
        for model, old in self.base['models'].items():
            self.assertEqual(self.summary['models'][model], old)
        for old_family, new_family in zip(self.base['by_family'], self.summary['by_family']):
            for model, value in old_family['models'].items():
                self.assertEqual(new_family['models'][model], value)

    def test_exact_addition_ledgers(self):
        for model in self.summary['added_model_ids']:
            first, eventual, attempts = a.validate_model(model)
            self.assertEqual(len(first), 1136)
            self.assertEqual(len(eventual), 1136)
            self.assertEqual(len(attempts), 1136)
            self.assertTrue(all(r['status'] == 'ok' for r in attempts))

    def test_sources_and_denominators(self):
        for name, expected in self.summary['source_files_sha256'].items():
            self.assertEqual(sha256(frozen_file(repo_file(name, root=a.ROOT)).read_bytes()).hexdigest(), expected)
        for model, value in self.summary['models'].items():
            self.assertEqual(sum(f['models'][model]['correct'] for f in self.summary['by_family']), value['primary']['correct'])
            p = value['primary']
            self.assertEqual(p['correct'] + p['wrong'] + p['unanswered'], 1136)
        self.assertEqual(self.summary['none_of_tested_models_correct'], 16)

    def test_calculated_cost_separate_from_reported(self):
        s = self.summary
        for model in ('nimble_v4', 'nimble_v4_max'):
            value = s['models'][model]['cost_all_attempts']
            self.assertEqual(value['reported_attempts'], 0)
            self.assertEqual(value['sources'], {'usage_times_published_tariff': 1136})
            self.assertEqual(value['missing_attempts'], 0)
        self.assertEqual(s['total_selected_accounted_cost']['exact_usd'], '0.382861929')
        self.assertEqual(s['total_selected_accounted_cost']['missing_attempts'], 70)
        self.assertEqual(s['total_selected_reported_cost']['exact_usd'], '0.334242319')
        self.assertEqual(s['total_selected_reported_cost']['missing_attempts'], 2342)

    def test_image_acceptance_is_not_vision(self):
        capability = json.loads((a.OVERALL / 'image_capabilities.json').read_text())
        self.assertEqual(capability['scored_image_questions_added'], 0)
        self.assertEqual(capability['native_image_compatibility_requests'], 3)
        self.assertEqual(capability['models']['microsoft_decision']['probe_http_status'], 400)
        for model in ('nimble_v4', 'nimble_v4_max'):
            self.assertEqual(capability['models'][model]['probe_http_status'], 200)
            self.assertEqual(capability['models'][model]['probe_input_tokens'], 26253)
            self.assertIsNone(capability['models'][model]['accuracy'])
        self.assertFalse(capability['probe_cost']['included_in_scored_benchmark_costs'])

    def test_combined_publication(self):
        # The October16 assertions describe that version, not the current leader.
        # Its exact presentation bytes remain bound by the original release seal.
        archive=repo_file('publication_archive_2026-10-16', root=a.ROOT)
        manifest=json.loads((archive/'manifest.json').read_text())
        text=(archive/manifest['files']['README.md']['archive_path']).read_text()
        current=json.loads((repo_file('overall_expanded_2026-10-16/summary.json', root=a.ROOT)).read_text())
        self.assertIn(str(current['publication']['ranked_model_count'])+' models', text)
        self.assertIn(f"{current['model_count']*1136:,}", text)
        self.assertIn('Added October 16, 2026', text)
        self.assertIn('Nimble v4 Max now leads', text)
        for model in self.summary['added_model_ids']:
            self.assertIn(self.summary['models'][model]['label'], text)
        graphics = json.loads((repo_file('overall_expanded_2026-10-16/graphics_integrity.json', root=a.ROOT)).read_text())
        self.assertEqual(graphics['source_summary_sha256'], sha256((repo_file('overall_expanded_2026-10-16/summary.json', root=a.ROOT)).read_bytes()).hexdigest())
        self.assertEqual(graphics['plotter_sha256'], sha256(frozen_file(source_file(repo_file('plot_overall.py', root=a.ROOT))).read_bytes()).hexdigest())
        for name, expected in graphics['files_sha256'].items():
            self.assertEqual(sha256((repo_file('figures', root=a.ROOT) / name).read_bytes()).hexdigest(), expected)


if __name__ == '__main__':
    unittest.main()
