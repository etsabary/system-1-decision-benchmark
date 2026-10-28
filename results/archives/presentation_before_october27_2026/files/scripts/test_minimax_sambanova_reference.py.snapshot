import unittest
import minimax_sambanova_reference as m


class MiniMaxSambaNova(unittest.TestCase):
    def test_route_and_guards(self):
        q={'instructions':'','context':'','question':'','options':['']*5}
        b=m.payload(q)
        self.assertEqual(b['provider']['only'],['sambanova'])
        self.assertEqual(b['reasoning'],{'enabled':False})
        r={'status':'ok','provider':'SambaNova','model_returned':m.MODEL,'reported_cost_usd':.001,'reported_reasoning_tokens':0,'reasoning_text_present':False}
        m.check_route(r)
        for change in ({'reported_reasoning_tokens':None},{'reported_reasoning_tokens':1},{'provider':'Other'}):
            with self.assertRaises(AssertionError):m.check_route({**r,**change})

    def test_same_bank_and_prompt(self):
        _,plan=m.prepare();_,old=m.base.prepare()
        self.assertEqual(len(plan),1342)
        self.assertEqual([r['message_sha256'] for r in plan],[r['message_sha256'] for r in old])


if __name__=='__main__':unittest.main()
