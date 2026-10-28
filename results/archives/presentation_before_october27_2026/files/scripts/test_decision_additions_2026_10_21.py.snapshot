import copy
import unittest
import decision_additions_2026_10_21 as r


def response(mid):
    return dict(http_status=200,error='',raw_response=dict(model=r.MODELS[mid]['snapshot'],
        provider=r.MODELS[mid]['provider_name'],answers=dict(decision=dict(choice='3',
        probabilities=dict(zip('12345',(0,0,1,0,0))),confidence=1)),
        usage=dict(input_tokens=100,output_tokens=0,cost=0 if mid != 'drex_max' else .000006)))


class October21Tests(unittest.TestCase):
    def test_full_bank_original_inputs_and_backend_pin(self):
        qs,plan = r.bank.prepare()
        self.assertEqual(len(plan),1342)
        for mid in r.MODELS:
            for q in qs.values():
                body = r.payload(q,mid)
                self.assertEqual({k:v for k,v in body.items() if k not in ('model','provider')},q['native_input'])
                self.assertEqual(list(body['questions']['decision']['criteria']),list('12345'))
                self.assertFalse(body['provider']['allow_fallbacks'])
                self.assertEqual(body['provider']['only'],[r.MODELS[mid]['provider_tag']])

    def test_identity_provider_generation_and_answer(self):
        for mid in r.MODELS:
            good = response(mid)
            self.assertEqual(r.parse(good,mid)['status'],'ok')
            for field,value,status in (('model','wrong','identity_mismatch'),('provider','wrong','provider_mismatch')):
                bad = copy.deepcopy(good)
                bad['raw_response'][field] = value
                self.assertEqual(r.parse(bad,mid)['status'],status)
            bad = copy.deepcopy(good)
            bad['raw_response']['usage']['reasoning_tokens'] = 1
            self.assertEqual(r.parse(bad,mid)['status'],'unexpected_reasoning')
            native = copy.deepcopy(good)
            native['raw_response']['usage']['output_tokens'] = 170
            self.assertEqual(r.parse(native,mid)['status'],'ok')
            self.assertEqual(r.parse(native,mid)['usage']['output_tokens'],170)
            native['raw_response']['model'] = r.MODELS[mid]['snapshot'].removesuffix(':free')
            self.assertEqual(r.parse(native,mid)['status'],'ok')
            bad = copy.deepcopy(good)
            bad['raw_response']['answers']['decision']['choice'] = '3 because ON'
            self.assertIsNone(r.parse(bad,mid)['choice'])

    def test_cost_zero_is_receipt_not_invented(self):
        good = response('mammoth1')
        self.assertEqual(r.parse(good,'mammoth1')['accounted_cost_usd'],0)
        del good['raw_response']['usage']['cost']
        parsed = r.parse(good,'mammoth1')
        self.assertIsNone(parsed['accounted_cost_usd'])
        self.assertEqual(parsed['cost_source'],'unreported')

    def test_median_screen_not_mean_or_one_slow_outlier(self):
        rows = [dict(attempt=1,latency_ms=2100) for _ in range(19)]
        self.assertFalse(r.speed_stop(rows))
        self.assertTrue(r.speed_stop(rows+[dict(attempt=1,latency_ms=2100)]))
        self.assertFalse(r.speed_stop([dict(attempt=1,latency_ms=2000) for _ in range(20)]))
        rows = [dict(attempt=1,latency_ms=200) for _ in range(20)]
        self.assertFalse(r.speed_stop(rows+[dict(attempt=1,latency_ms=90000)]))
        self.assertFalse(r.speed_stop(rows+[dict(attempt=2,latency_ms=90000) for _ in range(21)]))


if __name__ == '__main__':
    unittest.main()
