"""BM25 retrieval over the knowledge base. No embeddings: small, inspectable and free to run."""
import math
import re
from collections import Counter
from dataclasses import dataclass

STOP = set("a an and are as at be but by can do does for from how i if in is it its me my of on or our so that the their them there this to up was we what when where which who will with you your".split())


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9.]+", text.lower())
    out = []
    for t in tokens:
        t = t.strip(".")
        if not t or t in STOP:
            continue
        out.append(t[:-1] if len(t) > 3 and t.endswith("s") and not t.endswith("ss") else t)
    return out


@dataclass(frozen=True)
class Hit:
    id: str
    title: str
    text: str
    score: float


class BM25:
    def __init__(self, docs: list[dict], k1: float = 1.5, b: float = 0.75):
        self.docs, self.k1, self.b = docs, k1, b
        self.tf = [Counter(tokenize(f"{d['title']} {d['title']} {d['text']}")) for d in docs]
        self.len = [sum(c.values()) for c in self.tf]
        self.avg = sum(self.len) / len(docs)
        df = Counter(t for c in self.tf for t in c)
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def search(self, query: str, k: int = 3) -> list[Hit]:
        terms = tokenize(query)
        scored = []
        for i, d in enumerate(self.docs):
            s = 0.0
            for t in terms:
                f = self.tf[i].get(t, 0)
                if f:
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.len[i] / self.avg))
            scored.append(Hit(d["id"], d["title"], d["text"], round(s, 3)))
        return sorted((h for h in scored if h.score > 0), key=lambda h: -h.score)[:k]
