"""Bind public data, analysis and figure bytes after reviewed regeneration."""
from repo_layout import logical_relative, repo_file
from pathlib import Path
import json
from analyze import file_hash
root=Path(__file__).resolve().parents[1]
paths=sorted(p for folder in ["data","analysis","figures"] for p in (repo_file(folder, root=root)).glob("*") if p.is_file() and p.name!="checksums.json")
(repo_file("data/checksums.json", root=root)).write_text(json.dumps({logical_relative(p, root=root).as_posix():file_hash(p) for p in paths},indent=2)+"\n")
print(f"Recorded {len(paths)} artifact hashes")
