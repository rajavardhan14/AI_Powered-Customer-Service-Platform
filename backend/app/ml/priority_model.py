"""
Ticket Priority Prediction using Random Forest Classifier.
Evaluates ticket text, sentiment scores, customer urgency indicators,
and ticket category to predict priority level: Low, Medium, High, Urgent.
"""

import os
import re
import numpy as np
import joblib
from typing import Dict, Any, Optional, List

PRIORITY_LEVELS = ["Low", "Medium", "High", "Urgent"]

URGENT_KEYWORDS = [
    "urgent", "immediately", "asap", "emergency", "critical", "broken",
    "downtime", "outage", "loss", "crash", "blocked", "escalate",
    "overcharged", "fraud", "unauthorized", "fail", "failed", "unacceptable",
    "disaster", "legal", "lawsuit", "refund immediately", "breach"
]

CATEGORY_MAPPING = {
    "Technical Issue": 0,
    "Billing & Payment": 1,
    "Account Management": 2,
    "Product Feature Request": 3,
    "Cancellation & Refund": 4,
    "General Inquiry": 5
}

class TicketPriorityModel:
    """
    Random Forest Classifier for predicting ticket priority.
    """

    def __init__(self, model_dir: Optional[str] = None):
        if model_dir is None:
            model_dir = os.path.join(os.path.dirname(__file__), "models")
        self.model_dir = model_dir
        self.model_path = os.path.join(self.model_dir, "priority_model.joblib")
        self.model = None
        self.is_loaded = False
        self._load_model_if_exists()

    def _load_model_if_exists(self) -> bool:
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                self.is_loaded = True
                return True
            except Exception as e:
                print(f"Error loading priority model: {e}")
                self.is_loaded = False
                return False
        return False

    def extract_features(
        self,
        text: str,
        compound_sentiment: float,
        neg_sentiment: float,
        category: str
    ) -> np.ndarray:
        """
        Extract numerical features for Random Forest:
        1. compound_sentiment (-1.0 to 1.0)
        2. neg_sentiment (0.0 to 1.0)
        3. text_length (char count)
        4. word_count
        5. urgent_keyword_count
        6. exclamation_count
        7. question_count
        8. uppercase_ratio
        9-14. Category one-hot encoding (6 features)
        """
        lower = text.lower()
        words = re.findall(r"\b\w+\b", text)
        word_count = len(words)
        char_count = len(text)

        urgent_count = sum(1 for kw in URGENT_KEYWORDS if kw in lower)
        exclamation_count = text.count("!")
        question_count = text.count("?")

        upper_words = sum(1 for w in words if w.isupper() and len(w) > 1)
        uppercase_ratio = upper_words / max(word_count, 1)

        # One-hot category
        cat_index = CATEGORY_MAPPING.get(category, 5)
        cat_one_hot = [0.0] * len(CATEGORY_MAPPING)
        cat_one_hot[cat_index] = 1.0

        features = [
            compound_sentiment,
            neg_sentiment,
            float(char_count),
            float(word_count),
            float(urgent_count),
            float(exclamation_count),
            float(question_count),
            uppercase_ratio
        ] + cat_one_hot

        return np.array(features).reshape(1, -1)

    def predict(
        self,
        text: str,
        compound_sentiment: float,
        neg_sentiment: float,
        category: str
    ) -> Dict[str, Any]:
        """
        Predict ticket priority (Low, Medium, High, Urgent).
        """
        if not self.is_loaded:
            if not self._load_model_if_exists():
                return self._rule_based_priority(text, compound_sentiment, neg_sentiment, category)

        try:
            feats = self.extract_features(text, compound_sentiment, neg_sentiment, category)
            pred_class = self.model.predict(feats)[0]
            probs = self.model.predict_proba(feats)[0]
            classes = self.model.classes_

            prob_dict = {str(c): round(float(p), 4) for c, p in zip(classes, probs)}

            return {
                "priority": str(pred_class),
                "confidence": round(float(prob_dict.get(str(pred_class), 0.7)), 3),
                "probabilities": prob_dict,
                "urgency_score": self._compute_urgency_score(text, compound_sentiment, neg_sentiment)
            }
        except Exception as e:
            print(f"Error in priority prediction: {e}")
            return self._rule_based_priority(text, compound_sentiment, neg_sentiment, category)

    def _compute_urgency_score(self, text: str, compound: float, neg: float) -> float:
        """Score from 0.0 to 100.0 indicating overall urgency."""
        lower = text.lower()
        score = 20.0  # baseline
        # Sentiment penalty
        if compound < -0.4:
            score += 30.0
        elif compound < 0.0:
            score += 15.0

        score += min(neg * 35.0, 25.0)

        # Keyword boost
        for kw in URGENT_KEYWORDS:
            if kw in lower:
                score += 15.0
                break

        if "!" in text:
            score += min(text.count("!") * 5.0, 15.0)

        return round(min(100.0, max(0.0, score)), 1)

    def _rule_based_priority(
        self,
        text: str,
        compound: float,
        neg: float,
        category: str
    ) -> Dict[str, Any]:
        """Rule-based heuristic when model is not yet compiled."""
        lower = text.lower()
        has_urgent_kw = any(kw in lower for kw in ["urgent", "immediately", "critical", "downtime", "emergency", "fraud"])

        if has_urgent_kw or (compound <= -0.6 and category in ["Technical Issue", "Billing & Payment"]):
            priority = "Urgent"
        elif compound <= -0.2 or category in ["Technical Issue", "Cancellation & Refund"] or "!" in text:
            priority = "High"
        elif compound < 0.2 or category in ["Billing & Payment", "Account Management"]:
            priority = "Medium"
        else:
            priority = "Low"

        urgency_score = self._compute_urgency_score(text, compound, neg)
        return {
            "priority": priority,
            "confidence": 0.85,
            "probabilities": {
                "Low": 0.1 if priority != "Low" else 0.7,
                "Medium": 0.1 if priority != "Medium" else 0.7,
                "High": 0.1 if priority != "High" else 0.7,
                "Urgent": 0.1 if priority != "Urgent" else 0.7
            },
            "urgency_score": urgency_score
        }
