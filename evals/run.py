"""Run the golden set against one or more models and write results/results.json."""
import json
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from anthropic import Anthropic

from copilot.agent import ROOT, Copilot, claude_llm

PRICES = {"claude-opus-5-5": (4.0, 20.0), "claude-haiku-5-5": (0.10, 0.50), "claude-sonnet-5-5": (2.0, 10.0)}


def golden() -> list[dict]:
    return [json.loads(l) for l in (ROOT / "evals" / "golden.jsonl").read_text().splitlines() if l.strip()]


def score(case: dict, r: dict) -> dict:
    expected, got = case["expected"], r["decision"]
    row = {"id": case["id"], "ticket": case["ticket"], "expected": expected, "got": got, "route": r["route"], "reason": r["reason"],
           "answer": r["answer"], "citations": r["citations"], "retrieved": r["retrieved"], "kb": case["kb"], "decision_ok": expected == got}
    if expected == "answer":
        text = r["answer"].lower()
        row["retrieved_ok"] = bool(set(case["kb"]) & set(r["retrieved"]))
        row["facts_ok"] = got == "answer" and all(any(o.lower() in text for o in f.split("|")) for f in case["facts"])
        row["citation_ok"] = got == "answer" and bool(set(r["citations"]) & set(case["kb"]))
        row["citation_exact"] = got == "answer" and set(r["citations"]) == set(case["kb"])
        row["resolved"] = row["facts_ok"] and row["citation_ok"]
    row["unsafe"] = expected == "handoff" and got == "answer"
    row["pass"] = row["resolved"] if expected == "answer" else not row["unsafe"]
    return row


def summarize(rows: list[dict], results: list[dict], model: str) -> dict:
    ans = [r for r in rows if r["expected"] == "answer"]
    hand = [r for r in rows if r["expected"] == "handoff"]
    pct = lambda n, d: round(100 * n / d, 1) if d else None
    pin, pout = PRICES.get(model, (0, 0))
    called = [r for r in results if r["usage"]]
    cost = sum(r["usage"]["input"] * pin + r["usage"]["output"] * pout for r in called) / 1e6
    return {
        "model": model, "tickets": len(rows),
        "overall_pass_pct": pct(sum(r["pass"] for r in rows), len(rows)),
        "retrieval_recall_at_3_pct": pct(sum(r["retrieved_ok"] for r in ans), len(ans)),
        "resolved_pct": pct(sum(r["resolved"] for r in ans), len(ans)),
        "exact_citation_pct": pct(sum(r["citation_exact"] for r in ans), len(ans)),
        "over_handoff_pct": pct(sum(r["got"] == "handoff" for r in ans), len(ans)),
        "handoff_recall_pct": pct(sum(r["got"] == "handoff" for r in hand), len(hand)),
        "unsafe_answers": sum(r["unsafe"] for r in rows),
        "model_calls": len(called), "total_cost_usd": round(cost, 4),
        "cost_per_1000_tickets_usd": round(1000 * cost / len(rows), 2),
        "p50_latency_s": round(statistics.median([r["latency_s"] for r in called]), 2) if called else 0,
    }


def run(model: str, client) -> dict:
    copilot = Copilot(claude_llm(client, model))
    cases = golden()
    with ThreadPoolExecutor(4) as pool:
        results = [r.to_dict() for r in pool.map(lambda c: copilot.handle(c["ticket"]), cases)]
    rows = [score(c, r) for c, r in zip(cases, results)]
    return {"summary": summarize(rows, results, model), "rows": rows}


if __name__ == "__main__":
    models = sys.argv[1:] or ["claude-haiku-5-5", "claude-opus-5-5"]
    client = Anthropic()
    out = [run(m, client) for m in models]
    target = Path(ROOT / "evals" / "results.json")
    target.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    for o in out:
        print(json.dumps(o["summary"]))
