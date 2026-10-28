import json
import unittest

import publish_direct_decisions as b


class DirectPublication(unittest.TestCase):
    def test_full_publication(self):
        if not (b.DEST/'manifest.json').exists():self.skipTest('Not built')
        from validate_direct_release import validate
        validate()

    def test_free_access_has_no_fake_numeric_price(self):
        s=json.loads((b.DEST/'statistics.json').read_text())
        for mid in ('d3_turbo','amos_large'):
            m=s['models'][mid]
            self.assertIsNone(m['cost']['known_usd'])
            self.assertIsNone(m['cost']['known_usd_per_1000'])
            self.assertEqual(b.price(mid,m),'Free public access*')

    def test_previous_measurements_preserved_exactly(self):
        old=json.loads((b.BASE/'statistics.json').read_text())
        new=json.loads((b.DEST/'statistics.json').read_text())
        for mid,m in old['models'].items():self.assertEqual(m,new['models'][mid])

    def test_partial_summary_not_accepted(self):
        # Synthetic aggregate, no private key or completed run required in CI.
        v={'complete':False}
        with self.assertRaises(AssertionError):b.normalize('d3_turbo',v)
        v={'complete':True,'label':'d3-turbo','statistics':{
            'n':100,'families':{},'first_statuses':{'ok':100}}}
        with self.assertRaises(AssertionError):b.normalize('d3_turbo',v)

    def test_rebase_keeps_fragments_and_external_links(self):
        v='<a href="#functions">A</a><img src="rules.png"><a href="../consolidated_2026-10-19/questions_1342.csv">Q</a><a href="https://example.com">E</a>'
        out=b.rebase(v,b.NAME)
        self.assertIn('href="#functions"',out)
        self.assertIn('src="'+b.NAME+'/rules.png"',out)
        self.assertIn('href="consolidated_2026-10-19/questions_1342.csv"',out)
        self.assertIn('href="https://example.com"',out)

    def test_capabilities_are_not_an_image_score(self):
        v=json.loads((b.DEST/'image_capabilities.json').read_text())
        self.assertEqual(v['image_inference_calls'],0)
        self.assertEqual(v['status'],'DOCUMENTED_CAPABILITIES_NOT_IMAGE_SCORES')
        for item in v['models'].values():
            self.assertNotIn('accuracy',item)
            self.assertIn('source_sha256',item)


if __name__=='__main__':unittest.main()
