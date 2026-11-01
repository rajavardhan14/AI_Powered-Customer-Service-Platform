/**
 * Main Application Logic for AI Customer Service Platform
 */

let currentSelectedTicket = null;

document.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  initFilterListeners();
  initModalListeners();
  initPlayground();
  initWorkbenchListeners();
  loadDashboard();
  loadTickets();
});

// Tab Navigation
function initNavigation() {
  document.querySelectorAll(".nav-item").forEach(item => {
    item.addEventListener("click", () => {
      const targetTab = item.getAttribute("data-tab");
      switchTab(targetTab);
    });
  });
}

function switchTab(tabId) {
  document.querySelectorAll(".nav-item").forEach(i => i.classList.remove("active"));
  document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

  const navEl = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
  const contentEl = document.getElementById(tabId);

  if (navEl) navEl.classList.add("active");
  if (contentEl) contentEl.classList.add("active");

  const titleMap = {
    dashboard: "Business Analytics & Executive KPIs",
    tickets: "Customer Ticket Management Queue",
    workbench: "Agent AI Copilot & Workbench",
    playground: "Real-Time Machine Learning Triage Playground",
    powerbi: "Microsoft Power BI Integration & Reporting"
  };
  const titleEl = document.getElementById("pageTitle");
  if (titleEl) titleEl.textContent = titleMap[tabId] || "Customer Support Platform";

  if (tabId === "dashboard") loadDashboard();
  if (tabId === "tickets") loadTickets();
}

// Load Dashboard KPIs & Charts
async function loadDashboard() {
  try {
    const data = await api.getAnalytics();
    const k = data.kpis || {};

    document.getElementById("kpiTotal").textContent = k.total_tickets || 0;
    document.getElementById("kpiOpen").textContent = (k.open_tickets || 0) + (k.in_progress || 0);
    document.getElementById("kpiResolved").textContent = `${k.resolution_rate_percent || 0}%`;
    document.getElementById("kpiUrgent").textContent = k.urgent_tickets || 0;
    document.getElementById("kpiCsat").textContent = `${k.customer_satisfaction_index || 0}%`;

    renderAnalyticsCharts(data);
  } catch (err) {
    console.error("Dashboard error:", err);
  }
}

// Load Tickets Table
async function loadTickets() {
  const filters = {
    category: document.getElementById("filterCategory").value,
    priority: document.getElementById("filterPriority").value,
    status: document.getElementById("filterStatus").value,
    sentiment: document.getElementById("filterSentiment").value,
    search: document.getElementById("ticketSearch").value
  };

  try {
    const tickets = await api.getTickets(filters);
    renderTicketsTable(tickets);
  } catch (err) {
    console.error("Tickets error:", err);
  }
}

function renderTicketsTable(tickets) {
  const tbody = document.getElementById("ticketsTableBody");
  if (!tbody) return;

  if (!tickets || tickets.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:32px; color:var(--text-muted);">No tickets match the current filters.</td></tr>`;
    return;
  }

  tbody.innerHTML = tickets.map(t => {
    const prioClass = `badge-${t.priority.toLowerCase()}`;
    const sentClass = `badge-${t.sentiment_label.toLowerCase()}`;
    const sentEmoji = t.sentiment_label === "Positive" ? "😊" : (t.sentiment_label === "Negative" ? "😡" : "😐");
    const statusClass = `badge-${t.status.toLowerCase().replace(" ", "-")}`;

    return `
      <tr>
        <td><strong>${t.ticket_code}</strong></td>
        <td>
          <div style="font-weight:600;">${escapeHtml(t.customer_name)}</div>
          <div style="font-size:11px; color:var(--text-muted);">${escapeHtml(t.customer_email)}</div>
        </td>
        <td style="max-width:240px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
          ${escapeHtml(t.subject)}
        </td>
        <td><span class="badge" style="background:#334155;">${escapeHtml(t.category)}</span></td>
        <td><span class="badge ${sentClass}">${sentEmoji} ${t.sentiment_label} (${t.sentiment_score > 0 ? "+" : ""}${t.sentiment_score})</span></td>
        <td><span class="badge ${prioClass}">${t.priority}</span></td>
        <td><span class="badge ${statusClass}">${t.status}</span></td>
        <td>
          <button class="btn btn-primary btn-sm" onclick="openTicketWorkbench(${t.id})">
            AI Copilot
          </button>
        </td>
      </tr>
    `;
  }).join("");
}

function initFilterListeners() {
  ["filterCategory", "filterPriority", "filterStatus", "filterSentiment"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("change", loadTickets);
  });

  const searchEl = document.getElementById("ticketSearch");
  if (searchEl) {
    let timeout;
    searchEl.addEventListener("input", () => {
      clearTimeout(timeout);
      timeout = setTimeout(loadTickets, 300);
    });
  }
}

// Open Ticket into AI Workbench
async function openTicketWorkbench(ticketId) {
  try {
    const ticket = await api.getTicket(ticketId);
    currentSelectedTicket = ticket;

    // Switch to workbench tab
    switchTab("workbench");

    // Populate ticket info
    document.getElementById("wbTicketCode").textContent = ticket.ticket_code;
    document.getElementById("wbSubject").textContent = ticket.subject;
    document.getElementById("wbCustomer").textContent = `${ticket.customer_name} (${ticket.customer_email})`;
    document.getElementById("wbStatus").textContent = ticket.status;
    document.getElementById("wbStatus").className = `badge badge-${ticket.status.toLowerCase().replace(" ", "-")}`;
    document.getElementById("wbCategory").textContent = ticket.category;
    document.getElementById("wbAgent").textContent = ticket.assigned_agent;

    // ML Card
    document.getElementById("mlPredCategory").textContent = ticket.predicted_category;
    document.getElementById("mlPredConf").textContent = `${Math.round(ticket.category_confidence * 100)}%`;
    document.getElementById("mlSentiment").textContent = `${ticket.sentiment_label} (${ticket.sentiment_score})`;
    document.getElementById("mlPriority").textContent = ticket.priority;

    // Original Description in Conversation
    const conversationEl = document.getElementById("wbConversation");
    conversationEl.innerHTML = `
      <div class="message-bubble msg-customer">
        <div class="msg-sender">
          <span>👤 ${escapeHtml(ticket.customer_name)} (Customer)</span>
          <span style="font-size:10px; color:var(--text-muted);">${formatDate(ticket.created_at)}</span>
        </div>
        <div>${escapeHtml(ticket.description)}</div>
      </div>
    `;

    // Load Replies
    const replies = await api.getReplies(ticketId);
    replies.forEach(r => {
      const isAgent = r.sender_type === "Agent";
      const isAI = r.sender_type === "AI Assistant";
      const bubbleClass = isAgent ? "msg-agent" : (isAI ? "msg-ai" : "msg-customer");
      const icon = isAgent ? "👔" : (isAI ? "🤖" : "👤");

      const msgDiv = document.createElement("div");
      msgDiv.className = `message-bubble ${bubbleClass}`;
      msgDiv.innerHTML = `
        <div class="msg-sender">
          <span>${icon} ${escapeHtml(r.sender_name)} (${r.sender_type})</span>
          <span style="font-size:10px; color:var(--text-muted);">${formatDate(r.created_at)}</span>
        </div>
        <div>${escapeHtml(r.message)}</div>
      `;
      conversationEl.appendChild(msgDiv);
    });

    conversationEl.scrollTop = conversationEl.scrollHeight;

    // Set existing AI Summary if present
    const summaryBox = document.getElementById("wbAiSummary");
    if (ticket.ai_summary) {
      summaryBox.textContent = ticket.ai_summary;
    } else {
      summaryBox.textContent = "Click 'Generate AI Summary' below to distill this ticket into key problem, customer impact, and action items.";
    }

    document.getElementById("wbGeneratedReply").textContent = "Select desired response tone and click 'Generate Response' to draft a reply.";
  } catch (err) {
    console.error("Open workbench error:", err);
    alert("Could not load ticket details.");
  }
}

// Workbench Listeners
function initWorkbenchListeners() {
  // Generate Summary
  const btnSummary = document.getElementById("btnGenSummary");
  if (btnSummary) {
    btnSummary.addEventListener("click", async () => {
      if (!currentSelectedTicket) return;
      btnSummary.textContent = "Analyzing Ticket...";
      btnSummary.disabled = true;

      try {
        const res = await api.summarizeTicket({
          ticket_id: currentSelectedTicket.id,
          subject: currentSelectedTicket.subject,
          description: currentSelectedTicket.description,
          category: currentSelectedTicket.category,
          sentiment_label: currentSelectedTicket.sentiment_label,
          priority: currentSelectedTicket.priority
        });
        document.getElementById("wbAiSummary").textContent = res.summary;
        currentSelectedTicket.ai_summary = res.summary;
      } catch (err) {
        alert("Summary generation failed.");
      } finally {
        btnSummary.textContent = "⚡ Generate AI Summary";
        btnSummary.disabled = false;
      }
    });
  }

  // Generate Reply
  const btnReply = document.getElementById("btnGenReply");
  if (btnReply) {
    btnReply.addEventListener("click", async () => {
      if (!currentSelectedTicket) return;
      btnReply.textContent = "Drafting with AI...";
      btnReply.disabled = true;

      const tone = document.getElementById("wbToneSelect").value;
      try {
        const res = await api.generateReply({
          ticket_id: currentSelectedTicket.id,
          customer_name: currentSelectedTicket.customer_name,
          subject: currentSelectedTicket.subject,
          description: currentSelectedTicket.description,
          category: currentSelectedTicket.category,
          tone: tone,
          ai_summary: currentSelectedTicket.ai_summary
        });
        document.getElementById("wbGeneratedReply").textContent = res.reply;
      } catch (err) {
        alert("Reply drafting failed.");
      } finally {
        btnReply.textContent = "✨ Draft AI Response";
        btnReply.disabled = false;
      }
    });
  }

  // Insert AI Reply into Composer
  const btnInsert = document.getElementById("btnInsertReply");
  if (btnInsert) {
    btnInsert.addEventListener("click", () => {
      const replyText = document.getElementById("wbGeneratedReply").textContent;
      if (replyText && !replyText.startsWith("Select desired")) {
        document.getElementById("wbReplyInput").value = replyText;
      }
    });
  }

  // Send Reply
  const btnSend = document.getElementById("btnSendReply");
  if (btnSend) {
    btnSend.addEventListener("click", async () => {
      if (!currentSelectedTicket) return;
      const msg = document.getElementById("wbReplyInput").value.trim();
      if (!msg) return;

      try {
        await api.addReply(currentSelectedTicket.id, {
          sender_type: "Agent",
          sender_name: "Support Specialist",
          message: msg
        });
        document.getElementById("wbReplyInput").value = "";
        openTicketWorkbench(currentSelectedTicket.id);
      } catch (err) {
        alert("Failed to send reply");
      }
    });
  }

  // Quick Resolve Ticket
  const btnResolve = document.getElementById("btnResolveTicket");
  if (btnResolve) {
    btnResolve.addEventListener("click", async () => {
      if (!currentSelectedTicket) return;
      try {
        await api.updateTicket(currentSelectedTicket.id, { status: "Resolved" });
        alert(`Ticket ${currentSelectedTicket.ticket_code} marked as Resolved!`);
        openTicketWorkbench(currentSelectedTicket.id);
        loadDashboard();
      } catch (err) {
        alert("Failed to update status");
      }
    });
  }
}

// Real-Time ML Playground
function initPlayground() {
  const btnAnalyze = document.getElementById("btnPlaygroundAnalyze");
  if (btnAnalyze) {
    btnAnalyze.addEventListener("click", async () => {
      const text = document.getElementById("playgroundText").value.trim();
      if (!text) {
        alert("Please enter customer message text to analyze.");
        return;
      }

      btnAnalyze.textContent = "Computing Features...";
      btnAnalyze.disabled = true;

      try {
        const res = await api.predictML(text);
        renderPlaygroundResults(res);
      } catch (err) {
        alert("Prediction error: " + err.message);
      } finally {
        btnAnalyze.textContent = "🚀 Run ML Intelligence Pipeline";
        btnAnalyze.disabled = false;
      }
    });
  }

  // Sample prompt buttons
  document.querySelectorAll(".sample-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.getElementById("playgroundText").value = btn.getAttribute("data-sample");
      document.getElementById("btnPlaygroundAnalyze").click();
    });
  });
}

function renderPlaygroundResults(res) {
  document.getElementById("pgResults").style.display = "block";

  // Category
  document.getElementById("pgCatName").textContent = res.category;
  document.getElementById("pgCatConf").textContent = `${Math.round(res.category_confidence * 100)}% Confidence`;

  const catBarsEl = document.getElementById("pgCatBars");
  catBarsEl.innerHTML = Object.entries(res.category_probabilities).map(([cat, prob]) => `
    <div style="margin-bottom:6px;">
      <div style="display:flex; justify-content:space-between; font-size:11px; margin-bottom:2px;">
        <span>${cat}</span>
        <span>${Math.round(prob * 100)}%</span>
      </div>
      <div style="background:#334155; height:6px; border-radius:3px; overflow:hidden;">
        <div style="background:#3b82f6; width:${Math.round(prob * 100)}%; height:100%;"></div>
      </div>
    </div>
  `).join("");

  // Sentiment
  const emoji = res.sentiment_label === "Positive" ? "😊" : (res.sentiment_label === "Negative" ? "😡" : "😐");
  document.getElementById("pgSentLabel").textContent = `${emoji} ${res.sentiment_label}`;
  document.getElementById("pgSentScore").textContent = `Compound: ${res.sentiment_score}`;

  document.getElementById("pgSentBars").innerHTML = `
    <div style="font-size:11px; display:flex; justify-content:space-between; margin-top:8px;">
      <span style="color:#10b981;">Pos: ${Math.round(res.sentiment_details.pos * 100)}%</span>
      <span style="color:#94a3b8;">Neu: ${Math.round(res.sentiment_details.neu * 100)}%</span>
      <span style="color:#ef4444;">Neg: ${Math.round(res.sentiment_details.neg * 100)}%</span>
    </div>
  `;

  // Priority
  const prioColors = { Urgent: "#ef4444", High: "#f59e0b", Medium: "#3b82f6", Low: "#94a3b8" };
  const prioEl = document.getElementById("pgPrioLabel");
  prioEl.textContent = res.priority;
  prioEl.style.color = prioColors[res.priority] || "#3b82f6";

  document.getElementById("pgUrgencyScore").textContent = `Urgency Meter: ${res.urgency_score}/100`;
  document.getElementById("pgUrgencyBar").style.width = `${res.urgency_score}%`;
  document.getElementById("pgUrgencyBar").style.backgroundColor = res.urgency_score > 60 ? "#ef4444" : (res.urgency_score > 35 ? "#f59e0b" : "#10b981");
}

// Modal Listeners
function initModalListeners() {
  const modal = document.getElementById("newTicketModal");
  const openBtn = document.getElementById("btnOpenNewTicket");
  const closeBtn = document.getElementById("btnCloseModal");
  const cancelBtn = document.getElementById("btnCancelModal");
  const form = document.getElementById("newTicketForm");

  if (openBtn) openBtn.addEventListener("click", () => modal.classList.add("active"));
  if (closeBtn) closeBtn.addEventListener("click", () => modal.classList.remove("active"));
  if (cancelBtn) cancelBtn.addEventListener("click", () => modal.classList.remove("active"));

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = {
        customer_name: document.getElementById("formCustomerName").value.trim(),
        customer_email: document.getElementById("formCustomerEmail").value.trim(),
        subject: document.getElementById("formSubject").value.trim(),
        description: document.getElementById("formDescription").value.trim(),
        category: document.getElementById("formCategory").value || null,
        priority: document.getElementById("formPriority").value || null,
        assigned_agent: document.getElementById("formAgent").value || "Unassigned"
      };

      try {
        const created = await api.createTicket(payload);
        modal.classList.remove("active");
        form.reset();
        alert(`Ticket ${created.ticket_code} created and triaged successfully!`);
        loadDashboard();
        loadTickets();
      } catch (err) {
        alert("Failed to create ticket: " + err.message);
      }
    });
  }

  // Seed Button
  const seedBtn = document.getElementById("btnSeedData");
  if (seedBtn) {
    seedBtn.addEventListener("click", async () => {
      if (confirm("Seed database with realistic customer service tickets?")) {
        const res = await api.seedData();
        alert(res.status);
        loadDashboard();
        loadTickets();
      }
    });
  }
}

// Helpers
function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function formatDate(isoStr) {
  if (!isoStr) return "";
  try {
    const d = new Date(isoStr);
    return d.toLocaleDateString() + " " + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return isoStr;
  }
}

// Copy to Clipboard Utility
function copyText(elemId) {
  const el = document.getElementById(elemId);
  if (!el) return;
  navigator.clipboard.writeText(el.textContent);
  alert("Copied to clipboard!");
}
