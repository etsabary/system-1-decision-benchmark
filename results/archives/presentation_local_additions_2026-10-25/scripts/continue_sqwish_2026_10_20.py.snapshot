"""Resume the frozen Sqwish run under the account's 30rpm/concurrency1 limit.

This adds only an outer admission/pacing wrapper; the frozen payload, parser,
timed HTTPS transport and first-attempt journals are unchanged. Earlier valid
attempts are retained. No key, account identity or wallet enters the receipt.
"""
import threading
import time
import direct_decisions_2026_10_20 as run


def main():
    out=run.OUT/'kettei_fat'
    attempts,results,_=run.validate('kettei_fat',out)
    assert all(r['status']=='ok' for r in attempts), 'Inspect earlier failures before continuation'
    run.d.save_bound(out/'account_rate_amendment.json',dict(
        version='sqwish-account-rate-admission-v1',
        observed_limits=dict(rpm=30,concurrency=1),
        minimum_dispatch_interval_seconds=2.1,
        before_continuation=dict(attempts=len(attempts),settled=len(results)),
        controller_sha256=run.bank.file_hash(__file__),
        preservation='Retain original valid first attempts; no resampling or changed question input',
        timing='Outer lock and dispatch spacing excluded from unchanged connect-to-full-body timer'))
    send=run.send
    admission=threading.Lock()
    last=[time.monotonic()]
    def paced(body,key,mid,operation):
        assert mid=='kettei_fat'
        with admission:
            delay=max(0,2.1-(time.monotonic()-last[0]))
            if delay:time.sleep(delay)
            last[0]=time.monotonic()
            return send(body,key,mid,operation)
    run.send=paced
    run.execute('kettei_fat',out)


if __name__=='__main__':main()
