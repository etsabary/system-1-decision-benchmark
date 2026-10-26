import copy
import unittest
from unittest.mock import patch
import direct_decisions_2026_10_20 as r


def response(mid='d3_turbo'):
    return {'http_status':200,'error':'','raw_response':{'model':r.MODELS[mid]['model'],
        'answers':{'decision':{'type':'choice','choice':'3','probabilities':dict(zip('12345',(0.,0.,1.,0.,0.))),'confidence':1.}},
        'usage':{'input_tokens':100,'output_tokens':0}}}


class DirectDecisionTests(unittest.TestCase):
    def test_payload_keeps_original_native_input_and_option_order(self):
        questions,plan=r.bank.prepare()
        for mid in r.MODELS:
            for q in questions.values():
                body=r.payload(q,mid)
                self.assertEqual({k:v for k,v in body.items() if k!='model'},q['native_input'])
                self.assertEqual(list(body['questions']['decision']['criteria']),list('12345'))
            self.assertEqual(len(plan),1342)

    def test_free_cost_is_not_invented_api_report(self):
        for mid in ('d3_turbo','amos_large'):
            value=r.parse(response(mid),mid)
            self.assertEqual(value['status'],'ok')
            self.assertIsNone(value['reported_cost_usd'])
            self.assertEqual(value['accounted_cost_usd'],0)
            self.assertIn('not_api_reported',value['cost_source'])

    def test_paid_cost_preserves_charge_and_unknown(self):
        value=response('kettei_fat');value['raw_response']['charge']={'amount_usd':'0.000006000'}
        self.assertEqual(r.parse(value,'kettei_fat')['cost_source'],'api_reported_charge')
        self.assertEqual(r.parse(value,'kettei_fat')['accounted_cost_usd'],.000006)
        del value['raw_response']['charge'];del value['raw_response']['usage']['input_tokens']
        self.assertIsNone(r.parse(value,'kettei_fat')['accounted_cost_usd'])

    def test_wrong_identity_or_generation_is_unusable(self):
        value=response();value['raw_response']['model']='different'
        self.assertEqual(r.parse(value,'d3_turbo')['status'],'identity_mismatch')
        value=response();value['raw_response']['usage']['output_tokens']=10
        self.assertEqual(r.parse(value,'d3_turbo')['status'],'unverified_zero_generation')

    def test_provider_errors_and_bad_choices_cannot_score(self):
        value=response();value['raw_response']['error']={'message':'failure'}
        self.assertEqual(r.parse(value,'d3_turbo')['status'],'provider_error')
        value=response();value['raw_response']['answers']['decision']['choice']='3 because on'
        self.assertNotEqual(r.parse(value,'d3_turbo')['status'],'ok')

    def test_public_endpoint_does_not_need_credential(self):
        with patch.object(r,'dotenv_values',side_effect=AssertionError('Must not read secret')):
            self.assertEqual(r.credentials('amos_large'),'')


if __name__=='__main__':unittest.main()
