import unittest
import baseten_decisions_2026_10_21 as r


class BasetenTests(unittest.TestCase):
    def test_original_inputs_and_1342_not_1136(self):
        qs,order = r.bank.prepare()
        self.assertEqual(len(order),1342)
        for mid in r.MODELS:
            for q in qs.values():
                body = r.payload(q,mid)
                self.assertEqual({k:v for k,v in body.items() if k != 'model'},q['native_input'])
                self.assertNotIn('provider',body)

    def test_named_identity_and_no_invented_reported_cost(self):
        response = dict(http_status=200,error='',raw_response=dict(model='mammoth-1',
            answers=dict(decision=dict(choice='3')),usage=dict(input_tokens=100,output_tokens=1)))
        value = r.parse(response,'mammoth1')
        self.assertEqual(value['status'],'ok')
        self.assertIsNone(value['reported_cost_usd'])
        self.assertEqual(value['accounted_cost_usd'],0)
        self.assertIn('not_receipt',value['cost_source'])
        response['raw_response']['model'] = 'some-other-model'
        self.assertEqual(r.parse(response,'mammoth1')['status'],'identity_mismatch')


if __name__ == '__main__':
    unittest.main()
