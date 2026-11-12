"""Input → deterministic floor → constrained classifier → allowed response → output guard."""

from dataclasses import asdict, dataclass, field
from time import perf_counter

from .backend import Backend, parse_label
from .policy import (
    CLARIFICATION,
    CONTEXT_TURNS,
    ESCALATION,
    FALLBACK,
    MAX_INPUT,
    REFUSAL,
    Route,
    output_issue,
    rule_route,
)


@dataclass
class Session:
    messages: list[dict] = field(default_factory=list)
    escalated: bool = False
    awaiting_clarification: bool = False

    def clear(self):
        self.messages.clear()
        self.escalated = False
        self.awaiting_clarification = False


@dataclass
class Reply:
    route: Route
    response: str
    reason: str
    latency_ms: float
    fallback: bool = False
    output_blocked: bool = False
    classifier_called: bool = False
    generator_called: bool = False

    def record(self):
        return asdict(self)


class Chatbot:
    def __init__(self, backend: Backend):
        self.backend = backend

    def respond(self, session: Session, text: str) -> Reply:
        start = perf_counter()
        classifier_called = generator_called = blocked = False
        fallback = False
        valid = isinstance(text, str) and bool(text.strip()) and len(text) <= MAX_INPUT
        # Scan the complete submitted string before rejecting length. Do not silently truncate danger.
        rule, reason = (
            rule_route(text, session.awaiting_clarification)
            if isinstance(text, str)
            else (Route.SAFE_FALLBACK, "invalid_input")
        )
        context = [*session.messages[-CONTEXT_TURNS:], {"role": "user", "content": text}] if valid else []
        if session.escalated or rule == Route.ESCALATE:
            route, response = Route.ESCALATE, ESCALATION
            reason = "escalation_latched" if session.escalated else reason
        elif not valid:
            route, response, reason, fallback = Route.SAFE_FALLBACK, FALLBACK, "invalid_input", True
        else:
            try:
                classifier_called = True
                label = parse_label(self.backend.classify(context))
                # LLM may promote; it can never downgrade deterministic uncertainty or danger.
                if label == Route.ESCALATE:
                    route, response, reason = label, ESCALATION, "classifier_danger"
                elif rule == Route.CLARIFY or label == Route.CLARIFY:
                    route = Route.CLARIFY
                    response = REFUSAL if reason == "content_boundary" else CLARIFICATION
                    reason = reason if rule == Route.CLARIFY else "classifier_uncertainty"
                else:
                    generator_called = True
                    response = self.backend.generate(context)
                    issue = output_issue(response)
                    if issue:
                        blocked = True
                        raise ValueError(issue)
                    route, reason = Route.ROUTINE, "supportive_generation"
            except Exception:
                # Deliberately sanitize arbitrary adapter failures. Do not expose upstream text or secrets.
                route, response, fallback = Route.SAFE_FALLBACK, FALLBACK, True
                reason = "output_rejected" if blocked else "model_failure"
        session.escalated = session.escalated or route == Route.ESCALATE
        session.awaiting_clarification = route in {Route.CLARIFY, Route.SAFE_FALLBACK}
        if valid:
            session.messages.extend(
                [{"role": "user", "content": text}, {"role": "assistant", "content": response}]
            )
            session.messages[:] = session.messages[-CONTEXT_TURNS:]
        return Reply(
            route,
            response,
            reason,
            round((perf_counter() - start) * 1000, 3),
            fallback,
            blocked,
            classifier_called,
            generator_called,
        )
