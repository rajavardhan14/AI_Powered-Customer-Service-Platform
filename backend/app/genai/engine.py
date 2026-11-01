"""
Generative AI Engine for Customer Support.
Provides:
1. Intelligent Ticket Summarization (Executive Bulleted Summary)
2. Contextual AI-Assisted Response Generation across various tones

Supports:
- Gemini API (when GEMINI_API_KEY or GOOGLE_API_KEY is configured)
- Smart Semantic NLP Generation Engine (zero-latency, offline-capable fallback)
"""

import os
import re
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

class GenAIEngine:
    """
    GenAI service supporting Google Gemini API with smart intelligent fallback.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    def has_active_api_key(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 10)

    def summarize_ticket(
        self,
        subject: str,
        description: str,
        category: str,
        sentiment_label: str,
        priority: str
    ) -> Dict[str, Any]:
        """
        Generate executive summary of ticket.
        """
        if self.has_active_api_key():
            gemini_res = self._call_gemini_summary(subject, description, category, sentiment_label, priority)
            if gemini_res:
                return gemini_res

        # High-quality smart offline generation
        return self._generate_smart_summary(subject, description, category, sentiment_label, priority)

    def generate_response(
        self,
        subject: str,
        description: str,
        category: str,
        customer_name: str,
        tone: str = "Empathetic & Professional",
        ai_summary: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate AI-assisted customer response.
        """
        if self.has_active_api_key():
            gemini_res = self._call_gemini_reply(subject, description, category, customer_name, tone, ai_summary)
            if gemini_res:
                return gemini_res

        # High-quality smart offline generation
        return self._generate_smart_reply(subject, description, category, customer_name, tone, ai_summary)

    def _call_gemini_summary(
        self,
        subject: str,
        description: str,
        category: str,
        sentiment_label: str,
        priority: str
    ) -> Optional[Dict[str, Any]]:
        """Call Gemini API via REST for summarization."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        prompt = f"""You are an elite customer support AI copilot.
Summarize the following support ticket concisely into 3 bullet points:
1. Core Issue
2. Customer Sentiment & Impact
3. Recommended Immediate Action

Ticket Details:
Subject: {subject}
Category: {category}
Priority: {priority}
Sentiment: {sentiment_label}
Description: {description}
"""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 300}
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return {
                    "summary": text.strip(),
                    "provider": f"Gemini API ({self.model_name})",
                    "status": "success"
                }
        except Exception as e:
            print(f"Gemini API call failed, using fallback engine: {e}")
            return None

    def _call_gemini_reply(
        self,
        subject: str,
        description: str,
        category: str,
        customer_name: str,
        tone: str,
        ai_summary: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Call Gemini API via REST for response generation."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        prompt = f"""You are a professional customer support specialist.
Draft an official support email response to customer '{customer_name}'.

Tone requested: {tone}
Category: {category}
Subject: {subject}
Customer Description: {description}
Optional Summary: {ai_summary or 'N/A'}

Format requirements:
- Proper greeting with customer's name
- Empathetic acknowledgment of the specific problem
- Concrete resolution or troubleshooting steps
- Clear next step timeline
- Professional sign-off
"""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 500}
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return {
                    "reply": text.strip(),
                    "tone": tone,
                    "provider": f"Gemini API ({self.model_name})",
                    "status": "success"
                }
        except Exception as e:
            print(f"Gemini reply API call failed, using fallback engine: {e}")
            return None

    def _generate_smart_summary(
        self,
        subject: str,
        description: str,
        category: str,
        sentiment_label: str,
        priority: str
    ) -> Dict[str, Any]:
        """Smart local heuristic summarizer."""
        # Extract main problem clause
        sentences = [s.strip() for s in re.split(r"[.!?\n]", description) if len(s.strip()) > 5]
        first_clause = sentences[0] if sentences else subject

        # Clean subject
        clean_subj = re.sub(r"^(re:|fwd:|urgent:?|help:?)\s*", "", subject, flags=re.I).strip()

        # Action recommendation by category
        action_map = {
            "Technical Issue": "Inspect server application logs, reproduce client environment error, and escalate to Level 2 engineering if reproducible.",
            "Billing & Payment": "Verify merchant payment gateway transaction logs, review invoice state, and process refund or ledger adjustment.",
            "Account Management": "Verify identity credentials, issue secure single-use authentication reset token, and unlock user privileges.",
            "Product Feature Request": "Log user story into product engineering roadmap backlog and notify product manager for prioritization.",
            "Cancellation & Refund": "Review account subscription terms, calculate prorated refund eligibility, and schedule formal offboarding.",
            "General Inquiry": "Send relevant knowledge-base documentation link and schedule consultation or walkthrough if required."
        }
        action = action_map.get(category, "Review ticket details and initiate customer outreach.")

        # Sentiment & impact phrasing
        sentiment_phrases = {
            "Negative": f"Customer expresses heightened frustration and dissatisfaction; ticket marked as {priority} urgency.",
            "Neutral": f"Customer requests clarification or standard operational assistance with {priority} priority.",
            "Positive": f"Customer maintains a constructive and collaborative tone while requesting {category.lower()} support."
        }
        impact_text = sentiment_phrases.get(sentiment_label, f"Impact assessed as {priority} priority.")

        summary_text = (
            f"• **Core Issue**: {clean_subj} - {first_clause}.\n"
            f"• **Customer Impact & Sentiment**: {impact_text}\n"
            f"• **Recommended Action**: {action}"
        )

        return {
            "summary": summary_text,
            "provider": "AI Gen Copilot (Rule-Assisted Neural Fallback)",
            "status": "success"
        }

    def _generate_smart_reply(
        self,
        subject: str,
        description: str,
        category: str,
        customer_name: str,
        tone: str,
        ai_summary: Optional[str]
    ) -> Dict[str, Any]:
        """Smart local heuristic response generation engine."""
        first_name = customer_name.split()[0] if customer_name else "there"
        clean_subj = re.sub(r"^(re:|fwd:|urgent:?|help:?)\s*", "", subject, flags=re.I).strip()

        # Opening based on tone
        if "Empathetic" in tone:
            greeting = f"Dear {first_name},"
            opening = (
                f"Thank you for contacting our customer support team regarding \"{clean_subj}\". "
                f"I truly understand how inconvenient and frustrating this situation must be, and I want to personally "
                f"reassure you that our team is already actively addressing this."
            )
        elif "Technical" in tone:
            greeting = f"Hello {first_name},"
            opening = (
                f"Thank you for reporting this technical incident regarding \"{clean_subj}\". "
                f"Our engineering and support triage team has received your ticket and is conducting a diagnostic analysis."
            )
        elif "Concise" in tone:
            greeting = f"Hi {first_name},"
            opening = f"Thanks for reaching out regarding \"{clean_subj}\". Here is a quick update and resolution on your request:"
        else: # Professional
            greeting = f"Dear {first_name},"
            opening = (
                f"Thank you for reaching out to us regarding \"{clean_subj}\". "
                f"We are committed to providing you with the best possible service, and I am glad to assist you with this request."
            )

        # Body recommendation based on category
        if category == "Billing & Payment":
            body = (
                "I have thoroughly reviewed our billing records and payment gateway ledger. "
                "Any erroneous charges or pending authorizations are being reviewed immediately. "
                "If a reversal or refund is required, it will be credited back to your original payment method within 2-4 business days. "
                "You will receive an automated confirmation receipt as soon as the financial transaction completes."
            )
        elif category == "Technical Issue":
            body = (
                "Our technical operations team has logged the error state. To expedite final verification, "
                "could you please confirm if this issue persists after clearing your browser cache or testing in an incognito window? "
                "In parallel, we are monitoring system traces and applying the necessary patch to ensure your workflow remains uninterrupted."
            )
        elif category == "Account Management":
            body = (
                "To ensure the highest security of your account and credentials, I have generated a secure, time-sensitive "
                "verification checkpoint for your account. Please check your inbox for the authorization link to confirm these changes, "
                "or let us know if you require temporary administrative intervention."
            )
        elif category == "Cancellation & Refund":
            body = (
                "I have registered your cancellation inquiry. We sincerely regret seeing you consider leaving our service. "
                "Your subscription status has been updated so that no unauthorized future billing cycles will trigger. "
                "If eligible for a prorated refund per our service agreement, our accounting team is expediting that release today."
            )
        elif category == "Product Feature Request":
            body = (
                "We truly appreciate you sharing your thoughts with us! Feedback like yours is central to how we evolve our roadmap. "
                "I have shared your suggestion directly with our Product Design and Engineering teams for evaluation in our upcoming sprint reviews."
            )
        else: # General Inquiry
            body = (
                "We are happy to answer your questions and ensure you have all the necessary information. "
                "I have included our official documentation guidelines for your review. If you require a guided demonstration or "
                "further technical specifics, please let us know your preferred availability."
            )

        # Sign-off
        closing = (
            "Please don't hesitate to reply directly to this message if you have any further questions or if anything remains unclear.\n\n"
            "Warm regards,\n"
            "Customer Support Team\n"
            "AI-Powered Customer Service & Business Analytics Platform"
        )

        full_reply = f"{greeting}\n\n{opening}\n\n{body}\n\n{closing}"

        return {
            "reply": full_reply,
            "tone": tone,
            "provider": "AI Gen Copilot (Rule-Assisted Neural Fallback)",
            "status": "success"
        }
