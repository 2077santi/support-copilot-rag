"""Deterministic rules around the model. Risky cases never depend on a model decision."""
import re

RULES = [
    ("cancellation", r"\bcancel\w*\b.*\b(contract|line|service|subscription|account)\b|\b(leave|terminate)\b.*\bcontract\b"),
    ("legal", r"\b(lawyer|solicitor|sue|lawsuit|legal action|consumer authority|ombudsman|regulator)\b"),
    ("fraud", r"\b(fraud|stolen identity|hacked|without (my )?permission|sim swap|account was accessed)\b"),
    ("vulnerable_customer", r"\b(medical alarm|life support|carer|suicid\w*|self[- ]harm)\b"),
    ("prompt_injection", r"\b(ignore|disregard)\b.{0,40}\b(instructions?|knowledge base|rules|policy)\b|\bsystem prompt\b"),
    ("billing_dispute", r"\b(never agreed|did not authori[sz]e|overcharged|reverse[d]? (it|the charge)|dispute)\b"),
]


def pre_guard(ticket: str) -> str | None:
    text = ticket.lower()
    for reason, pattern in RULES:
        if re.search(pattern, text):
            return reason
    return None


def numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+(?:[.,]\d+)?", text))


def post_guard(answer: str, citations: list[str], retrieved: dict[str, str]) -> str | None:
    """Return a handoff reason if the answer cannot be traced to the articles it cites."""
    if not citations:
        return "no_citation"
    if any(c not in retrieved for c in citations):
        return "unknown_citation"
    source = " ".join(retrieved[c] for c in citations)
    if numbers(answer) - numbers(source):
        return "ungrounded_number"
    return None
