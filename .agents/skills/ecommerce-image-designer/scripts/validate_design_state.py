"""Read-only v2 design contract validation against independently supplied evidence."""
import argparse
import html
import json
import ntpath
from pathlib import Path

BASE = ('title', 'subtitle', 'labels', 'footnote', 'canvas', 'kind',
        'product_count', 'view', 'style', 'delivery', 'previous_layout')
CONTRACT_ID = 'ecommerce-design-state/v2'
SERVER_ALIASES = {
    'zhenzhen-gptimagegen2.5-mcp': 'zhenzhen-gptimagegen2.5-mcp',
    'zhenzhen-gptimagegen2-5-mcp': 'zhenzhen-gptimagegen2.5-mcp',
    'zhenzhen-nanobanana-mcp': 'zhenzhen-nanobanana-mcp',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def shape(value, keys, name):
    require(isinstance(value, dict) and set(value) == set(keys), name + ': closed fields required')


def unique(values, name):
    require(isinstance(values, list) and all(isinstance(v, str) and v for v in values)
            and len(set(values)) == len(values), name + ': unique nonempty strings required')


def parse_answer(text):
    text = text.strip()
    if text.startswith('```json\n') and text.endswith('\n```'):
        text = text[8:-4]
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON field: ' + key)
            result[key] = value
        return result
    return json.loads(text, object_pairs_hook=pairs,
                      parse_constant=lambda value: require(False, 'Non-finite JSON number'))


def validate(record, evidence):
    shape(record, ('contract', 'mode', 'validation', 'state', 'proposal', 'next'), 'record')
    require(record['contract'] == CONTRACT_ID and record['validation'] == 'pending', 'Contract/validation marker')
    mode = record['mode']
    require(mode in ('status', 'plan', 'revision') and mode == evidence['mode'], 'Wrong mode')
    state = record['state']
    shape(state, ('images', 'facts', 'capabilities', 'locked_images', 'edit_images', 'baseline'), 'state')
    shape(state['baseline'], BASE, 'baseline')
    require(state['baseline'] == evidence['baseline'], 'Baseline differs from actual evidence')
    for key in ('locked_images', 'edit_images'):
        unique(state[key], key)
        require(set(state[key]) == set(evidence[key]), key + ': scope differs from evidence')
    require(not set(state['locked_images']) & set(state['edit_images']), 'Frozen/edit scope overlap')
    images = state['images']
    require(isinstance(images, list), 'images must be array')
    unique([item.get('id') for item in images if isinstance(item, dict)], 'image ids')
    require(len(images) == len(evidence['images']), 'Image roster differs')
    expected_images = {item['id']: item for item in evidence['images']}
    for item in images:
        shape(item, ('id', 'source', 'role', 'provenance', 'reference_use', 'drawing_use', 'input_index'), 'image')
        expected = expected_images.get(item['id'])
        require(expected is not None, 'Unexpected image identity')
        def canonical_source(value):
            if value is None:
                return None
            require(isinstance(value, str) and bool(value), 'Image source must be path/reference or null')
            return value if '://' in value else ntpath.normcase(ntpath.normpath(value))
        allowed_sources = [expected.get('source'), *expected.get('allowed_sources', [])]
        require(canonical_source(item['source']) in [canonical_source(v) for v in allowed_sources], 'Image source reference differs from evidence')
        for key in ('role', 'provenance', 'reference_use'):
            require(item[key] == expected[key], 'Image ' + key + ' differs from source')
        require(item['role'] in ('product', 'reference', 'generated', 'unknown'), 'Image role enum')
        require(item['provenance'] in ('photo', 'synthetic', 'illustration', 'unknown'), 'Image provenance enum')
        require(item['reference_use'] in ('none', 'style', 'structure', 'both', 'unknown'), 'Reference use enum')
        require(item['drawing_use'] in ('analysis_only', 'undecided', 'upload'), 'Drawing use enum')
        entry = evidence.get('generation_entry')
        require(item['input_index'] is None or (entry and item['drawing_use'] == 'upload'
                and type(item['input_index']) is int and item['input_index'] > 0), 'Premature image input index')
        require(entry or item['drawing_use'] != 'upload', 'Upload mapping requires selected entry')
        require(item['drawing_use'] == 'upload' or item['input_index'] is None, 'Analysis/undecided has no input index')
    facts = state['facts']
    require(isinstance(facts, list), 'facts must be array')
    for item in facts:
        shape(item, ('id', 'text', 'source'), 'fact')
        require(item['source'] in ('user', 'record', 'observation'), 'Fact source enum')
    unique([item['id'] for item in facts], 'fact ids')
    alternatives = [evidence['facts'], *evidence.get('fact_alternatives', [])]
    require(any(sorted((f['text'], f['source']) for f in facts) ==
                sorted((f['text'], f['source']) for f in alternative)
                for alternative in alternatives), 'Facts differ from evidence')
    if mode == 'revision':
        require(facts == evidence['facts'], 'Revision fact identity changed')
    caps = state['capabilities']
    require(isinstance(caps, list), 'capabilities must be array')
    expected_caps = {SERVER_ALIASES.get(row['server']): row for row in evidence['capabilities']}
    require(None not in expected_caps, 'Unknown independently recorded service')
    require(len(caps) == len(expected_caps), 'Capability roster differs')
    unique([row.get('server') for row in caps if isinstance(row, dict)], 'capability services')
    canonical_services = [SERVER_ALIASES.get(row.get('server')) for row in caps if isinstance(row, dict)]
    unique(canonical_services, 'canonical capability services')
    require(set(canonical_services) == set(expected_caps), 'Capability service identities differ')
    for row in caps:
        shape(row, ('server', 'query_tool', 'models', 'query_succeeded', 'configured', 'upstream', 'performance'), 'capability')
        canonical_server = SERVER_ALIASES.get(row['server'])
        require(canonical_server in expected_caps, 'Unknown capability service')
        expected = expected_caps[canonical_server]
        unique(row['models'], 'models')
        qualified_tool = expected['query_tool']
        require(row['query_tool'] in (qualified_tool, qualified_tool.rsplit('__', 1)[-1])
                and set(row['models']) == set(expected['models']), 'Model/tool service binding differs')
        require(row['query_succeeded'] is True and row['configured'] is expected['configured'], 'Query/configuration status differs')
        require(row['upstream'] == row['performance'] == 'not_tested', 'Free query cannot prove readiness/history/performance')
    next_step = record['next']
    shape(next_step, ('rollback_stage', 'stage', 'confirm_images', 'missing_fields', 'execution'), 'next')
    require(next_step['execution'] == 'not_authorized', 'Draft cannot authorize execution')
    require(next_step['rollback_stage'] == ('S2' if mode == 'revision' else None), 'Rollback stage differs from local text-edit mode')
    unique(next_step['confirm_images'], 'confirm_images')
    unique(next_step['missing_fields'], 'missing_fields')
    require(not set(next_step['confirm_images']) & set(state['locked_images']), 'Frozen images cannot be reconfirmed')
    allowed_missing = {key for key, value in state['baseline'].items() if value is None}
    if mode == 'status':
        allowed_missing |= {'product_image', 'product_details', 'brand'}
    require(set(next_step['missing_fields']) <= allowed_missing, 'Only unknown editable fields may be requested')
    proposal = record['proposal']
    if mode == 'status':
        require(proposal is None and not images and not facts and not state['locked_images'] and not state['edit_images'], 'Status output must not invent design')
        require(next_step['stage'] == 'S0' and not next_step['confirm_images'], 'Status next scope')
        require(all(value is None for value in state['baseline'].values()), 'Status has no design baseline')
        return record
    require(next_step['stage'] == 'S3', 'Draft proceeds through S3 confirmation')
    shape(proposal, ('canvas', 'copy', 'layout', 'appearance', 'reference_style'), 'proposal')
    shape(proposal['copy'], ('title', 'subtitle', 'labels', 'footnote'), 'copy')
    for key in ('title', 'subtitle', 'footnote'):
        require(proposal['copy'][key] is None or isinstance(proposal['copy'][key], str), 'Copy text/null required')
    require(proposal['copy']['labels'] is None or (isinstance(proposal['copy']['labels'], list)
            and all(isinstance(v, str) for v in proposal['copy']['labels'])), 'labels text array/null required')
    if proposal['canvas'] is not None:
        shape(proposal['canvas'], ('width', 'height'), 'canvas')
        require(all(type(v) is int and v > 0 for v in proposal['canvas'].values()), 'Canvas dimensions')
    shape(proposal['appearance'], ('background', 'typography', 'lighting'), 'appearance')
    require(all(v is None or isinstance(v, str) for v in proposal['appearance'].values()), 'Appearance text/null required')
    require(isinstance(proposal['layout'], list) and proposal['layout'], 'Concrete layout required')
    for row in proposal['layout']:
        shape(row, ('element', 'region', 'align', 'max_lines', 'if_present', 'overflow'), 'layout')
        require(row['element'] in ('title', 'subtitle', 'labels', 'footnote', 'product', 'gap'), 'Layout element enum')
        region = row['region']
        shape(region, ('x', 'y', 'width', 'height'), 'region')
        require(all(type(v) in (int, float) and 0 <= v <= 100 for v in region.values())
                and region['width'] > 0 and region['height'] > 0
                and region['x'] + region['width'] <= 100 and region['y'] + region['height'] <= 100,
                'Layout percentage region')
        require(row['align'] in ('left', 'center', 'right') and type(row['if_present']) is bool, 'Layout align/condition')
        require(row['max_lines'] is None or (type(row['max_lines']) is int and row['max_lines'] > 0), 'Positive max_lines/null')
        require(row['overflow'] == 'reflow_preserve_all_copy', 'Overflow must preserve all copy')
        if mode == 'revision' and row['element'] in ('subtitle', 'labels', 'footnote') and state['baseline'][row['element']] is None:
            require(row['if_present'] is True, 'Unknown auxiliary text must be conditional')
    require(isinstance(proposal['reference_style'], list), 'reference_style array required')
    for row in proposal['reference_style']:
        shape(row, ('image_id', 'attribute', 'value'), 'reference style')
        image = expected_images.get(row['image_id'], {})
        require(image.get('reference_use') in ('style', 'both') and row['attribute'] in
                ('art_medium', 'background_tone', 'lighting', 'texture', 'font_tone'), 'Reference permission dimension')
        require(isinstance(row['value'], str) and bool(row['value']), 'Reference attribute text required')
    if mode == 'revision':
        require(len(state['edit_images']) == 1 and set(next_step['confirm_images']) == set(state['edit_images']), 'Confirm exactly one editable image')
        require(proposal['canvas'] == state['baseline']['canvas'] and all(v is None for v in proposal['appearance'].values()), 'Local revision cannot invent global style/canvas')
        require(proposal['copy'] == {key: state['baseline'][key] for key in proposal['copy']}, 'Original copy must be preserved including unknowns')
        require(not proposal['reference_style'], 'Text-only recovery has no new visual reference observations')
    else:
        require(not state['locked_images'] and not state['edit_images'] and len(next_step['confirm_images']) == 1, 'New single-image plan scope')
    # Free design strings may not reopen source/status/frozen metadata. Those
    # facts have one typed location rather than duplicated prose/prompt fields.
    def strings(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for v in value.values():
                yield from strings(v)
        elif isinstance(value, list):
            for v in value:
                yield from strings(v)
    require(not any(locked in value for locked in state['locked_images'] for value in strings(proposal)), 'Frozen identity leaked into editable proposal')
    return record


def render(record):
    """Human view and full prompt derive from exactly one validated record."""
    def cell(value):
        if value is None:
            return '待补／未定'
        if isinstance(value, (list, dict)):
            value = json.dumps(value, ensure_ascii=False)
        return html.escape(str(value)).replace('|', '\\|').replace('\n', ' ')
    state, proposal, next_step = record['state'], record['proposal'], record['next']
    lines = ['# 本轮方案（未确认，不可提交）', '']
    if state['capabilities']:
        lines += ['本次仅完成目录／配置查询；上游与性能未实测，不代表生产就绪。', '',
                  '| 服务 | 模型目录 | 配置存在 | 上游／性能 |', '|---|---|---|---|']
        for row in state['capabilities']:
            configured = '未知' if row['configured'] is None else ('是' if row['configured'] else '否')
            lines.append('| ' + ' | '.join(map(cell, (row['server'], row['models'], configured, '本次未测试'))) + ' |')
    if state['images']:
        lines += ['', '| 图片 | 文件／附件引用 | 业务角色 | 来源性质 | 参考用途 | 绘图用途／序号 |', '|---|---|---|---|---|---|']
        for row in state['images']:
            lines.append('| ' + ' | '.join(map(cell, (row['id'], row['source'], row['role'], row['provenance'],
                         row['reference_use'], [row['drawing_use'], row['input_index']]))) + ' |')
    if state['locked_images']:
        lines += ['', '冻结保留：' + cell(state['locked_images']) + '。本轮修改：' + cell(state['edit_images']) + '。']
    if state['facts']:
        lines += ['', '## 产品事实', ''] + ['- ' + cell(row['id']) + '：' + cell(row['text']) + '（' + cell(row['source']) + '）' for row in state['facts']]
    if proposal is not None:
        lines += ['', '## 文案与新布局（建议）', '', '| 文案项 | 内容 |', '|---|---|']
        for key, value in proposal['copy'].items():
            lines.append('| ' + cell(key) + ' | ' + cell(value) + ' |')
        lines += ['', '| 元素 | x / y / 宽 / 高（画布%） | 对齐 | 行数上限 | 存在条件 |', '|---|---|---|---|---|']
        for row in proposal['layout']:
            region = row['region']
            lines.append('| ' + ' | '.join(map(cell, (row['element'], [region[k] for k in ('x', 'y', 'width', 'height')],
                         row['align'], row['max_lines'], '若存在' if row['if_present'] else '本方案元素'))) + ' |')
        lines += ['', '视觉建议：' + cell(proposal['appearance']), '参考风格字段：' + cell(proposal['reference_style'])]
    lines += ['', '## 下一步', '']
    if next_step['rollback_stage']:
        lines.append('回退 ' + cell(next_step['rollback_stage']) + '，随后进入 ' + cell(next_step['stage']) + '。')
    else:
        lines.append('下一阶段：' + cell(next_step['stage']) + '。')
    lines += ['待确认图号：' + cell(next_step['confirm_images']) + '。',
              '待补字段：' + cell(next_step['missing_fields']) + '。',
              '', '## 完整结构化提示词草案', '', '```json', json.dumps(record, ensure_ascii=False, indent=2), '```']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record', type=Path)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--render', action='store_true')
    args = parser.parse_args()
    try:
        record = validate(parse_answer(args.record.read_text(encoding='utf-8')),
                          json.loads(args.evidence.read_text(encoding='utf-8')))
        print(render(record) if args.render else json.dumps({'valid': True, 'contract': record['contract']}))
        return 0
    except (ValueError, TypeError, KeyError, OSError) as error:
        print(json.dumps({'valid': False, 'error': str(error)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
