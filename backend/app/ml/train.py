"""
Training Pipeline for Customer Support Ticket Intelligence.
1. Ticket Category Classification: TF-IDF Vectorizer + Logistic Regression
2. Ticket Priority Prediction: Feature Extraction + Random Forest Classifier
"""

import os
import re
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

from .vader_sentiment import VaderSentimentAnalyzer

# Seed dataset of realistic customer support tickets
DATASET = [
    # Technical Issue
    ("Our web application crashes every time a user uploads a PDF larger than 5MB with error 500.", "Technical Issue", "Urgent"),
    ("Database timeout error on the production server during high traffic peak hours.", "Technical Issue", "Urgent"),
    ("Mobile app keeps freezing on the checkout screen after the latest iOS 17 update.", "Technical Issue", "High"),
    ("API webhook returns 401 Unauthorized even though my API key is valid and active.", "Technical Issue", "High"),
    ("Slow query response when fetching user analytics dashboard for the past 90 days.", "Technical Issue", "Medium"),
    ("White blank screen appears when opening the settings tab in Firefox browser.", "Technical Issue", "Medium"),
    ("Minor styling glitch on mobile Safari where navigation bar overlaps with top banner.", "Technical Issue", "Low"),
    ("Typo found in the error notification message when entering invalid email format.", "Technical Issue", "Low"),
    ("Critical system crash! All customers are unable to access their files right now!", "Technical Issue", "Urgent"),
    ("Server is throwing continuous 503 service unavailable errors since 10 minutes ago.", "Technical Issue", "Urgent"),
    ("Exported Excel file corrupted and missing columns for transaction history.", "Technical Issue", "Medium"),
    ("Bluetooth sync not connecting with our hardware terminal on Android 14.", "Technical Issue", "High"),

    # Billing & Payment
    ("I was double charged on my credit card for the month of October! Please refund immediately!", "Billing & Payment", "Urgent"),
    ("Unauthorized debit of $149 from my account without prior notification or renewal consent.", "Billing & Payment", "Urgent"),
    ("My payment failed with error card declined but bank confirmed transaction approved.", "Billing & Payment", "High"),
    ("Can I get an updated VAT invoice with our company tax registration number?", "Billing & Payment", "Medium"),
    ("How do I update our credit card details on file for automatic monthly recurring billing?", "Billing & Payment", "Low"),
    ("We were charged enterprise pricing even though we downgraded to the team plan last week.", "Billing & Payment", "High"),
    ("Where can I download the previous 12 months receipts for annual tax accounting?", "Billing & Payment", "Low"),
    ("Promo discount code WELCOME20 was not applied during the checkout process.", "Billing & Payment", "Medium"),
    ("Our account has been suspended due to an alleged billing failure but payment was made.", "Billing & Payment", "Urgent"),
    ("Does your platform charge international foreign transaction fees on transactions?", "Billing & Payment", "Low"),

    # Account Management
    ("Locked out of my admin account and 2-step verification recovery code is not arriving.", "Account Management", "Urgent"),
    ("Employee left company, need to immediately revoke their access and transfer ownership.", "Account Management", "Urgent"),
    ("Password reset email link has expired or is giving invalid token error.", "Account Management", "High"),
    ("How do I invite additional team members and assign role-based permissions?", "Account Management", "Medium"),
    ("Need assistance changing the primary contact email address associated with our workspace.", "Account Management", "Medium"),
    ("How do I permanently delete my user account and associated personal data?", "Account Management", "Medium"),
    ("Where do I set up Single Sign-On (SSO) with Okta or Azure Active Directory?", "Account Management", "Medium"),
    ("Can we rename our workspace subdomain from company-old.app to company-new.app?", "Account Management", "Low"),
    ("Forgot my security questions and cannot login from a new device.", "Account Management", "High"),
    ("Please update the phone number used for SMS authentication.", "Account Management", "Medium"),

    # Product Feature Request
    ("Would love to see a native Dark Mode option for late night working hours.", "Product Feature Request", "Low"),
    ("Please add support for Zapier and Make.com integrations to automate our workflows.", "Product Feature Request", "Medium"),
    ("Is there any plan to support multi-language localization for Spanish and German?", "Product Feature Request", "Medium"),
    ("It would be very helpful if we could export reports directly to PDF and PowerPoint.", "Product Feature Request", "Medium"),
    ("Requesting ability to bulk edit ticket tags and assignees across multiple pages.", "Product Feature Request", "Medium"),
    ("Can you add Kanban board view in addition to the existing table list view?", "Product Feature Request", "Low"),
    ("Custom webhook alerts sent to Microsoft Teams channels would be a huge time saver.", "Product Feature Request", "Medium"),
    ("Please increase the maximum file attachment size limit from 10MB to 50MB.", "Product Feature Request", "Low"),
    ("Feature suggestion: auto-translate customer incoming messages in real-time.", "Product Feature Request", "Low"),
    ("Add customizable dashboard widgets for support team leads to track hourly SLA.", "Product Feature Request", "Medium"),

    # Cancellation & Refund
    ("Cancel my subscription immediately and issue a full refund under your 30-day guarantee.", "Cancellation & Refund", "Urgent"),
    ("I want to terminate our annual contract due to prolonged service outages.", "Cancellation & Refund", "Urgent"),
    ("Please stop automatic renewal on our account expiring at the end of this month.", "Cancellation & Refund", "High"),
    ("We are downsizing our team and need to downgrade from Enterprise to Starter tier.", "Cancellation & Refund", "Medium"),
    ("Requesting refund for unused months following our department restructuring.", "Cancellation & Refund", "High"),
    ("Service did not meet our project expectations, how do I initiate refund procedure?", "Cancellation & Refund", "High"),
    ("Please confirm that my subscription has been cancelled and my credit card will not be charged.", "Cancellation & Refund", "Medium"),
    ("How do I turn off recurring billing while keeping my account active until cycle ends?", "Cancellation & Refund", "Low"),
    ("I did not authorize the annual renewal, please refund immediately or I will dispute with my bank.", "Cancellation & Refund", "Urgent"),
    ("Please close my business account and confirm all data will be purged.", "Cancellation & Refund", "Medium"),

    # General Inquiry
    ("What are the pricing tiers for your enterprise plan with custom SLA support?", "General Inquiry", "Medium"),
    ("Do you offer nonprofit or educational discounts for certified universities?", "General Inquiry", "Low"),
    ("Where is your data hosted and are you SOC2 Type II and GDPR compliant?", "General Inquiry", "Medium"),
    ("What are the customer support operating hours and phone contact numbers?", "General Inquiry", "Low"),
    ("Is there an official API documentation or SDK available for Python and Node.js?", "General Inquiry", "Low"),
    ("Can we schedule a 30-minute product demonstration for our executive leadership?", "General Inquiry", "Medium"),
    ("Where can I find your terms of service and privacy policy documentation?", "General Inquiry", "Low"),
    ("Do you provide on-premise installation or is this strictly a SaaS platform?", "General Inquiry", "Low"),
    ("How does your AI assistant protect sensitive customer personal identifiable data?", "General Inquiry", "Medium"),
    ("What is the average response time for standard priority tickets?", "General Inquiry", "Low")
]

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


def build_priority_features(
    text: str,
    compound_sentiment: float,
    neg_sentiment: float,
    category: str
) -> list:
    lower = text.lower()
    words = re.findall(r"\b\w+\b", text)
    word_count = len(words)
    char_count = len(text)

    urgent_count = sum(1 for kw in URGENT_KEYWORDS if kw in lower)
    exclamation_count = text.count("!")
    question_count = text.count("?")

    upper_words = sum(1 for w in words if w.isupper() and len(w) > 1)
    uppercase_ratio = upper_words / max(word_count, 1)

    cat_index = CATEGORY_MAPPING.get(category, 5)
    cat_one_hot = [0.0] * len(CATEGORY_MAPPING)
    cat_one_hot[cat_index] = 1.0

    return [
        compound_sentiment,
        neg_sentiment,
        float(char_count),
        float(word_count),
        float(urgent_count),
        float(exclamation_count),
        float(question_count),
        uppercase_ratio
    ] + cat_one_hot


def train_models():
    """Execute training for both Category Classifier and Priority Model."""
    model_dir = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(model_dir, exist_ok=True)

    print("==================================================")
    print("AI CUSTOMER SERVICE PLATFORM - ML MODEL TRAINING")
    print("==================================================")

    texts = [item[0] for item in DATASET]
    categories = [item[1] for item in DATASET]
    priorities = [item[2] for item in DATASET]

    # --- 1. TF-IDF + LOGISTIC REGRESSION FOR CATEGORY ---
    print("\n[1/3] Training TF-IDF + Logistic Regression Category Classifier...")
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=2500,
        sublinear_tf=True
    )
    X_vec = vectorizer.fit_transform(texts)

    cat_clf = LogisticRegression(
        C=2.5,
        max_iter=1000,
        class_weight="balanced",
        random_state=42
    )
    cat_clf.fit(X_vec, categories)
    cat_preds = cat_clf.predict(X_vec)
    cat_acc = accuracy_score(categories, cat_preds)
    print(f"Category Classifier Training Accuracy: {cat_acc * 100:.2f}%")

    # Save category models
    vec_path = os.path.join(model_dir, "category_vectorizer.joblib")
    clf_path = os.path.join(model_dir, "category_classifier.joblib")
    joblib.dump(vectorizer, vec_path)
    joblib.dump(cat_clf, clf_path)
    print(f"Saved Vectorizer: {vec_path}")
    print(f"Saved Category Classifier: {clf_path}")

    # --- 2. VADER SENTIMENT FEATURE EXTRACTION ---
    print("\n[2/3] Extracting VADER Sentiment Scores and Text Urgency Features...")
    vader = VaderSentimentAnalyzer()
    sentiment_compounds = []
    sentiment_negs = []

    for t in texts:
        scores = vader.polarity_scores(t)
        sentiment_compounds.append(scores["compound"])
        sentiment_negs.append(scores["neg"])

    # --- 3. RANDOM FOREST FOR PRIORITY PREDICTION ---
    print("\n[3/3] Training Random Forest Priority Model...")
    X_priority = []
    for i in range(len(texts)):
        feats = build_priority_features(
            text=texts[i],
            compound_sentiment=sentiment_compounds[i],
            neg_sentiment=sentiment_negs[i],
            category=categories[i]
        )
        X_priority.append(feats)

    X_priority = np.array(X_priority)
    rf_clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=6,
        class_weight="balanced",
        random_state=42
    )
    rf_clf.fit(X_priority, priorities)
    rf_preds = rf_clf.predict(X_priority)
    rf_acc = accuracy_score(priorities, rf_preds)
    print(f"Priority Classifier Training Accuracy: {rf_acc * 100:.2f}%")

    # Save priority model
    priority_path = os.path.join(model_dir, "priority_model.joblib")
    joblib.dump(rf_clf, priority_path)
    print(f"Saved Priority Model: {priority_path}")

    print("\n==================================================")
    print("SUCCESS: All models trained and serialized successfully!")
    print("==================================================")
    return True

if __name__ == "__main__":
    train_models()
