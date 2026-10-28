"""Current expanded-bank publication, separate from retained capture tests."""
from repo_layout import repo_file
import json
from pathlib import Path
import re
import unittest

import publish_consolidated_report as b
import validate_consolidated_release as v


def publication_text(name):
    archive = repo_file('presentation_archive_2026-10-19', root=b.ROOT)
    if archive.exists():
        manifest = json.loads((archive / 'manifest.json').read_text())['files']
        if name in manifest:
            return (archive / manifest[name]['archive_path']).read_text()
    return (repo_file(name, root=b.ROOT)).read_text()


class ConsolidatedPublication(unittest.TestCase):
    def test_exported_bundle_consistency_and_privacy(self):
        v.validate()

    def test_all20_readme_rows_match_full_bank_statistics(self):
        s = json.loads((b.DEST / 'statistics.json').read_text())
        text = publication_text('README.md')
        lines = text.splitlines()
        begin = next(i for i, line in enumerate(lines) if line.startswith('| Model | Correct /'))
        rows = []
        for line in lines[begin + 2:]:
            if not line.startswith('|'):
                break
            rows.append([c.strip() for c in line.strip('|').split('|')])
        self.assertEqual(len(rows), 20)
        from build_october18_report import format_speed, format_cost
        for row, mid in zip(rows, s['ranked_model_ids']):
            m = s['models'][mid]
            self.assertEqual(row[0], m['label'])
            self.assertEqual(row[1], str(m['correct']))
            self.assertEqual(row[2], f"{100*m['accuracy']:.1f}%")
            self.assertEqual(row[3], format_speed(m['median_ms']))
            self.assertEqual(row[4], f"{m['p95_ms']:.0f} ms")
            self.assertEqual(row[5], ('~' if mid == 'nimble_v4_max' else '') + format_cost(m['cost']['known_usd_per_1000'], m['cost']['unknown_attempts']))
            self.assertEqual(row[6], ', '.join(m['dates_toronto']))
        for phrase in ('Thirty-seven author-development', 'not independent external verification of every original',
                       '218 attempt costs unreported', '1,136-question reference', '31 categories'):
            self.assertIn(phrase, text)
        self.assertNotIn('each actual 1,136-question run', text)

    def test_function_table_and_quality_rows(self):
        s = json.loads((b.DEST / 'statistics.json').read_text())
        functions = publication_text('FUNCTIONS.md')
        rows = [line for line in functions.splitlines() if re.match(r'^\| F\d\d[ |]', line)]
        self.assertEqual(len(rows), 62)  # 31 definitions and 31 score rows
        for f in s['families']:
            row = next(r for r in rows if r.startswith('| ' + f['family_id'] + ' ' + f['family'] + ' |'))
            cells = [c.strip() for c in row.strip('|').split('|')]
            self.assertEqual(cells[1], str(f['n']))
            self.assertEqual(cells[2:], [str(f['models'][mid]['correct']) for mid in s['ranked_model_ids']])
        from archive_frontier_presentation import historical_path
        quality = historical_path(repo_file('OUTPUT_COMPLIANCE.md', root=b.ROOT)).read_text()
        self.assertEqual(sum(line.startswith('| ') for line in quality.splitlines()), 22)

    def test_prior_seals_and_archive_bytes_are_unchanged(self):
        from freeze_corrected_release import hashes
        old = json.loads((repo_file('corrected_2026-10-18/release_checksums.json', root=b.ROOT)).read_text())
        self.assertEqual(hashes(), old)
        manifest = json.loads((repo_file('publication_archive_2026-10-19/manifest.json', root=b.ROOT)).read_text())
        self.assertEqual(len(manifest['files']), 17)
        for name, entry in manifest['files'].items():
            self.assertEqual(b.digest(repo_file('publication_archive_2026-10-19', root=b.ROOT) / entry['archive_path']), old[name])


if __name__ == '__main__':
    unittest.main()
