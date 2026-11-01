"""
Ticket Category Classifier using TF-IDF Vectorizer and Logistic Regression.
Predicts ticket category and returns confidence scores.
"""

import os
import joblib
from typing import Dict, Any, Tuple, Optional

# Supported categories
CATEGORIES = [
    "Technical Issue",
    "Billing & Payment",
    "Account Management",
    "Product Feature Request",
    "Cancellation & Refund",
    "General Inquiry"
]

class TicketCategoryClassifier:
    """
    ML Classifier using TF-IDF + Logistic Regression for ticket categorization.
    """

    def __init__(self, model_dir: Optional[str] = None):
        if model_dir is None:
            model_dir = os.path.join(os.path.dirname(__file__), "models")
        self.model_dir = model_dir
        self.vectorizer_path = os.path.join(self.model_dir, "category_vectorizer.joblib")
        self.classifier_path = os.path.join(self.model_dir, "category_classifier.joblib")
        self.vectorizer = None
        self.model = None
        self.is_loaded = False
        self._load_models_if_exist()

    def _load_models_if_exist(self) -> bool:
        if os.path.exists(self.vectorizer_path) and os.path.exists(self.classifier_path):
            try:
                self.vectorizer = joblib.load(self.vectorizer_path)
                self.model = joblib.load(self.classifier_path)
                self.is_loaded = True
                return True
            except Exception as e:
                print(f"Error loading category model: {e}")
                self.is_loaded = False
                return False
        return False

    def predict(self, text: str) -> Dict[str, Any]:
        """
        Predict category and probabilities for given ticket text.
        """
        if not self.is_loaded:
            if not self._load_models_if_exist():
                # Fallback rule-based if model not yet trained
                return self._rule_based_fallback(text)

        cleaned_text = text.strip()
        if not cleaned_text:
            return {
                "category": "General Inquiry",
                "confidence": 0.5,
                "probabilities": {cat: 1.0 / len(CATEGORIES) for cat in CATEGORIES}
            }

        try:
            features = self.vectorizer.transform([cleaned_text])
            probs = self.model.predict_proba(features)[0]
            classes = self.model.classes_

            prob_dict = {str(c): float(p) for c, p in zip(classes, probs)}
            best_cat = max(prob_dict, key=prob_dict.get)
            confidence = prob_dict[best_cat]

            return {
                "category": best_cat,
                "confidence": round(float(confidence), 3),
                "probabilities": {k: round(v, 4) for k, v in prob_dict.items()}
            }
        except Exception as e:
            print(f"Prediction exception: {e}")
            return self._rule_based_fallback(text)

    def _rule_based_fallback(self, text: str) -> Dict[str, Any]:
        """Rule-based heuristic fallback when model is initializing."""
        lower = text.lower()
        scores = {cat: 0.1 for cat in CATEGORIES}

        if any(w in lower for w in ["invoice", "charge", "payment", "card", "bill", "price", "receipt"]):
            scores["Billing & Payment"] += 0.7
        if any(w in lower for w in ["error", "bug", "crash", "500", "404", "exception", "failed", "broken", "api"]):
            scores["Technical Issue"] += 0.8
        if any(w in lower for w in ["password", "login", "mfa", "2fa", "profile", "permission", "email", "account"]):
            scores["Account Management"] += 0.7
        if any(w in lower for w in ["cancel", "refund", "money back", "subscription cancel", "unsubscribe", "terminate"]):
            scores["Cancellation & Refund"] += 0.85
        if any(w in lower for w in ["feature", "request", "would love", "dark mode", "add", "integration", "enhancement"]):
            scores["Product Feature Request"] += 0.75
        if any(w in lower for w in ["how to", "question", "pricing", "enterprise", "info", "what is"]):
            scores["General Inquiry"] += 0.6

        total = sum(scores.values())
        norm_probs = {k: round(v / total, 3) for k, v in scores.items()}
        best = max(norm_probs, key=norm_probs.get)

        return {
            "category": best,
            "confidence": norm_probs[best],
            "probabilities": norm_probs
        }
