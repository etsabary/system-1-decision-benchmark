import unittest
from pathlib import Path
import repo_identity as r


class RepoIdentity(unittest.TestCase):
    def test_neutral_current_report_link(self):
        old = 'https://etsabary.github.io/' + r.OLD + '/llm_references_2026-10-19/report.html#functions'
        self.assertEqual(r.neutral_links(old), r.SITE + '/report.html#functions')

    def test_rebase_assets_without_changing_fragments(self):
        text = '<a href="#functions">X</a><img src="rules.png"><a href="../consolidated_2026-10-19/questions_1342.csv">Q</a>'
        out = r.root_report(text)
        self.assertIn('href="#functions"', out)
        self.assertIn('src="llm_references_2026-10-19/rules.png"', out)
        self.assertIn('href="consolidated_2026-10-19/questions_1342.csv"', out)

    def test_migration_when_built(self):
        if not (r.DEST / 'manifest.json').exists():
            self.skipTest('Identity migration has not been built')
        r.validate()


if __name__ == '__main__':
    unittest.main()
