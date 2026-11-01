"""
API and Database Integration Tests.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import (
    init_db,
    create_ticket,
    get_tickets,
    get_ticket_by_id,
    update_ticket,
    delete_ticket,
    add_reply,
    get_replies,
    get_analytics_metrics
)
from app.genai.engine import GenAIEngine

class TestDatabaseAndAPI(unittest.TestCase):

    def setUp(self):
        init_db()

    def test_ticket_crud_and_replies(self):
        # 1. Create ticket
        t = create_ticket(
            customer_name="Test Customer",
            customer_email="test@example.com",
            subject="Test Account Issue",
            description="Unable to access the workspace settings page.",
            category="Account Management",
            predicted_category="Account Management",
            category_confidence=0.91,
            sentiment_label="Neutral",
            sentiment_score=0.0,
            priority="Medium",
            predicted_priority="Medium",
            status="Open"
        )
        ticket_id = t["id"]
        self.assertIsNotNone(ticket_id)
        self.assertEqual(t["customer_name"], "Test Customer")

        # 2. Add reply
        reply = add_reply(
            ticket_id=ticket_id,
            sender_type="Agent",
            sender_name="Alex Support",
            message="We have granted you workspace permissions."
        )
        self.assertEqual(reply["sender_name"], "Alex Support")

        # Status should update to 'In Progress' automatically on agent reply
        updated_t = get_ticket_by_id(ticket_id)
        self.assertEqual(updated_t["status"], "In Progress")

        # 3. Get replies
        replies = get_replies(ticket_id)
        self.assertGreaterEqual(len(replies), 1)

        # 4. Resolve ticket
        resolved = update_ticket(ticket_id, status="Resolved", resolution_notes="Permission granted.")
        self.assertEqual(resolved["status"], "Resolved")

        # 5. Delete ticket
        deleted = delete_ticket(ticket_id)
        self.assertTrue(deleted)
        self.assertIsNone(get_ticket_by_id(ticket_id))

    def test_analytics_metrics(self):
        metrics = get_analytics_metrics()
        self.assertIn("kpis", metrics)
        self.assertIn("category_distribution", metrics)
        self.assertIn("sentiment_distribution", metrics)
        self.assertIn("priority_distribution", metrics)

    def test_genai_summary_and_reply(self):
        engine = GenAIEngine()
        summary = engine.summarize_ticket(
            subject="Cannot connect to SQL database",
            description="Our service is getting connection refused error 500.",
            category="Technical Issue",
            sentiment_label="Negative",
            priority="Urgent"
        )
        self.assertIn("summary", summary)
        self.assertIn("Core Issue", summary["summary"])

        reply = engine.generate_response(
            subject="Cannot connect to SQL database",
            description="Our service is getting connection refused error 500.",
            category="Technical Issue",
            customer_name="Alice Smith",
            tone="Technical & In-Depth"
        )
        self.assertIn("reply", reply)
        self.assertIn("Alice", reply["reply"])

if __name__ == "__main__":
    unittest.main()
