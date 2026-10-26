"""Honor a Hyper cooldown, then pace the unchanged, answer-blind executor.

No request-body or first-attempt edits. The original full-response HTTPS timer
starts after these operator queue waits. This separate source/receipt makes the
operational continuation explicit without changing frozen capture software.
"""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import time

import hyper_reference as h


def main(env):
    policy=json.loads((h.OUT/'provider_cooldown_extension.json').read_text())
    not_before=datetime.fromisoformat(policy['resume_not_before_utc'])
    print(json.dumps({'status':'WAITING_FOR_EXTENDED_PROVIDER_COOLDOWN','resume_utc':not_before.isoformat()}),flush=True)
    while True:
        remaining=(not_before-datetime.now(timezone.utc)).total_seconds()
        if remaining<=0:break
        time.sleep(min(45,remaining))
    interval=policy['minimum_request_start_interval_seconds'];last_start=None
    original=h.base.transport.send
    def paced_send(*args,**kwargs):
        nonlocal last_start
        if last_start is not None:
            wait=max(0,interval-(time.perf_counter()-last_start))
            if wait:
                h.d.append(h.OUT/'pacing_waits.jsonl',{'seconds':wait,'outside_response_timer':True,'time':h.d.timestamps()})
                time.sleep(wait)
        last_start=time.perf_counter()
        return original(*args,**kwargs)
    h.d.save_bound(h.OUT/'pacing_receipt.json',{'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'minimum_request_start_interval_seconds':interval,'start':h.d.timestamps(),
        'scope':'Only inter-request queue waits; original request bodies, timer and prior first attempts unchanged'})
    h.d.append(h.OUT/'operator_events.jsonl',{'event':'Resume untested cases with two-second start pacing after extended provider cooldown','time':h.d.timestamps()})
    h.base.transport.send=paced_send
    try:h.execute(h.OUT,env)
    finally:h.base.transport.send=original


if __name__=='__main__':
    assert len(sys.argv)==2,'Pass the existing credential env path; no purchases or top-ups'
    main(Path(sys.argv[1]))
