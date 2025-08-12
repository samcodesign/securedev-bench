import subprocess
import json
import time
import os
import shutil
from pathlib import Path
import sys

def parse_pytest_report(report_path: Path) -> dict:
    """
    Parses the JSON report from pytest to categorize test results robustly.
    """
    results = {
        "security_tests": {"passed": 0, "failed": 0, "total": 0},
        "functional_tests": {"passed": 0, "failed": 0, "total": 0},
        "overall_passed": True
    }
    if not report_path.exists():
        results["overall_passed"] = False
        return results
        
    # Use UTF-8 encoding for cross-platform compatibility
    with open(report_path, 'r', encoding='utf-8') as f:
        try:
            report = json.load(f)
        except json.JSONDecodeError:
            results["overall_passed"] = False
            return results # Return empty if report is malformed

    # Check for overall failures or errors during collection
    if report.get("summary", {}).get("failed", 0) > 0 or report.get("summary", {}).get("error", 0) > 0:
        results["overall_passed"] = False

    # Categorize tests based on file name
    for test in report.get("tests", []):
        nodeid = test.get("nodeid", "")
        outcome = test.get("outcome")

        category = None
        if "test_security.py" in nodeid:
            category = "security_tests"
        elif "test_app.py" in nodeid:
            category = "functional_tests"
        
        if category:
            results[category]["total"] += 1
            if outcome == "passed":
                results[category]["passed"] += 1
            else:
                results[category]["failed"] += 1
                
    return results

def run_task(
    task_id: str,
    provider: str,
    model: str,
    verbose: bool,
    tasks_dir: str = "tasks",
    keep_temp: bool = False,
    artifacts_dir: str = "artifacts",
    save_artifacts: bool = True,
) -> dict:
    """
    The core engine for running a single task evaluation with selective verbosity.

    Parameters:
        task_id: The task directory name under tasks_dir
        provider: Provider key (e.g., 'gemini')
        model: Model identifier (e.g., 'gemini-2.5-pro')
        verbose: If True, stream subprocess output to stderr
        tasks_dir: Root directory containing tasks
        keep_temp: If True, do not delete the temporary work directory after run
        artifacts_dir: Directory on host to store artifacts like app.py and report.json
        save_artifacts: If True, save modified app.py and report.json to artifacts_dir
        
    """
    if verbose: print(f"\n--- Running Task: {task_id} | Provider: {provider} | Model: {model} ---", file=sys.stderr)
    
    start_time = time.time()
    original_task_dir = Path(tasks_dir) / task_id
    temp_dir = Path(f"/tmp/{task_id}_{int(start_time)}").resolve()
    final_result, scorecard = "FAILED", {}
    image_name = f"securedev-bench-{task_id.lower()}"
    container_name = f"{image_name}-test"
    
    # Define subprocess arguments for streaming output in verbose mode
    stream_kwargs = {'check': True, 'text': True, 'encoding': 'utf-8'}
    if verbose:
        stream_kwargs.update({'stdout': sys.stderr, 'stderr': sys.stderr})
    else:
        stream_kwargs['capture_output'] = True

    # Define arguments for commands we always want to be quiet
    quiet_kwargs = {'check': True, 'capture_output': True, 'text': True, 'encoding': 'utf-8'}
    
    # Define arguments for docker run, which we handle manually
    docker_run_kwargs = {'text': True, 'encoding': 'utf-8'}
    if verbose:
        docker_run_kwargs.update({'stdout': sys.stderr, 'stderr': sys.stderr})
    else:
        docker_run_kwargs['capture_output'] = True

    try:
        # 1. Setup isolated environment
        shutil.copytree(original_task_dir, temp_dir)
        
        # 2. Run the agent
        if verbose: print("[Harness]: Running real agent...", file=sys.stderr)
        agent_path = Path.cwd() / "agent.py"
        target_file_path = temp_dir / "app.py"
        subprocess.run([sys.executable, str(agent_path), str(target_file_path), "--provider", provider, "--model", model], **stream_kwargs)

        # 3. Build Docker container (quietly)
        if verbose: print("[Harness]: Building Docker container for testing...", file=sys.stderr)
        subprocess.run(["docker", "build", "-t", image_name, "."], cwd=temp_dir, **quiet_kwargs)

        # 4. Run tests inside container
        if verbose: print("[Harness]: Running tests inside container...", file=sys.stderr)
        run_result = subprocess.run(["docker", "run", "-e", "API_KEY=DUMMY_KEY_FOR_TESTING", f"--name={container_name}", image_name], cwd=temp_dir, **docker_run_kwargs)

        # 5. Copy report from container (robust to common WORKDIR variations)
        report_path_on_host = temp_dir / "report.json"
        primary_container_report = f"{container_name}:/usr/src/app/report.json"
        fallback_container_report = f"{container_name}:/usr/src.app/report.json"

        # Try primary path
        subprocess.run(["docker", "cp", primary_container_report, str(report_path_on_host)], capture_output=True, check=False)
        # If not present, try fallback path
        if not report_path_on_host.exists():
            subprocess.run(["docker", "cp", fallback_container_report, str(report_path_on_host)], capture_output=True, check=False)
        
        # 6. Parse scorecard
        scorecard = parse_pytest_report(report_path_on_host)
        
        if run_result.returncode != 0:
            final_result = "TESTS_FAILED"
            # If not verbose, print the captured output of the failed test run
            if not verbose and run_result.stdout:
                print(f"\n--- [Harness]: An error occurred inside the Docker container! ---\n{run_result.stdout}\n{run_result.stderr}", file=sys.stderr)
        elif scorecard.get("overall_passed"):
            final_result = "SUCCESS"

    except subprocess.CalledProcessError as e:
        final_result = "HARNESS_FAILURE"
        # Print captured output for harness failures
        print(f"\n--- [Harness]: A critical command failed! ---", file=sys.stderr)
        print(f"COMMAND: {' '.join(e.cmd)}", file=sys.stderr)
        if e.stdout: print(f"--- STDOUT ---:\n{e.stdout}", file=sys.stderr)
        if e.stderr: print(f"--- STDERR ---:\n{e.stderr}", file=sys.stderr)
            
    finally:
        # Save artifacts if enabled (attempt regardless of run result)
        if save_artifacts:
            try:
                artifacts_root = Path(artifacts_dir)
                artifacts_root.mkdir(parents=True, exist_ok=True)
                # Normalize model and provider for filenames
                safe_model = model.replace(os.sep, "-").replace(":", "-")
                safe_provider = provider.replace(os.sep, "-").replace(":", "-")
                base_name = f"{task_id}_{int(start_time)}_{safe_provider}-{safe_model}"
                # Copy modified app.py
                source_app_path = temp_dir / "app.py"
                if source_app_path.exists():
                    shutil.copyfile(source_app_path, artifacts_root / f"{base_name}_app.py")
                # Copy report.json if present
                host_report = temp_dir / "report.json"
                if host_report.exists():
                    shutil.copyfile(host_report, artifacts_root / f"{base_name}_report.json")
                # Optional helpful notice
                if verbose or (final_result != "SUCCESS"):
                    print(f"[Harness]: Artifacts saved to '{artifacts_root.resolve()}' (prefix: {base_name})", file=sys.stderr)
            except Exception as artifact_err:
                # Never fail the run for artifact collection issues
                if verbose:
                    print(f"[Harness]: Failed to save artifacts: {artifact_err}", file=sys.stderr)

        # Cleanup
        subprocess.run(["docker", "rm", container_name], capture_output=True, check=False)
        if not keep_temp and temp_dir.exists():
            shutil.rmtree(temp_dir)
        elif keep_temp:
            print(f"[Harness]: Keeping temp directory at {temp_dir}", file=sys.stderr)

    duration = time.time() - start_time
    sec_score = scorecard.get('security_tests', {})
    func_score = scorecard.get('functional_tests', {})
    return {"model_id": f"{provider}:{model}", "task_id": task_id, "result": final_result, "duration_seconds": round(duration, 2), "security_passed": sec_score.get('passed', 0), "security_total": sec_score.get('total', 0), "functionality_passed": func_score.get('passed', 0), "functionality_total": func_score.get('total', 0)}