"""
Unit and Integration Tests for Machine Learning Components.
1. TF-IDF + Logistic Regression Category Classifier
2. VADER Sentiment Analysis
3. Random Forest Priority Prediction
"""

import sys
import os
import unittest

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ml.vader_sentiment import VaderSentimentAnalyzer
from app.ml.classifier import TicketCategoryClassifier
from app.ml.priority_model import TicketPriorityModel

class TestMLPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.vader = VaderSentimentAnalyzer()
        cls.classifier = TicketCategoryClassifier()
        cls.priority_model = TicketPriorityModel()

    def test_vader_positive_sentiment(self):
        text = "Thank you so much! The support team was extremely helpful and resolved my issue fast!"
        scores = self.vader.polarity_scores(text)
        label = self.vader.get_sentiment_label(scores["compound"])
        self.assertGreater(scores["compound"], 0.2)
        self.assertEqual(label, "Positive")

    def test_vader_negative_sentiment(self):
        text = "This is a terrible disaster! My production database crashed and all services are down!"
        scores = self.vader.polarity_scores(text)
        label = self.vader.get_sentiment_label(scores["compound"])
        self.assertLess(scores["compound"], -0.2)
        self.assertEqual(label, "Negative")

    def test_category_classifier_billing(self):
        text = "I was double charged on my credit card for invoice #9921. Please issue refund."
        result = self.classifier.predict(text)
        self.assertIn("category", result)
        self.assertEqual(result["category"], "Billing & Payment")
        self.assertGreater(result["confidence"], 0.35)

    def test_category_classifier_technical(self):
        text = "Server returns 500 internal server error when uploading file to our cluster."
        result = self.classifier.predict(text)
        self.assertEqual(result["category"], "Technical Issue")

    def test_priority_model_urgent(self):
        text = "CRITICAL: Production server is down immediately! Huge financial loss!"
        scores = self.vader.polarity_scores(text)
        result = self.priority_model.predict(
            text=text,
            compound_sentiment=scores["compound"],
            neg_sentiment=scores["neg"],
            category="Technical Issue"
        )
        self.assertIn(result["priority"], ["Urgent", "High"])
        self.assertGreaterEqual(result["urgency_score"], 60.0)

if __name__ == "__main__":
    unittest.main()
