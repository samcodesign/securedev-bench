import subprocess
import json
import time
import os
import shutil
from pathlib import Path
import sys

def simulate_agent_fix(task_dir: Path):
    """Simulates a successful agent fix."""
    print("[Harness]: Simulating agent fix...")
    app_path = task_dir / "app.py"
    solution_path = task_dir / "solution.py"
    if not solution_path.exists():
        print("[Harness]: WARNING - No solution.py found.")
        return
    shutil.copy(solution_path, app_path)
    print("[Harness]: Agent simulation complete.")

def parse_pytest_report(report_path: Path) -> dict:
    """Parses the JSON report from pytest."""
    results = {
        "security_tests": {"passed": 0, "failed": 0, "total": 0},
        "functional_tests": {"passed": 0, "failed": 0, "total": 0},
        "overall_passed": True
    }
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

def run_task(task_id: str):
    """Runs a full evaluation for a given task."""
    print(f"--- Running Task: {task_id} ---")
    start_time = time.time()
    original_task_dir = Path(task_id)
    temp_dir = Path(f"/tmp/{task_id}_{int(start_time)}").resolve()
    final_result, scorecard = "FAILED", {}
    image_name = f"securedev-bench-{task_id.lower()}"
    container_name = f"{image_name}-test"

    try:
        if not original_task_dir.exists():
            print(f"[Harness]: ERROR - Task directory not found: {original_task_dir}")
            return
        shutil.copytree(original_task_dir, temp_dir)
        print(f"[Harness]: Created isolated environment at {temp_dir}")

        # 2. Run the real agent via a command-line call
        print("[Harness]: Running real agent...")
        agent_path = Path(__file__).parent / "agent.py"
        target_file_path = temp_dir / "app.py"
        provider_to_test = "gemini"  # You can change this to "openai" later
        
        try:
            # This builds the command: python agent.py /path/to/app.py --provider gemini
            subprocess.run(
                [
                    sys.executable, str(agent_path),
                    str(target_file_path),
                    "--provider", provider_to_test
                ],
                check=True, capture_output=True, text=True
            )
        except subprocess.CalledProcessError as e:
            # This block catches errors if the agent.py script itself fails
            print("[Harness]: The agent script returned an error!")
            print("--- Agent STDOUT ---")
            print(e.stdout)
            print("--- Agent STDERR ---")
            print(e.stderr)
            raise e # Stop the task if the agent fails

        print("[Harness]: Building Docker container...")
        subprocess.run(["docker", "build", "-t", image_name, "."], cwd=temp_dir, check=True, capture_output=True)

        print("[Harness]: Running tests inside container...")
        run_result = subprocess.run(
            [
                "docker", "run",
                "-e", "API_KEY=DUMMY_KEY_FOR_TESTING", # <--- ADD THIS LINE
                f"--name={container_name}", image_name
            ],
            cwd=temp_dir, capture_output=True, text=True
        )
        print(f"\n--- Container logs for {container_name}: ---")
        print(run_result.stdout)
        if run_result.stderr:
            print("--- Stderr ---")
            print(run_result.stderr)
        print("--- End of logs ---")

        if run_result.returncode != 0:
            raise subprocess.CalledProcessError(run_result.returncode, run_result.args, run_result.stdout, run_result.stderr)

        report_path_in_container = f"{container_name}:/usr/src/app/report.json"
        report_path_on_host = temp_dir / "report.json"
        subprocess.run(["docker", "cp", report_path_in_container, str(report_path_on_host)], check=True, capture_output=True)

        scorecard = parse_pytest_report(report_path_on_host)
        if scorecard.get("overall_passed"):
            final_result = "SUCCESS"

    except subprocess.CalledProcessError as e:
        print(f"\n--- [Harness]: A critical command failed! ---")
        final_result = "HARNESS_FAILURE"
    finally:
        print(f"[Harness]: Cleaning up container '{container_name}'...")
        subprocess.run(["docker", "rm", container_name], capture_output=True, check=False)
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        print("[Harness]: Cleaned up temporary environment.")

    duration = time.time() - start_time
    print(f"\n--- Task {task_id} Finished ---")
    print(f"FINAL RESULT: {final_result}")
    print(f"Duration: {duration:.2f}s")
    print("\nSCORECARD:")
    if scorecard:
        sec = scorecard.get('security_tests', {})
        func = scorecard.get('functional_tests', {})
        print(f"  - Correctness (Security): {sec.get('passed', 0)}/{sec.get('total', 0)} PASSED")
        print(f"  - Functionality (Tests):  {func.get('passed', 0)}/{func.get('total', 0)} PASSED")
    else:
        print("  - No results generated.")
    print("--------------------------------\n")

if __name__ == "__main__":
    tasks = [d for d in os.listdir('.') if os.path.isdir(d) and d.startswith('task-')]
    if not tasks:
        print("No task directories found. Exiting.")
    else:
        for task in sorted(tasks):
            run_task(task)