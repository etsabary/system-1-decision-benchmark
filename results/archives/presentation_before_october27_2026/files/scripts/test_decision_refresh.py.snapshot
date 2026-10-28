"""Offline refresh guards. No paid requests."""
from repo_layout import repo_file
import ast
import copy
from pathlib import Path
import tempfile
import unittest

import decision_refresh as d
from run_benchmark import packet, read_csv


class Refresh(unittest.TestCase):
    def test_versions_are_explicit(self):
        self.assertEqual(set(d.MODELS), {'typesafe/jev-1.13', 'typesafe/jev-1.14', 'openai/gpt-6-luna-decisions'})
        self.assertTrue(all('latest' not in v[4] for v in d.MODELS.values()))

    def test_exact_native_content(self):
        q = read_csv(repo_file('data/questions_1136.csv', root=d.ROOT))[0]
        for model in d.MODELS:
            body = d.payload(q, model)
            self.assertEqual({k: body[k] for k in ('state', 'questions')}, packet(q))
            self.assertFalse(body['provider']['allow_fallbacks'])

    def test_plan_and_limits(self):
        with tempfile.TemporaryDirectory() as temp:
            qq, pp = d.prepare(Path(temp))
            self.assertEqual(len(pp), 3408)
            self.assertEqual(len({(p['item_id'], p['model_requested']) for p in pp}), 3408)
            for wave in range(1, 569):
                tasks = [p for p in pp if p['wave'] == wave]
                self.assertEqual(len(tasks), 6)
                self.assertTrue(all(sum(p['model_requested'] == m for p in tasks) == 2 for m in d.MODELS))
            for start in range(0, len(pp), 3):
                self.assertEqual(len({p['native_input_sha256'] for p in pp[start:start+3]}), 1)

    def test_timer_identical_to_eight_llms(self):
        original = repo_file('runs/visual_benchmark_curation_PRIVATE/codex_llm_pilot_2026-10-15/pilot_runner.py', root=d.ROOT)
        if not original.exists():
            self.skipTest('Original private executor absent; public timer remains inspectable')
        functions = []
        for path in (original, Path(d.__file__)):
            functions.append(next(n for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == 'send'))
        self.assertEqual(ast.dump(functions[0]), ast.dump(functions[1]))

    def base(self):
        return {'http_status': 200, 'error': '', 'raw_response': {
            'model': 'typesafe/jev-1.13-20260917', 'provider': 'TypeSafe',
            'answers': {'decision': {'choice': '3', 'confidence': .9, 'probabilities': {'1': 0, '2': 0, '3': 1, '4': 0, '5': 0}}},
            'usage': {'cost': .00001}}}

    def test_probability_warning_does_not_lose_choice(self):
        response = self.base()
        response['raw_response']['answers']['decision']['probabilities']['3'] = .999
        parsed = d.parse(response)
        self.assertEqual(parsed['choice'], '3')
        self.assertEqual(parsed['status'], 'ok')
        self.assertFalse(parsed['probabilities_valid'])

    def test_invalid_and_failed_choices(self):
        response = self.base()
        response['raw_response']['answers']['decision']['choice'] = True
        self.assertIsNone(d.parse(response)['choice'])
        response = self.base()
        response['http_status'] = 499
        self.assertIsNone(d.parse(response)['choice'])

    def test_exact_identity_guard(self):
        response = self.base()
        parsed = d.parse(response)
        d.check_identity({**response, **parsed, 'model_requested': 'typesafe/jev-1.13'})
        parsed['model_returned'] = 'typesafe/jev-1.14-20261014'
        with self.assertRaises(AssertionError):
            d.check_identity({**response, **parsed, 'model_requested': 'typesafe/jev-1.13'})

    def test_unknown_cost_and_confidence(self):
        response = self.base()
        response['raw_response']['usage'] = {}
        response['raw_response']['answers']['decision']['confidence'] = float('nan')
        parsed = d.parse(response)
        self.assertIsNone(parsed['reported_cost_usd'])
        self.assertIsNone(parsed['confidence'])
        self.assertEqual(parsed['choice'], '3')

    def test_no_blind_resume(self):
        with self.assertRaises(AssertionError):
            d.reconcile([{'request_index': 1, 'attempt': 1}], [], [], [{'request_index': 1}])


if __name__ == '__main__':
    unittest.main()
