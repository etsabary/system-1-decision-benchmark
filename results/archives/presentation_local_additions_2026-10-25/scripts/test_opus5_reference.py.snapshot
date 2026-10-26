"""Offline Opus5 protocol, identity, answer-blind plan and no-thinking tests."""
from copy import deepcopy
import unittest
from unittest.mock import patch

import opus5_reference as run


class OpusReference(unittest.TestCase):
    def response(self, text='3'):
        return {'http_status': 200, 'error': '', 'transport_failure': False,
                'raw_response': {'model': run.MODEL, 'provider': 'Anthropic',
                    'content': [{'type': 'text', 'text': text}], 'stop_reason': 'end_turn',
                    'usage': {'input_tokens': 100, 'output_tokens': 1, 'cost': .000525,
                              'output_tokens_details': {'thinking_tokens': 0}}}}

    def test_payload_explicitly_disables_thinking_no_tools(self):
        body = run.payload(run.PROBE)
        self.assertEqual(body['model'], 'anthropic/claude-opus-5')
        self.assertEqual(body['thinking'], {'type': 'disabled'})
        self.assertEqual(body['output_config'], {'effort': 'high'})
        self.assertEqual(body['max_tokens'], 16)
        self.assertEqual(body['provider']['only'], ['anthropic'])
        self.assertFalse(body['provider']['allow_fallbacks'])
        self.assertNotIn('tools', body)

    def test_answer_blind_frozen_plan_same_prompts_and_order(self):
        with patch.object(run.base.transport, 'send', side_effect=AssertionError('No network')):
            questions, plan = run.prepare()
            old_questions, old_plan = run.base.prepare()
        self.assertEqual(questions, old_questions)
        self.assertEqual(len(plan), 1342)
        self.assertEqual([p['item_id'] for p in plan], [p['item_id'] for p in old_plan])
        self.assertEqual({p['message_sha256'] for p in plan}, {p['message_sha256'] for p in old_plan})
        self.assertTrue(all(p['request_payload_sha256'] == run.d.digest(run.payload(questions[p['item_id']])) for p in plan))

    def test_output_must_be_just_one_option(self):
        for text in ('1', ' 3\n', '5'):
            response = self.response(text)
            result = run.parse(response)
            self.assertEqual(result['status'], 'ok')
            run.check_route({**response, **result})
        for text in ('Answer: 3', '3 because...', '', 'A', '13'):
            self.assertEqual(run.parse(self.response(text))['status'], 'invalid_output')

    def test_reasoning_must_be_explicitly_zero_not_merely_hidden(self):
        for count in (None, False, '0', 1):
            response = self.response()
            response['raw_response']['usage']['output_tokens_details']['thinking_tokens'] = count
            result = run.parse(response)
            self.assertEqual(result['status'], 'unexpected_reasoning')
            with self.assertRaises(AssertionError):
                run.check_route({**response, **result})
        response = self.response()
        response['raw_response']['content'].insert(0, {'type': 'thinking', 'thinking': ''})
        self.assertEqual(run.parse(response)['status'], 'unexpected_reasoning')

    def test_fail_closed_for_identity_provider_or_missing_cost(self):
        for field, value in (('model', 'anthropic/claude-opus-5.5'), ('provider', 'Google')):
            response = self.response()
            response['raw_response'][field] = value
            with self.assertRaises(AssertionError):
                run.check_route({**response, **run.parse(response)})
        response = self.response()
        del response['raw_response']['usage']['cost']
        with self.assertRaises(AssertionError):
            run.check_route({**response, **run.parse(response)})

    def test_sanitize_does_not_publish_unrelated_provider_data(self):
        response = self.response()
        response['raw_response']['private_extra'] = 'not retained'
        self.assertNotIn('private_extra', run.sanitize(response)['raw_response'])

    def test_truncation_is_not_a_usable_decision(self):
        response = self.response()
        response['raw_response']['stop_reason'] = 'max_tokens'
        self.assertEqual(run.parse(response)['status'], 'invalid_output')


if __name__ == '__main__':
    unittest.main()
