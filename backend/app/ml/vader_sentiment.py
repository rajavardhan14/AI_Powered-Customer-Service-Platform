"""
VADER (Valence Aware Dictionary for sEntiment Reasoning)
A rule-based and lexicon-driven sentiment analysis engine tailored for customer support messages,
social texts, and support tickets.
"""

import math
import re
from typing import Dict, Any, List

# Core valence lexicon for customer support and general sentiment
LEXICON = {
    # High negative / frustration
    "terrible": -3.4, "horrible": -3.4, "awful": -3.3, "worst": -3.5, "hate": -3.2,
    "furious": -3.5, "angry": -3.0, "disaster": -3.3, "unacceptable": -3.2, "scam": -3.5,
    "fraud": -3.4, "rip-off": -3.3, "broken": -2.8, "crashed": -2.6, "crash": -2.5,
    "failing": -2.4, "failed": -2.3, "fail": -2.2, "bug": -1.8, "buggy": -2.2,
    "glitch": -1.9, "error": -2.0, "errors": -2.1, "useless": -3.0, "garbage": -3.2,
    "worthless": -3.1, "pathetic": -3.3, "disappointed": -2.8, "disappointing": -2.7,
    "frustrated": -2.9, "frustrating": -2.8, "annoyed": -2.4, "annoying": -2.3,
    "stuck": -2.1, "blocked": -2.2, "down": -1.9, "outage": -2.5, "downtime": -2.4,
    "slow": -1.7, "hangs": -1.8, "timeout": -2.0, "refused": -2.2, "denied": -2.1,
    "cancelled": -1.5, "cancel": -1.4, "charging": -1.0, "overcharged": -3.0,
    "unauthorized": -3.2, "stolen": -3.3, "complaint": -2.4, "poor": -2.2,
    "bad": -2.5, "urgent": -2.0, "critical": -2.3, "immediately": -1.6, "asap": -1.5,
    "emergency": -2.7, "loss": -2.4, "lost": -2.3, "lose": -2.1,

    # Moderate negative
    "problem": -1.9, "issues": -1.8, "issue": -1.7, "trouble": -1.8, "difficult": -1.6,
    "confusing": -1.5, "confused": -1.4, "delay": -1.6, "delayed": -1.7, "waiting": -1.2,
    "missing": -1.8, "wrong": -2.1, "incorrect": -1.9, "inaccurate": -1.8, "unable": -1.7,
    "cannot": -1.8, "cant": -1.8, "not working": -2.6, "doesnt work": -2.7,

    # Positive / Gratitude / Satisfaction
    "good": 2.2, "great": 3.1, "excellent": 3.4, "amazing": 3.5, "awesome": 3.4,
    "fantastic": 3.5, "wonderful": 3.4, "superb": 3.3, "brilliant": 3.2, "love": 3.3,
    "best": 3.2, "perfect": 3.4, "perfectly": 3.3, "happy": 2.8, "pleased": 2.6,
    "glad": 2.4, "satisfied": 2.5, "helpful": 2.7, "helped": 2.5, "thanks": 2.1,
    "thank": 2.0, "appreciate": 2.6, "appreciated": 2.7, "resolved": 2.5, "fixed": 2.4,
    "working": 2.0, "works": 2.1, "fast": 2.2, "quick": 2.0, "prompt": 2.3,
    "efficient": 2.6, "smooth": 2.4, "impressive": 2.9, "friendly": 2.5, "polite": 2.3,
    "recommend": 2.7, "recommended": 2.6, "easy": 2.2, "convenient": 2.3, "clear": 2.0,
    "intuitive": 2.4, "reliable": 2.7, "seamless": 2.8, "success": 2.7, "successful": 2.6
}

# Modifiers
BOOSTER_DICT = {
    "absolutely": 0.293, "extremely": 0.293, "really": 0.293, "so": 0.293, "very": 0.293,
    "totally": 0.293, "completely": 0.293, "highly": 0.293, "super": 0.293,
    "barely": -0.293, "hardly": -0.293, "rarely": -0.293, "slightly": -0.293,
    "somewhat": -0.293, "little": -0.293
}

NEGATIONS = {
    "not", "never", "no", "neither", "nor", "none", "without", "hardly", "scarcely",
    "barely", "didnt", "didn't", "wasnt", "wasn't", "isnt", "isn't", "cant", "can't",
    "wont", "won't", "dont", "don't", "couldnt", "couldn't", "shouldnt", "shouldn't"
}


def normalize_compound(score: float, alpha: float = 15.0) -> float:
    """Normalize score between -1.0 and 1.0 using standard VADER normalization."""
    return score / math.sqrt((score * score) + alpha)


class VaderSentimentAnalyzer:
    """
    Self-contained VADER sentiment analyzer optimized for customer service texts.
    Falls back gracefully if external nltk/vaderSentiment is not present.
    """

    def __init__(self):
        # Try importing official vaderSentiment if installed
        self._external_vader = None
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self._external_vader = SentimentIntensityAnalyzer()
        except ImportError:
            try:
                from nltk.sentiment.vader import SentimentIntensityAnalyzer
                self._external_vader = SentimentIntensityAnalyzer()
            except ImportError:
                self._external_vader = None

    def polarity_scores(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of text.
        Returns dictionary with: 'compound', 'pos', 'neu', 'neg'.
        """
        if not text or not text.strip():
            return {"compound": 0.0, "pos": 0.0, "neu": 1.0, "neg": 0.0}

        if self._external_vader:
            try:
                return self._external_vader.polarity_scores(text)
            except Exception:
                pass

        # Native implementation of VADER algorithm
        words = re.findall(r"\b[\w'-]+\b", text.lower())
        if not words:
            return {"compound": 0.0, "pos": 0.0, "neu": 1.0, "neg": 0.0}

        sentiments: List[float] = []

        for i, word in enumerate(words):
            valence = LEXICON.get(word, 0.0)

            if valence != 0.0:
                # Check preceding words for boosters or negation
                for distance in (1, 2, 3):
                    if i - distance >= 0:
                        prev_word = words[i - distance]
                        if prev_word in NEGATIONS:
                            valence = valence * -0.74
                        elif prev_word in BOOSTER_DICT:
                            b_factor = BOOSTER_DICT[prev_word]
                            valence += b_factor if valence > 0 else -b_factor

                # Check ALL CAPS in original text
                orig_token = re.findall(r"\b[\w'-]+\b", text)[i] if i < len(re.findall(r"\b[\w'-]+\b", text)) else word
                if orig_token.isupper() and len(orig_token) > 1:
                    valence += 0.733 if valence > 0 else -0.733

                sentiments.append(valence)

        # Exclamation marks boost
        excl_count = min(text.count("!"), 4)
        if excl_count > 0:
            if sentiments:
                mean_val = sum(sentiments) / len(sentiments)
                if mean_val > 0:
                    sentiments.append(excl_count * 0.292)
                elif mean_val < 0:
                    sentiments.append(-excl_count * 0.292)

        # Question mark boost (frustration)
        ques_count = text.count("?")
        if ques_count > 1 and sentiments and (sum(sentiments) < 0):
            sentiments.append(-0.5)

        if not sentiments:
            return {"compound": 0.0, "pos": 0.0, "neu": 1.0, "neg": 0.0}

        sum_s = sum(sentiments)
        compound = normalize_compound(sum_s)

        # Calculate pos, neg, neu ratios
        pos_sum = sum(s for s in sentiments if s > 0)
        neg_sum = sum(abs(s) for s in sentiments if s < 0)
        total_valence = pos_sum + neg_sum + 0.001

        pos_ratio = round(pos_sum / (total_valence + len(words)), 3)
        neg_ratio = round(neg_sum / (total_valence + len(words)), 3)
        neu_ratio = round(max(0.0, 1.0 - (pos_ratio + neg_ratio)), 3)

        return {
            "compound": round(compound, 4),
            "pos": pos_ratio,
            "neu": neu_ratio,
            "neg": neg_ratio
        }

    def get_sentiment_label(self, compound_score: float) -> str:
        """Categorize sentiment compound score into Positive, Neutral, or Negative."""
        if compound_score >= 0.05:
            return "Positive"
        elif compound_score <= -0.05:
            return "Negative"
        else:
            return "Neutral"
