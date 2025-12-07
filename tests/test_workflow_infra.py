import os
import yaml
import pytest

WORKFLOW_DIR = ".github/workflows"
WORKFLOW_FILE = os.path.join(WORKFLOW_DIR, "daily_scrape.yml")

def test_workflow_directory_exists():
    assert os.path.isdir(WORKFLOW_DIR), f"Directory {WORKFLOW_DIR} does not exist"

def test_workflow_file_exists():
    assert os.path.isfile(WORKFLOW_FILE), f"File {WORKFLOW_FILE} does not exist"

def test_workflow_content():
    if not os.path.isfile(WORKFLOW_FILE):
        pytest.skip("Workflow file not found, skipping content checks")
    
    with open(WORKFLOW_FILE, "r") as f:
        content = yaml.safe_load(f)
    
    assert content is not None, "Workflow file is empty or invalid YAML"
    
    # Check Name
    assert content.get("name") == "Daily Fuel Price Scrape"
    
    # Check Triggers
    on_triggers = content.get("on")
    assert "push" in on_triggers
    assert "workflow_dispatch" in on_triggers
    
    # Check Permissions
    assert content.get("permissions") == {"contents": "write"}
    
    # Check Job
    jobs = content.get("jobs", {})
    assert "scrape" in jobs
    scrape_job = jobs["scrape"]
    
    assert scrape_job.get("runs-on") == "ubuntu-latest"
    assert scrape_job.get("timeout-minutes") == 5
    
    steps = scrape_job.get("steps", [])
    assert len(steps) >= 3
    
    # Check steps loosely
    step_uses = [step.get("uses", "") for step in steps]
    step_runs = [step.get("run", "") for step in steps]
    
    assert any("actions/checkout@v4" in s for s in step_uses)
    assert any("actions/setup-python@v5" in s for s in step_uses)
    
    # Check python version in setup-python
    setup_python_step = next((s for s in steps if "actions/setup-python@v5" in s.get("uses", "")), None)
    assert setup_python_step is not None
    assert setup_python_step.get("with", {}).get("python-version") == "3.11"
    
    # Check placeholder run
    assert any(s for s in step_runs if s)
