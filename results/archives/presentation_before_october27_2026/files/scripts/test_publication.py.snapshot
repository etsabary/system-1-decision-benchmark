from repo_layout import repo_file
from repo_layout import frozen_file
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest

from text_models import ROOT,EXPANSION,rows


def evidence_files():
    return [p for folder in (EXPANSION,repo_file('decision_refresh_2026-10-15', root=ROOT),repo_file('matched_2026-10-15', root=ROOT),
                             repo_file('additions_2026-10-16', root=ROOT),repo_file('overall_2026-10-16', root=ROOT),
                             repo_file('llm_additions_2026-10-16', root=ROOT),repo_file('overall_expanded_2026-10-16', root=ROOT))
            for p in folder.rglob('*') if p.is_file()]


class Links(HTMLParser):
    def __init__(self):super().__init__();self.targets=[]
    def handle_starttag(self,tag,attrs):
        self.targets.extend(v for k,v in attrs if k in ('href','src'))


class Publication(unittest.TestCase):
    def test_original_evidence_unchanged(self):
        for name,digest in json.loads((repo_file('data/checksums.json', root=ROOT)).read_text()).items():
            self.assertEqual(sha256(frozen_file(repo_file(name, root=ROOT)).read_bytes()).hexdigest(),digest,name)

    def test_reference_report_bytes_preserved(self):
        audit=json.loads((EXPANSION/'source_audit.json').read_text())
        for name,expected in audit['preserved_reference_reports'].items():
            self.assertEqual(sha256(frozen_file(repo_file(name, root=ROOT)).read_bytes()).hexdigest(),expected)

    def test_release_file_hashes(self):
        archive=repo_file('publication_archive_2026-10-16', root=ROOT)
        archived=json.loads((archive/'manifest.json').read_text())['files']
        self.assertEqual(set(archived),{'README.md','FUNCTIONS.md','OUTPUT_COMPLIANCE.md',
            'docs/index.html','docs/functions.html','docs/output_compliance.html','test_overall.py','test_publication.py'})
        for name, entry in archived.items():self.assertEqual(entry['archive_path'],name+'.snapshot')
        for name,digest in json.loads((EXPANSION/'release_checksums.json').read_text()).items():
            path=archive/archived[name]['archive_path'] if name in archived else repo_file(name, root=ROOT)
            if name in archived:self.assertEqual(archived[name]['sha256'],digest,name)
            self.assertEqual(sha256(frozen_file(path).read_bytes()).hexdigest(),digest,name)

    def test_no_private_fields_in_public_data(self):
        forbidden={'user_id','is_byok','gold_option','gold_text','gold_canonical','correct_first','correct_eventual',
                   'choice_first_correct','leading_id_correct_first','correct_option_id','api_key','authorization'}
        def inspect(value):
            if isinstance(value,dict):
                self.assertFalse(forbidden.intersection(value),forbidden.intersection(value))
                for v in value.values():inspect(v)
            elif isinstance(value,list):
                for v in value:inspect(v)
        # Aggregate correct_first in the already-public image summary is intentional.
        for p in evidence_files():
            if p.name=='companion_images.json':continue
            if p.suffix=='.jsonl':
                for r in rows(p):inspect(r)
            elif p.suffix=='.json':inspect(json.loads(p.read_text()))

    def test_no_secrets_or_owner_paths(self):
        for p in evidence_files():
            if p.is_file():
                text=p.read_text()
                self.assertNotIn('/Users/',text,p)
                self.assertIsNone(re.search(r'sk-(?:or-v1-)?[A-Za-z0-9_-]{24,}',text),p)

    def test_relative_site_links_and_images(self):
        for name in ['index.html','functions.html','three_model_reference.html','output_compliance.html']:
            p=repo_file('docs', root=ROOT)/name;links=Links();links.feed(p.read_text())
            for target in links.targets:
                if re.match(r'^(https?:|mailto:|#|data:)',target):continue
                self.assertTrue((p.parent/target.split('#')[0]).exists(),target)

    def test_new_and_old_figure_parity(self):
        for image in (repo_file('figures', root=ROOT)).iterdir():
            self.assertEqual(image.read_bytes(),(repo_file('docs/figures', root=ROOT)/image.name).read_bytes())

    def test_main_table_all_1136_latencies(self):
        s=json.loads((repo_file('matched_2026-10-15/summary.json', root=ROOT)).read_text())
        for m,d in s['models'].items():
            q=d['latency_first_all']
            self.assertEqual(q['n'],1136)
        # This regression describes the captured October15/16 measurements.
        # The corrected release separately checks all pooled1134+2 latencies.
        text=(repo_file('publication_archive_2026-10-16/README.md.snapshot', root=ROOT)).read_text()
        self.assertNotIn('{{',text)
        self.assertNotIn('historical',text.lower())
        current=json.loads((repo_file('overall_expanded_2026-10-16/summary.json', root=ROOT)).read_text())
        for m,d in s['models'].items():
            if m not in current['publication']['eligible_model_ids']:continue
            self.assertIn(f"{d['latency_first_all']['median_ms']:.0f} ms",text)
        self.assertIn('System 1-style',text)
        self.assertIn('327 first responses',(repo_file('publication_archive_2026-10-16/OUTPUT_COMPLIANCE.md.snapshot', root=ROOT)).read_text())

    def test_output_exclusions_applied_to_every_current_table(self):
        s=json.loads((repo_file('overall_expanded_2026-10-16/summary.json', root=ROOT)).read_text())
        for name in ('README.md','FUNCTIONS.md'):
            text=(repo_file(name, root=ROOT)).read_text()
            rows=[line for line in text.splitlines() if line.startswith('|')]
            for m in s['publication']['excluded_model_ids']:
                self.assertFalse(any(s['models'][m]['label'] in row for row in rows),(name,m))
        import csv
        with (repo_file('overall_expanded_2026-10-16/family_comparison.csv', root=ROOT)).open() as f:
            fields=csv.DictReader(f).fieldnames
        for m in s['publication']['excluded_model_ids']:
            self.assertNotIn(s['models'][m]['label'],fields)


if __name__=='__main__':unittest.main()
