"""Offline native Tev adapter and frozen chat-engine isolation regressions."""
import argparse
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import llm_field_2026_10_18 as ordinary
import tev_native_adapter_2026_10_18 as n


class TevNativeAdapter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.questions, cls.plan = n.prepare()
        cls.question = cls.questions[cls.plan[0]['item_id']]

    def response(self, choice='2'):
        return {'http_status': 200, 'error': '', 'transport_failure': False,
                'response_headers': {}, 'headers_latency_ms': 60, 'latency_ms': 80,
                'started': {'utc': 'test'}, 'completed': {'utc': 'test'},
                'raw_response': {'id': 'test', 'provider': 'Together',
                                 'model': n.MODELS[n.MODEL_ID]['snapshot'],
                                 'answers': {'decision': {'choice': choice, 'confidence': .8,
                                                         'probabilities': {'1': .05, '2': .8, '3': .05, '4': .05, '5': .05}}},
                                 'usage': {'input_tokens': 100, 'output_tokens': 1, 'cost': .0000042}}}

    def metadata(self):
        return {'architecture': {'input_modalities': ['text'], 'output_modalities': ['decisions']},
                'endpoints': [{'name': 'Together | togethercomputer/tev1-4b-experimental-20260923',
                               'provider_name': 'Together', 'tag': 'together', 'status': 0,
                               'service_tier': None, 'supported_parameters': [], 'max_completion_tokens': 8,
                               'pricing': {'prompt': '0.000000042', 'completion': '0'}}]}

    def fixture(self, out):
        n.freeze(n.MODEL_ID, out, self.plan)
        n.d.save_bound(out / 'model_metadata.json', {'model_id': n.MODEL_ID, 'data': self.metadata()})
        task = {**self.plan[0], 'attempt': 1, 'stage': 'compatibility_probe'}
        response = n.sanitize_response(self.response())
        record = {**task, **response, **n.parse(response)}
        n.d.append(out / 'probe_dispatches.jsonl', {**task, 'dispatch': {'utc': 'test'}})
        n.d.append(out / 'probe_attempts.jsonl', record)
        n.d.save_bound(out / 'compatibility_probe.json', record)

    def test_isolated_module_does_not_modify_frozen_ordinary_chat(self):
        self.assertIsNot(n.engine, ordinary)
        self.assertEqual(len(ordinary.MODELS), 10)
        self.assertEqual(len(n.engine.MODELS), 1)
        self.assertEqual(ordinary.MODELS['tev1_4b']['path'], '/api/v1/chat/completions')
        self.assertEqual(n.MODELS[n.MODEL_ID]['path'], '/api/alpha/decisions')
        self.assertNotIn('answers', ordinary.sanitize_response(self.response())['raw_response'])
        self.assertIn('answers', n.sanitize_response(self.response())['raw_response'])

    def test_exact_frozen_native_input_and_full_original_order(self):
        _, original = ordinary.prepare('gemma4_31b')
        self.assertEqual([p['item_id'] for p in self.plan], [p['item_id'] for p in original])
        self.assertEqual(len(self.plan), 1136)
        self.assertEqual([p['wave'] for p in self.plan], [i // 2 + 1 for i in range(1136)])
        body = n.payload(self.question)
        self.assertEqual({k: body[k] for k in ('state', 'questions')}, n.d.packet(self.question))
        self.assertNotIn('messages', body)
        self.assertNotIn('max_tokens', body)
        self.assertNotIn('temperature', body)
        self.assertNotIn('reasoning', body)
        self.assertEqual(body['provider'], {'only': ['together'], 'allow_fallbacks': False, 'require_parameters': True})
        self.assertEqual(n.d.digest(body), self.plan[0]['request_payload_sha256'])

    def test_accurate_architecture_and_native_limits_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            n.freeze(n.MODEL_ID, out, self.plan)
            value = json.loads((out / 'manifest.json').read_text())
            self.assertIn('generative', value['classification'])
            self.assertIsNone(value['max_tokens'])
            self.assertIn('not prove', value['architecture_limit'])
            sources = json.loads((out / 'software.json').read_text())
            self.assertIn('llm_field_2026_10_18.py', sources)
            self.assertIn('tev_native_adapter_2026_10_18.py', sources)
            self.assertIn('test_tev_native_adapter_2026_10_18.py', sources)

    def test_native_choice_and_usage_preserved_without_account_metadata(self):
        response = self.response()
        response['raw_response']['user_id'] = 'private'
        response['raw_response']['usage']['cost_details'] = {'account': 'private'}
        clean = n.sanitize_response(response)
        self.assertNotIn('private', json.dumps(clean))
        record = n.parse(clean)
        self.assertEqual(record['choice'], '2')
        self.assertTrue(record['probabilities_valid'])
        self.assertEqual(record['usage']['input_tokens'], 100)
        self.assertEqual(record['accounted_cost_usd'], .0000042)
        n.check_identity({'model_id': n.MODEL_ID, **clean, **record})

    def test_rounding_warning_does_not_discard_valid_native_choice(self):
        response = self.response()
        response['raw_response']['answers']['decision']['probabilities']['2'] = .799
        record = n.parse(n.sanitize_response(response))
        self.assertEqual(record['status'], 'ok')
        self.assertEqual(record['choice'], '2')
        self.assertFalse(record['probabilities_valid'])

    def test_no_recovery_for_malformed_choice_or_http200_error(self):
        response = self.response('A')
        record = n.parse(n.sanitize_response(response))
        self.assertEqual(record['status'], 'invalid_answer')
        self.assertTrue(record['model_output_failure'])
        self.assertFalse(n.retryable({**response, **record}))
        response['raw_response'] = {'error': {'message': 'upstream failed', 'code': 502}}
        record = {'model_id': n.MODEL_ID, **response, **n.parse(response)}
        self.assertEqual(record['status'], 'provider_error')
        self.assertFalse(record['model_output_failure'])
        self.assertIsNone(record['choice'])
        self.assertFalse(n.retryable(record))
        n.check_identity(record)

    def test_metadata_native_modality_tariff_and_pin(self):
        n.validate_metadata(self.metadata())
        wrong = self.metadata()
        wrong['endpoints'][0]['pricing']['prompt'] = '.042'
        with self.assertRaises(AssertionError): n.validate_metadata(wrong)
        wrong = self.metadata()
        wrong['architecture']['output_modalities'] = ['text']
        with self.assertRaises(AssertionError): n.validate_metadata(wrong)

    def test_first100_then_authorized_chunk_and_no_duplicate_requests(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            self.fixture(out)
            args = argparse.Namespace(model=n.MODEL_ID, out=out, execute=True,
                                      continue_receipt=None, waves=0)
            calls = []
            def fake_send(body, key, cfg):
                self.assertEqual(cfg['path'], '/api/alpha/decisions')
                calls.append(n.sha256(body).hexdigest())
                return self.response()
            with patch.object(n.d, 'api_key', return_value='test'), patch.object(n.old, 'send', side_effect=fake_send), redirect_stdout(io.StringIO()):
                n.execute(args)
                self.assertEqual(len(calls), 100)
                n.execute(args)
                self.assertEqual(len(calls), 100)
                receipt = {'model_id': n.MODEL_ID, 'decision': 'continue', 'gate_result': 'pass',
                           'screen_policy': n.SCREEN_POLICY,
                           'screen_sha256': n.file_hash(out / 'screen_100.json'),
                           'manifest_sha256': n.file_hash(out / 'manifest.json'),
                           'authorized_by': 'offline test', 'reason': 'Passes external approved gates'}
                path = out / 'external_continuation.json'
                n.d.save_bound(path, receipt)
                args.continue_receipt = path
                args.waves = 50
                n.execute(args)
                self.assertEqual(len(calls), 200)
                args.waves = 0
                n.execute(args)
                self.assertEqual(len(calls), 1136)
                n.validate(n.MODEL_ID, out, require_complete=True)
            self.assertEqual(len(set(calls)), 1136)
            self.assertEqual(len(n.d.rows(out / 'results.jsonl')), 1136)


if __name__ == '__main__':
    unittest.main()
