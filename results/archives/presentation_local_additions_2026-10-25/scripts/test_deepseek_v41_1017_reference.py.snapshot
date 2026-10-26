"""Offline tests of the explicitly dated DeepSeek no-reasoning reference."""
import unittest
from unittest.mock import patch

import deepseek_v41_1017_reference as run


class DeepSeekReference(unittest.TestCase):
    def setUp(self):
        run.configure('deepseek')

    def response(self):
        return {'http_status': 200, 'error': '', 'transport_failure': False,
                'raw_response': {'model': run.MODEL, 'provider': 'DeepSeek',
                    'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': '3'}}],
                    'usage': {'prompt_tokens': 100, 'completion_tokens': 2, 'cost': .0000162,
                              'completion_tokens_details': {'reasoning_tokens': 0}}}}

    def test_dated_model_no_reasoning_and_no_fallback(self):
        body = run.payload(run.PROBE)
        self.assertEqual(body['model'], 'deepseek/deepseek-v4.1-flash-1017')
        self.assertEqual(body['reasoning'], {'enabled': False, 'effort': 'none'})
        self.assertEqual(body['max_tokens'], 16)
        self.assertEqual(body['provider']['only'], ['deepseek'])
        self.assertFalse(body['provider']['allow_fallbacks'])
        self.assertNotIn('tools', body)

    def test_success_requires_explicit_zero_and_exact_identity(self):
        response = self.response()
        run.check_route({**response, **run.parse(response)})
        for value in (None, False, '0', 1):
            response = self.response()
            response['raw_response']['usage']['completion_tokens_details']['reasoning_tokens'] = value
            with self.assertRaises(AssertionError):
                run.check_route({**response, **run.parse(response)})
        response = self.response()
        response['raw_response']['model'] = 'deepseek/deepseek-v4.1-flash'
        with self.assertRaises(AssertionError):
            run.check_route({**response, **run.parse(response)})

    def test_native_and_deepinfra_routes_are_separate(self):
        before = run.OUT
        run.configure('deepinfra')
        self.assertNotEqual(before, run.OUT)
        self.assertEqual(run.payload(run.PROBE)['provider']['only'], ['deepinfra/fp8'])
        response = self.response()
        with self.assertRaises(AssertionError):
            run.check_route({**response, **run.parse(response)})

    def test_same_frozen_bank_order_and_prompt(self):
        with patch.object(run.base.transport, 'send', side_effect=AssertionError('No network')):
            questions, plan = run.prepare()
            _, old = run.base.prepare()
        self.assertEqual(len(questions), 1342)
        self.assertEqual([p['item_id'] for p in plan], [p['item_id'] for p in old])
        self.assertEqual([p['message_sha256'] for p in plan], [p['message_sha256'] for p in old])


if __name__ == '__main__':
    unittest.main()
