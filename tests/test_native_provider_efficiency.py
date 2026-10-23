"""Offline checks of the installed native adapter and its existing SDK lifecycle."""
import asyncio
import copy
import importlib.util
import json
from pathlib import Path

import pytest


@pytest.fixture
def native(monkeypatch):
    if importlib.util.find_spec('harbor') is None:
        pytest.skip('optional pinned Harbor runtime is not installed')
    monkeypatch.setenv('LITELLM_LOCAL_MODEL_COST_MAP', 'True')
    from harbor.llms import lite_llm
    monkeypatch.setattr(lite_llm, 'get_supported_openai_params', lambda *args: [])
    return lite_llm


def test_openrouter_request_preserves_history_and_generation(native, monkeypatch):
    from harbor.llms.chat import Chat
    from litellm.llms.openrouter.chat.transformation import OpenrouterConfig
    spec = json.loads((Path(__file__).parents[1] / 'config/openrouter-execution.example.json').read_text())
    settings = spec['llm_call_kwargs']
    seen = []

    async def completion(**kwargs):
        seen.append(copy.deepcopy(kwargs))
        return native.litellm.ModelResponse(model='fixture/returned-revision',
            choices=[{'message': {'role': 'assistant', 'content': 'fresh-' + str(len(seen))}, 'finish_reason': 'stop'}],
            usage={'prompt_tokens': 100, 'completion_tokens': 20,
                   'prompt_tokens_details': {'cached_tokens': 60}})

    monkeypatch.setattr(native.litellm, 'acompletion', completion)
    model = native.LiteLLM('openrouter/fixture/model', session_id='attempt-affinity', reasoning_effort='high')
    chat = Chat(model, interleaved_thinking=True)

    async def exercise():
        first = await chat.chat('unchanged task instruction', **copy.deepcopy(settings))
        second = await chat.chat('unchanged terminal result', **copy.deepcopy(settings))
        assert first.content != second.content
    asyncio.run(exercise())
    assert seen[0]['messages'] == [{'role': 'user', 'content': 'unchanged task instruction'}]
    assert seen[1]['messages'] == [
        {'role': 'user', 'content': 'unchanged task instruction'},
        {'role': 'assistant', 'content': 'fresh-1'},
        {'role': 'user', 'content': 'unchanged terminal result'}]
    for request in seen:
        assert request['caching'] is False
        assert request['reasoning_effort'] == 'high'
        assert request['max_tokens'] == 16384
        assert request['extra_headers']['X-OpenRouter-Cache'] == 'false'
        assert request['extra_body']['session_id'] == 'attempt-affinity'
        assert request['extra_body']['provider']['allow_fallbacks'] is False
        assert 'temperature' not in request
        wire = OpenrouterConfig().transform_request('fixture/model', copy.deepcopy(request['messages']),
            {'extra_body': copy.deepcopy(request['extra_body']), 'max_tokens': request['max_tokens']}, {}, {})
        assert wire['messages'] == request['messages']
        assert wire['provider'] == settings['extra_body']['provider']
    assert settings == spec['llm_call_kwargs']
    assert Chat(model).messages == []


def test_openrouter_high_reasoning_reaches_serialized_request(native, monkeypatch):
    import httpx
    from litellm.llms.custom_httpx.async_client_cleanup import close_litellm_async_clients
    spec = json.loads((Path(__file__).parents[1] / 'config/openrouter-execution.example.json').read_text())
    settings = copy.deepcopy(spec['llm_call_kwargs'])
    settings['extra_body']['provider']['only'] = ['deepinfra/fp8']
    monkeypatch.setenv('OPENROUTER_API_KEY', 'offline-fixture-key')
    seen = []

    async def send(client, request, *args, **kwargs):
        assert str(request.url) == 'https://openrouter.ai/api/v1/chat/completions'
        seen.append((json.loads(request.content), dict(request.headers)))
        return httpx.Response(200, request=request, json={
            'id': 'offline-response', 'object': 'chat.completion', 'created': 0,
            'model': 'deepseek/deepseek-v4.1-flash-1017',
            'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': '{}'},
                         'finish_reason': 'stop'}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 2, 'total_tokens': 12}})

    monkeypatch.setattr(httpx.AsyncClient, 'send', send)

    async def exercise():
        model = native.LiteLLM(spec['harbor_model'], reasoning_effort='high',
                              session_id='offline-attempt', model_info=spec['model_info'])
        try:
            await model.call('unchanged instruction', **settings)
        finally:
            await close_litellm_async_clients()
    asyncio.run(exercise())
    assert len(seen) == 1
    body, headers = seen[0]
    assert body['model'] == 'deepseek/deepseek-v4.1-flash-1017'
    assert body['reasoning_effort'] == 'high'
    assert body['max_tokens'] == 16384
    assert body['provider'] == settings['extra_body']['provider']
    assert body['session_id'] == 'offline-attempt'
    assert body['messages'] == [{'role': 'user', 'content': 'unchanged instruction'}]
    assert headers['x-openrouter-cache'] == 'false'
    assert 'temperature' not in body


def test_native_cancellation_does_not_retry(native, monkeypatch):
    calls = []

    async def cancelled(**kwargs):
        calls.append(kwargs)
        raise asyncio.CancelledError()
    monkeypatch.setattr(native.litellm, 'acompletion', cancelled)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(native.LiteLLM('openrouter/fixture/model').call('instruction'))
    assert len(calls) == 1


def test_sdk_pool_reuses_connections_with_credential_and_timeout_separation(native, monkeypatch):
    import httpx
    from litellm.llms.openai.openai import OpenAIChatCompletion
    from litellm.llms.custom_httpx.async_client_cleanup import close_litellm_async_clients
    seen = []

    async def handle(request):
        data = json.loads(request.content)
        seen.append(data)
        if data.get('stream'):
            wire = ('data: ' + json.dumps({'id': 'fixture-stream', 'object': 'chat.completion.chunk',
                'created': 0, 'model': 'fixture', 'choices': [{'index': 0,
                'delta': {'content': 'fresh stream'}, 'finish_reason': None}]}) + '\n\ndata: [DONE]\n\n')
            return httpx.Response(200, text=wire, headers={'content-type': 'text/event-stream'})
        if len(seen) == 1:
            return httpx.Response(500, json={'error': {'message': 'fixture retry', 'type': 'server_error'}})
        return httpx.Response(200, json={'id': 'fixture-response', 'object': 'chat.completion',
            'created': 0, 'model': 'fixture', 'choices': [{'index': 0,
            'message': {'role': 'assistant', 'content': 'fresh response'}, 'finish_reason': 'stop'}]})

    async def exercise():
        transport = httpx.AsyncClient(transport=httpx.MockTransport(handle))
        monkeypatch.setattr(OpenAIChatCompletion, '_get_async_http_client', staticmethod(lambda **kwargs: transport))
        adapter = OpenAIChatCompletion()
        kwargs = {'is_async': True, 'api_key': 'fixture-key-a', 'api_base': 'https://offline.invalid/v1',
                  'timeout': 7.0, 'max_retries': 1}
        first = adapter._get_openai_client(**kwargs)
        assert adapter._get_openai_client(**kwargs) is first
        other = adapter._get_openai_client(**{**kwargs, 'api_key': 'fixture-key-b'})
        assert other is not first
        assert adapter._get_openai_client(**{**kwargs, 'timeout': 8.0}) is not first
        assert first.max_retries == 1 and first.timeout == 7
        try:
            response = await first.chat.completions.create(model='fixture', messages=[{'role': 'user', 'content': 'same'}])
            assert response.choices[0].message.content == 'fresh response'
            stream = await first.chat.completions.create(model='fixture', messages=[{'role': 'user', 'content': 'next'}], stream=True)
            async with stream:
                chunks = [chunk.choices[0].delta.content or '' async for chunk in stream]
                assert ''.join(chunks) == 'fresh stream'
            assert [row['messages'][0]['content'] for row in seen] == ['same', 'same', 'next']
        finally:
            await close_litellm_async_clients()
            await transport.aclose()
        assert transport.is_closed
    asyncio.run(exercise())
