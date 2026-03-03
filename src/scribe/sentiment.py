"""
Per-segment sentiment analysis using VADER.
Returns a label (positive / neutral / negative) for each segment text.
"""

from typing import List, Tuple

# (label, compound_score) per segment; label is "positive" | "neutral" | "negative"
SentimentResult = Tuple[str, float]

# Thresholds on compound score for VADER: [-1, 1]
# Standard VADER: positive >= 0.05, negative <= -0.05, else neutral
POSITIVE_THRESHOLD = 0.05
NEGATIVE_THRESHOLD = -0.05


def _get_sentiment_label(compound: float) -> str:
    if compound >= POSITIVE_THRESHOLD:
        return "positive"
    if compound <= NEGATIVE_THRESHOLD:
        return "negative"
    return "neutral"


def run_sentiment(segment_texts: List[str]) -> List[SentimentResult]:
    """
    Run sentiment analysis on each segment text.
    Loads the VADER analyzer once per run.
    Returns a list of (label, compound_score) per segment.
    """
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    analyzer = SentimentIntensityAnalyzer()
    results: List[SentimentResult] = []
    for text in segment_texts:
        text = (text or "").strip()
        if not text:
            results.append(("neutral", 0.0))
            continue
        scores = analyzer.polarity_scores(text)
        compound = scores["compound"]
        label = _get_sentiment_label(compound)
        results.append((label, compound))
    return results
