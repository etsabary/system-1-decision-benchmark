"""Offline tests; no credentials or network calls."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import frontier_reference as n


class FrontierReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.questions, cls.plan = n.prepare()

    def response(self, text='2'):
        return {'http_status': 200, 'error': '', 'transport_failure': False,
                'latency_ms': 200, 'raw_response': {'model': n.MODEL, 'provider': 'OpenAI',
                'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': text}}],
                'usage': {'prompt_tokens': 100, 'completion_tokens': 5, 'cost': .00025,
                          'completion_tokens_details': {'reasoning_tokens': 0}}}}

    def test_frozen_complete_answer_blind_bank(self):
        self.assertEqual(len(self.questions), 1342)
        self.assertEqual(len(self.plan), 1342)
        self.assertEqual(len({p['item_id'] for p in self.plan}), 1342)
        self.assertEqual(n.prepare()[1], self.plan)
        self.assertEqual({p['wave'] for p in self.plan}, set(range(1, 672)))
        self.assertNotIn('J001641', self.questions)
        self.assertNotIn('J001610', self.questions)
        self.assertEqual(len([i for i in self.questions if '-R1-' in i]), 2)

    def test_explicit_no_reasoning_and_exact_model_no_tools(self):
        body = n.payload(self.questions[self.plan[0]['item_id']])
        self.assertEqual(body['model'], 'openai/gpt-6-sol')
        self.assertEqual(body['reasoning'], {'enabled': False, 'effort': 'none'})
        self.assertEqual(body['service_tier'], 'default')
        self.assertEqual(body['max_tokens'], 16)
        self.assertFalse(body['provider']['allow_fallbacks'])
        self.assertIn('openai/flex', body['provider']['ignore'])
        self.assertNotIn('tools', body)
        self.assertEqual(n.d.digest(body), self.plan[0]['request_payload_sha256'])

    def test_strict_answer_contract(self):
        for text in ('1', '2', '3', '4', '5', ' 3\n'):
            self.assertEqual(n.parse(self.response(text))['status'], 'ok')
        for text in ('The answer is 3', '3. Because...', 'A', '13', '', None):
            r = n.parse(self.response(text))
            self.assertEqual(r['status'], 'invalid_output')
            self.assertIsNone(r['choice'])

    def test_truncated_answers_not_scored(self):
        r = self.response('3')
        r['raw_response']['choices'][0]['finish_reason'] = 'length'
        self.assertEqual(n.parse(r)['status'], 'invalid_output')

    def test_reasoning_must_be_reported_exactly_zero(self):
        for count in (1, 20, None, False, '0'):
            r = self.response()
            r['raw_response']['usage']['completion_tokens_details']['reasoning_tokens'] = count
            parsed = n.parse(r)
            self.assertEqual(parsed['status'], 'unexpected_reasoning')
            with self.assertRaises(AssertionError):
                n.check_route({**r, **parsed})
        for field in ('reasoning', 'reasoning_content', 'reasoning_details'):
            r = self.response()
            r['raw_response']['choices'][0]['message'][field] = 'present'
            self.assertEqual(n.parse(r)['status'], 'unexpected_reasoning')

    def test_identity_and_missing_cost_fail_closed(self):
        for field, value in (('model', 'openai/gpt-6.1-sol'), ('provider', 'Azure')):
            r = self.response()
            r['raw_response'][field] = value
            with self.assertRaises(AssertionError):
                n.check_route({**r, **n.parse(r)})
        r = self.response()
        del r['raw_response']['usage']['cost']
        self.assertIsNone(n.parse(r)['reported_cost_usd'])
        with self.assertRaises(AssertionError):
            n.check_route({**r, **n.parse(r)})

    def test_transport_failure_is_not_an_answer(self):
        r = self.response()
        r.update(http_status=0, error='timeout', transport_failure=True)
        r['raw_response'] = {}
        parsed = n.parse(r)
        self.assertEqual(parsed['status'], 'transport_failure')
        self.assertIsNone(parsed['choice'])
        self.assertIsNone(parsed['reported_cost_usd'])
        n.check_route({**r, **parsed})

    def test_reserve_is_positive(self):
        self.assertTrue(all(n.reserve(p) > 0 for p in self.plan))

    def test_unknown_dispatch_cannot_be_replayed(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            n.d.append(out / 'dispatches.jsonl', {**self.plan[0], 'attempt': 1})
            with self.assertRaisesRegex(AssertionError, 'Unresolved dispatch'):
                n.ledger_state(out, self.plan)

    def test_empty_ledger_and_dry_run_do_not_call_provider(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(n.ledger_state(Path(folder), self.plan), ([], [], set()))
        with patch.object(n.transport, 'send', side_effect=AssertionError('network forbidden')):
            questions, plan = n.prepare()
            self.assertEqual(len(plan), len(questions))


if __name__ == '__main__':
    unittest.main()
