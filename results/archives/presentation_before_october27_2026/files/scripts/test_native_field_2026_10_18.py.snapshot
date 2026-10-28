"""Offline gates for the October 18 native decision expansion."""
import ast
import copy
from pathlib import Path
import tempfile
import unittest

import native_field_2026_10_18 as n


class NativeField(unittest.TestCase):
    def response(self):
        return dict(http_status=200, error='', transport_failure=False, raw_response={
            'model':'liquid/d1-ultra-20261015', 'provider':'Liquid',
            'answers':{'decision':{'choice':'2', 'confidence':.8,
                        'probabilities':{'1':.05,'2':.8,'3':.05,'4':.05,'5':.05}}},
            'usage':{'input_tokens':500,'cost':.000021}})

    def test_complete_frozen_plans_and_exact_native_input(self):
        self.assertEqual(len(n.MODELS),15)
        for m in n.MODELS:
            with tempfile.TemporaryDirectory() as directory:
                questions, plan = n.prepare(m, Path(directory))
                self.assertEqual(len(plan),1136)
                self.assertEqual(len({r['item_id'] for r in plan}),1136)
                self.assertEqual(Counter(r['wave'] for r in plan),Counter({i:2 for i in range(1,569)}))
                q=questions[plan[0]['item_id']]
                body=n.payload(q,m)
                self.assertEqual({k:body[k] for k in ('state','questions')},n.d.packet(q))
                self.assertEqual(body['provider']['only'],[n.MODELS[m]['provider_tag']])
                self.assertFalse(body['provider']['allow_fallbacks'])
                n.prepare(m,Path(directory))

    def test_reuses_unchanged_transport(self):
        source=ast.parse(Path(n.__file__).read_text())
        self.assertFalse(any(isinstance(x,ast.FunctionDef) and x.name=='send' for x in source.body))
        self.assertIn('old.send',Path(n.__file__).read_text())

    def test_success_identity_cost(self):
        r=self.response()
        value={**r,**n.parse(r),'model_id':'liquid_ultra'}
        self.assertEqual(value['status'],'ok')
        self.assertEqual(value['accounted_cost_usd'],.000021)
        n.check_identity(value)
        for field,bad in [('model_returned','liquid/d1'),('provider','Wrong'),('reported_cost_usd',None)]:
            changed={**value,field:bad}
            with self.assertRaises(AssertionError): n.check_identity(changed)

    def test_error_envelope_not_model_output_or_false_identity(self):
        r=self.response()
        r['raw_response']={'error':{'code':502,'message':'upstream failed'}}
        value={**r,**n.parse(r),'model_id':'liquid_ultra'}
        self.assertEqual(value['status'],'provider_error')
        self.assertIsNone(value['choice'])
        self.assertIsNone(value['accounted_cost_usd'])
        n.check_identity(value)
        self.assertFalse(n.retryable(value))

    def test_retry_policy_and_malformed_answers(self):
        r=self.response()
        r['raw_response']['answers']['decision']['choice']='6'
        value={**r,**n.parse(r),'model_id':'liquid_ultra'}
        n.check_identity(value)
        self.assertEqual(value['status'],'invalid_answer')
        self.assertFalse(n.retryable(value))
        for code in (408,429,500,503):
            self.assertTrue(n.retryable({**value,'http_status':code}))
        self.assertFalse(n.retryable({**value,'http_status':400}))
        self.assertTrue(n.retryable({**value,'transport_failure':True}))

    def test_transport_no_choice_even_if_partial_response(self):
        r=self.response()
        r.update(transport_failure=True,error='body-read timeout')
        value=n.parse(r)
        self.assertIsNone(value['choice'])
        self.assertEqual(value['status'],'transport_failure')


from collections import Counter

if __name__=='__main__':
    unittest.main()
