"""Versioned operational policy; rules are defense in depth, not a clinical instrument."""

import re
import unicodedata
from enum import StrEnum

POLICY_VERSION = "safety-1.3"
MAX_INPUT = 2000
CONTEXT_TURNS = 8


class Route(StrEnum):
    ROUTINE = "ROUTINE"
    CLARIFY = "CLARIFY"
    ESCALATE = "ESCALATE"
    SAFE_FALLBACK = "SAFE_FALLBACK"


ESCALATION = (
    "I'm sorry things feel so difficult. Your immediate safety matters. "
    "Please seek urgent human help now: contact local emergency services or go to the nearest emergency department. "
    "If you can, reach a trusted nearby person or campus staff member and ask them to stay with you "
    "or the person at risk. Move away from anything that could cause harm if you can do so safely. "
    "I am an AI support tool and cannot provide emergency intervention or contact anyone for you. "
    "Is there a trusted person nearby you can reach right now?"
)
CLARIFICATION = (
    "That sounds difficult, and I want to understand what you mean. "
    "Are you thinking about harming yourself or someone else, or feeling unable to stay safe right now? "
    "If there is immediate danger, please seek local emergency help and a trusted nearby person now."
)
FALLBACK = (
    "I'm having trouble responding reliably. I want to check your safety: "
    "are you thinking about harming yourself or someone else, or unable to stay safe right now? "
    "If there is immediate danger, seek local emergency help and a trusted nearby person now. "
    "For other support, you could contact your campus counseling team."
)
REFUSAL = (
    "I can't provide harmful instructions, a diagnosis, or medication advice. "
    "A qualified professional can help with health questions. "
) + CLARIFICATION


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower().replace("’", "'")
    text = re.sub(r"[\u200b-\u200f\ufeff]", "", text)
    text = text.replace("su1cide", "suicide").replace("k1ll", "kill").replace("mys3lf", "myself")
    return re.sub(r"\s+", " ", text).strip()


# Each clause is checked independently so a negation/quote cannot hide a later current threat.
DANGER = re.compile(
    r"\b(?:suicid(?:al|e)|kill(?:ing)?\s+(?:myself|my\s*self|himself|herself|themselves|him|her|them|someone)|"
    r"(?:hurt(?:ing)?|harm(?:ing)?|endanger(?:ing)?)\s+(?:myself|my\s*self|himself|herself|themselves|him|her|them|someone)|"
    r"(?:end(?:ing)?|tak(?:e|ing))\s+(?:my|his|her|their)\s+(?:own\s+)?life|wants?\s+to\s+die|wish\s+i\s+(?:was|were)\s+dead|"
    r"(?:can't|cannot|can not|unable to)\s+(?:stay|keep myself|be)\s+safe|"
    r"(?:won't|will not)\s+(?:be alive|make it through|survive)|"
    r"(?:already|just)\s+(?:took too many|overdosed|hurt myself)|"
    r"(?:going|plan|planning|about|intend)\s+to\s+(?:jump|attack)|"
    r"(?:ending it|end it all)|(?:not safe|unsafe)\s+(?:alone|with myself|right now))\b"
)
NEGATED_OR_DISTANT = re.compile(
    r"\b(?:not\s+(?:suicidal|thinking (?:of|about)|going to|planning to)|"
    r"(?:don't|do not|never|wouldn't|would not)\s+(?:want to|plan to|intend to|hurt|harm|kill)|"
    r"(?:last year|years ago|in the past|used to)|"
    r"(?:novel|fictional|script|character|quote|poem|essay).*(?:says|reads|line|phrase|quotes?))\b"
)
CURRENT_OVERRIDE = re.compile(
    r"\b(?:i might|i will|i intend|i plan|i am going|i'm going|"
    r"i have a plan|already|just took|cannot stay safe|can't stay safe)\b"
)
AMBIGUOUS = re.compile(
    r"\b(?:can't go on|cannot go on|can't keep going|cannot keep going|cannot keep living|"
    r"can't do this anymore|cannot do this anymore|can't take (?:it|this) anymore|"
    r"disappear|no point|nothing matters|burden|better off without me|"
    r"give up|hopeless|not wake up|never wake up|stop existing|done with everything|"
    r"everyone would be happier|no reason to live|don't feel safe|do not feel safe)\b"
)
BOUNDARY = re.compile(
    r"(?:harmful instructions|how (?:do|can|should) i (?:hurt|harm|kill)|"
    r"(?:give|show|tell).*\b(?:suicide|self.harm|lethal|overdose)\b.*(?:steps|method|instructions)|"
    r"(?:diagnos\w*|prescri\w*|medication|dosage|dose|antidepressant)|"
    r"ignore (?:your|all|the) (?:rules|safety)|disable (?:your )?safety|"
    r"system prompt|pretend (?:you are|to be) (?:a doctor|my therapist))"
)


def rule_route(text: str, awaiting_clarification: bool = False) -> tuple[Route, str]:
    text = normalize(text)
    for clause in re.split(r"[.!?;\n]|\bbut\b", text):
        if DANGER.search(clause):
            if not NEGATED_OR_DISTANT.search(clause) or CURRENT_OVERRIDE.search(clause):
                return Route.ESCALATE, "explicit_danger"
    if (
        awaiting_clarification
        and re.search(r"\b(?:yes|yeah|i am|i might|i have a plan|not safe|unsafe|tonight|right now)\b", text)
        and not re.search(r"\b(?:yes.*\b(?:safe|not thinking)|i am safe)\b", text)
    ):
        return Route.ESCALATE, "safety_followup"
    if AMBIGUOUS.search(text):
        return Route.CLARIFY, "ambiguous_distress"
    if BOUNDARY.search(text):
        return Route.CLARIFY, "content_boundary"
    return Route.ROUTINE, "no_rule_signal"


def output_issue(text: str) -> str | None:
    if not isinstance(text, str) or not text.strip() or len(text) > 800:
        return "invalid_length_or_type"
    text = normalize(text)
    forbidden = [
        r"\d|https?://|www\.|<[^>]+>",  # referrals and contacts may only come from configuration
        r"\b(?:diagnos\w*|bipolar|schizophren\w*|disorder|prescri\w*|dosage|medication|antidepressant)\b",
        r"\b(?:you (?:have|are suffering from) (?:depression|anxiety)|clinical depression)\b",
        r"\b(?:take|increase|decrease|stop|start).{0,35}\b(?:pills?|dose|tablet|drug|mg|medicine)\b",
        r"\b(?:kill|cut|hang|poison|overdose|hurt)\s+(?:yourself|myself)\b",
        r"\b(?:suicide|self.harm|lethal|weapon|bleed|jump off|tie a|sharp blade)\b",
        r"\b(?:keep (?:this|it) secret|between (?:us|you and me)|promise|guarantee|cure)\b",
        r"\b(?:everything will be (?:fine|okay)|you (?:will be|are completely) safe)\b",
        r"\b(?:i (?:have |already )?(?:called|contacted|alerted)|i am (?:a|your) (?:therapist|doctor))\b",
    ]
    if any(re.search(pattern, text) for pattern in forbidden):
        return "unsafe_or_unverified_content"
    return None
