"""Remove the local H2O E4B screen from the active presentation."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

source, dest = (Path(s).resolve() for s in sys.argv[1:])
if dest.exists() or dest == source or source in dest.parents:
    raise SystemExit('Destination must be a new release')
shutil.copytree(source, dest)

def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new, 1)

partial_path = dest / 'partial_models.json'
partial = json.loads(partial_path.read_text())
assert partial[-1]['provider_model_id'] == 'h2o-lightning:e4b-nf4'
partial_path.write_text(json.dumps(partial[:-1], indent=2) + '\n')

p = dest / 'report.html'
page = replace_once(p.read_text(), ' H2O E4B NF4: 6/16 usable answers correct; 4/20 requests exceeded the local 1,024-token limit, 930 ms median on usable answers.', '')
p.write_text(page)

p = dest / 'README_V4.md'
readme = p.read_text().replace('results/releases/' + source.name + '/', 'results/releases/' + dest.name + '/')
readme = replace_once(readme, '; H2O E4B NF4: 6/16 usable answers correct and 4/20 requests rejected for the 1,024-token limit, 930 ms median on usable answers', '')
p.write_text(readme)

p = dest / 'NEW_LOCAL_SCREEN_NOTES.md'
notes = p.read_text()
notes = replace_once(notes, '# Three incomplete local model screens', '# Two incomplete local model screens')
notes = replace_once(notes, '| H2O Lightning E4B, NF4 | 20 | 16 | 6 | 930 ms | 15 / 14 |\n', '')
notes = replace_once(notes, "H2O stopped at the 20-question reliability screen: four inputs were rejected for exceeding the local configuration's 1,024-token limit. The 6/16 usable-answer result is too small to establish full-bank accuracy. No question was truncated or retried. Local NF4 quantization affects H2O's probabilities. Both NF4 configurations are specific local implementations.\n\n", '')
notes = replace_once(notes, ', and 2,348 ms for H2O', '')
notes = replace_once(notes, ', and all 16 usable H2O responses', '')
p.write_text(notes)

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = json.loads((source / 'manifest.json').read_text())
manifest['prior_new_local_screens_manifest_sha256'] = sha(source / 'manifest.json')
manifest['presentation_note'] = 'Remove the local E4B screen from the active presentation at the owner’s request; full-bank results and graphics remain unchanged.'
manifest['files_sha256'] = {str(p.relative_to(dest)): sha(p) for p in sorted(dest.rglob('*')) if p.is_file() and p.name != 'manifest.json'}
(dest / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
print('Created', dest)
