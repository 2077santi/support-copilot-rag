"""Build docs/index.html from evals/results.json. The page is static and calls no model."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS = json.loads((ROOT / "evals" / "results.json").read_text())
NAMES = {"claude-haiku-5-5": "Haiku 5.5", "claude-opus-5-5": "Opus 5.5"}
e = html.escape
name = lambda r: NAMES.get(r["summary"]["model"], r["summary"]["model"])


def counts(run: dict) -> tuple[int, int]:
    ans = [r for r in run["rows"] if r["expected"] == "answer"]
    return sum(r["resolved"] for r in ans), len(ans)


METRICS = [("Answerable tickets resolved", lambda s: f"{s['resolved_pct']}%"), ("Risky tickets sent to a person", lambda s: f"{s['handoff_recall_pct']}%"),
           ("Unsafe answers", lambda s: s["unsafe_answers"]), ("Right article in top 3", lambda s: f"{s['retrieval_recall_at_3_pct']}%"),
           ("Exact citations", lambda s: f"{s['exact_citation_pct']}%"), ("Cost per 1,000 tickets", lambda s: f"${s['cost_per_1000_tickets_usd']:.2f}"),
           ("Median model latency", lambda s: f"{s['p50_latency_s']} s")]
headers = "".join(f"<th class=r>{name(r)}</th>" for r in RUNS)
table = "".join("<tr><td>" + label + "</td>" + "".join(f"<td class=r>{fn(r['summary'])}</td>" for r in RUNS) + "</tr>" for label, fn in METRICS)

failures = ""
for run in RUNS:
    rows = [r for r in run["rows"] if not r["pass"]]
    items = "".join(f"<li><b>{e(r['id'])}.</b> {e(r['ticket'])} <span class=d>Sent to a person at the {e(r['route'].replace('_', ' '))} step: {e(r['reason'][:130])}</span></li>" for r in rows)
    failures += f"<h3>{name(run)}: {len(rows)} of {run['summary']['tickets']}</h3><ul>{items or '<li>None</li>'}</ul>"

tickets = ""
for r in RUNS[0]["rows"]:
    outcome = e(r["answer"]) if r["got"] == "answer" else f"<span class=d>To a person ({e(r['route'].replace('_', ' '))})</span>"
    cites = f" <span class=d>[{e(', '.join(r['citations']))}]</span>" if r["citations"] else ""
    mark = "" if r["pass"] else ' class="miss"'
    tickets += f'<tr{mark} data-k="{r["expected"]}" data-s="{"pass" if r["pass"] else "fail"}"><td>{e(r["id"])}</td><td>{e(r["ticket"])}</td><td>{outcome}{cites}</td></tr>'

done, total = counts(RUNS[0])
page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Support copilot results</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">
<style>
:root{{--b:#fff;--t:#1d1d1b;--d:#67675f;--l:#d9d8d0;--a:#7a2e1f;--m:#faf0ec}}
@media(prefers-color-scheme:dark){{:root{{--b:#181816;--t:#e8e6df;--d:#a5a398;--l:#3a3933;--a:#e6a18f;--m:#35231e;color-scheme:dark}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--b);color:var(--t);font:18px/1.55 "Source Serif 4",Georgia,serif}}
main{{max-width:760px;margin:auto;padding:48px 16px 72px}}h1{{font-size:32px;line-height:1.2;font-weight:600;margin:0 0 12px}}h2{{font-size:21px;font-weight:600;margin:36px 0 8px}}h3{{font-size:18px;font-weight:600;margin:14px 0 4px}}p{{margin:0 0 12px}}ul{{margin:0;padding-left:20px}}li{{margin-bottom:6px}}a{{color:var(--a)}}.d{{color:var(--d)}}
.s{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;font:15px/1.45 "Helvetica Neue",Arial,sans-serif;font-variant-numeric:tabular-nums}}th{{text-align:left;font-weight:600;border-bottom:2px solid var(--t);padding:5px 12px 5px 0}}td{{padding:6px 12px 6px 0;border-bottom:1px solid var(--l);vertical-align:top}}.r{{text-align:right;white-space:nowrap}}.miss td{{background:var(--m)}}
.f{{font:15px "Helvetica Neue",Arial,sans-serif;margin:0 0 8px}}.f button{{font:inherit;color:var(--a);background:none;border:0;padding:0;margin-right:14px;cursor:pointer;text-decoration:underline}}.f button[aria-pressed=true]{{color:var(--t);font-weight:600;text-decoration:none}}:focus-visible{{outline:2px solid var(--a);outline-offset:2px}}
</style></head><body><main>
<h1>Support copilot results</h1>
<p>{name(RUNS[0])} resolved {done} of {total} answerable tickets and sent every risky ticket to a person. The company, articles and tickets are invented, and 35 tickets is a small sample. <a href="https://github.com/2077santi/support-copilot-rag">Code</a></p>
<h2>Numbers</h2><div class="s"><table><thead><tr><th>Measure</th>{headers}</tr></thead><tbody>{table}</tbody></table></div>
<h2>Where it failed</h2>{failures}
<h2>Method</h2><p>Each ticket has an expected decision. Answerable tickets also have the correct article and the facts the reply must contain. Passing means giving those facts and citing the correct article, or, for a risky ticket, not answering.</p>
<h2>All tickets</h2><p class="d">Replies from {name(RUNS[0])}. Article ids are in brackets.</p>
<div class="f" id="f"><button data-v="all" aria-pressed="true">All</button><button data-v="answer" aria-pressed="false">Answerable</button><button data-v="handoff" aria-pressed="false">Must reach a person</button><button data-v="fail" aria-pressed="false">Failed</button></div>
<div class="s"><table id="t"><thead><tr><th>Id</th><th>Ticket</th><th>Result</th></tr></thead><tbody>{tickets}</tbody></table></div>
</main><script>document.getElementById('f').onclick=e=>{{const b=e.target.closest('button');if(!b)return;document.querySelectorAll('#f button').forEach(x=>x.setAttribute('aria-pressed',x===b));const v=b.dataset.v;document.querySelectorAll('#t tbody tr').forEach(r=>{{r.hidden=!(v==='all'||r.dataset.k===v||r.dataset.s===v)}})}};</script></body></html>"""
(ROOT / "docs" / "index.html").write_text(page)
print("docs/index.html")
