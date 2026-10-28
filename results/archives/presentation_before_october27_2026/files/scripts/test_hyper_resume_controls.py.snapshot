import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock,patch

import resume_hyper_reference as r


class HyperResume(unittest.TestCase):
    def test_pacing_is_outside_unchanged_transport_and_restores_it(self):
        with TemporaryDirectory() as name:
            out=Path(name);(out/'provider_cooldown_extension.json').write_text(json.dumps({
                'resume_not_before_utc':'2020-01-01T00:00:00+00:00','minimum_request_start_interval_seconds':2}))
            clock=[0.0];original=Mock(return_value={'latency_ms':7})
            def sleep(seconds):clock[0]+=seconds
            def execute(folder,env):
                self.assertEqual((folder,env),(out,Path('test.env')))
                first=r.h.base.transport.send(b'body','not-a-real-key',{'host':'test'})
                second=r.h.base.transport.send(b'body','not-a-real-key',{'host':'test'})
                self.assertEqual(first,second)
            with patch.object(r.h,'OUT',out),patch.object(r.h,'execute',side_effect=execute),\
                 patch.object(r.h.base.transport,'send',original),patch.object(r.time,'perf_counter',side_effect=lambda:clock[0]),\
                 patch.object(r.time,'sleep',side_effect=sleep):
                r.main(Path('test.env'))
                self.assertIs(r.h.base.transport.send,original)
            self.assertEqual(original.call_count,2)
            self.assertEqual(clock[0],2)
            waits=[json.loads(line) for line in (out/'pacing_waits.jsonl').read_text().splitlines()]
            self.assertTrue(all(v['outside_response_timer'] for v in waits))


if __name__=='__main__':unittest.main()
