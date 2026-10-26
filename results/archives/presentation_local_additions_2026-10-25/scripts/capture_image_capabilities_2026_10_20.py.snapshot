"""Public GET-only modality review; no credentials, inference or image scores."""
from repo_layout import repo_file
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import ssl
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
DEST=repo_file('direct_additions_2026-10-20', root=ROOT)
MODELS={
 'respan02':'respan/span-02','pplx_decider12':'perplexity/pplx-decider-v1.2',
 'pplx_flash12':'perplexity/pplx-decider-flash-v1.2','jev114':'typesafe/jev-1.14',
 'jev113':'typesafe/jev-1.13','luna_decisions':'openai/gpt-6-luna-decisions',
 'liquid_ultra':'liquid/d1-ultra','liquid_d1':'liquid/d1','mercury_decide':'inception/mercury-decide',
 'microsoft_decision':'microsoft/microsoft-decision-1','clef':'cloudflare/clef',
 'clef_flash':'cloudflare/clef-flash','clef_omni':'cloudflare/clef-omni',
 'solar_flash':'upstage/solar-decide-flash','drex20':'nace-ai/drex-v2.0','drex15':'nace-ai/drex-v1.5',
 'classify1':'scaledown/classify-1','kev4b':'jaredpalmer/kev-4b',
 'tev1_4b_native':'togethercomputer/tev1-4b-experimental',
 'reference_sol':'openai/gpt-6-sol','reference_sonnet':'anthropic/claude-sonnet-5.5',
}


def get(url):
    with urllib.request.urlopen(url,context=ssl.create_default_context(cafile='/etc/ssl/cert.pem'),timeout=30) as r:
        data=r.read()
    return data,sha256(data).hexdigest()


def capture():
    target=DEST/'image_capabilities.json'
    assert not target.exists(),'Do not overwrite the dated capability capture'
    base=json.loads((repo_file('llm_references_2026-10-19/statistics.json', root=ROOT)).read_text())
    found={}
    def one(pair):
        mid,model=pair;url='https://openrouter.ai/api/v1/models/'+model+'/endpoints'
        raw,h=get(url);v=json.loads(raw)['data'];a=v['architecture']
        assert v['id']==model
        return mid,dict(image_input='image' in a['input_modalities'],evidence='provider_catalog',
            source=url,source_sha256=h,input_modalities=a['input_modalities'],
            output_modalities=a['output_modalities'])
    with ThreadPoolExecutor(max_workers=6) as pool:
        found.update(pool.map(one,MODELS.items()))
    url='https://decision.vllm-sr.ai/api/info';raw,h=get(url)
    m=next(x for x in json.loads(raw)['models'] if x['id']=='vllm-sr/d3-turbo')
    assert 'image' in m['inputs']
    found['d3_turbo']=dict(image_input=True,evidence='provider_catalog',source=url,
        source_sha256=h,input_modalities=m['inputs'])
    url='https://huggingface.co/mukaddamzaid/amos-1-large/raw/main/README.md';raw,h=get(url)
    assert 'photo' in raw.decode() and 'image processor' in raw.decode()
    found['amos_large']=dict(image_input=True,evidence='author_model_card',source=url,
        source_sha256=h,note='Author documents photo input and image-region questions; not an image accuracy result from this benchmark.')
    url='https://docs.sqwish.ai/guides/models-and-fallback.md';raw,h=get(url)
    assert '| fat | `kettei-fat` | Yes |' in raw.decode()
    found['kettei_fat']=dict(image_input=True,evidence='provider_documentation',source=url,
        source_sha256=h,additional_source='https://docs.sqwish.ai/guides/images',
        note='fat supports images; core is a different text-only size. The /v1/systemone contract documents native image decoding.')
    url='https://docs.bespokelabs.ai/api-reference/openapi.yaml';raw,h=get(url)
    assert 'Nimble reads a JSON state as JSON text.' in raw.decode()
    found['nimble_v4_max']=dict(image_input=False,evidence='documented_text_json_contract',
        source=url,source_sha256=h,note='An image-shaped JSON object is text, not evidence of decoded vision. Earlier compatibility review is retained in the separate image benchmark.')
    url='https://hyper.charm.land/v1/models';raw,h=get(url)
    m=next(x for x in json.loads(raw)['data'] if x['id']=='qwen3.8-max')
    assert m['capabilities']['vision'] is True
    found['reference_qwen']=dict(image_input=True,evidence='tested_provider_catalog',source=url,
        source_sha256=h,note='Hyper Charm catalog explicitly declares vision for this exact model.')
    assert set(found)==set(base['models'])|{'d3_turbo','amos_large','kettei_fat'}
    payload=dict(review_date_toronto='2026-10-20',status='DOCUMENTED_CAPABILITIES_NOT_IMAGE_SCORES',
        image_inference_calls=0,models=found,
        limits=['Catalog and documentation claims are not native-image compatibility probes or image accuracy measurements.',
                'Support can depend on the route and request encoding. No OCR or caption substitution was used.',
                'Text accuracy, text latency and text costs must not be presented as image measurements.'])
    DEST.mkdir(exist_ok=True);target.write_text(json.dumps(payload,indent=2)+'\n')
    print('Captured public documentation for',len(found),'routes; no inference calls.')


if __name__=='__main__':capture()
