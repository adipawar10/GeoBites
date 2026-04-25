"""
Lightweight lexicon sentiment scoring (no external downloads).

Returns:
- sentiment_score: numeric (positive higher)
- sentiment_label: {"positive","neutral","negative"}
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd


POS_WORDS = {
    "great",
    "good",
    "excellent",
    "amazing",
    "love",
    "loved",
    "tasty",
    "fresh",
    "friendly",
    "fast",
    "perfect",
    "awesome",
}
NEG_WORDS = {
    "bad",
    "terrible",
    "awful",
    "cold",
    "slow",
    "rude",
    "overpriced",
    "disappointed",
    "never",
    "worst",
    "dirty",
}


_TOKEN_RE = re.compile(r"[a-z']+")


def score_text(text: str) -> float:
    if not isinstance(text, str) or not text.strip():
        return 0.0
    toks = _TOKEN_RE.findall(text.lower())
    if not toks:
        return 0.0
    pos = sum(t in POS_WORDS for t in toks)
    neg = sum(t in NEG_WORDS for t in toks)
    return float(pos - neg) / float(len(toks) ** 0.5)


def label_score(s: float, pos_th: float = 0.25, neg_th: float = -0.25) -> str:
    if s >= pos_th:
        return "positive"
    if s <= neg_th:
        return "negative"
    return "neutral"


def add_sentiment(df: pd.DataFrame, text_col: str = "review_text") -> pd.DataFrame:
    out = df.copy()
    scores = out[text_col].astype(str).map(score_text).to_numpy(dtype=float)
    out["sentiment_score"] = scores
    out["sentiment_label"] = [label_score(s) for s in scores]
    return out

