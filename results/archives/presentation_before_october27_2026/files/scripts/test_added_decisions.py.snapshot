"""Offline regression checks for the October 16 additions. No API calls."""
from repo_layout import repo_file
import ast
import copy
from pathlib import Path
import tempfile
import unittest

import added_decisions as a
import decision_refresh as d


class AddedDecisions(unittest.TestCase):
    def test_frozen_content_and_pinned_names(self):
        q = d.read_csv(repo_file('data/questions_1136.csv', root=a.ROOT))[0]
        for model_id, spec in a.MODELS.items():
            self.assertNotIn('latest', spec['model'])
            body = a.payload(q, model_id)
            self.assertEqual({k: body[k] for k in ('state', 'questions')}, d.packet(q))
            self.assertEqual('provider' in body, spec['host'] == 'openrouter.ai')

    def test_plan_coverage_and_concurrency(self):
        for model_id in a.MODELS:
            with tempfile.TemporaryDirectory() as temp:
                questions, plan = a.prepare(model_id, Path(temp))
                self.assertEqual(len(plan), 1136)
                self.assertEqual({p['item_id'] for p in plan}, set(questions))
                self.assertEqual(set(p['wave'] for p in plan), set(range(1, 569)))
                self.assertTrue(all(sum(p['wave'] == wave for p in plan) == 2 for wave in range(1, 569)))

    def response(self):
        return {'http_status': 200, 'error': '', 'raw_response': {
            'model': 'nimble-v4', 'answers': {'decision': {
                'choice': '2', 'confidence': .8, 'probabilities': {'1': .05, '2': .8, '3': .05, '4': .05, '5': .05}}},
            'usage': {'input_tokens': 500}}}

    def test_cost_is_not_mislabeled_as_reported(self):
        result = a.parse(self.response(), 'nimble_v4')
        self.assertIsNone(result['reported_cost_usd'])
        self.assertAlmostEqual(result['accounted_cost_usd'], .00002)
        self.assertEqual(result['cost_source'], 'usage_times_published_tariff')
        self.assertEqual(result['status'], 'ok')

    def test_reported_cost_takes_priority(self):
        response = self.response()
        response['raw_response']['usage']['cost'] = .0001
        result = a.parse(response, 'nimble_v4')
        self.assertEqual(result['accounted_cost_usd'], .0001)
        self.assertEqual(result['cost_source'], 'api_reported')

    def test_transport_unknown_is_not_free(self):
        response = {'http_status': 0, 'error': 'timeout', 'raw_response': {}}
        result = a.parse(response, 'nimble_v4')
        self.assertIsNone(result['accounted_cost_usd'])
        response['http_status'] = 503
        result = a.parse(response, 'nimble_v4')
        self.assertEqual(result['accounted_cost_usd'], 0)
        self.assertEqual(result['cost_source'], 'documented_no_charge_http_error')

    def test_identity_and_choice_guards(self):
        response = self.response()
        result = {**response, **a.parse(response, 'nimble_v4'), 'model_id': 'nimble_v4'}
        a.check_identity(result)
        result['model_returned'] = 'nimble-latest'
        with self.assertRaises(AssertionError):
            a.check_identity(result)

    def test_same_timer_operations(self):
        # Endpoint selection and timestamp helper qualification are the only
        # transport differences; body reading and monotonic timers are retained.
        def calls(path):
            fn = next(n for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == 'send')
            return [ast.unparse(n.func) for n in ast.walk(fn) if isinstance(n, ast.Call)]
        added, original = calls(Path(a.__file__)), calls(Path(d.__file__))
        self.assertEqual([c.replace('d.timestamps', 'timestamps') for c in added], original)


if __name__ == '__main__':
    unittest.main()
