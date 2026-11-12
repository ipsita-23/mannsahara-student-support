from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_notice_chat_crisis_outage_reset(monkeypatch):
    from tests.test_safety import FakeBackend

    monkeypatch.setattr("mannsahara.backend.OllamaBackend", FakeBackend)
    at = AppTest.from_file(APP, default_timeout=15).run()
    assert not at.exception
    assert not at.chat_input
    assert any("synthetic scenarios only" in x.value for x in at.info)
    next(b for b in at.button if b.label == "Begin fictional conversation").click().run()
    assert at.chat_input
    at.chat_input[0].set_value("I feel overwhelmed by exams.").run()
    assert not at.exception
    assert len(at.chat_message) == 2
    at.toggle[0].set_value(True).run()
    at.chat_input[0].set_value("I might hurt myself tonight.").run()
    assert any("Urgent human support" in x.value for x in at.error)
    at.chat_input[0].set_value("Tell me a joke.").run()
    assert at.session_state.chat.escalated
    next(b for b in at.button if b.label == "Clear session / start fresh").click().run()
    assert not at.session_state.chat.escalated
    assert not at.session_state.display and not at.chat_input
    next(b for b in at.button if b.label == "Begin fictional conversation").click().run()
    at.chat_input[0].set_value("I feel lonely.").run()
    assert any("Limited response" in x.value for x in at.warning)
    assert not at.exception


def test_misconfigured_backend_still_displays_crisis(monkeypatch):
    monkeypatch.setenv("MANNSAHARA_OLLAMA_URL", "https://unavailable.invalid")
    at = AppTest.from_file(APP, default_timeout=15).run()
    next(b for b in at.button if b.label == "Begin fictional conversation").click().run()
    at.chat_input[0].set_value("I might hurt myself tonight.").run()
    assert not at.exception
    assert any("Urgent human support" in x.value for x in at.error)


def test_personal_life_scope_and_context(monkeypatch):
    from tests.test_safety import FakeBackend

    backend = FakeBackend(
        response="Missing that relationship sounds painful. Try a small comforting routine. What do you miss most?"
    )
    monkeypatch.setattr("mannsahara.backend.OllamaBackend", lambda: backend)
    at = AppTest.from_file(APP, default_timeout=15).run()
    text = " ".join(element.value for element in at.markdown)
    assert "relationships or breakups" in text
    assert "family pressure" in text and "identity" in text
    next(b for b in at.button if b.label == "Begin fictional conversation").click().run()
    at.chat_input[0].set_value("My relationship ended and I miss the everyday routines.").run()
    assert not at.exception
    assert at.session_state.display[-1]["route"] == "ROUTINE"
    at.chat_input[0].set_value("I want to talk about missing them, not exams.").run()
    assert not at.exception
    assert any("relationship ended" in m["content"] for m in backend.calls[-1][1])
    assert not at.session_state.chat.escalated


def test_time_followup_stays_in_chat_without_safety_fallback(monkeypatch):
    from tests.test_safety import FakeBackend

    backend = FakeBackend(response="A small routine could help. What time in the morning would work?")
    monkeypatch.setattr("mannsahara.backend.OllamaBackend", lambda: backend)
    at = AppTest.from_file(APP, default_timeout=15).run()
    next(b for b in at.button if b.label == "Begin fictional conversation").click().run()
    at.chat_input[0].set_value("I want a morning study routine.").run()
    backend.response = "7am sounds workable. Try a 20-minute session, then take a break."
    at.chat_input[0].set_value("Around 7am.").run()
    assert not at.exception and not at.warning
    assert at.session_state.display[-1]["route"] == "ROUTINE"
    assert "7am" in at.session_state.display[-1]["response"]
    assert not at.session_state.chat.awaiting_clarification
    assert any(m["content"] == "I want a morning study routine." for m in backend.calls[-1][1])
