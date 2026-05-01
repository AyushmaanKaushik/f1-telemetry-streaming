# Dashboard Deployment Quickstart

Step-by-step guide to deploying the F1 Telemetry AI/BI Dashboard on Databricks Free Edition using the CLI.

---

## Prerequisites

1. ✅ Databricks CLI installed and authenticated (`databricks configure --token`)
2. ✅ All 4 Gold tables populated (run the **Dashboard Readiness Validation** cell in `gold_aggregations.py`)
3. ✅ Python 3.11+ available locally (for `deploy_dashboard.py`)

Verify your CLI is working:
```powershell
databricks lakeview --help
```

---

## Step 1 — Deploy the Dashboard (First Time)

From the repo root:
```powershell
cd src\databricks\dashboards
python deploy_dashboard.py create
```

Expected output:
```
Running: databricks lakeview create --json @<tmpfile> --output json

✅ Dashboard created successfully!
   dashboard_id : 01efd...abc123
   display_name : F1 Telemetry Dashboard

Next steps:
  Update widgets : python deploy_dashboard.py update 01efd...abc123
  Publish        : python deploy_dashboard.py publish 01efd...abc123
```

> **Important**: Copy the `dashboard_id` from the output. You will need it for all subsequent update and publish commands.

**Record your dashboard_id here** (fill in after running create):
```
dashboard_id = <YOUR_DASHBOARD_ID>
```

---

## Step 2 — Verify the Dashboard in Databricks UI

1. Open your Databricks workspace: `https://community.cloud.databricks.com`
2. Go to **Dashboards** in the left sidebar
3. Find **F1 Telemetry Dashboard** — it will be in Draft state
4. Open it and confirm the **Driver Position Gaps** bar chart is rendering

At this point only Widget 1 (Driver Gaps) is present. Widgets 2–4 are added in Phases 4–6.

---

## Step 3 — Update After Adding Widgets

After each phase of implementation adds new widgets to `f1_dashboard_spec.json`:
```powershell
cd src\databricks\dashboards
python deploy_dashboard.py update <YOUR_DASHBOARD_ID>
```

Run this after:
- Phase 4 adds the Vehicle Health table (Widget 2)
- Phase 5 adds the Tyre Degradation line chart (Widget 3)
- Phase 6 adds the Player Speed KPI tile (Widget 4)

---

## Step 4 — Publish the Dashboard

Once all widgets are complete and verified:
```powershell
cd src\databricks\dashboards
python deploy_dashboard.py publish <YOUR_DASHBOARD_ID>
```

This makes the dashboard accessible via a shareable URL. The URL will be printed on success.

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `Error: dashboard_id not found` | The `create` response schema changed | Run `databricks lakeview get <id>` to verify |
| `403 Forbidden` on publish | Free Edition may restrict external sharing | Share the draft URL instead |
| `dataset not found` in widget | SQL query references wrong table name | Verify `f1_catalog.gold.<table>` exists in Databricks SQL Editor |
| `serialized_dashboard parse error` | Corrupted spec JSON | Run `python -c "import json; json.load(open('f1_dashboard_spec.json'))"` to validate |
