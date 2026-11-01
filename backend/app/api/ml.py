"""
Machine Learning API Endpoints.
Provides ticket classification, VADER sentiment analysis, and Random Forest priority scoring.
"""

from fastapi import APIRouter
from app.schemas import MLPredictRequest, MLPredictResponse
from app.ml.vader_sentiment import VaderSentimentAnalyzer
from app.ml.classifier import TicketCategoryClassifier
from app.ml.priority_model import TicketPriorityModel

router = APIRouter(prefix="/api/ml", tags=["Machine Learning"])

vader = VaderSentimentAnalyzer()
classifier = TicketCategoryClassifier()
priority_model = TicketPriorityModel()

def run_ml_pipeline(text: str, override_category: str = None) -> dict:
    """Run full ML analysis on text."""
    # 1. Category Classification (TF-IDF + Logistic Regression)
    cat_res = classifier.predict(text)
    assigned_category = override_category or cat_res["category"]

    # 2. Sentiment Analysis (VADER)
    sentiment_scores = vader.polarity_scores(text)
    compound = sentiment_scores["compound"]
    sentiment_label = vader.get_sentiment_label(compound)

    # 3. Priority Prediction (Random Forest)
    prio_res = priority_model.predict(
        text=text,
        compound_sentiment=compound,
        neg_sentiment=sentiment_scores["neg"],
        category=assigned_category
    )

    return {
        "category": assigned_category,
        "category_confidence": cat_res["confidence"],
        "category_probabilities": cat_res["probabilities"],
        "sentiment_label": sentiment_label,
        "sentiment_score": compound,
        "sentiment_details": sentiment_scores,
        "priority": prio_res["priority"],
        "priority_confidence": prio_res["confidence"],
        "priority_probabilities": prio_res["probabilities"],
        "urgency_score": prio_res["urgency_score"]
    }

@router.post("/predict", response_model=MLPredictResponse)
def predict_ticket(payload: MLPredictRequest):
    """
    Run the full ML prediction pipeline on customer inquiry text:
    - Ticket Category: TF-IDF + Logistic Regression
    - Sentiment: VADER (Compound score, Pos/Neu/Neg)
    - Priority: Random Forest Classifier
    """
    return run_ml_pipeline(payload.text, payload.category)
