"""Seal a new public version once, or check its unchanged artifact hashes."""
import argparse
import json

from validate_consolidated_release import SEAL, hashes, validate


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    validate()
    value = hashes()
    if args.check:
        assert value == json.loads(SEAL.read_text())
    else:
        assert not SEAL.exists(), 'A public release seal is immutable; create a later release instead'
        SEAL.write_text(json.dumps(value, indent=2) + '\n')
    print('PASS:', len(value), 'consolidated release files')
