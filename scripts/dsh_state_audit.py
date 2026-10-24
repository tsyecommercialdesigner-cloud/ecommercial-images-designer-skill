"""Bind contract output to original fixed-case inputs and actual MCP results."""
import hashlib
import importlib.util
import json
from pathlib import Path

BASE = ('title', 'subtitle', 'labels', 'footnote', 'canvas', 'kind', 'product_count', 'view', 'style', 'delivery', 'previous_layout')
QUERIES = {
    'mcp__zhenzhen-gptimagegen2-5-mcp__get_model_guide': ('zhenzhen-gptimagegen2.5-mcp', 'key_present'),
    'mcp__zhenzhen-nanobanana-mcp__list_models': ('zhenzhen-nanobanana-mcp', 'api_key_configured'),
}


def evidence_for(case, snapshot, work, *, target_images=None):
    """Ground truth comes from the original fixture request, never the answer."""
    evidence = dict(mode={'explicit': 'status', 'implicit': 'plan', 'recovery': 'revision'}[case],
                    images=[], facts=[], capabilities=[], locked_images=[], edit_images=[], baseline=dict.fromkeys(BASE))
    if target_images is not None:
        if case != 'implicit' or not isinstance(target_images, list) or len(target_images) != 1 or not isinstance(target_images[0], str) or not target_images[0].strip() or target_images[0] in {'P01', 'R01'}:
            raise ValueError('Expected one independently allocated new draft identity')
        evidence['target_images'] = target_images[:]
    if case == 'implicit':
        # These are annotations of the unchanged request already sent to the
        # model, not an expected answer or a new instruction appended to it.
        evidence['images'] = [dict(id='P01', source='P01.png', role='product', provenance='synthetic', reference_use='none'),
                              dict(id='R01', source='R01.png', role='reference', provenance='unknown', reference_use='style')]
        evidence['facts'] = [dict(id='F01', text='灰色盒体', source='user'), dict(id='F02', text='深灰盖沿', source='user')]
        evidence['fact_alternatives'] = [[dict(text=text, source='user')]
                                         for text in ('灰色盒体和深灰盖沿', '灰色盒体、深灰盖沿')]
        evidence['baseline']['kind'] = 'main'
    if case == 'recovery':
        actual = json.loads((work / 'design-record.json').read_text(encoding='utf-8'))
        evidence.update(images=[dict(id=row['id'], source=row.get('source'), role=row['role'], provenance=row.get('provenance', 'unknown'),
                                     reference_use=row.get('reference_use', 'none')) for row in actual['images']],
                        facts=[dict(id=row['id'], text=row['value'], source='record') for row in actual['facts']],
                        locked_images=actual['accepted_images'], edit_images=[actual['changed_image']],
                        baseline={key: actual.get('baseline', actual).get(key) for key in BASE})
    image_map = work / 'image-map.json'
    if image_map.exists():
        aliases = json.loads(image_map.read_text(encoding='utf-8'))
        for image in evidence['images']:
            entry = next((row for row in aliases if row['name'] == image.get('source')), None)
            if entry:
                image['allowed_sources'] = [entry['source'], *entry['verifiedAliases']]
    calls = {row['data']['callId']: row['data']['name'] for row in snapshot['events'] if row['type'] == 'tool/call'}
    for event in snapshot['events']:
        if event['type'] != 'tool/result':
            continue
        message = event['data']['message']
        tool = calls.get(message['toolCallId'])
        if tool not in QUERIES:
            continue
        payloads = [json.loads(block['text']) for block in message['content'] if block['type'] == 'text']
        payload = next(row for row in payloads if isinstance(row, dict) and 'models' in row)
        server, configured = QUERIES[tool]
        evidence['capabilities'].append(dict(server=server, query_tool=tool, models=payload['models'],
                                             configured=payload.get(configured)))
    return evidence


def verify(answer, case, snapshot, work):
    script = work / '.agents/skills/ecommerce-image-designer/scripts/validate_design_state.py'
    spec = importlib.util.spec_from_file_location('frozen_design_state_' + work.name.replace('-', '_'), script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    evidence = evidence_for(case, snapshot, work)
    target = work.parent / 'verification' / work.name
    target.mkdir(parents=True, exist_ok=True)
    (target / 'evidence.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
    metadata = dict(contract=getattr(module, 'CONTRACT_ID', 'ecommerce-design-state/v1'),
                    validator_sha256=hashlib.sha256(script.read_bytes()).hexdigest(),
                    evidence_sha256=hashlib.sha256((target / 'evidence.json').read_bytes()).hexdigest())
    try:
        state = module.parse_answer(answer)
        module.validate(state, evidence)
    except (ValueError, TypeError, KeyError) as error:
        (target / 'result.json').write_text(json.dumps(dict(metadata, valid=False, error=str(error)), ensure_ascii=False, indent=2), encoding='utf-8')
        raise ValueError('State contract: ' + str(error)) from error
    (target / 'state.json').write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    (target / 'rendered-draft.txt').write_text(module.render(state), encoding='utf-8')
    result = dict(metadata, valid=True)
    (target / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result
