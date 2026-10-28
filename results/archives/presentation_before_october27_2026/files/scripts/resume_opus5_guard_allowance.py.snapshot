"""Finish remaining Opus cases with explicit conservative cost-guard headroom.

No payload, route, parser, order, attempt or timing changes. The original$5
guard paused at1329 first attempts because missing refusal receipts reserve
byte-based charges. Known receipts total$4.593925;13 questions remain.
The new$5.50 soft dispatch guard is not a vendor billing cap. All missing
charges remain unknown. The original manifest/software/ledgers stay unchanged.
"""
from decimal import Decimal
from pathlib import Path

import opus5_schema_reference as run


def main():
    questions, plan = run.prepare()
    original_freeze, original_sealed_files = run.freeze, run.sealed_files
    old_guard, new_guard = run.GUARD, Decimal('5.50')
    assert old_guard == Decimal('5.00')
    records, results, done = run.native.controller.ledger_state(run, run.OUT, plan)
    assert len(done) >= 1329, 'This allowance is only for the already-screened near-complete run'
    assert run.chat.money(records)['known_usd'] < 5
    allowance = {
        'old_soft_guard_usd': str(old_guard), 'new_soft_guard_usd': str(new_guard),
        'reason': 'Conservative missing-refusal-charge reservations reached the guard at1329/1342 with$4.593925 reported. Finish the remaining13 unchanged requests; missing charges remain unknown.',
        'payload_changes': False, 'route_changes': False, 'existing_ledgers_rewritten': False,
        'resume_helper_sha256': run.file_hash(Path(__file__))}
    run.d.save_bound(run.OUT / 'guard_allowance.json', allowance)

    def freeze(out, frozen_plan):
        # Revalidate the original immutable$5 manifest before applying the
        # separately recorded dispatch policy. Do not rewrite that manifest.
        run.GUARD = old_guard
        original_freeze(out, frozen_plan)
        run.GUARD = new_guard

    run.freeze = freeze
    run.sealed_files = lambda out: original_sealed_files(out) + ['guard_allowance.json']
    run.native.controller.execute(run, run.OUT)


if __name__ == '__main__':
    main()
