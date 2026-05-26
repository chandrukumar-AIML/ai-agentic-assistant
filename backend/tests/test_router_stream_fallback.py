import asyncio
# FIXED: removed unused `import inspect` — inspect.isasyncgen was replaced with hasattr(__aiter__)
from unittest.mock import patch  # FIXED: import patch for correct mock patching

from backend.llm.router import llm_router, OpenAICallError
import backend.llm.router as router_module


class DummyOllamaStream:
    def __init__(self, items):
        self._items = list(items)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._items:
            raise StopAsyncIteration
        return self._items.pop(0)


async def _collect_async_gen(agen):
    items = []
    async for item in agen:
        items.append(item)
    return items


async def _fake_openai_chat(messages, temperature, max_tokens, stream=False):
    raise OpenAICallError("simulated OpenAI failure")


async def _fake_ollama_chat(messages, temperature, max_tokens, stream=False):
    if stream:
        return DummyOllamaStream(["fallback"])
    return "fallback"


def test_llm_router_falls_back_to_ollama_streaming():
    llm_router.reset()
    # FIXED: patch where the names are USED (backend.llm.router), not where defined.
    # Direct attribute assignment on the module does NOT rebind the already-imported
    # names inside complete(); unittest.mock.patch does.
    with patch("backend.llm.router.openai_chat", side_effect=_fake_openai_chat), \
         patch("backend.llm.router.ollama_chat", side_effect=_fake_ollama_chat):

        response, model = asyncio.run(
            llm_router.complete(
                [{"role": "user", "content": "ping"}],
                stream=True,
            )
        )

        assert model.startswith("ollama/")
        # FIXED: DummyOllamaStream is an async iterator, not an async generator.
        # inspect.isasyncgen() only returns True for async generator objects (async def + yield).
        # Check for async iterable protocol instead.
        assert hasattr(response, "__aiter__"), "response must be async-iterable"  # FIXED: was inspect.isasyncgen(response)
        assert asyncio.run(_collect_async_gen(response)) == ["fallback"]
