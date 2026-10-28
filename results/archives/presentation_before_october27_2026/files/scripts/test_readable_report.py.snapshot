from repo_layout import repo_file
import json
import re
import unittest

import build_readable_report as b
from validate_readable_report import Page, validate


class ReadableReport(unittest.TestCase):
    def test_fidelity_explanations_names_and_preserved_source(self):
        validate()

    def test_groups_are_complete_without_duplicates(self):
        ids = [fid for _, _, fids, _ in b.GROUPS for fid in fids]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(sorted(ids), [f'F{i:02}' for i in range(1, 32)])
        self.assertLessEqual(max(len(fids) for _, _, fids, _ in b.GROUPS), 7)

    def test_readable_svg_text_and_large_plot_labels(self):
        for slug, _, fids, _ in b.GROUPS:
            svg = (b.DEST / (slug + '.svg')).read_text()
            self.assertIn('<text', svg)
            self.assertIn('100%', svg)
            self.assertNotIn('without a prior', svg)
            self.assertIn('20 models', svg)
            self.assertGreater((b.DEST / (slug + '.png')).stat().st_size, 10000)

    def test_foreground_contrast_exceeds_four_point_five(self):
        def luminance(color):
            rgb = [int(color[i:i+2], 16)/255 for i in (1, 3, 5)]
            rgb = [x/12.92 if x <= .04045 else ((x+.055)/1.055)**2.4 for x in rgb]
            return sum(a*c for a,c in zip((.2126,.7152,.0722),rgb))
        for i in range(101):
            bg,fg = b.color(i/100)
            low,high = sorted((luminance(bg),luminance(fg)))
            self.assertGreaterEqual((high+.05)/(low+.05),4.5)

    def test_readme_and_functions_have_exact_current_stats(self):
        from archive_frontier_presentation import historical_path
        s,_ = b.load()
        text = historical_path(repo_file('README.md', root=b.ROOT)).read_text()
        lines = text.splitlines()
        start = next(i for i,line in enumerate(lines) if line.startswith('| Model | Correct /'))
        rows = []
        for line in lines[start+2:]:
            if not line.startswith('|'):
                break
            rows.append([c.strip() for c in line.strip('|').split('|')])
        self.assertEqual(len(rows),20)
        for row,mid in zip(rows,s['ranked_model_ids']):
            value=s['models'][mid]
            self.assertEqual(row[0],value['label'])
            self.assertEqual(row[1],str(value['correct']))
            self.assertEqual(row[2],f"{value['accuracy']:.1%}")
        functions = historical_path(repo_file('FUNCTIONS.md', root=b.ROOT)).read_text()
        for mid in s['ranked_model_ids']:
            m=s['models'][mid]
            for fid in b.LABELS:
                self.assertIn(b.score(m['families'][fid]),functions)

    def test_compact_mobile_rankings_and_sticky_names(self):
        html = (b.DEST / 'report.html').read_text()
        self.assertEqual(html.count('All 20 models in this category</summary>'),31)
        self.assertIn('position:sticky;left:0',html)
        self.assertIn('.category-cards{grid-template-columns:1fr}',html)
        self.assertIn('font-size:18px',html)


if __name__ == '__main__':
    unittest.main()
