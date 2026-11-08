# Support copilot

A support assistant for a made-up telecom. It answers from a small knowledge base, cites the article it used, and sends anything risky to a person.

[Results and every test ticket](https://2077santi.github.io/support-copilot-rag/)

I came from contact centre work, so I cared less about a good demo answer and more about what happens when the model should not answer at all.

Ticket flow:

```
risk rules -> BM25 search -> Claude -> check citations and numbers -> reply or hand off
```

Legal threats, fraud, cancellations and prompt injection are caught by plain rules before the model runs. After it runs, any price or deadline that is not in the cited article sends the ticket to a person.

## Results

35 synthetic tickets, 23 answerable and 12 that must reach a person.

| | Haiku 5.5 | Opus 5.5 |
|---|---:|---:|
| Answerable tickets resolved | 95.7% | 91.3% |
| Risky tickets sent to a person | 100% | 100% |
| Cost per 1,000 tickets | $0.10 | $4.17 |

I would use Haiku here. That is a call for this small task, not a claim about the models in general.

My first run put Opus at 78%. The model was mostly fine: my scorer rejected "20%" because it wanted "20 percent". I changed it to accept alternatives for both models.

One miss is still there on purpose. "Japan" is in no article, so BM25 does not find the outside-EU roaming page and the ticket goes to a person. Embeddings would probably fix it. I did not want to add the word to the article just to pass the test.

## Run it

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/pytest
export ANTHROPIC_API_KEY=your_key
.venv/bin/python -m copilot "How much is a new SIM card?"
.venv/bin/python -m evals.run
.venv/bin/python -m evals.report
```

The tests use a fake model. A full evaluation of both models costs about $0.15.

## Not done yet

Conversations, account lookups, retrieval in Spanish, and a test set big enough to trust.
