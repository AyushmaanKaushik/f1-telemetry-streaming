#!/usr/bin/env python3
"""
F1 Telemetry Dashboard — Deployment Script
===========================================

Reads f1_dashboard_spec.json (the clean, human-readable inner dashboard spec),
wraps it as a properly serialized Databricks Lakeview API request, and deploys
or updates the dashboard using the Databricks CLI.

Usage
-----
# First-time deploy (creates a new dashboard draft):
    python deploy_dashboard.py create

# Update an existing dashboard after adding widgets:
    python deploy_dashboard.py update <dashboard_id>

# Publish the dashboard (makes it accessible via shared URL):
    python deploy_dashboard.py publish <dashboard_id>

Prerequisites
-------------
- Databricks CLI installed and authenticated (`databricks configure --token`)
- f1_dashboard_spec.json in the same directory as this script
"""

import json
import subprocess
import sys
import tempfile
import os
from pathlib import Path

DISPLAY_NAME = "F1 Telemetry Dashboard"
SPEC_FILE    = Path(__file__).parent / "f1_dashboard_spec.json"


def load_spec() -> dict:
    """Load the inner dashboard spec from f1_dashboard_spec.json."""
    if not SPEC_FILE.exists():
        print(f"ERROR: Spec file not found: {SPEC_FILE}")
        sys.exit(1)
    with open(SPEC_FILE, encoding="utf-8") as f:
        return json.load(f)


def build_request(spec: dict) -> dict:
    """
    Wrap the inner spec as a Databricks CreateDashboard request body.
    The API requires `serialized_dashboard` to be a JSON-encoded *string*
    (i.e., the inner JSON object serialised with json.dumps).
    """
    return {
        "display_name":          DISPLAY_NAME,
        "serialized_dashboard":  json.dumps(spec, separators=(",", ":")),
    }


def run_cli(args: list[str]) -> dict:
    """Run a Databricks CLI command and return the parsed JSON output."""
    cmd = ["databricks"] + args + ["--output", "json"]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"ERROR: CLI command failed:\n{result.stderr}")
        sys.exit(result.returncode)
    return json.loads(result.stdout) if result.stdout.strip() else {}


def cmd_create():
    """Create a new draft dashboard and print the dashboard_id."""
    spec    = load_spec()
    request = build_request(spec)

    # Write request to a temp file so we can use --json @file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                    delete=False, encoding="utf-8") as tmp:
        json.dump(request, tmp)
        tmp_path = tmp.name

    try:
        response = run_cli(["lakeview", "create", "--json", f"@{tmp_path}"])
    finally:
        os.unlink(tmp_path)

    dashboard_id = response.get("dashboard_id") or response.get("id", "")
    print(f"\n✅ Dashboard created successfully!")
    print(f"   dashboard_id : {dashboard_id}")
    print(f"   display_name : {DISPLAY_NAME}")
    print(f"\nNext steps:")
    print(f"  Update widgets : python deploy_dashboard.py update {dashboard_id}")
    print(f"  Publish        : python deploy_dashboard.py publish {dashboard_id}")
    return dashboard_id


def cmd_update(dashboard_id: str):
    """Push updated spec to an existing draft dashboard."""
    spec    = load_spec()
    request = build_request(spec)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                    delete=False, encoding="utf-8") as tmp:
        json.dump(request, tmp)
        tmp_path = tmp.name

    try:
        run_cli(["lakeview", "update", dashboard_id, "--json", f"@{tmp_path}"])
    finally:
        os.unlink(tmp_path)

    print(f"\n✅ Dashboard {dashboard_id} updated successfully!")
    print(f"   Publish when ready: python deploy_dashboard.py publish {dashboard_id}")


def cmd_publish(dashboard_id: str):
    """Publish the dashboard to make it accessible via a shareable URL."""
    response = run_cli(["lakeview", "publish", dashboard_id])
    url = (
        response.get("embed_url")
        or response.get("url")
        or f"(open Databricks UI → Dashboards → {DISPLAY_NAME})"
    )
    print(f"\n✅ Dashboard published!")
    print(f"   URL: {url}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "create":
        cmd_create()

    elif command == "update":
        if len(sys.argv) < 3:
            print("Usage: python deploy_dashboard.py update <dashboard_id>")
            sys.exit(1)
        cmd_update(sys.argv[2])

    elif command == "publish":
        if len(sys.argv) < 3:
            print("Usage: python deploy_dashboard.py publish <dashboard_id>")
            sys.exit(1)
        cmd_publish(sys.argv[2])

    else:
        print(f"Unknown command: {command}")
        print("Commands: create | update <id> | publish <id>")
        sys.exit(1)


if __name__ == "__main__":
    main()
