"""Discover installed core schemas and validate requests without calling generation.

Run with the selected MCP's existing Python environment. No credentials are read,
no Host config is loaded, and no tools/call, provider or network request is made.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.metadata
import json
from pathlib import Path
import tempfile


def schema_of(tool):
    return getattr(tool, 'input_schema', None) or getattr(tool, 'inputSchema')


async def probe(server, output):
    from jsonschema import Draft202012Validator
    from pydantic import ValidationError

    output.mkdir(parents=True, exist_ok=False)
    rows = []
    scratch = Path(__file__).resolve().parents[1] / '.eval-workspaces'
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='core-contract-', dir=scratch) as temporary:
        work = Path(temporary)
        if server == 'nano':
            from zhenzhen_nanobanana_mcp.config import Settings
            from zhenzhen_nanobanana_mcp.models import ImageTask
            from zhenzhen_nanobanana_mcp.server import create_server
            from fastmcp import Client
            # Explicit synthetic settings avoid reading .env or existing task storage.
            app = create_server(Settings(api_key='synthetic-unused', base_url='https://example.invalid',
                                         output_dir=work / 'outputs', project_dir=work))
            async with Client(app) as client:
                tools = await client.list_tools()  # Discovery only, no tools/call.
            names = {'submit_image_tasks', 'generate_images', 'get_image_tasks', 'wait_image_tasks'}
            version = importlib.metadata.version('zhenzhen-nanobanana-mcp')
            task = dict(task_id='v3-M01', prompt='合成契约：图1产品，图2仅风格；标题“灰色款”。',
                        model='nano-banana-pro', aspect_ratio='1:1',
                        reference_images=['P01', 'R01'], reference_sha256=['1' * 64, '2' * 64])
            batch = dict(checkpointer='skill-core', thread_id='synthetic-product', tasks=[task])
            cases = [('async', 'submit_image_tasks', batch, True),
                     ('sync', 'generate_images', dict(batch, wait_timeout_seconds=30), True),
                     ('twenty', 'submit_image_tasks', dict(batch, tasks=[dict(task, task_id=f'v3-M{i:02}') for i in range(20)]), True),
                     ('too_many', 'submit_image_tasks', dict(batch, tasks=[dict(task, task_id=f'v3-M{i:02}') for i in range(21)]), False),
                     ('foreign_brief', 'submit_image_tasks', dict(batch, brief={}), False),
                     ('foreign_approval', 'submit_image_tasks', dict(batch, authorize_paid=True), False),
                     ('query', 'get_image_tasks', dict(checkpointer='skill-core', thread_id='synthetic-product', task_ids=['v3-M01']), True)]
            ImageTask.model_validate(task)
            try:
                ImageTask.model_validate(dict(task, reference_sha256=['1' * 64]))
            except ValidationError as exc:
                rows.append(dict(case='hash_count_mismatch', expected='rejected', actual='rejected', error=str(exc)))
            else:
                raise AssertionError('Real ImageTask accepted mismatched image hashes')
        else:
            from zhenzhen_image_mcp.server import mcp
            from zhenzhen_image_mcp.contracts import BatchImageTask
            # Direct discovery avoids starting the existing batch monitor/lifespan.
            tools = await mcp.list_tools()
            names = {'submit_image_edit', 'submit_image_generation', 'submit_image_batch',
                     'run_image_batch', 'get_image_batch', 'get_batch_image_task'}
            version = importlib.metadata.version('zhenzhen-image')
            task = dict(task_id='v3-M01', operation='edit', prompt='合成契约：图1产品，图2仅风格；标题“灰色款”。',
                        model='gpt-image-2.5-sunburst', images=['P01', 'R01'], size='1024x1024')
            batch = dict(checkpointer='skill-core', thread_id='synthetic-product', tasks=[task], max_concurrency=5)
            cases = [('async_batch', 'submit_image_batch', batch, True),
                     ('sync_batch', 'run_image_batch', batch, True),
                     ('twenty', 'submit_image_batch', dict(batch, tasks=[dict(task, task_id=f'v3-M{i:02}') for i in range(20)]), True),
                     ('too_many', 'submit_image_batch', dict(batch, tasks=[dict(task, task_id=f'v3-M{i:02}') for i in range(21)]), False),
                     ('single_edit', 'submit_image_edit', {k:v for k,v in task.items() if k not in {'task_id','operation'}}, True),
                     ('foreign_nano_field', 'submit_image_batch', dict(batch, reference_images=['P01']), False),
                     ('foreign_approval', 'submit_image_batch', dict(batch, user_confirmed=True), False),
                     ('query', 'get_image_batch', dict(checkpointer='skill-core', thread_id='synthetic-product'), True)]
            BatchImageTask.model_validate(task)
        schemas = {t.name: schema_of(t) for t in tools if t.name in names}
        assert names == set(schemas), names - set(schemas)
        for label, tool, request, valid in cases:
            errors = list(Draft202012Validator(schemas[tool]).iter_errors(request))
            assert bool(errors) != valid, (label, [e.message for e in errors])
            rows.append(dict(case=label, tool=tool, expected='accepted' if valid else 'rejected',
                             actual='rejected' if errors else 'accepted',
                             errors=[e.message for e in errors], request=request))
        (output / 'schemas.json').write_text(json.dumps(schemas, ensure_ascii=False, indent=2), encoding='utf-8')
        result = dict(server=server, installed_version=version, checked_tools=sorted(names), cases=rows,
                      tool_calls=0, provider_requests=0, paid_image_calls=0, host_config_loaded=False,
                      proof='Installed server discovery + JSON Schema and Pydantic validation, no generation execution',
                      temporary_workspace_removed_on_exit=True)
        (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    assert not work.exists()
    print(json.dumps(dict(server=server, version=version, cases=len(rows), result='passed', tool_calls=0)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', choices=['nano', 'gpt'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(probe(args.server, args.output.resolve()))
