from repo_layout import repo_file
from decimal import Decimal
import tempfile
from pathlib import Path
import unittest

import text_models as t


class TextModels(unittest.TestCase):
    def test_eight_models_no_duplicate_granite(self):
        self.assertEqual(len(t.MODELS), 8)
        self.assertEqual(sum(m.startswith('ibm-granite/') for m in t.MODELS), 1)

    def test_same_prompt_and_five_options(self):
        q = t.read_csv(repo_file('data/questions_1136.csv', root=t.ROOT))[0]
        messages = [t.payload(q, m)['messages'] for m in t.MODELS]
        self.assertTrue(all(message == messages[0] for message in messages))
        self.assertEqual(messages[0][0]['content'], q['prompt_text']+t.SUFFIX)

    def test_cap_provider_and_reasoning(self):
        q = {'prompt_text': 'Fixture question'}
        for m, spec in t.MODELS.items():
            p = t.payload(q, m)
            self.assertEqual(p['max_tokens'], 16)
            self.assertFalse(p['provider']['allow_fallbacks'])
            self.assertTrue(p['provider']['require_parameters'])
            self.assertEqual(p['provider']['only'], [spec[1]])
            if spec[3] == 'switchable':
                self.assertFalse(p['reasoning']['enabled'])
            else:
                self.assertNotIn('reasoning', p)

    def test_unapproved_model(self):
        with self.assertRaises(KeyError):
            t.payload({'prompt_text': 'Fixture'}, 'unapproved')

    def test_parse_strict_stop_only(self):
        r = {'http_status': 200, 'error': '', 'raw_response': {'choices': [{'finish_reason': 'stop', 'message': {'content': ' 3\n'}}]}}
        self.assertEqual(t.parse(r)['choice'], '3')
        r['raw_response']['choices'][0]['finish_reason'] = 'length'
        self.assertIsNone(t.parse(r)['choice'])

    def test_explanation_is_not_primary_choice(self):
        r = {'http_status': 200, 'error': '', 'raw_response': {'choices': [{'finish_reason': 'stop', 'message': {'content': '3. Explanation'}}]}}
        self.assertEqual(t.parse(r)['status'], 'invalid_output')
        self.assertEqual(t.leading_id({**r, 'output_text': '3. Explanation'}), '3')

    def test_leading_id_not_any_number(self):
        for text in ['Answer: 3', '30', '3rd', '6', '']:
            self.assertIsNone(t.leading_id({'http_status': 200, 'error': '', 'output_text': text}))

    def test_money_is_exact_and_missing_is_unknown(self):
        d = t.money([{'reported_cost_usd': .1}, {'reported_cost_usd': .2}, {'reported_cost_usd': None}])
        self.assertEqual(Decimal(d['exact_usd']), Decimal('.3'))
        self.assertEqual(d['missing_attempts'], 1)

    def test_retry_wrong_or_format_is_forbidden(self):
        with self.assertRaises(AssertionError):
            t.first_and_eventual([{'request_index': 1, 'attempt': 1, 'http_status': 200, 'transport_failure': False},
                                  {'request_index': 1, 'attempt': 2}])

    def test_quantiles(self):
        self.assertEqual(t.quantiles([1, 2, 3, 4])['median_ms'], 2.5)
        self.assertAlmostEqual(t.quantiles([1, 2, 3, 4])['p95_ms'], 3.85)

    def test_historical_speed_values_retained(self):
        s = t.historical_speeds()
        self.assertAlmostEqual(s['jev113']['saved_successful_latency_all_records']['median_ms'], 327.385)
        self.assertAlmostEqual(s['jev114']['saved_successful_latency_all_records']['median_ms'], 148.01916645956226)
        self.assertAlmostEqual(s['luna_decisions']['saved_successful_latency_all_records']['median_ms'], 222.68941700167488)
        self.assertEqual(s['luna_decisions']['shared_136_extension_saved_latency']['n'], 130)

    def test_offline_module_has_no_network_executor(self):
        source = Path(t.__file__).read_text()
        self.assertNotIn('import urllib', source)
        self.assertNotIn('OPENROUTER_API_KEY', source)


if __name__ == '__main__':
    unittest.main()
