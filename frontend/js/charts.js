/**
 * Chart rendering module for Business Analytics Dashboard
 */

let categoryChartInstance = null;
let sentimentChartInstance = null;
let priorityChartInstance = null;
let agentChartInstance = null;

const chartColors = {
  blue: "#3b82f6",
  emerald: "#10b981",
  amber: "#f59e0b",
  red: "#ef4444",
  purple: "#8b5cf6",
  cyan: "#06b6d4",
  slate: "#64748b"
};

function renderAnalyticsCharts(data) {
  renderCategoryChart(data.category_distribution || {});
  renderSentimentChart(data.sentiment_distribution || {});
  renderPriorityChart(data.priority_distribution || {});
  renderAgentChart(data.agent_performance || []);
}

function renderCategoryChart(catData) {
  const ctx = document.getElementById("categoryChart");
  if (!ctx) return;

  const labels = Object.keys(catData);
  const values = Object.values(catData);

  if (categoryChartInstance) categoryChartInstance.destroy();

  categoryChartInstance = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: [
          "#3b82f6", "#10b981", "#8b5cf6", "#f59e0b", "#ec4899", "#06b6d4"
        ],
        borderWidth: 1,
        borderColor: "#1e293b"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "right",
          labels: { color: "#94a3b8", font: { size: 11 } }
        }
      },
      cutout: "68%"
    }
  });
}

function renderSentimentChart(sentimentData) {
  const ctx = document.getElementById("sentimentChart");
  if (!ctx) return;

  const labels = ["Positive", "Neutral", "Negative"];
  const values = [
    sentimentData["Positive"] || 0,
    sentimentData["Neutral"] || 0,
    sentimentData["Negative"] || 0
  ];

  if (sentimentChartInstance) sentimentChartInstance.destroy();

  sentimentChartInstance = new Chart(ctx, {
    type: "pie",
    data: {
      labels: ["😊 Positive", "😐 Neutral", "😡 Negative"],
      datasets: [{
        data: values,
        backgroundColor: ["#10b981", "#94a3b8", "#ef4444"],
        borderWidth: 1,
        borderColor: "#1e293b"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: "#94a3b8", font: { size: 12 } }
        }
      }
    }
  });
}

function renderPriorityChart(priorityData) {
  const ctx = document.getElementById("priorityChart");
  if (!ctx) return;

  const labels = ["Urgent", "High", "Medium", "Low"];
  const values = [
    priorityData["Urgent"] || 0,
    priorityData["High"] || 0,
    priorityData["Medium"] || 0,
    priorityData["Low"] || 0
  ];

  if (priorityChartInstance) priorityChartInstance.destroy();

  priorityChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Tickets",
        data: values,
        backgroundColor: ["#ef4444", "#f59e0b", "#3b82f6", "#64748b"],
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          ticks: { color: "#94a3b8" },
          grid: { display: false }
        },
        y: {
          ticks: { color: "#94a3b8", stepSize: 1 },
          grid: { color: "rgba(51, 65, 85, 0.5)" }
        }
      }
    }
  });
}

function renderAgentChart(agentStats) {
  const ctx = document.getElementById("agentChart");
  if (!ctx) return;

  const labels = agentStats.map(a => a.assigned_agent);
  const totalAssigned = agentStats.map(a => a.total_assigned);
  const totalResolved = agentStats.map(a => a.resolved);

  if (agentChartInstance) agentChartInstance.destroy();

  agentChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels.length ? labels : ["No Agents Assigned"],
      datasets: [
        {
          label: "Total Assigned",
          data: totalAssigned.length ? totalAssigned : [0],
          backgroundColor: "#3b82f6",
          borderRadius: 4
        },
        {
          label: "Resolved",
          data: totalResolved.length ? totalResolved : [0],
          backgroundColor: "#10b981",
          borderRadius: 4
        }
      ]
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "top",
          labels: { color: "#94a3b8" }
        }
      },
      scales: {
        x: {
          ticks: { color: "#94a3b8", stepSize: 1 },
          grid: { color: "rgba(51, 65, 85, 0.5)" }
        },
        y: {
          ticks: { color: "#94a3b8" },
          grid: { display: false }
        }
      }
    }
  });
}
