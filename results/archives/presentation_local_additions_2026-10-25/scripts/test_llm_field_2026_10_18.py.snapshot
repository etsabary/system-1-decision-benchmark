"""Offline regressions for the answer-blind October18 chat screen executor."""
import argparse
import ast
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import llm_field_2026_10_18 as n


class ChatField(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.questions, cls.plan = n.prepare('gemma4_31b')
        cls.question = cls.questions[cls.plan[0]['item_id']]

    def response(self, model_id='gemma4_31b', text='2', cost=.00001):
        cfg = n.MODELS[model_id]
        return {'http_status': 200, 'error': '', 'transport_failure': False,
                'response_headers': {}, 'headers_latency_ms': 50,
                'started': {'utc': 'test'}, 'completed': {'utc': 'test'}, 'latency_ms': 100,
                'raw_response': {'model': cfg['snapshot'], 'provider': cfg['provider_name'],
                                 'id': 'test-request', 'choices': [{'finish_reason': 'stop',
                                                                 'message': {'role': 'assistant', 'content': text}}],
                                 'usage': {'prompt_tokens': 100, 'completion_tokens': 1,
                                           'total_tokens': 101, 'cost': cost,
                                           'completion_tokens_details': {'reasoning_tokens': 0}}}}

    def record(self, model_id='gemma4_31b', response=None):
        r = response or self.response(model_id)
        return {'model_id': model_id, **r, **n.parse(r, model_id)}

    def metadata(self, model_id='gemma4_31b'):
        cfg = n.MODELS[model_id]
        params = [] if model_id == 'tev1_4b' else ['max_tokens', 'reasoning']
        return {'architecture': {'input_modalities': ['text'], 'output_modalities': ['text']},
                'endpoints': [{'provider_name': cfg['provider_name'], 'tag': cfg['provider_tag'],
                               'status': 0, 'service_tier': None,
                               'name': cfg['provider_name'] + ' | ' + cfg['snapshot'],
                               'pricing': {'prompt': str(n.Decimal(cfg['input_usd_per_million']) / 10**6),
                                           'completion': str(n.Decimal(cfg['output_usd_per_million']) / 10**6)},
                               'supported_parameters': params, 'max_completion_tokens': 16}]}

    def args(self, out, **extra):
        return argparse.Namespace(model='gemma4_31b', out=out, execute=True,
                                  waves=0, continue_receipt=None, **extra)

    def write_probe_fixture(self, out, model_id='gemma4_31b'):
        _, plan = n.prepare(model_id)
        n.freeze(model_id, out, plan)
        n.d.save_bound(out / 'model_metadata.json', {'model_id': model_id, 'data': self.metadata(model_id)})
        task = {**plan[0], 'attempt': 1, 'stage': 'compatibility_probe'}
        record = {**task, **self.record(model_id)}
        n.d.append(out / 'probe_dispatches.jsonl', {**task, 'dispatch': {'utc': 'test'}})
        n.d.append(out / 'probe_attempts.jsonl', record)
        n.d.save_bound(out / 'compatibility_probe.json', record)

    def receipt(self, out):
        return {'model_id': 'gemma4_31b', 'decision': 'continue', 'screen_policy': n.SCREEN_POLICY,
                'screen_sha256': n.file_hash(out / 'screen_100.json'),
                'manifest_sha256': n.file_hash(out / 'manifest.json'),
                'gate_result': 'pass', 'authorized_by': 'offline-unit-test',
                'reason': 'Fixture passes the separately evaluated screen'}

    def test_ten_complete_exact_frozen_plans(self):
        self.assertEqual(len(n.MODELS), 10)
        for model_id in n.MODELS:
            questions, plan = n.prepare(model_id)
            self.assertEqual(len(plan), 1136)
            self.assertEqual([p['item_id'] for p in plan], [p['item_id'] for p in self.plan])
            self.assertEqual([p['wave'] for p in plan], [i // 2 + 1 for i in range(1136)])
            body = n.payload(questions[plan[0]['item_id']], model_id)
            self.assertEqual(n.d.digest(body), plan[0]['request_payload_sha256'])
            self.assertEqual(body['provider'], {'only': [n.MODELS[model_id]['provider_tag']],
                                               'allow_fallbacks': False, 'require_parameters': True})

    def test_regular_exact_original_suffix_and_token_cap(self):
        for model_id, cfg in n.MODELS.items():
            if model_id == 'tev1_4b':
                continue
            p = n.payload(self.question, model_id)
            self.assertEqual(p['messages'], [{'role': 'user', 'content': self.question['prompt_text'] + n.chat.SUFFIX}])
            self.assertEqual(p['max_tokens'], 16)
            self.assertNotIn('temperature', p)
            if cfg['kind'] == 'nonthinking_checkpoint':
                self.assertNotIn('reasoning', p)
            else:
                self.assertEqual(p['reasoning'], {'enabled': False})

    def test_tev_documented_adapter_preserves_all_content_and_order(self):
        p = n.payload(self.question, 'tev1_4b')
        self.assertEqual(p['messages'][0], {'role': 'system', 'content': n.TEV_SYSTEM})
        task = json.loads(p['messages'][1]['content'])
        self.assertEqual(task['state'], self.question['context'])
        self.assertEqual(task['question'], self.question['instructions'] + '\n\n' + self.question['question'])
        self.assertEqual(task['options'], [{'label': chr(64 + i), 'key': str(i),
                                           'description': self.question[f'option_{i}']} for i in range(1, 6)])
        self.assertEqual(p['max_tokens'], 8)
        self.assertEqual(p['temperature'], 0)
        self.assertTrue(p['provider']['require_parameters'])

    def test_uses_original_configurable_full_body_timer(self):
        source = Path(n.__file__).read_text()
        tree = ast.parse(source)
        self.assertFalse(any(isinstance(x, ast.FunctionDef) and x.name == 'send' for x in tree.body))
        self.assertEqual(source.count('old.send('), 2)
        self.assertTrue(all(cfg['path'] == '/api/v1/chat/completions' for cfg in n.MODELS.values()))

    def test_no_gold_lookup_or_correctness_scoring_in_executor(self):
        tree = ast.parse(Path(n.__file__).read_text())
        imports = [x.module or '' for x in ast.walk(tree) if isinstance(x, ast.ImportFrom)]
        self.assertFalse(any('score_expansion' in x or 'analysis_core' in x for x in imports))
        values = [x.value for x in ast.walk(tree) if isinstance(x, ast.Constant) and isinstance(x.value, str)]
        self.assertFalse(any('answer_key_PRIVATE' in x or 'answer_key_' in x for x in values))

    def test_strict_numeric_parse_and_cost(self):
        r = self.record()
        self.assertEqual(r['status'], 'ok')
        self.assertEqual(r['choice'], '2')
        self.assertEqual(r['accounted_cost_usd'], .00001)
        self.assertFalse(r['model_output_failure'])
        n.check_identity(r)
        for text in ('2.', 'Answer: 2', '2 because', '', 'A', '0', '6'):
            r = self.record(response=self.response(text=text))
            self.assertEqual(r['status'], 'invalid_output')
            self.assertIsNone(r['choice'])
            self.assertTrue(r['model_output_failure'])
            self.assertFalse(n.retryable(r))

    def test_tev_letter_only_and_stopped_completion(self):
        for i, letter in enumerate('ABCDE', 1):
            r = self.record('tev1_4b', self.response('tev1_4b', ' ' + letter + '\n'))
            self.assertEqual(r['choice'], str(i))
        for text in ('1', 'a', 'A.', 'A because'):
            self.assertEqual(self.record('tev1_4b', self.response('tev1_4b', text))['status'], 'invalid_output')
        r = self.response(text='2')
        r['raw_response']['choices'][0]['finish_reason'] = 'length'
        self.assertEqual(self.record(response=r)['status'], 'invalid_output')

    def test_explanation_and_refusal_not_provider_failure(self):
        r = self.response(text='The correct answer is option 2')
        self.assertTrue(self.record(response=r)['model_output_failure'])
        r['raw_response']['choices'][0]['message']['refusal'] = 'Cannot answer'
        self.assertEqual(self.record(response=r)['status'], 'refusal')

    def test_unexpected_reasoning_halts_not_silently_excluded(self):
        for change in ('text', 'reasoning_content', 'tokens'):
            r = self.response()
            if change == 'text':
                r['raw_response']['choices'][0]['message']['reasoning'] = 'hidden work'
            elif change == 'reasoning_content':
                r['raw_response']['choices'][0]['message']['reasoning_content'] = 'hidden work'
            else:
                r['raw_response']['usage']['completion_tokens_details']['reasoning_tokens'] = 4
            record = self.record(response=r)
            self.assertEqual(record['status'], 'unexpected_reasoning')
            with self.assertRaises(AssertionError):
                n.check_identity(record)

    def test_identity_and_missing_cost_success_guards(self):
        for key, value in [('provider', 'Other'), ('model_returned', 'other/model'), ('reported_cost_usd', None)]:
            with self.assertRaises(AssertionError):
                n.check_identity({**self.record(), key: value})
        n.check_identity(self.record('xing4_free', self.response('xing4_free', cost=0)))
        r = self.response('qwen3_235b')
        self.assertEqual(self.record('qwen3_235b', r)['model_returned'], 'qwen/qwen3-235b-a22b-07-25')
        n.check_identity(self.record('qwen3_235b', r))

    def test_http200_error_envelope_is_provider_failure_and_not_retried(self):
        r = self.response()
        r['raw_response'] = {'error': {'code': 502, 'message': 'upstream failed'}}
        record = self.record(response=r)
        self.assertEqual(record['status'], 'provider_error')
        self.assertFalse(record['model_output_failure'])
        self.assertFalse(n.retryable(record))
        self.assertIsNone(record['accounted_cost_usd'])
        n.check_identity(record)

    def test_transport_and_http_failure_not_output_failure(self):
        for code in (408, 429, 500, 503):
            r = self.response()
            r.update(http_status=code, error='HTTP ' + str(code))
            record = self.record(response=r)
            self.assertEqual(record['status'], 'http_failure')
            self.assertFalse(record['model_output_failure'])
            self.assertTrue(n.retryable(record))
        r = self.response()
        r.update(error='body-read timeout', transport_failure=True)
        record = self.record(response=r)
        self.assertEqual(record['status'], 'transport_failure')
        self.assertIsNone(record['choice'])
        self.assertFalse(record['model_output_failure'])

    def test_malformed_envelopes_do_not_crash_parser(self):
        for raw in ([], None, {'choices': 'bad'}, {'choices': [None]},
                    {'choices': [{'message': 'bad'}]}, {'usage': 'bad'},
                    {'choices': [{'message': {'content': ['2']}}]}):
            r = self.response()
            r['raw_response'] = raw
            self.assertIsNone(self.record(response=r)['choice'])

    def test_account_fields_never_retained(self):
        r = self.response()
        r['raw_response'].update(user_id='private-user', is_byok=True,
                                  provider_metadata={'account': 'private'})
        r['raw_response']['usage']['cost_details'] = {'account': 'private'}
        r['raw_response']['choices'][0]['message']['reasoning_details'] = [{'account_id': 'private'}]
        clean = n.sanitize_response(r)
        serialized = json.dumps(clean)
        self.assertNotIn('private', serialized)
        self.assertNotIn('user_id', serialized)
        self.assertNotIn('cost_details', serialized)
        self.assertEqual(n.parse(clean, 'gemma4_31b')['status'], 'unexpected_reasoning')
        r['raw_response']['choices'][0]['message'].pop('reasoning_details')
        r['raw_response']['choices'][0]['message']['reasoning_content'] = 'hidden work'
        self.assertEqual(n.parse(n.sanitize_response(r), 'gemma4_31b')['status'], 'unexpected_reasoning')

    def test_metadata_prices_provider_and_parameter_checks(self):
        for model_id in n.MODELS:
            n.validate_metadata(self.metadata(model_id), model_id)
        bad = self.metadata()
        bad['endpoints'][0]['pricing']['prompt'] = '0.1'
        with self.assertRaises(AssertionError): n.validate_metadata(bad, 'gemma4_31b')
        bad = self.metadata()
        bad['endpoints'][0]['supported_parameters'] = ['max_tokens']
        with self.assertRaises(AssertionError): n.validate_metadata(bad, 'gemma4_31b')
        bad['endpoints'][0]['service_tier'] = 'priority'
        with self.assertRaises(AssertionError): n.validate_metadata(bad, 'gemma4_31b')

    def test_unresolved_dispatch_cannot_be_replayed(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            n.d.append(out / 'dispatches.jsonl', {**self.plan[0], 'attempt': 1})
            with self.assertRaisesRegex(AssertionError, 'Unresolved dispatch'):
                n.ledger_state(out, self.plan)

    def test_source_binding_and_freeze_are_immutable(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            n.freeze('gemma4_31b', out, self.plan)
            n.freeze('gemma4_31b', out, self.plan)
            manifest = json.loads((out / 'manifest.json').read_text())
            self.assertEqual(manifest['screen_policy']['hold_if_accuracy_below'], .5)
            self.assertEqual(manifest['screen_policy']['hold_if_model_output_failures_fraction_at_least'], .05)
            with patch.object(n, 'GUARD', n.Decimal('1.00')):
                with self.assertRaises(AssertionError):
                    n.freeze('gemma4_31b', out, self.plan)

    def test_dry_run_does_not_call_api_or_write(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'absent'
            args = self.args(out)
            args.execute = False
            with patch.object(n.old, 'send', side_effect=AssertionError('paid call forbidden')):
                n.execute(args)
            self.assertFalse(out.exists())

    def test_100_screen_stops_and_bound_receipt_continues_without_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            self.write_probe_fixture(out)
            calls = []
            def fake_send(body, key, cfg):
                calls.append(n.sha256(body).hexdigest())
                return self.response()
            with patch.object(n.d, 'api_key', return_value='test-key'), patch.object(n.old, 'send', side_effect=fake_send), redirect_stdout(io.StringIO()):
                n.execute(self.args(out))
                self.assertEqual(len(calls), 100)
                self.assertEqual(len(n.d.rows(out / 'results.jsonl')), 100)
                self.assertEqual(json.loads((out / 'screen_100.json').read_text())['status'], 'SCREEN_100_COMPLETE')
                n.execute(self.args(out))
                self.assertEqual(len(calls), 100)
                receipt_path = out / 'external_receipt.json'
                n.d.save_bound(receipt_path, self.receipt(out))
                args = self.args(out)
                args.continue_receipt = receipt_path
                n.execute(args)
                n.execute(args)
            self.assertEqual(len(calls), 1136)
            self.assertEqual(len(set(calls)), 1136)
            self.assertEqual(len(n.d.rows(out / 'results.jsonl')), 1136)
            n.validate('gemma4_31b', out, require_complete=True)
            n.verify_prefixes(out, json.loads((out / 'screen_100.json').read_text())['files_prefix_binding'])

    def test_execution_retries_transport_once_never_malformed_output(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            self.write_probe_fixture(out)
            first_hash = self.plan[0]['request_payload_sha256']
            second_hash = self.plan[1]['request_payload_sha256']
            calls = []
            def fake_send(body, key, cfg):
                body_hash = n.sha256(body).hexdigest()
                calls.append(body_hash)
                if body_hash == first_hash and calls.count(first_hash) == 1:
                    response = self.response()
                    response.update(http_status=429, error='HTTP429')
                    response['raw_response'] = {'error': {'message': 'rate limit'}}
                    return response
                return self.response(text='2 because' if body_hash == second_hash else '2')
            with patch.object(n.d, 'api_key', return_value='test-key'), patch.object(n.old, 'send', side_effect=fake_send), patch.object(n.d, 'retry_wait', return_value=0), redirect_stdout(io.StringIO()):
                n.execute(self.args(out))
            attempts, results, _, done = n.ledger_state(out, self.plan)
            self.assertEqual(len(done), 100)
            self.assertEqual(len(attempts), 101)
            self.assertEqual(calls.count(first_hash), 2)
            self.assertEqual(calls.count(second_hash), 1)
            first, eventual = n.chat.first_and_eventual(attempts)
            self.assertEqual(first[1]['status'], 'http_failure')
            self.assertEqual(eventual[1]['status'], 'ok')
            self.assertEqual(first[2]['status'], 'invalid_output')
            self.assertEqual(len(n.d.rows(out / 'dispatches.jsonl')), 101)

    def test_identity_halt_stores_received_attempt_and_terminal(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            self.write_probe_fixture(out)
            bad = self.response()
            bad['raw_response']['provider'] = 'Wrong'
            with patch.object(n.d, 'api_key', return_value='test-key'), patch.object(n.old, 'send', return_value=bad), redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(AssertionError, 'Unexpected provider'):
                    n.execute(self.args(out))
            attempts, results, _, done = n.ledger_state(out, self.plan)
            self.assertGreaterEqual(len(attempts), 1)
            self.assertEqual(len(attempts), len(results))
            self.assertEqual(len(done), len(results))
            self.assertLessEqual(len(results), 2)
            self.assertFalse((out / 'screen_100.json').exists())

    def test_foreign_failed_and_unbound_receipts_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            n.d.save_bound(out / 'screen_100.json', {'status': 'SCREEN_100_COMPLETE', 'screened_cases': 100,
                                                     'files_prefix_binding': {}})
            n.d.save_bound(out / 'manifest.json', {'model': 'test'})
            for changed in ({'decision': 'stop'}, {'gate_result': 'fail'}, {'model_id': 'other'},
                            {'screen_sha256': 'wrong'}, {'manifest_sha256': 'wrong'}, {'authorized_by': ''}):
                receipt = {**self.receipt(out), **changed}
                path = out / 'bad_receipt.json'
                path.write_text(json.dumps(receipt))
                with self.assertRaises(AssertionError):
                    n.authorize_continuation('gemma4_31b', out, path)

    def test_prefix_tampering_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'evidence.jsonl'
            path.write_text('one\n')
            binding = {'evidence.jsonl': n.bound_prefix(path)}
            with path.open('a') as stream: stream.write('two\n')
            n.verify_prefixes(Path(directory), binding)
            path.write_text('bad\ntwo\n')
            with self.assertRaises(AssertionError): n.verify_prefixes(Path(directory), binding)

    def test_probe_replay_and_unresolved_probe_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            self.write_probe_fixture(out)
            with patch.object(n.old, 'send', side_effect=AssertionError('must not dispatch')):
                with self.assertRaisesRegex(AssertionError, 'Refusing to replay'):
                    n.probe('gemma4_31b', out)
            (out / 'probe_attempts.jsonl').unlink()
            with self.assertRaises(AssertionError): n.validate_probe('gemma4_31b', out)

    def test_one_explanatory_probe_is_diagnostic_not_100_screen_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            self.write_probe_fixture(out)
            task = {**self.plan[0], 'attempt': 1, 'stage': 'compatibility_probe'}
            record = {**task, **self.record(response=self.response(text='Because of the supplied facts, 2'))}
            (out / 'probe_attempts.jsonl').write_text(json.dumps(record) + '\n')
            (out / 'compatibility_probe.json').write_text(json.dumps(record))
            self.assertEqual(n.validate_probe('gemma4_31b', out)['status'], 'invalid_output')
            failed = {**task, **self.record(response={**self.response(), 'http_status': 429, 'error': 'HTTP429'})}
            (out / 'probe_attempts.jsonl').write_text(json.dumps(failed) + '\n')
            (out / 'compatibility_probe.json').write_text(json.dumps(failed))
            with self.assertRaises(AssertionError): n.validate_probe('gemma4_31b', out)


if __name__ == '__main__':
    unittest.main()
