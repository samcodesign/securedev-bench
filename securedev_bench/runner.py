import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def parse_pytest_report(report_path: Path) -> dict:
    """
    Parses the JSON report from pytest to categorize test results robustly.
    """
    results = {
        "security_tests": {"passed": 0, "failed": 0, "total": 0},
        "functional_tests": {"passed": 0, "failed": 0, "total": 0},
        "overall_passed": True,
    }
    if not report_path.exists():
        results["overall_passed"] = False
        return results

    # Use UTF-8 encoding for cross-platform compatibility
    with open(report_path, encoding="utf-8") as f:
        try:
            report = json.load(f)
        except json.JSONDecodeError:
            results["overall_passed"] = False
            return results  # Return empty if report is malformed

    # Check for overall failures or errors during collection
    if (
        report.get("summary", {}).get("failed", 0) > 0
        or report.get("summary", {}).get("error", 0) > 0
    ):
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
    variant: str = None,
    tasks_root: str = None,
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
        variant: Optional variant name (e.g., 'var-01') for variant-based tasks
        tasks_root: Root directory for task discovery (may be different from tasks_dir)
    Returns:
        A dictionary with the result of the task run, including model ID, task ID,
    """
    from .console import info
    from .console import is_verbose as console_verbose

    if verbose or console_verbose():
        info(
            f"\n--- Running Task: {task_id}{f' (variant: {variant})' if variant else ''} | Provider: {provider} | Model: {model} ---"
        )

    start_time = time.time()
    # Use the new get_task_path function to handle variants
    from .discovery import get_task_path

    # Use tasks_root if provided, otherwise fall back to tasks_dir
    actual_tasks_dir = tasks_root if tasks_root else tasks_dir
    original_task_dir = get_task_path(task_id, variant, actual_tasks_dir)
    # Create a platform-safe temporary directory for the run
    temp_dir_path = tempfile.mkdtemp(prefix=f"sdb_{task_id}_")
    temp_dir = Path(temp_dir_path)
    final_result, scorecard = "FAILED", {}
    image_name = f"securedev-bench-{task_id.lower()}"
    container_name = f"{image_name}-test"

    # Define subprocess arguments for streaming output in verbose mode
    stream_kwargs = {"check": True, "text": True, "encoding": "utf-8"}
    if verbose or console_verbose():
        stream_kwargs.update({"stdout": sys.stderr, "stderr": sys.stderr})
    else:
        stream_kwargs["capture_output"] = True

    # Define arguments for commands we always want to be quiet
    quiet_kwargs = {"check": True, "capture_output": True, "text": True, "encoding": "utf-8"}

    # Define arguments for docker run, which we handle manually
    docker_run_kwargs = {"text": True, "encoding": "utf-8"}
    if verbose or console_verbose():
        docker_run_kwargs.update({"stdout": sys.stderr, "stderr": sys.stderr})
    else:
        docker_run_kwargs["capture_output"] = True

    try:
        # 1. Setup isolated environment
        run_workdir = temp_dir / "work"
        # Ensure temp dir exists (mkdtemp created it) and copy the task into a subdir
        if not temp_dir.exists():
            temp_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(original_task_dir, run_workdir)

        # 2. Run the agent
        if verbose or console_verbose():
            info("[Harness]: Running real agent...")
        agent_path = Path.cwd() / "agent.py"
        target_file_path = run_workdir / "app.py"
        subprocess.run(
            [
                sys.executable,
                str(agent_path),
                str(target_file_path),
                "--provider",
                provider,
                "--model",
                model,
            ],
            **stream_kwargs,
        )

        # Also attempt to sanitize common config files the agent might miss
        extra_paths = []
        for name in ("config.py", ".env", "settings.py"):
            p = run_workdir / name
            if p.exists():
                extra_paths.append(p)

        config_dir = run_workdir / "config"
        if config_dir.is_dir():
            for p in config_dir.glob("*.py"):
                extra_paths.append(p)

        settings_dir = run_workdir / "settings"
        if settings_dir.is_dir():
            for p in settings_dir.glob("*.py"):
                extra_paths.append(p)

        # Run the agent on each extra candidate file (best-effort)
        for candidate in extra_paths:
            try:
                # make a quick backup in case of regressions
                backup = candidate.with_name(candidate.name + ".bak")
                shutil.copyfile(candidate, backup)
                if verbose or console_verbose():
                    info(f"[Harness]: Running agent on additional file: {candidate}")
                subprocess.run(
                    [
                        sys.executable,
                        str(agent_path),
                        str(candidate),
                        "--provider",
                        provider,
                        "--model",
                        model,
                    ],
                    **stream_kwargs,
                )
            except Exception as e:
                if verbose or console_verbose():
                    info(f"[Harness]: Failed to run agent on {candidate}: {e}")

        # 3. Build Docker container (quietly)
        if verbose or console_verbose():
            info("[Harness]: Building Docker container for testing...")
        subprocess.run(["docker", "build", "-t", image_name, "."], cwd=run_workdir, **quiet_kwargs)

        # 4. Run tests inside container
        if verbose or console_verbose():
            info("[Harness]: Running tests inside container...")
        run_result = subprocess.run(
            [
                "docker",
                "run",
                "-e",
                "API_KEY=DUMMY_KEY_FOR_TESTING",
                f"--name={container_name}",
                image_name,
            ],
            cwd=run_workdir,
            **docker_run_kwargs,
        )

        # 5. Copy report from container (robust to common WORKDIR variations)
        report_path_on_host = run_workdir / "report.json"
        primary_container_report = f"{container_name}:/usr/src/app/report.json"
        fallback_container_report = f"{container_name}:/usr/src.app/report.json"

        # Try primary path
        subprocess.run(
            ["docker", "cp", primary_container_report, str(report_path_on_host)],
            capture_output=True,
            check=False,
        )
        # If not present, try fallback path
        if not report_path_on_host.exists():
            subprocess.run(
                ["docker", "cp", fallback_container_report, str(report_path_on_host)],
                capture_output=True,
                check=False,
            )

        # 6. Parse scorecard
        scorecard = parse_pytest_report(report_path_on_host)

        if run_result.returncode != 0:
            final_result = "TESTS_FAILED"
            # If not verbose, print the captured output of the failed test run
            if (
                not (verbose or console_verbose())
                and hasattr(run_result, "stdout")
                and run_result.stdout
            ):
                info(
                    f"\n--- [Harness]: An error occurred inside the Docker container! ---\n{run_result.stdout}\n{run_result.stderr}"
                )
        elif scorecard.get("overall_passed"):
            final_result = "SUCCESS"

    except subprocess.CalledProcessError as e:
        final_result = "HARNESS_FAILURE"
        # Print captured output for harness failures
        info("\n--- [Harness]: A critical command failed! ---")
        info(f"COMMAND: {' '.join(e.cmd)}")
        if e.stdout:
            info(f"--- STDOUT ---:\n{e.stdout}")
        if e.stderr:
            info(f"--- STDERR ---:\n{e.stderr}")

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
                source_app_path = run_workdir / "app.py"
                if source_app_path.exists():
                    shutil.copyfile(source_app_path, artifacts_root / f"{base_name}_app.py")
                # Copy report.json if present
                host_report = run_workdir / "report.json"
                if host_report.exists():
                    shutil.copyfile(host_report, artifacts_root / f"{base_name}_report.json")
                # Optional helpful notice
                if verbose or console_verbose() or (final_result != "SUCCESS"):
                    info(
                        f"[Harness]: Artifacts saved to '{artifacts_root.resolve()}' (prefix: {base_name})"
                    )
            except Exception as artifact_err:
                # Never fail the run for artifact collection issues
                if verbose or console_verbose():
                    info(f"[Harness]: Failed to save artifacts: {artifact_err}")

        # Cleanup
        subprocess.run(["docker", "rm", container_name], capture_output=True, check=False)
        if not keep_temp and temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                # Best effort cleanup for temp dirs; ignore errors
                pass
        elif keep_temp:
            info(f"[Harness]: Keeping temp directory at {temp_dir}")

    duration = time.time() - start_time
    sec_score = scorecard.get("security_tests", {})
    func_score = scorecard.get("functional_tests", {})
    return {
        "model_id": f"{provider}:{model}",
        "task_id": task_id,
        "result": final_result,
        "duration_seconds": round(duration, 2),
        "security_passed": sec_score.get("passed", 0),
        "security_total": sec_score.get("total", 0),
        "functionality_passed": func_score.get("passed", 0),
        "functionality_total": func_score.get("total", 0),
    }
