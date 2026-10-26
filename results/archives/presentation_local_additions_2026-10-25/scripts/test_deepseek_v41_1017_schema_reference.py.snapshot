import unittest
from unittest.mock import patch

import deepseek_v41_1017_schema_reference as run
import test_deepseek_v41_1017_reference as bare_test


class DeepSeekSchema(unittest.TestCase):
    def setUp(self):
        self.original_route = run.native.ROUTE
        run.configure('deepinfra')

    def tearDown(self):
        run.native.configure(self.original_route)

    def response(self, text='{"choice":"3"}'):
        response = bare_test.DeepSeekReference().response()
        response['raw_response']['provider'] = 'DeepInfra'
        response['raw_response']['choices'][0]['message']['content'] = text
        return response

    def test_only_output_grammar_changes(self):
        body = run.payload(run.native.PROBE)
        schema = body.pop('response_format')
        self.assertEqual(body, run.native.payload(run.native.PROBE))
        self.assertTrue(schema['json_schema']['strict'])
        self.assertFalse(schema['json_schema']['schema']['additionalProperties'])

    def test_strict_choice_schema(self):
        for text in ('{"choice":"1"}', '{"choice":"5"}'):
            response = self.response(text)
            parsed = run.parse(response)
            self.assertEqual(parsed['status'], 'ok')
            run.check_route({**response, **parsed})
        for text in ('3', '{"choice":3}', '{"choice":"3","reason":"x"}', '{"choice":"6"}'):
            self.assertEqual(run.parse(self.response(text))['status'], 'invalid_output')

    def test_thinking_or_truncation_is_rejected(self):
        response = self.response()
        response['raw_response']['usage']['completion_tokens_details']['reasoning_tokens'] = 1
        self.assertEqual(run.parse(response)['status'], 'unexpected_reasoning')
        response = self.response()
        response['raw_response']['choices'][0]['finish_reason'] = 'length'
        self.assertEqual(run.parse(response)['status'], 'invalid_output')

    def test_same_question_order_and_prompt_hashes(self):
        with patch.object(run.base.transport, 'send', side_effect=AssertionError('No network')):
            _, plan = run.prepare()
            _, old = run.native.prepare()
        self.assertEqual(len(plan), 1342)
        self.assertEqual([p['item_id'] for p in plan], [p['item_id'] for p in old])
        self.assertEqual([p['message_sha256'] for p in plan], [p['message_sha256'] for p in old])


if __name__ == '__main__':
    unittest.main()
