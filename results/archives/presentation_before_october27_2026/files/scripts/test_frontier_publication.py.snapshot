from repo_layout import repo_file
from copy import deepcopy
import json
import unittest

import publish_frontier_references as b


def report(model='openai/gpt-6-sol'):
    old=json.loads((repo_file('consolidated_2026-10-19/statistics.json', root=b.ROOT)).read_text())['models']['respan02']
    stats=deepcopy(old)
    stats.update(statuses=stats['first_statuses'],latency_first_all={'median_ms':stats['median_ms'],'p95_ms':stats['p95_ms']},
                 cost_all_attempts={'known_usd':.8,'exact_usd':'.8','missing_attempts':0})
    return {'model':model,'statistics':stats,'route_description':'test route',
            'reasoning_description':'none','reasoning_verification_note':'test note','compatibility_probe_cost_usd':.001}


class FrontierPublication(unittest.TestCase):
    def test_only_the_three_selected_references_are_published(self):
        self.assertEqual(set(b.REFERENCE_IDS),{'openai/gpt-6-sol','anthropic/claude-sonnet-5.5','qwen3.8-max'})
        self.assertEqual(len(b.LABELS),3)

    def test_normalization_preserves_primary_denominator_and_unknown_cost(self):
        v=report();v['statistics']['cost_all_attempts']['missing_attempts']=1
        mid,m=b.normalize(v)
        self.assertEqual(mid,'reference_sol');self.assertEqual(m['n'],1342)
        self.assertEqual(m['cost']['unknown_attempts'],1);self.assertIsNone(m['cost']['exact_usd'])
        self.assertAlmostEqual(m['cost']['known_usd_per_1000'],.8/1342*1000)

    def test_hyper_quota_not_cash(self):
        _,m=b.normalize(report('qwen3.8-max'))
        self.assertIn('not cash invoice',m['cost']['scope'])

    def test_accuracy_legend_uses_continuous_endpoints(self):
        self.assertEqual(b.readable.color(1),b.readable.color(1.0))
        self.assertNotEqual(b.readable.color(1),b.readable.color(0))

    def test_partial_reference_rejected(self):
        v=report();v['statistics']['n']=100
        with self.assertRaises(AssertionError):b.normalize(v)

    def test_complete_publication_when_built(self):
        if not (b.DEST/'manifest.json').exists():self.skipTest('Publication has not been built; complete references still running')
        from validate_frontier_release import validate
        validate()


if __name__=='__main__':unittest.main()
