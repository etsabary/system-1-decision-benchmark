import unittest
import hyper_reference as n


class HyperReference(unittest.TestCase):
    def response(self, text='2'):
        return {'http_status': 200, 'error': '', 'transport_failure': False,
                'raw_response': {'model': n.MODEL, 'choices': [{'finish_reason': 'stop', 'message': {'content': text}}],
                'usage': {'prompt_tokens': 100, 'completion_tokens': 1, 'total_tokens': 101,
                          'cost': {'usd': .000206, 'hypercredits': .00412}}}}

    def test_same_bank_messages_and_explicit_none(self):
        q, p = n.prepare()
        self.assertEqual(len(p), 1342)
        body = n.payload(q[p[0]['item_id']])
        self.assertEqual(body['reasoning_effort'], 'none')
        self.assertEqual(body['max_tokens'], 16)
        self.assertEqual(body['messages'], n.base.payload(q[p[0]['item_id']])['messages'])
        self.assertNotIn('tools', body)
        self.assertNotIn('provider', body)

    def test_quota_currency_and_missing_telemetry_are_not_zero(self):
        r = self.response()
        v = n.parse(r)
        self.assertEqual(v['status'], 'ok')
        self.assertEqual(v['reported_cost_usd'], .000206)
        self.assertEqual(v['reported_hypercredits'], .00412)
        self.assertIsNone(v['reported_reasoning_tokens'])
        self.assertEqual(v['reasoning_verification'], 'requested_none_catalog_supported_no_token_telemetry')
        n.check_route({**r, **v})

    def test_explanation_and_actual_reasoning_rejected(self):
        self.assertEqual(n.parse(self.response('2. explanation'))['status'], 'invalid_output')
        r = self.response()
        r['raw_response']['choices'][0]['message']['reasoning_content'] = 'some deliberation'
        self.assertEqual(n.parse(r)['status'], 'unexpected_reasoning')
        with self.assertRaises(AssertionError):
            n.check_route({**r, **n.parse(r)})

    def test_wrong_model_and_missing_currency_fail_closed(self):
        r = self.response()
        r['raw_response']['model'] = 'kimi-k3'
        with self.assertRaises(AssertionError):
            n.check_route({**r, **n.parse(r)})
        r = self.response()
        del r['raw_response']['usage']['cost']
        self.assertIsNone(n.parse(r)['reported_cost_usd'])
        with self.assertRaises(AssertionError):
            n.check_route({**r, **n.parse(r)})


if __name__ == '__main__':
    unittest.main()
