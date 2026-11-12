import httpx
import pytest

from mannsahara.backend import BackendError, OllamaBackend


def backend_for(handler):
    backend = OllamaBackend()
    backend.client.close()
    backend.client = httpx.Client(transport=httpx.MockTransport(handler), trust_env=False)
    return backend


def test_local_adapter_sends_schema_settings_and_context():
    import json

    seen = []

    def handle(request):
        body = json.loads(request.content)
        seen.append(body)
        return httpx.Response(200, json={"message": {"content": '{"route":"CLARIFY"}'}, "done": True})

    backend = backend_for(handle)
    assert backend.classify([{"role": "user", "content": "fictional worry"}])
    assert seen[0]["format"]["properties"]["route"]["enum"] == [
        "NO_SAFETY_SIGNAL",
        "UNCERTAIN_SAFETY",
        "CURRENT_DANGER",
    ]
    assert seen[0]["options"]["temperature"] == 0
    assert seen[0]["messages"][0]["role"] == "system"
    assert seen[0]["messages"][-1]["content"] == "fictional worry"
    assert seen[0]["stream"] is False


@pytest.mark.parametrize("kind", ["timeout", "500", "bad_json", "incomplete"])
def test_adapter_errors_are_sanitized(kind):
    def handle(request):
        if kind == "timeout":
            raise httpx.ReadTimeout("secret-data", request=request)
        if kind == "500":
            return httpx.Response(500, text="secret-data")
        if kind == "bad_json":
            return httpx.Response(200, text="secret-data")
        return httpx.Response(200, json={"message": {"content": "secret-data"}, "done": False})

    with pytest.raises(BackendError) as error:
        backend_for(handle).classify([{"role": "user", "content": "fictional"}])
    assert "secret-data" not in str(error.value)
