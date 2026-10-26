import json
import unittest

import publish_opus5_reference as b


class OpusPublication(unittest.TestCase):
    def test_current_release(self):
        from validate_opus5_release import validate
        s = validate()
        self.assertEqual(s['models'][b.MID]['correct'],1109)

    def test_old_model_measurements_are_unchanged(self):
        s = json.loads((b.DEST/'statistics.json').read_text())
        old = json.loads((b.previous.DEST/'statistics.json').read_text())
        for mid,model in old['models'].items(): self.assertEqual(s['models'][mid],model)

    def test_pale_yellow_llm_graph_label_and_missing_charge_marker(self):
        s = json.loads((b.DEST/'statistics.json').read_text())
        self.assertIn(b.MID,s['reference_model_ids'])
        self.assertEqual(s['model_kinds'][b.MID],'LLM reference')
        svg = (b.DEST/'accuracy_speed_cost.svg').read_text()
        self.assertIn('Opus 5',svg)
        self.assertIn('82.6%',svg)
        self.assertIn('fill-opacity: 0.6',svg)
        self.assertIn('+ ?',svg)


if __name__ == '__main__':
    unittest.main()
