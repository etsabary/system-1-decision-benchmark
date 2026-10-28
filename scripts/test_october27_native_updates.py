from copy import deepcopy
import unittest
from october27_text_evidence import payload,packet

class NativeUpdateContract(unittest.TestCase):
    def test_payload_preserves_unicode_and_options(self):
        q={'native_input':{'state':'État: α → β','questions':{'decision':{'type':'choice','instructions':'Original rules','criteria':{'1':'a','2':'b','3':'c','4':'d','5':'e'}}}}}
        old=deepcopy(q)
        for mid in ('d3_ultra','liquid11'):
            p=payload(q,mid)
            self.assertEqual({k:p[k] for k in q['native_input']},q['native_input'])
        self.assertEqual(q,old)
    def test_provider_is_pinned_and_ultra_is_explicit(self):
        q={'native_input':{'state':'x','questions':{}}}
        self.assertEqual(payload(q,'d3_ultra')['model'],'vllm-sr/d3-ultra')
        self.assertEqual(payload(q,'liquid11')['provider'],dict(only=['liquid'],allow_fallbacks=False,require_parameters=True))
    def test_reordered_choices_change_packet_binding(self):
        q={'native_input':{'state':'x','questions':{'decision':{'criteria':{'1':'a','2':'b'}}}}}
        other=deepcopy(q);other['native_input']['questions']['decision']['criteria']={'1':'b','2':'a'}
        self.assertNotEqual(packet(payload(q,'d3_ultra')),packet(payload(other,'d3_ultra')))

if __name__=='__main__':unittest.main()
