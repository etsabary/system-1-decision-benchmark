import unittest
import sonnet55_schema_reference as n


class SonnetSchema(unittest.TestCase):
    def response(self, text='{"choice":"2"}'):
        return {'http_status': 200, 'error': '', 'transport_failure': False,
                'raw_response': {'model': n.MODEL, 'provider': 'Anthropic', 'stop_reason': 'end_turn',
                'content': [{'type': 'text', 'text': text}], 'usage': {'input_tokens': 100,
                'output_tokens': 10, 'cost': .0003, 'output_tokens_details': {'thinking_tokens': 0}}}}

    def test_schema_and_identical_question_text(self):
        q, plan = n.prepare()
        body = n.payload(q[plan[0]['item_id']])
        self.assertEqual(len(plan), 1342)
        self.assertEqual(body['messages'], n.native.payload(q[plan[0]['item_id']])['messages'])
        self.assertEqual(body['max_tokens'], 16)
        self.assertEqual(body['thinking'], {'type': 'between_tools'})
        self.assertNotIn('tools', body)
        self.assertEqual(body['output_config']['format']['schema']['properties']['choice']['enum'], list('12345'))
        self.assertEqual(n.d.digest(body), plan[0]['request_payload_sha256'])

    def test_only_exact_json_choice_allowed(self):
        for text in ('{"choice":"1"}', '{"choice":"5"}'):
            r = self.response(text)
            self.assertEqual(n.parse(r)['status'], 'ok')
            self.assertFalse(n.parse(r)['model_output_failure'])
        for text in ('2', '{"choice":2}', '{"choice":"2","reason":"x"}', '```json\n{"choice":"2"}\n```', '{"choice":"6"}'):
            r = n.parse(self.response(text))
            self.assertEqual(r['status'], 'invalid_output')
            self.assertIsNone(r['choice'])

    def test_schema_does_not_override_thinking_or_truncation(self):
        r = self.response()
        r['raw_response']['usage']['output_tokens_details']['thinking_tokens'] = 2
        self.assertEqual(n.parse(r)['status'], 'unexpected_reasoning')
        r = self.response()
        r['raw_response']['stop_reason'] = 'max_tokens'
        self.assertEqual(n.parse(r)['status'], 'invalid_output')


if __name__ == '__main__':
    unittest.main()
