"""Captured 1136-question publication regressions. No inference or answer key."""
from repo_layout import repo_file
from collections import Counter
import csv
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest

import build_corrected_report as report
import build_october18_report as web
from validate_corrected_release import validator

ROOT = Path(__file__).resolve().parents[1]
FOLDER = repo_file('corrected_2026-10-18', root=ROOT)


def presentation(name):
    """Preserve regressions on the exact superseded publication, not new rows."""
    archive = repo_file('publication_archive_2026-10-19', root=ROOT)
    if archive.exists():
        entries = json.loads((archive / 'manifest.json').read_text())['files']
        if name in entries:
            return (archive / entries[name]['archive_path']).read_text()
    return (repo_file(name, root=ROOT)).read_text()


class CorrectedRelease(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = json.loads((FOLDER / 'summary.json').read_text())
        cls.readme = presentation('README.md')

    def test_selected_evidence_checks_without_gold(self):
        result = validator().validate(FOLDER, ROOT)
        self.assertEqual(result['replacement_primary_cases'], 72)
        self.assertEqual(result['original_primary_cases_reused'], 40824)

    def test_exact_two_prompt_replacements_and_1134_identical_rows(self):
        def read(path):
            with path.open(newline='') as stream: return {r['item_id']:r for r in csv.DictReader(stream)}
        original = read(repo_file('data/questions_1136.csv', root=ROOT))
        current = read(FOLDER / 'questions_1136.csv')
        retired = set(self.s['retired_parent_ids']); fresh = set(self.s['replacement_ids'])
        self.assertEqual(set(original)-set(current), retired)
        self.assertEqual(set(current)-set(original), fresh)
        self.assertEqual(len(current), 1136)
        self.assertEqual(sum(current[i] == original[i] for i in set(current)&set(original)), 1134)
        for new in fresh:
            self.assertIn('After all the operations have been completed', current[new]['question'])
            self.assertNotIn('After every operation', current[new]['question'])

    def test_all36_main_table_rows_match_scores_pooled_speed_cost_dates(self):
        lines = self.readme.splitlines()
        begin = next(i for i,line in enumerate(lines) if line.startswith('| Model | Correct /'))
        rows = [line for line in lines[begin+2:] if line.startswith('|')][:36]
        self.assertEqual(len(rows),36)
        for line,mid in zip(rows,report.order(self.s)):
            v = self.s['models'][mid]
            cells=[c.strip() for c in line.strip('|').split('|')]
            self.assertTrue(cells[0].startswith(v['label']))
            self.assertEqual(cells[1],str(v['primary']['correct']))
            self.assertEqual(cells[2],f"{100*v['primary']['accuracy_attempted']:.1f}%")
            self.assertEqual(cells[3],f"{v['by_role']['core']['correct']}/640")
            self.assertEqual(cells[4],web.format_speed(v['latency_first_all']['median_ms']))
            self.assertEqual(cells[5],f"{v['latency_first_all']['p95_ms']:.0f} ms")
            self.assertEqual(cells[6],report.cost_cell(v))
            self.assertEqual(cells[7],report.dates(v))

    def test_order_and_ties_and_unchanged_core(self):
        old=json.loads((repo_file('overall_llm_expanded_2026-10-18/summary.json', root=ROOT)).read_text())
        self.assertEqual(report.order(self.s)[:4],['respan02','pplx_decider12','nimble_v4_max','liquid_ultra'])
        self.assertEqual(self.s['models']['tev1_4b_native']['primary']['correct'], self.s['models']['luna_decisions']['primary']['correct'])
        self.assertEqual(Counter(v['correct_delta'] for v in self.s['deltas'].values()),{0:25,-1:7,1:4})
        for mid,v in self.s['models'].items():
            self.assertEqual(v['by_role']['core'],old['models'][mid]['by_role']['core'])
            self.assertEqual(v['latency_first_all']['n'],1136)

    def test_current_function_table_has36_complete_rows_and_corrected_f13(self):
        text=presentation('FUNCTIONS.md')
        for mid,v in self.s['models'].items(): self.assertIn(v['label'],text)
        row=next(line for line in text.splitlines() if line.startswith('| Sequential procedure execution |'))
        self.assertEqual(row.count('|'),39)
        self.assertNotIn('| Nimble v4 |',text)
        self.assertNotIn('| Nimble v4 |',self.readme)
        f13=next(f for f in self.s['by_family'] if f['family_id']=='F13')
        self.assertEqual(f13['models']['respan02']['correct'],29)
        self.assertEqual(f13['models']['pplx_decider12']['correct'],10)

    def test_current_html_marker_links_images_and_color_counts(self):
        class Links(HTMLParser):
            def __init__(self):super().__init__();self.targets=[]
            def handle_starttag(self,tag,attrs):self.targets += [v for k,v in attrs if k in ('href','src')]
        for name in ('index.html','functions.html','output_compliance.html'):
            path=repo_file('docs', root=ROOT)/name;text=presentation('docs/'+name);self.assertIn(report.MARKER,text)
            parser=Links();parser.feed(text)
            for target in parser.targets:
                if re.match(r'^(https?:|mailto:|#|data:)',target):continue
                self.assertTrue((path.parent/target.split('#')[0]).exists(),target)
        html=presentation('docs/index.html')
        ranking=re.search(r'<table>.*?</table>',html,re.S).group()
        self.assertEqual(len(re.findall(r'class="[^"]*metric-speed',ranking)),36)
        self.assertEqual(len(re.findall(r'class="[^"]*metric-cost',ranking)),36)
        for p in (FOLDER/'figures').iterdir():self.assertEqual(p.read_bytes(),(repo_file('docs/figures/corrected', root=ROOT)/p.name).read_bytes())

    def test_original_release_seal_retained_with_exact_archive_bytes(self):
        from freeze_october18_release import hashes
        expected=json.loads((repo_file('overall_llm_expanded_2026-10-18/release_checksums.json', root=ROOT)).read_text())
        self.assertEqual(hashes(),expected)
        manifest=json.loads((repo_file('publication_archive_2026-10-18/manifest.json', root=ROOT)).read_text())
        for name,v in manifest['files'].items():
            self.assertEqual(sha256((repo_file('publication_archive_2026-10-18', root=ROOT)/v['archive_path']).read_bytes()).hexdigest(),expected[name])

    def test_scope_and_prose_do_not_claim_full_external_verification_or_current_v4(self):
        self.assertIn('181 had two independent verifiers',self.readme)
        self.assertIn('not establish independent verification of every',self.readme)
        self.assertIn('902/1,134 retained correct answers',self.readme)
        self.assertIn('Venice',self.readme);self.assertIn('Together',self.readme)
        self.assertNotIn('historical',self.readme.lower())
        self.assertNotIn('—',self.readme);self.assertNotIn('–',self.readme)


if __name__=='__main__':unittest.main()
