"""
SQL Database Management Layer.
Supports SQLite out-of-the-box with standard parameterized SQL, thread safety,
and automatic table creation and migrations.
"""

import os
import sqlite3
import datetime
from typing import List, Dict, Any, Optional

DB_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.getenv("SQLITE_DB_PATH", os.path.join(DB_DIR, "tickets.db"))

def get_connection() -> sqlite3.Connection:
    """Return a thread-safe sqlite3 connection with dict-like row factory."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables and indexes."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_code TEXT UNIQUE NOT NULL,
        customer_name TEXT NOT NULL,
        customer_email TEXT NOT NULL,
        subject TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        predicted_category TEXT NOT NULL,
        category_confidence REAL DEFAULT 0.0,
        sentiment_label TEXT NOT NULL,
        sentiment_score REAL DEFAULT 0.0,
        priority TEXT NOT NULL,
        predicted_priority TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Open',
        assigned_agent TEXT DEFAULT 'Unassigned',
        ai_summary TEXT DEFAULT '',
        resolution_notes TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ticket_replies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER NOT NULL,
        sender_type TEXT NOT NULL,
        sender_name TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
    )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_category ON tickets(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at)")

    conn.commit()
    conn.close()

# --- CRUD Operations ---

def create_ticket(
    customer_name: str,
    customer_email: str,
    subject: str,
    description: str,
    category: str,
    predicted_category: str,
    category_confidence: float,
    sentiment_label: str,
    sentiment_score: float,
    priority: str,
    predicted_priority: str,
    status: str = "Open",
    assigned_agent: str = "Unassigned",
    ai_summary: str = "",
    created_at: Optional[str] = None
) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.datetime.now().isoformat()
    created_time = created_at or now

    # Generate next ticket code
    cursor.execute("SELECT MAX(id) FROM tickets")
    max_id = cursor.fetchone()[0] or 1000
    ticket_code = f"TCK-{max_id + 1}"

    cursor.execute("""
    INSERT INTO tickets (
        ticket_code, customer_name, customer_email, subject, description,
        category, predicted_category, category_confidence,
        sentiment_label, sentiment_score, priority, predicted_priority,
        status, assigned_agent, ai_summary, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ticket_code, customer_name, customer_email, subject, description,
        category, predicted_category, category_confidence,
        sentiment_label, sentiment_score, priority, predicted_priority,
        status, assigned_agent, ai_summary, created_time, now
    ))

    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return get_ticket_by_id(ticket_id)

def get_ticket_by_id(ticket_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_tickets(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    sentiment: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM tickets WHERE 1=1"
    params = []

    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
    if priority and priority != "All":
        query += " AND priority = ?"
        params.append(priority)
    if status and status != "All":
        query += " AND status = ?"
        params.append(status)
    if sentiment and sentiment != "All":
        query += " AND sentiment_label = ?"
        params.append(sentiment)
    if search and search.strip():
        query += " AND (subject LIKE ? OR description LIKE ? OR customer_name LIKE ? OR ticket_code LIKE ?)"
        term = f"%{search.strip()}%"
        params.extend([term, term, term, term])

    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_ticket(
    ticket_id: int,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    assigned_agent: Optional[str] = None,
    ai_summary: Optional[str] = None,
    resolution_notes: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()

    updates = []
    params = []

    if status is not None:
        updates.append("status = ?")
        params.append(status)
    if priority is not None:
        updates.append("priority = ?")
        params.append(priority)
    if category is not None:
        updates.append("category = ?")
        params.append(category)
    if assigned_agent is not None:
        updates.append("assigned_agent = ?")
        params.append(assigned_agent)
    if ai_summary is not None:
        updates.append("ai_summary = ?")
        params.append(ai_summary)
    if resolution_notes is not None:
        updates.append("resolution_notes = ?")
        params.append(resolution_notes)

    if not updates:
        conn.close()
        return get_ticket_by_id(ticket_id)

    updates.append("updated_at = ?")
    params.append(datetime.datetime.now().isoformat())
    params.append(ticket_id)

    query = f"UPDATE tickets SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, params)
    conn.commit()
    conn.close()
    return get_ticket_by_id(ticket_id)

def delete_ticket(ticket_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ticket_replies WHERE ticket_id = ?", (ticket_id,))
    cursor.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

def add_reply(
    ticket_id: int,
    sender_type: str,
    sender_name: str,
    message: str
) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now().isoformat()

    cursor.execute("""
    INSERT INTO ticket_replies (ticket_id, sender_type, sender_name, message, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (ticket_id, sender_type, sender_name, message, now))

    reply_id = cursor.lastrowid
    conn.commit()

    # If agent replied, update status to 'In Progress' if currently 'Open'
    cursor.execute("SELECT status FROM tickets WHERE id = ?", (ticket_id,))
    row = cursor.fetchone()
    if row and row["status"] == "Open" and sender_type in ["Agent", "AI Assistant"]:
        cursor.execute("UPDATE tickets SET status = 'In Progress', updated_at = ? WHERE id = ?", (now, ticket_id))
        conn.commit()

    conn.close()
    return {
        "id": reply_id,
        "ticket_id": ticket_id,
        "sender_type": sender_type,
        "sender_name": sender_name,
        "message": message,
        "created_at": now
    }

def get_replies(ticket_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ticket_replies WHERE ticket_id = ? ORDER BY id ASC", (ticket_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_analytics_metrics() -> Dict[str, Any]:
    """Calculate real-time business analytics and Power BI KPI aggregations."""
    conn = get_connection()
    cursor = conn.cursor()

    # Total and status counts
    cursor.execute("SELECT COUNT(*) FROM tickets")
    total_tickets = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'Open'")
    open_tickets = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'In Progress'")
    in_progress = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'Resolved' OR status = 'Closed'")
    resolved_tickets = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM tickets WHERE priority = 'Urgent'")
    urgent_tickets = cursor.fetchone()[0] or 0

    # Category distribution
    cursor.execute("SELECT category, COUNT(*) as count FROM tickets GROUP BY category")
    category_counts = {r["category"]: r["count"] for r in cursor.fetchall()}

    # Sentiment distribution
    cursor.execute("SELECT sentiment_label, COUNT(*) as count FROM tickets GROUP BY sentiment_label")
    sentiment_counts = {r["sentiment_label"]: r["count"] for r in cursor.fetchall()}

    # Priority distribution
    cursor.execute("SELECT priority, COUNT(*) as count FROM tickets GROUP BY priority")
    priority_counts = {r["priority"]: r["count"] for r in cursor.fetchall()}

    # Average sentiment compound score
    cursor.execute("SELECT AVG(sentiment_score) FROM tickets")
    avg_sentiment = cursor.fetchone()[0] or 0.0

    # Agent performance leaderboard
    cursor.execute("""
    SELECT assigned_agent,
           COUNT(*) as total_assigned,
           SUM(CASE WHEN status IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) as resolved
    FROM tickets
    WHERE assigned_agent != 'Unassigned'
    GROUP BY assigned_agent
    ORDER BY total_assigned DESC
    """)
    agent_stats = [dict(r) for r in cursor.fetchall()]

    # Priority by Category breakdown
    cursor.execute("""
    SELECT category, priority, COUNT(*) as count
    FROM tickets
    GROUP BY category, priority
    """)
    priority_by_category = [dict(r) for r in cursor.fetchall()]

    conn.close()

    resolution_rate = round((resolved_tickets / total_tickets * 100) if total_tickets > 0 else 0, 1)

    return {
        "kpis": {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "in_progress": in_progress,
            "resolved_tickets": resolved_tickets,
            "urgent_tickets": urgent_tickets,
            "resolution_rate_percent": resolution_rate,
            "average_sentiment_score": round(avg_sentiment, 3),
            "customer_satisfaction_index": round(max(0.0, min(100.0, (avg_sentiment + 1.0) * 50)), 1)
        },
        "category_distribution": category_counts,
        "sentiment_distribution": sentiment_counts,
        "priority_distribution": priority_counts,
        "agent_performance": agent_stats,
        "priority_by_category": priority_by_category
    }

def seed_sample_tickets():
    """Populate database with rich realistic customer tickets."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tickets")
    count = cursor.fetchone()[0]
    conn.close()

    if count > 0:
        return {"status": "Database already seeded", "count": count}

    samples = [
        {
            "name": "Sarah Jenkins", "email": "sarah.j@enterprise.com",
            "subject": "CRITICAL: Database connection timed out on production cluster",
            "desc": "Our users are seeing HTTP 500 error messages when querying production data. All database connections timeout after 30 seconds. This is blocking our end of month accounting closure!",
            "cat": "Technical Issue", "pred_cat": "Technical Issue", "conf": 0.98,
            "sentiment": "Negative", "score": -0.68, "priority": "Urgent", "pred_prio": "Urgent",
            "status": "In Progress", "agent": "Alex Morgan",
            "summary": "• Core Issue: Production database connection timeout causing 500 errors.\n• Customer Impact: Blocks end-of-month financial closure.\n• Recommended Action: Escalate to Level 3 DevOps to analyze query connection pool.",
            "replies": [
                ("Customer", "Sarah Jenkins", "All our reporting dashboards are failing right now!"),
                ("Agent", "Alex Morgan", "Hi Sarah, our DevOps team has identified a stalled worker node and is restarting the connection pool now.")
            ]
        },
        {
            "name": "Michael Chang", "email": "m.chang@fintech.io",
            "subject": "Double charged on monthly corporate billing invoice",
            "desc": "I noticed two charges of $499.00 on our corporate Visa statement for invoice #INV-8821. Please verify our account ledger and issue a refund for the duplicate transaction immediately.",
            "cat": "Billing & Payment", "pred_cat": "Billing & Payment", "conf": 0.96,
            "sentiment": "Negative", "score": -0.42, "priority": "Urgent", "pred_prio": "Urgent",
            "status": "Open", "agent": "Elena Rostova",
            "summary": "• Core Issue: Duplicate $499 charge on invoice #INV-8821.\n• Customer Impact: Unauthorized charge on corporate card.\n• Recommended Action: Review Stripe gateway ledger and refund redundant authorization.",
            "replies": []
        },
        {
            "name": "David Ross", "email": "dross@acmecorp.net",
            "subject": "Need assistance enabling Okta Single Sign-On (SSO) for 150 users",
            "desc": "Our security department requires us to enforce SAML 2.0 SSO via Okta across our organization. Where can we input the metadata XML and certificate fingerprints?",
            "cat": "Account Management", "pred_cat": "Account Management", "conf": 0.94,
            "sentiment": "Neutral", "score": 0.12, "priority": "Medium", "pred_prio": "Medium",
            "status": "In Progress", "agent": "Marcus Vance",
            "summary": "• Core Issue: Assistance needed for SAML 2.0 Okta SSO configuration.\n• Customer Impact: Security requirement for 150 team members.\n• Recommended Action: Supply SSO documentation guide and configure Identity Provider credentials.",
            "replies": [
                ("Agent", "Marcus Vance", "Hello David, I have activated the Enterprise SSO provisioning module for your workspace.")
            ]
        },
        {
            "name": "Emily Watson", "email": "emily.w@designcraft.co",
            "subject": "Feature Request: Export Analytics reports to Microsoft Power BI and CSV",
            "desc": "We love the analytics dashboards! It would be fantastic if we could schedule automated CSV exports or connect via Power BI REST endpoints for weekly executive presentations.",
            "cat": "Product Feature Request", "pred_cat": "Product Feature Request", "conf": 0.92,
            "sentiment": "Positive", "score": 0.74, "priority": "Low", "pred_prio": "Low",
            "status": "Open", "agent": "Unassigned",
            "summary": "• Core Issue: Request for scheduled CSV export and Power BI direct API integration.\n• Customer Impact: Enhances executive reporting workflows.\n• Recommended Action: Add to product engineering backlog and share current Power BI guide.",
            "replies": []
        },
        {
            "name": "Robert Miller", "email": "rmiller@globaltrade.org",
            "subject": "Cancel subscription and request refund per 30-day money back guarantee",
            "desc": "The platform unfortunately lacks the ERP connectors our logistics team requires. We purchased the annual subscription 12 days ago. Please process our cancellation and refund.",
            "cat": "Cancellation & Refund", "pred_cat": "Cancellation & Refund", "conf": 0.95,
            "sentiment": "Negative", "score": -0.28, "priority": "High", "pred_prio": "High",
            "status": "Resolved", "agent": "Elena Rostova",
            "summary": "• Core Issue: Cancellation and refund request within 30-day guarantee period.\n• Customer Impact: Unmet ERP requirements.\n• Recommended Action: Process refund via payment processor and confirm account closure.",
            "replies": [
                ("Agent", "Elena Rostova", "Dear Robert, your cancellation has been processed and a full refund of $1,200 has been credited to your card.")
            ]
        },
        {
            "name": "Priya Sharma", "email": "priya.sharma@cloudtech.in",
            "subject": "What are your data privacy and GDPR compliance standards?",
            "desc": "Hello support team, we are evaluating your platform for our European clients. Could you provide your SOC2 Type II compliance report, Data Processing Agreement (DPA), and GDPR certifications?",
            "cat": "General Inquiry", "pred_cat": "General Inquiry", "conf": 0.89,
            "sentiment": "Positive", "score": 0.51, "priority": "Medium", "pred_prio": "Medium",
            "status": "Resolved", "agent": "Alex Morgan",
            "summary": "• Core Issue: Inquiry regarding GDPR, DPA, and SOC2 compliance documentation.\n• Customer Impact: Procurement prerequisite for EU client onboarding.\n• Recommended Action: Dispatch security compliance packet and DPA template.",
            "replies": [
                ("Agent", "Alex Morgan", "Hi Priya, I have attached our latest SOC2 Type II compliance audit and standard DPA.")
            ]
        },
        {
            "name": "Liam O'Connor", "email": "liam@fintech.ie",
            "subject": "Mobile app crashing repeatedly on login screen after iOS 17 update",
            "desc": "Several of our field reps reported that the mobile app crashes immediately when tapping the Biometric FaceID login button. Reinstalling the app did not resolve it.",
            "cat": "Technical Issue", "pred_cat": "Technical Issue", "conf": 0.97,
            "sentiment": "Negative", "score": -0.55, "priority": "High", "pred_prio": "High",
            "status": "In Progress", "agent": "Alex Morgan",
            "summary": "• Core Issue: iOS 17 FaceID crash on mobile login.\n• Customer Impact: Field representatives locked out of mobile app.\n• Recommended Action: Inspect crash stack traces on iOS 17 and issue hotfix build.",
            "replies": []
        },
        {
            "name": "Jessica Taylor", "email": "jessica.t@retailhub.com",
            "subject": "Inquiry regarding Enterprise volume discount and SLA guarantees",
            "desc": "We are looking to expand from 20 to 180 support agent seats next quarter. Could an account executive reach out to discuss custom pricing and our 99.99% uptime SLA requirement?",
            "cat": "General Inquiry", "pred_cat": "General Inquiry", "conf": 0.91,
            "sentiment": "Positive", "score": 0.62, "priority": "Medium", "pred_prio": "Medium",
            "status": "Open", "agent": "Marcus Vance",
            "summary": "• Core Issue: Enterprise expansion inquiry for 180 seats and custom SLA.\n• Customer Impact: High-value commercial sales opportunity.\n• Recommended Action: Schedule introductory call between account executive and customer.",
            "replies": []
        }
    ]

    base_date = datetime.datetime.now() - datetime.timedelta(days=7)
    created_count = 0

    for i, s in enumerate(samples):
        dt = (base_date + datetime.timedelta(hours=i * 18)).isoformat()
        t = create_ticket(
            customer_name=s["name"],
            customer_email=s["email"],
            subject=s["subject"],
            description=s["desc"],
            category=s["cat"],
            predicted_category=s["pred_cat"],
            category_confidence=s["conf"],
            sentiment_label=s["sentiment"],
            sentiment_score=s["score"],
            priority=s["priority"],
            predicted_priority=s["pred_prio"],
            status=s["status"],
            assigned_agent=s["agent"],
            ai_summary=s["summary"],
            created_at=dt
        )
        # Add replies
        for r in s.get("replies", []):
            add_reply(t["id"], r[0], r[1], r[2])
        created_count += 1

    return {"status": "Seeded successfully", "count": created_count}
