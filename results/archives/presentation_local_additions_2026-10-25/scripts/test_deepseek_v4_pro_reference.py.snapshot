"""Offline no-reasoning, identity and prompt-parity regressions."""
import unittest
from unittest.mock import patch

import deepseek_v4_pro_reference as run


class DeepSeekProReference(unittest.TestCase):
    def response(self):
        return {'http_status': 200, 'error': '', 'transport_failure': False,
                'raw_response': {'model': run.MODEL, 'provider': 'DeepInfra',
                    'choices': [{'finish_reason': 'stop', 'message': {'content': '3'}}],
                    'usage': {'prompt_tokens': 100, 'completion_tokens': 1, 'cost': .0001326,
                              'completion_tokens_details': {'reasoning_tokens': 0}}}}

    def test_dated_model_pinned_and_off(self):
        p = run.payload(run.PROBE)
        self.assertEqual(p['model'], 'deepseek/deepseek-v4-pro-0813')
        self.assertEqual(p['reasoning'], {'enabled': False, 'effort': 'none'})
        self.assertEqual(p['max_tokens'], 16)
        self.assertEqual(p['provider'], {'only': ['deepinfra/fp8'], 'allow_fallbacks': False, 'require_parameters': True})
        self.assertNotIn('tools', p)

    def test_same_frozen_bank_order_and_messages(self):
        with patch.object(run.base.transport, 'send', side_effect=AssertionError('No network')):
            qs, plan = run.prepare()
            _, original = run.base.prepare()
        self.assertEqual(len(qs), 1342)
        self.assertEqual([p['item_id'] for p in plan], [p['item_id'] for p in original])
        self.assertEqual([p['message_sha256'] for p in plan], [p['message_sha256'] for p in original])

    def test_zero_reasoning_is_required_not_assumed(self):
        r = self.response()
        run.check_route({**r, **run.parse(r)})
        for value in (None, False, '0', 1):
            r = self.response()
            r['raw_response']['usage']['completion_tokens_details']['reasoning_tokens'] = value
            with self.assertRaises(AssertionError):
                run.check_route({**r, **run.parse(r)})
        r = self.response()
        r['raw_response']['choices'][0]['message']['reasoning_content'] = 'thinking'
        with self.assertRaises(AssertionError):
            run.check_route({**r, **run.parse(r)})

    def test_identity_and_format_not_relaxed(self):
        for field, value in (('model', 'deepseek/deepseek-v4-pro'), ('provider', 'Other')):
            r = self.response()
            r['raw_response'][field] = value
            with self.assertRaises(AssertionError):
                run.check_route({**r, **run.parse(r)})
        r = self.response()
        r['raw_response']['choices'][0]['message']['content'] = '3 because...'
        self.assertEqual(run.parse(r)['status'], 'invalid_output')
        self.assertIsNone(run.parse(r)['choice'])


if __name__ == '__main__':
    unittest.main()
