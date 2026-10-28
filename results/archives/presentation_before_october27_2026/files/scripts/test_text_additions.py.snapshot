from copy import deepcopy
from hashlib import sha256
import json
import unittest

import text_additions as a


class TextAdditions(unittest.TestCase):
    def test_payload(self):
        for model in a.MODELS:
            p=a.payload({'prompt_text':'fixed content'},model)
            self.assertEqual(p['messages'][0]['content'],'fixed content'+a.chat.SUFFIX)
            self.assertEqual(p['max_tokens'],16)
            self.assertEqual(p['reasoning'],{'enabled':False})
            self.assertFalse(p['provider']['allow_fallbacks'])
            self.assertNotIn('temperature',p)

    def test_account_metadata_removed(self):
        original={'user_id':'private','is_byok':True,'provider':'provider',
                  'choices':[{'finish_reason':'stop','message':{'content':'2','role':'assistant'}}],
                  'usage':{'cost':.0001,'prompt_tokens':250,'completion_tokens':2,'is_byok':True},
                  'error':{'message':'Provider returned error','code':429,
                           'metadata':{'provider_name':'provider','limit_source':'shared','account_id':'private'}}}
        raw=a.sanitized(original)
        self.assertNotIn('user_id',raw)
        self.assertNotIn('is_byok',raw['usage'])
        self.assertNotIn('account_id',raw['error']['metadata'])
        self.assertEqual(raw['choices'][0]['message']['content'],'2')

    def test_no_reasoning_and_strict_truncation(self):
        raw={'http_status':200,'error':'','raw_response':{'choices':[{'finish_reason':'stop','message':{'content':'2'}}],
            'usage':{'completion_tokens_details':{'reasoning_tokens':0}}}}
        self.assertEqual(a.parse(raw)['status'],'ok')
        bad=deepcopy(raw)
        bad['raw_response']['choices'][0]['finish_reason']='length'
        self.assertEqual(a.parse(bad)['status'],'invalid_output')
        bad=deepcopy(raw)
        bad['raw_response']['usage']['completion_tokens_details']['reasoning_tokens']=2
        self.assertEqual(a.parse(bad)['status'],'unexpected_reasoning')

    def test_provider_failures_are_not_format_failures(self):
        common={'http_status':200,'status':'invalid_output','raw_response':{},'error':''}
        records=[common,{**common,'error':'TimeoutError'},
                 {**common,'raw_response':{'error':{'code':502}}},
                 {**common,'http_status':429,'status':'http_failure'}]
        c=a.compliance(records)
        self.assertEqual(c['model_output_failures'],1)
        self.assertEqual(c['provider_transport_failures'],3)
        self.assertTrue(c['eligible_for_main_comparison'])
        self.assertFalse(a.compliance([common]*57)['eligible_for_main_comparison'])
        self.assertTrue(a.compliance([common]*56)['eligible_for_main_comparison'])

    def test_complete_public_ledgers(self):
        for model in a.MODELS:
            if (a.PUBLIC/model/'checksums.json').exists():
                first,eventual,attempts=a.validate_model(model)
                self.assertEqual(len(first),1136)
                self.assertEqual(len(eventual),1136)
                self.assertGreaterEqual(len(attempts),1136)

    def test_expanded_scores_preserve_fourteen(self):
        path=a.OVERALL/'summary.json'
        if not path.exists():
            self.skipTest('Expanded report not generated yet')
        s=json.loads(path.read_text())
        old=json.loads(a.BASE_SUMMARY.read_text())
        for model,result in old['models'].items():
            self.assertEqual(s['models'][model],result)
        for f,oldf in zip(s['by_family'],old['by_family']):
            for model,result in oldf['models'].items():
                self.assertEqual(f['models'][model],result)
        for model,result in s['models'].items():
            self.assertEqual(sum(f['models'][model]['correct'] for f in s['by_family']),result['primary']['correct'])
            self.assertEqual(result['primary']['correct']+result['primary']['wrong']+result['primary']['unanswered'],1136)
        self.assertEqual(s['model_count']*1136,s['total_scored_model_questions'])
        self.assertNotIn('glm53flash',s['models'])
        self.assertEqual(set(s['publication']['excluded_model_ids']),{'haiku55','deepseek41flash','microsoft/phi-4'})
        for model,c in s['output_compliance'].items():
            self.assertEqual(c['usable_first_answers']+c['model_output_failures']+c['provider_transport_failures'],1136,model)
            self.assertEqual(c['eligible_for_main_comparison'],model in s['publication']['eligible_model_ids'])
        if not s['pending_model_ids']:
            self.assertEqual(s['model_count'],22)
            self.assertEqual(s['publication']['ranked_model_count'],19)
            self.assertEqual(s['total_scored_model_questions'],24992)


if __name__=='__main__':
    unittest.main()
