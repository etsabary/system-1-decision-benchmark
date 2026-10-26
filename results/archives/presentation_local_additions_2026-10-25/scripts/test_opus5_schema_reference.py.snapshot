"""Offline tests of the separately labelled Opus5 constrained reference."""
import unittest
from unittest.mock import patch

import opus5_schema_reference as run
from test_opus5_reference import OpusReference


class OpusSchema(unittest.TestCase):
    def response(self, text='{"choice":"3"}'):
        return OpusReference().response(text)

    def test_only_grammar_changes(self):
        original = run.native.payload(run.native.PROBE)
        body = run.payload(run.native.PROBE)
        schema = body['output_config'].pop('format')
        self.assertEqual(body, original)
        self.assertEqual(schema['schema']['properties']['choice']['enum'], ['1', '2', '3', '4', '5'])
        self.assertFalse(schema['schema']['additionalProperties'])

    def test_strict_schema_and_no_explanation(self):
        for text in ('{"choice":"1"}', '{"choice":"5"}'):
            response = self.response(text)
            record = {**response, **run.parse(response)}
            self.assertEqual(record['status'], 'ok')
            run.check_route(record)
        for text in ('3', '{"choice":3}', '{"choice":"3","explanation":"x"}', '**3**'):
            self.assertEqual(run.parse(self.response(text))['status'], 'invalid_output')

    def test_refusal_missing_telemetry_not_misrepresented_as_zero(self):
        response = self.response()
        response['raw_response'].update(stop_reason='refusal', content=[])
        response['raw_response']['usage'].update(cost=None, output_tokens_details=None)
        record = {**response, **run.parse(response)}
        self.assertEqual(record['status'], 'refusal')
        self.assertIsNone(record['reported_reasoning_tokens'])
        self.assertIsNone(record['reported_cost_usd'])
        self.assertIsNone(record['choice'])
        run.check_route(record)

    def test_positive_thinking_still_fails(self):
        response = self.response()
        response['raw_response']['usage']['output_tokens_details']['thinking_tokens'] = 1
        record = {**response, **run.parse(response)}
        self.assertEqual(record['status'], 'unexpected_reasoning')
        with self.assertRaises(AssertionError):
            run.check_route(record)

    def test_frozen_order_and_prompt_preserved(self):
        with patch.object(run.native.base.transport, 'send', side_effect=AssertionError('No network')):
            questions, plan = run.prepare()
            _, old = run.native.prepare()
        self.assertEqual(len(plan), 1342)
        self.assertEqual([p['item_id'] for p in plan], [p['item_id'] for p in old])
        self.assertEqual([p['message_sha256'] for p in plan], [p['message_sha256'] for p in old])


if __name__ == '__main__':
    unittest.main()
