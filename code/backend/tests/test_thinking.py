import json

import httpx
import pytest

from imodar.llm import OllamaClient
from imodar.synthesizer import Synthesizer


@pytest.mark.parametrize("think", [True, False])
def test_choice_is_sent_to_ollama_per_call(warehouse, think):
    sent = []

    def respond(request):
        sent.append(json.loads(request.content))
        return httpx.Response(200, json={"message": {"content": "ok"}})

    llm = OllamaClient(think=not think)
    llm._http = httpx.Client(base_url="http://test", transport=httpx.MockTransport(respond))
    result = warehouse.execute("SELECT 1 AS n")
    Synthesizer(llm).synthesize("q", result.sql, result.df, 1, think=think)
    assert sent[0]["think"] is think and llm.think is not think


def test_invalid_plan_is_reported_as_a_model_failure():
    llm = OllamaClient()
    llm._http = httpx.Client(
        base_url="http://test",
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"message": {"content": ""}})),
    )
    with pytest.raises(RuntimeError):
        llm.chat_json([], {})
