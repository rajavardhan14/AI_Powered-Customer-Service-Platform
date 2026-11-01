/**
 * API Client for AI Customer Service Platform
 */

const API_BASE = "";

const api = {
  // Ticket endpoints
  async getTickets(filters = {}) {
    const params = new URLSearchParams();
    if (filters.category && filters.category !== "All") params.append("category", filters.category);
    if (filters.priority && filters.priority !== "All") params.append("priority", filters.priority);
    if (filters.status && filters.status !== "All") params.append("status", filters.status);
    if (filters.sentiment && filters.sentiment !== "All") params.append("sentiment", filters.sentiment);
    if (filters.search) params.append("search", filters.search);

    const res = await fetch(`${API_BASE}/api/tickets?${params.toString()}`);
    if (!res.ok) throw new Error("Failed to load tickets");
    return await res.json();
  },

  async getTicket(id) {
    const res = await fetch(`${API_BASE}/api/tickets/${id}`);
    if (!res.ok) throw new Error(`Ticket ${id} not found`);
    return await res.json();
  },

  async createTicket(payload) {
    const res = await fetch(`${API_BASE}/api/tickets`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Failed to create ticket");
    return await res.json();
  },

  async updateTicket(id, payload) {
    const res = await fetch(`${API_BASE}/api/tickets/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Failed to update ticket");
    return await res.json();
  },

  async deleteTicket(id) {
    const res = await fetch(`${API_BASE}/api/tickets/${id}`, {
      method: "DELETE"
    });
    if (!res.ok) throw new Error("Failed to delete ticket");
    return await res.json();
  },

  // Conversation Replies
  async getReplies(ticketId) {
    const res = await fetch(`${API_BASE}/api/tickets/${ticketId}/replies`);
    if (!res.ok) throw new Error("Failed to load replies");
    return await res.json();
  },

  async addReply(ticketId, payload) {
    const res = await fetch(`${API_BASE}/api/tickets/${ticketId}/replies`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Failed to add reply");
    return await res.json();
  },

  // Machine Learning
  async predictML(text, category = null) {
    const res = await fetch(`${API_BASE}/api/ml/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, category })
    });
    if (!res.ok) throw new Error("ML prediction failed");
    return await res.json();
  },

  // Generative AI
  async summarizeTicket(payload) {
    const res = await fetch(`${API_BASE}/api/genai/summarize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Summarization failed");
    return await res.json();
  },

  async generateReply(payload) {
    const res = await fetch(`${API_BASE}/api/genai/generate-reply`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("AI Reply generation failed");
    return await res.json();
  },

  // Analytics & Power BI
  async getAnalytics() {
    const res = await fetch(`${API_BASE}/api/analytics/dashboard`);
    if (!res.ok) throw new Error("Failed to fetch analytics");
    return await res.json();
  },

  async seedData() {
    const res = await fetch(`${API_BASE}/api/seed`, {
      method: "POST"
    });
    return await res.json();
  }
};
