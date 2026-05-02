#!/usr/bin/env python3
"""
F1 Telemetry Pipeline — Deploy Real-time Pipeline
======================================================

Deploys the unified real-time pipeline notebook to the Databricks workspace
and orchestrates it using a Databricks Job. Because Free Edition limits you
to a single cluster, this script ensures all 9 streams run concurrently on 
a single task, minimizing latency to just a few seconds.

Usage:
  python deploy_realtime_pipeline.py
"""

import json
import subprocess
import sys
import os
from pathlib import Path

# Setup paths
WORKSPACE_DIR = "/Workspace/Users/ayushmaan1362@gmail.com/f1_telemetry"
LOCAL_NB_DIR = Path(__file__).parent / "notebooks"
JOB_NAME = "F1 Telemetry Realtime Pipeline"

def run_cli(args: list[str]) -> dict:
    """Run a Databricks CLI command and return parsed JSON output."""
    cmd = ["databricks"] + args + ["--output", "json"]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"ERROR: CLI command failed:\n{result.stderr}")
        sys.exit(result.returncode)
        
    try:
        return json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError:
        return {}

def sync_notebooks():
    """Upload notebooks from local src/databricks/notebooks to the Workspace."""
    print(f"Syncing notebooks to {WORKSPACE_DIR}...")
    
    # We only need the realtime pipeline and data preview
    notebooks = [
        "realtime_pipeline.py", 
        "data_preview.py"
    ]
    
    subprocess.run(["databricks", "workspace", "mkdirs", WORKSPACE_DIR], capture_output=True)
    
    for nb in notebooks:
        local_path = LOCAL_NB_DIR / nb
        remote_path = f"{WORKSPACE_DIR}/{nb.replace('.py', '')}"
        
        print(f"  Uploading {local_path} to {remote_path}...")
        res = subprocess.run([
            "databricks", "workspace", "import", 
            remote_path, "--file", str(local_path), 
            "--format", "SOURCE", "--language", "PYTHON", "--overwrite"
        ], capture_output=True, text=True)
        
        if res.returncode != 0:
            print(f"Failed to upload {nb}: {res.stderr}")

def get_existing_job_id():
    """Check if the job already exists."""
    jobs_response = run_cli(["jobs", "list"])
    
    if isinstance(jobs_response, list):
        jobs = jobs_response
    elif isinstance(jobs_response, dict):
        jobs = jobs_response.get("jobs", [])
    else:
        jobs = []
        
    for job in jobs:
        if job.get("settings", {}).get("name") == JOB_NAME or job.get("name") == JOB_NAME:
            return job["job_id"]
    return None

def deploy_job():
    """Create or update the Databricks Workflow job using Serverless compute."""
    
    job_definition = {
        "name": JOB_NAME,
        "tasks": [
            {
                "task_key": "Realtime_Pipeline",
                "notebook_task": {
                    "notebook_path": f"{WORKSPACE_DIR}/realtime_pipeline",
                    "source": "WORKSPACE"
                }
            }
        ]
    }
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        json.dump(job_definition, tmp)
        tmp_path = tmp.name

    try:
        job_id = get_existing_job_id()
        if job_id:
            print(f"\nUpdating existing job: {job_id}")
            reset_payload = {
                "job_id": job_id,
                "new_settings": job_definition
            }
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as reset_tmp:
                json.dump(reset_payload, reset_tmp)
                reset_tmp_path = reset_tmp.name
            
            try:
                run_cli(["jobs", "reset", "--json", f"@{reset_tmp_path}"])
                print(f"\n[OK] Job updated successfully! ID: {job_id}")
            finally:
                os.unlink(reset_tmp_path)
        else:
            print("\nCreating new job...")
            response = run_cli(["jobs", "create", "--json", f"@{tmp_path}"])
            job_id = response.get("job_id")
            print(f"\n[OK] Job created successfully! ID: {job_id}")
            
        print(f"\nTo start continuous streaming, run:")
        print(f"  databricks jobs run-now {job_id}")
        print("\nNote: This is a continuous job. Remember to manually CANCEL the run in the Databricks UI when finished!")
            
    finally:
        os.unlink(tmp_path)

if __name__ == "__main__":
    print("Deploying Real-Time Pipeline using Databricks Serverless Compute...")
    sync_notebooks()
    deploy_job()
