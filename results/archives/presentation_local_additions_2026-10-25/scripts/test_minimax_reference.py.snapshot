import unittest
import minimax_reference as m


class MiniMaxReference(unittest.TestCase):
    def test_exact_model_route_and_no_reasoning(self):
        q={'instructions':'rules','context':'state','question':'choose','options':['a','b','c','d','e']}
        body=m.payload(q)
        self.assertEqual(body['model'],'minimax/minimax-m3')
        self.assertEqual(body['reasoning'],{'enabled':False})
        self.assertEqual(body['provider']['only'],['deepinfra/fp8'])
        self.assertFalse(body['provider']['allow_fallbacks'])
        self.assertEqual(body['max_tokens'],16)
        self.assertNotIn('tools',body)

    def test_reasoning_and_provider_guards(self):
        r={'status':'ok','provider':'DeepInfra','model_returned':m.MODEL,'reported_cost_usd':.001,
           'reported_reasoning_tokens':0,'reasoning_text_present':False}
        m.check_route(r)
        for change in ({'provider':'Other'},{'model_returned':'minimax/minimax-m3.1'},
                       {'reported_reasoning_tokens':None},{'reported_reasoning_tokens':True},
                       {'reasoning_text_present':True},{'reported_cost_usd':None}):
            with self.assertRaises(AssertionError):m.check_route({**r,**change})

    def test_same_complete_bank_and_order(self):
        q,plan=m.prepare();_,original=m.base.prepare()
        self.assertEqual(len(q),1342)
        self.assertEqual([r['item_id'] for r in plan],[r['item_id'] for r in original])
        self.assertEqual([r['message_sha256'] for r in plan],[r['message_sha256'] for r in original])


if __name__=='__main__':unittest.main()
