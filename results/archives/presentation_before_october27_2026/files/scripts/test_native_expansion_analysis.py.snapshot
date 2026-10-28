"""Offline integrity, privacy and aggregate checks for the October 18 expansion."""
from repo_layout import repo_file
from repo_layout import frozen_file
from hashlib import sha256
import json
import re
import unittest

import native_expansion_analysis as a


class NativeExpansionAnalysis(unittest.TestCase):
    def test_native_sanitization(self):
        raw={'user_id':'private','provider':'Liquid','model':'m',
             'answers':{'decision':{'choice':'2','confidence':.7,'probabilities':{'1':.3,'2':.7},'secret':'private'}},
             'usage':{'cost':.0001,'input_tokens':100,'is_byok':True,'cost_details':{'private':True}}}
        value=a.prior.sanitize_raw(raw)
        self.assertNotIn('user_id',value)
        self.assertNotIn('secret',value['answers']['decision'])
        self.assertNotIn('is_byok',value['usage'])
        self.assertNotIn('cost_details',value['usage'])
        self.assertEqual(value['answers']['decision']['choice'],'2')

    def test_missing_cost_not_zero(self):
        records=[{'accounted_cost_usd':.001,'reported_cost_usd':.001,'cost_source':'api_reported'},
                 {'accounted_cost_usd':None,'reported_cost_usd':None,'cost_source':'unreported'}]
        value=a.native16.accounted_money(records)
        self.assertEqual(value['known_usd'],.001)
        self.assertEqual(value['missing_attempts'],1)
        self.assertEqual(value['accounted_attempts'],1)

    def test_complete_ledgers(self):
        exported=0
        for model in a.runner.MODELS:
            if (a.PUBLIC/model/'checksums.json').exists():
                first,eventual,attempts=a.validate_model(model)
                self.assertEqual(len(first),1136)
                self.assertEqual(len(eventual),1136)
                self.assertGreaterEqual(len(attempts),1136)
                exported+=1
        self.assertGreater(exported,0)

    def test_preserved_prior_results_and_family_totals(self):
        p=a.OVERALL/'summary.json'
        if not p.exists(): self.skipTest('Aggregate expansion not generated yet')
        s=json.loads(p.read_text())
        base=json.loads(a.BASE.read_text())
        for m,value in base['models'].items(): self.assertEqual(s['models'][m],value)
        for family,old in zip(s['by_family'],base['by_family']):
            for m,value in old['models'].items(): self.assertEqual(family['models'][m],value)
        self.assertEqual(s['model_count'],36)
        self.assertEqual(s['total_scored_model_questions'],36*1136)
        self.assertEqual(len(s['native_added_october_18_model_ids']),14)
        self.assertEqual(s['stopped_model_ids'],['solar_decide'])
        self.assertFalse(s['pending_model_ids'])
        for m,value in s['models'].items():
            self.assertEqual(sum(f['models'][m]['correct'] for f in s['by_family']),value['primary']['correct'])
            self.assertEqual(value['primary']['correct']+value['primary']['wrong']+value['primary']['unanswered'],1136)
            c=s['output_compliance'][m]
            self.assertEqual(c['usable_first_answers']+c['model_output_failures']+c['provider_transport_failures'],1136)
        self.assertEqual(set(s['publication']['excluded_model_ids']),set(base['publication']['excluded_model_ids']))

    def test_summary_sources_and_timer_costs(self):
        if not (a.OVERALL/'summary.json').exists(): self.skipTest('Aggregate expansion not generated yet')
        a.validate_summary()

    def test_nimble_price_note_is_not_a_replacement_run(self):
        from decimal import Decimal
        note=json.loads((a.OVERALL/'current_pricing_note.json').read_text())
        prior=json.loads(a.BASE.read_text())['models']['nimble_v4_max']
        calculated=Decimal(prior['input_tokens_all_attempts'])*Decimal(note['current_input_usd_per_million'])/10**6
        self.assertEqual(calculated,Decimal(note['same_saved_usage_at_current_tariff_usd']))
        self.assertTrue(note['counterfactual_not_new_measurement'])
        self.assertEqual(Decimal(str(prior['cost_all_attempts']['known_usd'])),Decimal(note['historical_benchmark_cost_preserved_usd']))

    def test_no_private_data_in_new_exports(self):
        forbidden={'user_id','is_byok','gold_option','gold_text','gold_canonical','correct_first',
                   'correct_eventual','choice_first_correct','correct_option_id','api_key','authorization'}
        def inspect(value):
            if isinstance(value,dict):
                self.assertFalse(forbidden.intersection(value))
                for v in value.values():inspect(v)
            elif isinstance(value,list):
                for v in value:inspect(v)
        for folder in (a.PUBLIC,a.OVERALL):
            for p in folder.rglob('*'):
                if p.suffix not in ('.json','.jsonl','.csv','.md','.svg'):continue
                text=p.read_text()
                self.assertNotIn('/Users/',text,p)
                self.assertIsNone(re.search(r'sk-(?:or-v1-)?[A-Za-z0-9_-]{24,}',text),p)
                if p.suffix=='.json':inspect(json.loads(text))
                elif p.suffix=='.jsonl':
                    for line in text.splitlines():
                        if line.strip():inspect(json.loads(line))

    def test_user_stopped_partial_not_ranked_or_replayed(self):
        if not (a.PUBLIC/'solar_decide_partial/checksums.json').exists():self.skipTest('Partial export pending')
        records,receipt=a.validate_partial()
        self.assertEqual(len(records),347)
        self.assertEqual(receipt['dispatched_attempts'],348)
        self.assertTrue(receipt['do_not_replay_unresolved_dispatches'])
        self.assertEqual(receipt['unresolved_dispatches'],[{'request_index':347,'attempt':1}])

    def test_review_graphics_and_links(self):
        report=repo_file('NATIVE_DECISION_EXPANSION.md', root=a.ROOT)
        integrity=a.OVERALL/'graphics_integrity.json'
        if not report.exists() or not integrity.exists():self.skipTest('Review figures not generated yet')
        value=json.loads(integrity.read_text())
        self.assertEqual(value['source_summary_sha256'],sha256((a.OVERALL/'summary.json').read_bytes()).hexdigest())
        for name,expected in value['files_sha256'].items():
            self.assertEqual(sha256(frozen_file(repo_file(name, root=a.ROOT)).read_bytes()).hexdigest(),expected)
        text=report.read_text()
        for name in re.findall(r'\]\(([^)]+)\)',text):
            if not name.startswith('https:'):self.assertTrue((report.parent/name).exists(),name)
        self.assertNotIn('{{',text)
        rows=[line for line in text.splitlines() if line.startswith('|')]
        summary=json.loads((a.OVERALL/'summary.json').read_text())
        for m in summary['publication']['excluded_model_ids']:
            self.assertFalse(any(summary['models'][m]['label'] in row for row in rows))

    def test_local_review_seal(self):
        p=a.OVERALL/'review_checksums.json'
        if not p.exists():self.skipTest('Review not sealed yet')
        for name,h in json.loads(p.read_text()).items():
            self.assertEqual(sha256(frozen_file(repo_file(name, root=a.ROOT)).read_bytes()).hexdigest(),h,name)


if __name__=='__main__': unittest.main()
