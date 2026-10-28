"""Offline integration checks for the refreshed eleven-model publication."""
from repo_layout import repo_file
from repo_layout import frozen_file
from copy import deepcopy
from hashlib import sha256
import json
import unittest

import decision_refresh as d
import matched_analysis as a


class Matched(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads((a.MATCHED/'summary.json').read_text())
        cls.old = json.loads((a.EXPANSION/'summary.json').read_text())

    def test_complete_and_scores(self):
        self.assertEqual(self.summary['total_scored_model_questions'],12496)
        for m,score in [('jev113',919),('jev114',929),('luna_decisions',677)]:
            result = self.summary['models'][m]
            self.assertEqual(result['primary']['correct'],score)
            self.assertEqual(result['primary']['attempted'],1136)
            self.assertEqual(result['latency_first_all']['n'],1136)
            self.assertEqual(set(result['dates_toronto']),{'2026-10-15'})

    def test_eight_llms_unchanged(self):
        for m in a.LLMS:
            self.assertEqual(self.summary['models'][m],self.old['models'][m])
            for family in self.summary['by_family']:
                previous = next(f for f in self.old['by_family'] if f['family_id']==family['family_id'])
                self.assertEqual(family['models'][m],previous['models'][m])

    def test_selected_sources_frozen(self):
        for name,expected in self.summary['source_files_sha256'].items():
            self.assertEqual(sha256(frozen_file(repo_file(name, root=a.ROOT)).read_bytes()).hexdigest(),expected)

    def test_native_refresh_all_attempts(self):
        first,eventual,attempts = a.validate_refresh()
        self.assertEqual(len(first),3408)
        self.assertEqual(len(attempts),3441)
        self.assertEqual(sum(r['status']!='ok' for r in first.values()),33)
        self.assertEqual(sum(r['status']!='ok' for r in eventual.values()),28)

    def test_sanitization(self):
        raw = {'id':'test','user_id':'private','usage':{'cost':.1,'is_byok':True},
               'answers':{'decision':{'choice':'3','confidence':.8}},'internal_account':{'secret':'hidden'}}
        cleaned = a.sanitize_raw(raw)
        self.assertNotIn('user_id',cleaned)
        self.assertNotIn('is_byok',cleaned['usage'])
        self.assertNotIn('internal_account',cleaned)
        self.assertEqual(cleaned['answers']['decision']['choice'],'3')

    def test_rerun_net_and_category_changes(self):
        for m in ('jev113','jev114','luna_decisions'):
            r=self.summary['repeat_comparison'][m]
            self.assertEqual(r['old_to_new']['only_b_correct']-r['old_to_new']['only_a_correct'],
                             self.summary['models'][m]['primary']['correct']-r['previous_primary']['correct'])
        family={f['family_id']:f for f in self.summary['by_family']}
        self.assertEqual(family['F07']['models']['jev113']['correct'],family['F07']['models']['jev114']['correct'])
        self.assertLess(family['F13']['models']['jev114']['correct'],family['F13']['models']['jev113']['correct'])

    def test_aggregate_counts_and_cost(self):
        s=self.summary
        self.assertEqual(s['total_selected_reported_cost']['exact_usd'],'0.320965195')
        self.assertEqual(s['refresh_total_reported_cost']['exact_usd'],'0.093876324')
        for m,r in s['models'].items():
            p=r['primary']
            self.assertEqual(p['correct']+p['wrong']+p['unanswered'],1136)
            self.assertEqual(sum(f['models'][m]['correct'] for f in s['by_family']),p['correct'])


if __name__=='__main__':
    unittest.main()
