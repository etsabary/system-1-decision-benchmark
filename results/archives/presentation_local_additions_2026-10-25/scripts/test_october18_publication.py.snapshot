"""Offline fixed-scale accessibility and current-release publication checks."""
from repo_layout import repo_file
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest

import build_october18_report as b


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []
    def handle_starttag(self, tag, attrs):
        self.targets.extend(v for k, v in attrs if k in ('href', 'src'))


class October18Publication(unittest.TestCase):
    def test_exact_speed_thresholds_and_labels(self):
        for value, label in [(0, '🟩 Fastest'), (250, '🟩 Fastest'), (250.01, '🟨 Fast'),
                             (500, '🟨 Fast'), (500.01, '🟧 Moderate'), (1000, '🟧 Moderate'),
                             (1000.01, '🟥 Slow')]:
            self.assertEqual(b.speed_band(value), label)

    def test_exact_cost_thresholds_and_labels(self):
        for value, label in [(0, '🟩 Lowest'), (.01, '🟩 Lowest'), (.0100001, '🟨 Low'),
                             (.025, '🟨 Low'), (.0250001, '🟧 Mid'), (.05, '🟧 Mid'),
                             (.0500001, '🟥 Highest')]:
            self.assertEqual(b.cost_band(value), label)
        self.assertEqual(b.format_speed(202), '202 ms 🟩 Fastest')
        self.assertEqual(b.format_cost(.00338), '$0.00338 🟩 Lowest')
        self.assertEqual(b.format_cost(.02, 2), '$0.02000 🟨 Low + ?')

    def test_unknown_invalid_measurements_are_gray_not_free_or_fastest(self):
        for value in (None, float('nan'), float('inf'), -1, True, 'unreported'):
            self.assertEqual(b.speed_band(value), b.UNKNOWN)
            self.assertEqual(b.cost_band(value), b.UNKNOWN)
        self.assertEqual(b.format_cost(None, 1), '⬜ Unknown + ?')

    def test_html_cell_bands_text_labels_and_incomplete_cost_underline(self):
        text = '| Speed | Known cost |\n|---|---|\n| 202 ms 🟩 Fastest | $0.02000 🟨 Low + ? |\n'
        html = b.render(text, 'Test', {})
        self.assertIn('metric-cell band-1 metric-speed', html)
        self.assertIn('metric-cell band-2 metric-cost cost-incomplete', html)
        self.assertIn('additional charges unreported', html)
        self.assertIn('202 ms 🟩 Fastest', html)
        self.assertIn('$0.02000 🟨 Low + ?', html)
        self.assertIn('text-decoration-color:#9a6700', html)
        self.assertIn('overflow-x:auto', html)
        self.assertIn(b.COHORT_MARKER, html)
        for label, index in zip(b.SPEED_LABELS, range(1, 5)):
            row = b.annotate_metric_cells('<td>' + label + '</td>')
            self.assertIn('band-' + str(index), row)
            self.assertEqual(row.count('band-'), 1)

    def test_pale_band_text_contrast_at_least_four_point_five(self):
        def luminance(color):
            rgb = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
            rgb = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055)**2.4 for x in rgb]
            return .2126 * rgb[0] + .7152 * rgb[1] + .0722 * rgb[2]
        for background in (*b.PALETTES, '#e7eaee'):
            a, c = sorted((luminance(background), luminance(b.TEXT_COLOR)))
            self.assertGreaterEqual((c + .05) / (a + .05), 4.5)

    def test_legend_is_explicit_and_does_not_call_unknown_charges_complete(self):
        legend = b.legend_markdown()
        for text in ('≤250 ms', '≤500 ms', '≤1,000 ms', '≤$0.010', '≤$0.025', '≤$0.050',
                     'known lower bound', 'unrounded', 'Text labels'):
            self.assertIn(text, legend)

    def test_links_map_pages_new_images_and_evidence(self):
        source = 'overall_llm_expanded_2026-10-18/figures/overall_accuracy.png'
        mapping = {source: 'figures/october18/overall_accuracy.png'}
        self.assertEqual(b.target_url('FUNCTIONS.md#section', mapping), 'functions.html#section')
        self.assertEqual(b.target_url(source, mapping, image=True), mapping[source])
        self.assertEqual(b.target_url('figures/expanded_accuracy.png', mapping, image=True), 'figures/expanded_accuracy.png')
        self.assertEqual(b.target_url('https://example.com/path', mapping), 'https://example.com/path')
        html = b.render('[external](https://example.com/?a=1&b=2)', 'Test', mapping)
        self.assertIn('href="https://example.com/?a=1&amp;b=2"', html)
        self.assertNotIn('&amp;amp;', html)
        self.assertIn('/blob/main/overall_llm_expanded_2026-10-18/summary.json', b.target_url('overall_llm_expanded_2026-10-18/summary.json', mapping))
        self.assertIn('/tree/main/llm_additions_2026-10-18', b.target_url('llm_additions_2026-10-18', mapping))

    def test_functions_include_every_ranked_model_and_no_excluded_or_stopped(self):
        summary = json.loads(b.SOURCE.read_text())
        text = b.functions_markdown(summary)
        for m in summary['publication']['eligible_model_ids']:
            self.assertIn(summary['models'][m]['label'], text)
        for m in summary['publication']['excluded_model_ids']:
            self.assertNotIn(summary['models'][m]['label'], text)
        for sample in summary['partial_samples'].values():
            self.assertNotIn(sample['label'], text)
        self.assertIn('What the question types mean', text)
        self.assertNotIn('{{', text)

    def test_diagnostics_preserve_original_and_add_actual_partial_denominators(self):
        summary = json.loads(b.SOURCE.read_text())
        text = b.diagnostics_markdown(summary)
        self.assertIn('327 first responses', text)
        self.assertIn('781', text)
        self.assertIn('800', text)
        self.assertIn('424/800', text)
        self.assertIn('Compatibility-only interfaces', text)
        self.assertIn('unresolved dispatch', text)
        self.assertIn('not zero-accuracy', text)
        self.assertNotIn('{{', text)

    def test_original_reference_bytes_are_preserved(self):
        b.reference_hashes()

    def test_previous_presentation_and_tests_are_archived_against_original_seal(self):
        folder=repo_file('publication_archive_2026-10-16', root=b.ROOT)
        manifest=json.loads((folder/'manifest.json').read_text())
        self.assertEqual(manifest['source_commit'],'83dfec83825a39c55a225b9e567c0fc0513597e4')
        old=json.loads((repo_file('expansion_2026-10-15/release_checksums.json', root=b.ROOT)).read_text())
        self.assertEqual(len(manifest['files']),8)
        for name, entry in manifest['files'].items():
            self.assertEqual(entry['archive_path'],name+'.snapshot')
            self.assertEqual(entry['sha256'],old[name])
            self.assertEqual(sha256((folder/entry['archive_path']).read_bytes()).hexdigest(),old[name])

    def test_current_ranking_rows_match_every_full_bank_measurement(self):
        if not self.current_pages(): self.skipTest('Current publication has not been generated yet')
        summary=json.loads(b.SOURCE.read_text())
        lines=(repo_file('README.md', root=b.ROOT)).read_text().splitlines()
        begin=next(i for i,line in enumerate(lines) if line.startswith('| Model | Correct / 1,136'))
        rows=[]
        for line in lines[begin+2:]:
            if not line.startswith('|'):break
            rows.append([part.strip() for part in line.strip('|').split('|')])
        order=sorted(summary['publication']['eligible_model_ids'],key=lambda m:-summary['models'][m]['primary']['correct'])
        self.assertEqual(len(rows),37)
        self.assertTrue(rows[0][0].startswith('Respan Span-02'))
        for cells, model_id in zip(rows,order):
            value=summary['models'][model_id]
            self.assertEqual(cells[0].removesuffix(' *'),value['label'])
            self.assertEqual(cells[1],str(value['primary']['correct']))
            self.assertEqual(cells[2],f"{100*value['primary']['accuracy_attempted']:.1f}%")
            self.assertEqual(cells[3],f"{value['by_role']['core']['correct']}/640")
            self.assertEqual(cells[4],b.format_speed(value['latency_first_all']['median_ms']))
            self.assertEqual(cells[5],f"{value['latency_first_all']['p95_ms']:.0f} ms")
            self.assertIn(b.format_cost(value['known_usd_per_1000_questions'],value['cost_all_attempts']['missing_attempts']),cells[6])
            self.assertEqual(cells[7],', '.join(sorted(value['dates_toronto'])))

    def current_pages(self):
        path = repo_file('docs/index.html', root=b.ROOT)
        return path.exists() and b.COHORT_MARKER in path.read_text()

    def test_generated_current_pages_links_images_and_37_model_tables(self):
        if not self.current_pages(): self.skipTest('Current publication has not been generated yet')
        summary = json.loads(b.SOURCE.read_text())
        readme = (repo_file('README.md', root=b.ROOT)).read_text()
        self.assertIn(b.LEGEND_HEADING, readme)
        self.assertNotIn('hardening_2026-10-18', readme)
        for m in summary['publication']['eligible_model_ids']:
            self.assertIn(summary['models'][m]['label'], readme)
            self.assertIn(f"{summary['models'][m]['latency_first_all']['median_ms']:.0f} ms", readme)
        for filename in ('index.html', 'functions.html', 'output_compliance.html'):
            path = repo_file('docs', root=b.ROOT) / filename
            parser = Links()
            parser.feed(path.read_text())
            for target in parser.targets:
                if re.match(r'^(https?:|mailto:|#|data:)', target): continue
                self.assertTrue((path.parent / target.split('#')[0]).exists(), target)
        html = (repo_file('docs/index.html', root=b.ROOT)).read_text()
        self.assertIn('metric-speed', html)
        self.assertIn('metric-cost', html)
        self.assertIn('cost-incomplete', html)

    def test_old_figure_parity_and_new_scoped_copy(self):
        if not self.current_pages(): self.skipTest('Current publication has not been generated yet')
        for path in (repo_file('figures', root=b.ROOT)).iterdir():
            self.assertTrue(path.is_file())
            self.assertEqual(path.read_bytes(), (repo_file('docs/figures', root=b.ROOT) / path.name).read_bytes())
        for source, target in b.figure_mapping().items():
            self.assertEqual((repo_file(source, root=b.ROOT)).read_bytes(), (repo_file('docs', root=b.ROOT) / target).read_bytes())


if __name__ == '__main__': unittest.main()
