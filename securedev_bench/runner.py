import subprocess
import json
import time
import os
import shutil
from pathlib import Path
import sys

def _get_subprocess_kwargs(verbose: bool):
    """
    Determines the correct stdout/stderr handling for subprocess calls
    based on the verbose flag.
    """
    if verbose:
        # In verbose mode, stream the output directly to the user's terminal in real-time.
        return {'stdout': sys.stderr, 'stderr': sys.stderr, 'text': True}
    else:
        # In quiet mode, capture the output to be shown only on error.
        return {'capture_output': True, 'text': True}

def parse_pytest_report(report_path: Path) -> dict:
    """Parses the JSON report from pytest to categorize test results."""
    results = {"security_tests": {"passed": 0, "failed": 0, "total": 0}, "functional_tests": {"passed": 0, "failed": 0, "total": 0}, "overall_passed": True}
    if not report_path.exists():
        results["overall_passed"] = False
        return results
    with open(report_path, 'r') as f:
        report = json.load(f)
    if report.get("summary", {}).get("failed", 0) > 0:
        results["overall_passed"] = False
    for test in report.get("tests", []):
        category = "functional_tests" if "test_app.py" in test.get("nodeid") else "security_tests"
        results[category]["total"] += 1
        if test.get("outcome") == "passed":
            results[category]["passed"] += 1
        else:
            results[category]["failed"] += 1
    return results

def run_task(task_id: str, provider: str, model: str, verbose: bool, tasks_dir="tasks") -> dict:
    """The core engine for running a single task evaluation."""
    if verbose: print(f"\n--- Running Task: {task_id} | Provider: {provider} | Model: {model} ---")
    
    start_time = time.time()
    original_task_dir = Path(tasks_dir) / task_id
    temp_dir = Path(f"/tmp/{task_id}_{int(start_time)}").resolve()
    final_result, scorecard = "FAILED", {}
    image_name = f"securedev-bench-{task_id.lower()}"
    container_name = f"{image_name}-test"
    
    # Get the correct subprocess arguments based on the verbose flag
    subproc_kwargs = _get_subprocess_kwargs(verbose)

    try:
        shutil.copytree(original_task_dir, temp_dir)
        
        if verbose: print("[Harness]: Running real agent...")
        agent_path = Path.cwd() / "agent.py"
        target_file_path = temp_dir / "app.py"
        subprocess.run([sys.executable, str(agent_path), str(target_file_path), "--provider", provider, "--model", model], check=True, **subproc_kwargs)

        if verbose: print("[Harness]: Building Docker container for testing...")
        subprocess.run(["docker", "build", "-t", image_name, "."], cwd=temp_dir, check=True, **subproc_kwargs)

        if verbose: print("[Harness]: Running tests inside container...")
        run_result = subprocess.run(["docker", "run", "-e", "API_KEY=DUMMY_KEY_FOR_TESTING", f"--name={container_name}", image_name], cwd=temp_dir, **subproc_kwargs)

        report_path_in_container = f"{container_name}:/usr/src/app/report.json"
        report_path_on_host = temp_dir / "report.json"
        subprocess.run(["docker", "cp", report_path_in_container, str(report_path_on_host)], capture_output=True, check=False)
        
        scorecard = parse_pytest_report(report_path_on_host)
        
        if run_result.returncode != 0:
            final_result = "TESTS_FAILED"
            if verbose and run_result.stdout: # If verbose, output was already streamed. This is for the rare case it wasn't.
                print(f"\n--- [Harness]: An error occurred inside the Docker container! ---\n{run_result.stdout}\n{run_result.stderr}")
        elif scorecard.get("overall_passed"):
            final_result = "SUCCESS"

    except subprocess.CalledProcessError as e:
        final_result = "HARNESS_FAILURE"
        if not verbose: # Only print the captured output if we are in quiet mode
            print(f"\n--- [Harness]: A critical command failed! ---\nCOMMAND: {' '.join(e.cmd)}\n--- STDOUT ---\n{e.stdout}\n--- STDERR ---\n{e.stderr}")
    finally:
        subprocess.run(["docker", "rm", container_name], capture_output=True, check=False)
        if temp_dir.exists(): shutil.rmtree(temp_dir)

    duration = time.time() - start_time
    sec_score = scorecard.get('security_tests', {})
    func_score = scorecard.get('functional_tests', {})
    return {"model_id": f"{provider}:{model}", "task_id": task_id, "result": final_result, "duration_seconds": round(duration, 2), "security_passed": sec_score.get('passed', 0), "security_total": sec_score.get('total', 0), "functionality_passed": func_score.get('passed', 0), "functionality_total": func_score.get('total', 0)}