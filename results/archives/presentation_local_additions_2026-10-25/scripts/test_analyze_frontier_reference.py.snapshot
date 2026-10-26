"""Small, synthetic offline tests for the separate frontier scorer."""
import unittest
import analyze_frontier_reference as a


def record(index, item, choice, latency, cost, *, attempt=1, status='ok'):
    return {'request_index': index, 'item_id': item, 'choice': choice, 'latency_ms': latency,
            'reported_cost_usd': cost, 'attempt': attempt, 'status': status,
            'transport_failure': status == 'transport_failure', 'http_status': 0 if status == 'transport_failure' else 200,
            'reported_reasoning_tokens': 0 if status == 'ok' else None, 'reasoning_text_present': False,
            'usage': {'prompt_tokens': 100, 'completion_tokens': 5, 'total_tokens': 105},
            'provider': 'OpenAI', 'model_returned': a.run.MODEL,
            'started': {'toronto': '2026-10-19T11:00:00-04:00'}}


class FrontierAnalysis(unittest.TestCase):
    def test_failed_first_attempt_remains_unsuccessful_after_recovery(self):
        rows = [record(1, 'a', None, 9000, None, status='transport_failure'),
                record(1, 'a', '2', 700, .001, attempt=2), record(2, 'b', '4', 1000, .002)]
        md = {'a': {'family_id': 'F01', 'permanently_unscored_native_development': False},
              'b': {'family_id': 'F26', 'permanently_unscored_native_development': True}}
        s = a.summarize(rows, {'a': 2, 'b': 4}, md)
        self.assertEqual(s['correct'], 1)
        self.assertEqual(s['eventual']['correct'], 2)
        self.assertEqual(s['latency_first_all']['median_ms'], 5000)
        self.assertEqual(s['cost_all_attempts']['known_usd'], .003)
        self.assertEqual(s['cost_all_attempts']['missing_attempts'], 1)
        self.assertEqual(s['recoveries'], 1)
        self.assertEqual(s['release_exclusion_diagnostic']['n'], 1)
        self.assertEqual(s['new_domains']['n'], 1)
        self.assertEqual(s['new_domains']['correct'], 1)

    def test_explanatory_output_is_not_reinterpreted(self):
        rows = [record(1, 'a', None, 1000, .001, status='invalid_output')]
        self.assertEqual(a.outcomes(rows, {'a': 2})['failed'], 1)

    def test_duplicate_primary_item_is_rejected(self):
        with self.assertRaises(AssertionError):
            a.outcomes([record(1, 'a', '2', 1, 0), record(2, 'a', '2', 1, 0)], {'a': 2})

    def test_unknown_reasoning_telemetry_and_missing_quota_cost_are_not_zero(self):
        rows = [record(1, 'a', '2', 1000, .001),
                record(2, 'b', None, 10000, None, status='transport_failure')]
        for row in rows:
            row['reported_reasoning_tokens'] = None
            row['reported_hypercredits'] = .02 if row['status'] == 'ok' else None
            row['reasoning_verification'] = 'requested_none_catalog_supported_no_token_telemetry'
        md = {item: {'family_id': 'F01', 'permanently_unscored_native_development': False}
              for item in ('a', 'b')}
        s = a.summarize(rows, {'a': 2, 'b': 3}, md)
        self.assertEqual(s['reasoning_token_counts'], {'None': 2})
        self.assertEqual(s['cost_all_attempts']['known_usd'], .001)
        self.assertEqual(s['cost_all_attempts']['missing_attempts'], 1)
        self.assertEqual(s['hypercredits_all_attempts']['known'], .02)
        self.assertEqual(s['hypercredits_all_attempts']['missing_attempts'], 1)
        self.assertIn('not a cash invoice', s['hypercredits_all_attempts']['scope'])


if __name__ == '__main__':
    unittest.main()
