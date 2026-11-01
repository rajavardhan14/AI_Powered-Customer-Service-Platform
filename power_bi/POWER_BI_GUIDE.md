# Microsoft Power BI Integration Guide
## AI-Powered Customer Service and Business Analytics Platform

This guide explains how to connect **Microsoft Power BI Desktop & Power BI Service** to the platform to build executive customer support dashboards and business analytics reports.

---

## 1. Connecting Power BI to the Platform

You have two methods for ingesting ticket data into Power BI:

### Method A: Live REST Web API (Recommended for Auto-Refresh)
This method connects directly to your live FastAPI backend and refreshes automatically as new customer tickets arrive.

1. Open **Power BI Desktop**.
2. Click **Home** ➔ **Get Data** ➔ **Web**.
3. Select **Basic** and enter the URL:
   ```text
   http://localhost:8000/api/export/powerbi-json
   ```
   *(For Azure deployment, replace `localhost:8000` with your Azure App Service or Container App URL)*.
4. Click **OK**.
5. When the Power Query Editor opens:
   - Click on `Record` next to `data`.
   - Click **Into Table** in the top ribbon.
   - Click the **Expand Columns** icon (top-right of the column header) and select all fields:
     - `id`, `ticket_code`, `customer_name`, `customer_email`, `subject`, `category`, `predicted_category`, `category_confidence`, `sentiment_label`, `sentiment_score`, `priority`, `predicted_priority`, `status`, `assigned_agent`, `created_at`, `updated_at`.
   - Click **Close & Apply**.

### Method B: Power Query (M-Language) Script
Open **Power Query Editor** ➔ **New Source** ➔ **Blank Query** ➔ Click **Advanced Editor**, and paste:

```powerquery
let
    Source = Json.Document(Web.Contents("http://localhost:8000/api/export/powerbi-json")),
    DataList = Source[data],
    TableData = Table.FromList(DataList, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    Expanded = Table.ExpandRecordColumn(
        TableData,
        "Column1",
        {
            "id", "ticket_code", "customer_name", "customer_email", "subject",
            "category", "predicted_category", "category_confidence",
            "sentiment_label", "sentiment_score", "priority", "predicted_priority",
            "status", "assigned_agent", "created_at", "updated_at"
        }
    ),
    ChangedTypes = Table.TransformColumnTypes(Expanded, {
        {"id", Int64.Type},
        {"category_confidence", type number},
        {"sentiment_score", type number},
        {"created_at", type datetime},
        {"updated_at", type datetime}
    })
in
    ChangedTypes
```

### Method C: Offline CSV Ingestion
For offline demo or testing:
1. In Power BI Desktop, click **Get Data ➔ Text/CSV**.
2. Select `power_bi/sample_tickets_powerbi.csv` or download live via:
   `http://localhost:8000/api/export/csv`

---

## 2. Key DAX Measures for Business Analytics

Add these DAX measures to your `Tickets` table to calculate KPIs:

### 1. Total Tickets
```dax
Total Tickets = COUNTROWS('Tickets')
```

### 2. Resolution Rate %
```dax
Resolution Rate % =
DIVIDE(
    CALCULATE(COUNTROWS('Tickets'), 'Tickets'[status] IN {"Resolved", "Closed"}),
    COUNTROWS('Tickets'),
    0
) * 100
```

### 3. Urgent Tickets Backlog
```dax
Urgent Tickets Backlog =
CALCULATE(
    COUNTROWS('Tickets'),
    'Tickets'[priority] = "Urgent",
    'Tickets'[status] <> "Resolved"
)
```

### 4. Negative Sentiment Rate % (Customer Frustration Index)
```dax
Negative Sentiment Rate % =
DIVIDE(
    CALCULATE(COUNTROWS('Tickets'), 'Tickets'[sentiment_label] = "Negative"),
    COUNTROWS('Tickets'),
    0
) * 100
```

### 5. Average Sentiment Compound Score
```dax
Average Sentiment Score = AVERAGE('Tickets'[sentiment_score])
```

### 6. Customer Satisfaction Health Index (0-100)
```dax
CSAT Health Index = ([Average Sentiment Score] + 1) * 50
```

---

## 3. Recommended Power BI Dashboard Layout

| Visual Type | Fields | Business Insight |
| :--- | :--- | :--- |
| **Card (KPI)** | `[Total Tickets]`, `[Resolution Rate %]`, `[Urgent Tickets Backlog]`, `[CSAT Health Index]` | High-level executive pulse check |
| **Donut Chart** | Legend: `sentiment_label`, Values: `[Total Tickets]` | Customer sentiment breakdown (Positive vs Negative vs Neutral) |
| **Clustered Bar Chart** | Y-Axis: `category`, X-Axis: `[Total Tickets]`, Legend: `priority` | Identifies ticket volume and high-urgency concentrations by department |
| **Stacked Bar Chart** | Y-Axis: `assigned_agent`, X-Axis: `[Total Tickets]`, Legend: `status` | Support agent workload distribution & resolution capability |
| **Line Chart** | X-Axis: `created_at` (Date), Y-Axis: `[Total Tickets]` | Daily / weekly customer ticket inflow trends |
| **Table Visual** | `ticket_code`, `customer_name`, `category`, `sentiment_label`, `priority`, `status` | Detailed operational drill-down for team leads |

---

## 4. Power BI Service Scheduled Refresh
To set up automated scheduled refresh on Power BI Service (Cloud):
1. Publish your report to Power BI Service (**File ➔ Publish ➔ Publish to Power BI**).
2. Go to your Workspace ➔ Dataset settings.
3. If deployed on Azure, select **Anonymous** or **OAuth2** authentication for the REST endpoint.
4. Set **Scheduled refresh** to daily or hourly intervals.
