"""No-network tests for native Sonnet no-thinking reference."""
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
import tempfile
from unittest.mock import patch
import unittest
import sonnet55_reference as n


class SonnetReference(unittest.TestCase):
    def response(self, text='2'):
        return {'http_status': 200, 'error': '', 'transport_failure': False,
                'raw_response': {'model': n.MODEL, 'provider': 'Anthropic',
                'stop_reason': 'end_turn', 'content': [{'type': 'text', 'text': text}],
                'usage': {'input_tokens': 100, 'output_tokens': 3, 'cost': .00023,
                          'output_tokens_details': {'thinking_tokens': 0}}}}

    def test_full_bank_same_prompt_and_order_as_sol(self):
        q, plan = n.prepare()
        old_q, old_plan = n.base.prepare()
        self.assertEqual(q, old_q)
        self.assertEqual([p['item_id'] for p in plan], [p['item_id'] for p in old_plan])
        self.assertEqual(len(plan), 1342)
        body = n.payload(q[plan[0]['item_id']])
        self.assertEqual(body['messages'], n.base.payload(q[plan[0]['item_id']])['messages'])
        self.assertEqual(body['thinking'], {'type': 'between_tools'})
        self.assertEqual(body['output_config'], {'effort': 'high'})
        self.assertEqual(body['max_tokens'], 16)
        self.assertNotIn('tools', body)
        self.assertFalse(body['provider']['allow_fallbacks'])
        self.assertEqual(n.d.digest(body), plan[0]['request_payload_sha256'])

    def test_valid_numeric_and_strict_output(self):
        for text in ('1', '2', '3', '4', '5', ' 2\n'):
            r = self.response(text)
            self.assertEqual(n.parse(r)['status'], 'ok')
            n.check_route({**r, **n.parse(r)})
        for text in ('A', '2. explanation', 'The answer is 2', '', None):
            self.assertEqual(n.parse(self.response(text))['status'], 'invalid_output')
        r = self.response()
        r['raw_response']['stop_reason'] = 'max_tokens'
        self.assertEqual(n.parse(r)['status'], 'invalid_output')

    def test_thinking_blocks_or_missing_telemetry_rejected(self):
        for count in (None, 1, False, '0'):
            r = self.response()
            r['raw_response']['usage']['output_tokens_details']['thinking_tokens'] = count
            self.assertEqual(n.parse(r)['status'], 'unexpected_reasoning')
        r = self.response()
        r['raw_response']['content'].insert(0, {'type': 'thinking', 'thinking': '', 'signature': 'private'})
        clean = n.sanitize(r)
        self.assertNotIn('signature', clean['raw_response']['content'][0])
        self.assertEqual(n.parse(clean)['status'], 'unexpected_reasoning')
        with self.assertRaises(AssertionError):
            n.check_route({**clean, **n.parse(clean)})

    def test_account_fields_are_not_saved(self):
        r = self.response()
        r['raw_response'].update(user_id='private', container='private')
        clean = n.sanitize(r)['raw_response']
        self.assertNotIn('user_id', clean)
        self.assertNotIn('container', clean)

    def test_cost_missing_not_zero_and_cache_input_counting(self):
        r = self.response()
        r['raw_response']['usage'].update(cache_read_input_tokens=30, cache_creation_input_tokens=20)
        self.assertEqual(n.parse(r)['usage']['prompt_tokens'], 150)
        del r['raw_response']['usage']['cost']
        self.assertIsNone(n.parse(r)['reported_cost_usd'])
        with self.assertRaises(AssertionError):
            n.check_route({**r, **n.parse(r)})

    def test_wrong_provider_and_model_rejected(self):
        for key, value in (('model', 'anthropic/claude-opus-5.5'), ('provider', 'Google')):
            r = self.response()
            r['raw_response'][key] = value
            with self.assertRaises(AssertionError):
                n.check_route({**r, **n.parse(r)})

    def test_provider_failure_not_valid_decision(self):
        r = self.response()
        r.update(http_status=503, error='HTTP503')
        r['raw_response'] = {}
        parsed = n.parse(r)
        self.assertEqual(parsed['status'], 'http_failure')
        self.assertIsNone(parsed['choice'])
        self.assertIsNone(parsed['reported_cost_usd'])

    def test_controller_retries_only_transport_not_explanation(self):
        questions = {'a': {'id': 'a'}, 'b': {'id': 'b'}}
        make_payload = lambda q: {'id': q['id']}
        plan = [{'request_index': i, 'item_id': item, 'wave': 1,
                 'request_payload_sha256': n.d.digest(make_payload(questions[item])), 'request_body_bytes': 10}
                for i, item in enumerate(questions, 1)]
        calls = []
        def send(body, key, spec):
            value = n.json.loads(body)
            calls.append(value['id'])
            r = self.response('2' if value['id'] == 'a' else '2. explanation')
            r.update(latency_ms=100, started={'utc': 'test'}, completed={'utc': 'test'})
            if value['id'] == 'a' and calls.count('a') == 1:
                r.update(http_status=503, error='HTTP503', raw_response={})
            return r
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            adapter = SimpleNamespace(prepare=lambda: (questions, plan), freeze=lambda *args: None,
                       ROOT=out, MODEL=n.MODEL, SPEC=n.SPEC, GUARD=Decimal('1'),
                       probe_cost=lambda out: 0, reserve=lambda task: Decimal('.001'),
                       payload=make_payload, sanitize=n.sanitize, parse=n.parse, check_route=n.check_route)
            with patch.object(n.controller.transport, 'send', side_effect=send), patch.object(n.d, 'api_key', return_value='fake'), patch.object(n.d, 'retry_wait', return_value=0):
                n.controller.execute(adapter, out, waves=1)
            attempts, results, done = n.controller.ledger_state(adapter, out, plan)
            self.assertEqual(calls.count('a'), 2)
            self.assertEqual(calls.count('b'), 1)
            self.assertEqual(len(attempts), 3)
            self.assertEqual(len(results), 2)
            self.assertEqual(done, {1, 2})


if __name__ == '__main__':
    unittest.main()
