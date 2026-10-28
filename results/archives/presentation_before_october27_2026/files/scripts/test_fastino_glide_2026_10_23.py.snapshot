import base64
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import fastino_glide_2026_10_23 as r


class FastinoTests(unittest.TestCase):
    def response(self, **kwargs):
        raw = dict(model='glide_v2', answers=dict(decision=dict(choice='3',
            probabilities={'1':.05,'2':.05,'3':.8,'4':.05,'5':.05})),
            usage=dict(input_tokens=100, output_tokens=0))
        raw.update(kwargs)
        return dict(http_status=200, error='', raw_response=raw)

    def test_all_1342_text_inputs_unchanged(self):
        qs, plan = r.text_bank.prepare()
        self.assertEqual(len(qs), 1342)
        self.assertEqual(len(plan), 1342)
        for q in qs.values():
            body = r.payload(q, 'text', {})
            self.assertEqual({k:v for k,v in body.items() if k not in ('store','model')}, q['native_input'])
            self.assertIs(body['store'], False)
            self.assertNotIn('messages', body)

    def test_identity_output_and_calculated_not_reported_cost(self):
        row = r.parse(self.response(), set('12345'))
        self.assertEqual(row['status'], 'ok')
        self.assertTrue(row['probabilities_valid'])
        self.assertIsNone(row['reported_cost_usd'])
        self.assertEqual(row['accounted_cost_usd'], .000004)
        self.assertEqual(row['cost_source'], 'usage_times_published_tariff')
        self.assertEqual(r.parse(self.response(model='glide'), set('12345'))['status'], 'identity_mismatch')
        self.assertEqual(r.parse(self.response(reasoning='explanation'), set('12345'))['status'], 'unexpected_reasoning')

    def test_invalid_and_absent_usage_are_not_zero(self):
        for tokens in (None, True, -1, '100'):
            row = r.parse(self.response(usage={'input_tokens':tokens}), set('12345'))
            self.assertIsNone(row['accounted_cost_usd'])
            self.assertEqual(row['cost_source'], 'unreported')
        row = r.parse(self.response(usage={'cost':.01}), set('12345'))
        self.assertEqual(row['accounted_cost_usd'], .01)
        self.assertEqual(row['cost_source'], 'api_reported')

    def test_native_tokens_are_not_thinking_and_bad_probs_keep_choice(self):
        response = self.response(usage={'input_tokens':100, 'output_tokens':5})
        response['raw_response']['answers']['decision']['probabilities'] = {'3': 1}
        row = r.parse(response, set('12345'))
        self.assertEqual(row['status'], 'ok')
        self.assertEqual(row['choice'], '3')
        self.assertFalse(row['probabilities_valid'])
        response['raw_response']['answers']['decision']['choice'] = '3 because...'
        self.assertIsNone(r.parse(response, set('12345'))['choice'])
        response['http_status'] = 503
        self.assertEqual(r.parse(response, set('12345'))['status'], 'http_failure')

    def test_speed_gate_uses_all_first_attempts_not_recoveries(self):
        slow = [dict(attempt=1, latency_ms=2001, status='http_failure') for _ in range(20)]
        self.assertFalse(r.speed_stop(slow[:19]))
        self.assertTrue(r.speed_stop(slow))
        self.assertFalse(r.speed_stop([dict(x, latency_ms=2000) for x in slow]))
        self.assertTrue(r.speed_stop(slow + [dict(attempt=2, latency_ms=1) for _ in range(25)]))

    def test_images_use_exact_bytes_and_original_prompt(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'image.png'
            raw = b'unchanged-byte-control'
            path.write_bytes(raw)
            q = dict(asset_ids=['A'], question='Which?', rules='Original rules.',
                options=[dict(id='a',text='First'), dict(id='b',text='Second')])
            body = r.image_payload(q, {'A':dict(path=str(path), mime='image/png', sha256=sha256(raw).hexdigest())})
            encoded = body['state'][0]['image_url']['url'].split(',',1)[1]
            self.assertEqual(base64.b64decode(encoded), raw)
            self.assertEqual(body['questions']['decision']['instructions'], 'Which?\n\nRules: Original rules.')
            self.assertEqual(body['questions']['decision']['criteria'], {'a':'First','b':'Second'})
            with self.assertRaises(AssertionError):
                r.image_payload(dict(q, asset_ids=['A']*5), {'A':dict(path=str(path))})

    @unittest.skipUnless(((r.VISUAL/'image_models_2026_10_20.py').exists() or (r.VISUAL/'scripts/image_models_2026_10_20.py').exists()) and
        (r.ROOT/'runs/visual_benchmark_curation_PRIVATE/codex_execution_2026-10-15/run_01/input_variant_manifest.json').exists(),
        'Owner-only frozen image fixture; public CI verifies exported image hashes instead')
    def test_image_frozen_inputs_and_original_order(self):
        image = r.image_bank()
        qs, assets, order = image.inputs()
        self.assertEqual(len(qs), 200)
        self.assertEqual(len(assets), 227)
        for q in qs.values():
            original = image.payload(q, assets, 'pplx_decider12')
            actual = r.image_payload(q, assets)
            self.assertEqual({k:v for k,v in actual.items() if k not in ('model','store')},
                {k:v for k,v in original.items() if k not in ('model','provider')})
        self.assertEqual(len(set(order)), 200)


if __name__ == '__main__':
    unittest.main()
