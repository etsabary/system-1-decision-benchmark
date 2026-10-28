"""Publication boundaries: preserve old evidence and qualify new native counters."""
from copy import deepcopy
import json
import unittest

import native_additions_evidence as evidence
import publish_native_additions_2026_10_25 as b


class NativeAdditionsPublication(unittest.TestCase):
    def test_full_release_and_historical_preservation(self):
        from validate_native_additions_2026_10_25 import validate
        self.assertEqual(validate()['model_count'],52)

    def test_label_telemetry_is_model_specific(self):
        s=json.loads((b.DEST/'statistics.json').read_text())
        for name in ('h2o-lightning-nemotron:4b','knowline:4b-gen5.5'):
            m=s['models'][b.mid(name)]
            self.assertEqual((m['observed_output_tokens'],m['answered'],m['failed']),(1,1342,0))
            self.assertIsNone(m['cost']['known_usd'])
        self.assertEqual(s['models']['celeris11_decision']['observed_output_tokens'],0)

    def test_native_compatibility_does_not_accept_explanations_or_missing_proof(self):
        raw=dict(model='h2o-lightning-nemotron:4b',answers={'decision':dict(type='choice',choice='1',
            probabilities=dict(zip('12345',[.6,.1,.1,.1,.1])))},
            usage=dict(input_tokens=10,processed_input_tokens=10,output_tokens=1),
            state_truncated=False,done_reason='decide',probability_source='native',
            effort_used=dict(tier='fast',passes_per_decision=1))
        self.assertEqual(evidence.check_native(raw,raw['model'],True),'1')
        for mutate in (
            lambda r:r.update(explanation='extra'),
            lambda r:r['effort_used'].update(passes_per_decision=2),
            lambda r:r['usage'].update(processed_input_tokens=9),
            lambda r:r.update(state_truncated=True),
        ):
            changed=deepcopy(raw);mutate(changed)
            with self.assertRaises(AssertionError):evidence.check_native(changed,raw['model'],True)

    def test_knowline_admission_history_is_resolved_without_rewriting_it(self):
        old=json.loads((b.PREVIOUS/'screened_routes.json').read_text())
        resolution=json.loads((b.DEST/'historical_admission_resolutions.json').read_text())
        self.assertEqual(resolution['original'],[r for r in old if r['model']=='knowline:4b-gen5.5'])
        self.assertEqual(len(json.loads((b.DEST/'screened_routes.json').read_text())),3)


if __name__=='__main__':unittest.main()
