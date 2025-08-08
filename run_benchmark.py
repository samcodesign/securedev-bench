# run_benchmark.py
import subprocess, json, time, os, shutil

def run_task(task_id: str, agent_command: list):
    print(f"--- Running Task: {task_id} ---")
    start_time = time.time()
    task_dir = os.path.abspath(f"./{task_id}")
    app_file_path = os.path.join(task_dir, 'app.py')
    backup_file_path = os.path.join(task_dir, 'app.py.bak')

    shutil.copy(app_file_path, backup_file_path)
    
    try:
        print("[Harness]: Running agent...")
        agent_cmd = agent_command + [app_file_path]
        subprocess.run(agent_cmd, capture_output=True, text=True, check=True)

        print("[Harness]: Running tests...")
        image_name = f"securedev-{task_id}"
        subprocess.run(["docker", "build", "-t", image_name, "."], cwd=task_dir, check=True, capture_output=True)
        test_result = subprocess.run(["docker", "run", "--rm", image_name], capture_output=True, text=True, check=True)
        
        tests_passed = True
        output = test_result.stdout

    except subprocess.CalledProcessError as e:
        tests_passed = False
        output = e.stdout + e.stderr
    
    finally:
        print("[Harness]: Cleaning up...")
        shutil.move(backup_file_path, app_file_path)

    duration = time.time() - start_time
    result_status = 'ALL TESTS PASSED' if tests_passed else 'TESTS FAILED'
    print(f"\n--- Task {task_id} Finished ---")
    print(f"Result: {result_status}")
    print(f"Duration: {duration:.2f}s")
    print("--- Output ---")
    print(output.strip())
    print("----------------\n")

if __name__ == "__main__":
    run_task("task-001-hardcoded-key", ["python", "agent.py"])