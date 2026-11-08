import sys

from anthropic import Anthropic

from .agent import DEFAULT_MODEL, Copilot, claude_llm

if len(sys.argv) < 2:
    sys.exit('Usage: python -m copilot "your support question"')
result = Copilot(claude_llm(Anthropic(), DEFAULT_MODEL)).handle(" ".join(sys.argv[1:]))
if result.decision == "answer":
    print(f"{result.answer}\n\nSources: {', '.join(result.citations)}")
else:
    print(f"Handed off to a human agent ({result.route}: {result.reason}).")
