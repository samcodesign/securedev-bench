# How to Add a New Task

Adding new security tasks is the most valuable way to contribute to SecureDev-Bench. A good task is a self-contained, realistic security challenge.

## 1. Directory Structure

First, in the `tasks/` directory, create a new folder for your task. The name should follow the pattern `task-XXX-vulnerability-name`. For example:

`tasks/task-005-insecure-deserialization/`

## 2. Required Files

Your new task directory must contain the following six files:

* **`app.py`**: The vulnerable Python code. This is the code that the AI agent will be asked to fix.
* **`solution.py`**: The corrected, secure version of the code. The benchmark harness uses this as a reference during the (optional) simulation phase.
* **`test_app.py`**: A `pytest` file to test the core **functionality** of the application. These tests should pass for both `app.py` and `solution.py`.
* **`test_security.py`**: A `pytest` file that specifically tests for the **vulnerability**. This test must **fail** when run against `app.py` and **pass** when run against `solution.py`.
* **`requirements.txt`**: A list of all Python dependencies needed for the task (e.g., `Flask`, `requests`).
* **`Dockerfile`**: The Dockerfile to set up the isolated test environment. For most web-based tasks, you can use the `Dockerfile` from `task-004-cross-site-scripting` as a template.

## 3. The Golden Rule

The goal is to create a clear and unambiguous test. The difference between the "vulnerable" state and the "secure" state should be something that can be reliably checked by the `test_security.py` file.

## 4. Submitting Your Task

Once your task is complete and you have tested it locally, please open a pull request. We are excited to see new challenges added to the benchmark!

## 5. Local validation (recommended)

Before opening a PR, validate the task locally in an isolated container and using pytest. A simple local workflow is:

1. Build the Docker image from the task directory (example):

```powershell
# from repository root
docker build -t securedev-task-local:latest tasks/task-005-insecure-deserialization/
```

1. Run the test suite inside the container or on the host using the task's `requirements.txt`:

```powershell
# run pytest inside a temporary container (recommended)
docker run --rm securedev-task-local:latest pytest -q

# OR (local venv)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r tasks/task-005-insecure-deserialization/requirements.txt
pytest -q tasks/task-005-insecure-deserialization/
```

Notes:

* Keep tasks deterministic and avoid network calls in `test_*` files. If a task needs secrets for external services, prefer mocks or fixtures with placeholder values.
* Expected runtime for a well-formed task is small (typically under ~30s when run inside the task Dockerfile on a modern laptop).
