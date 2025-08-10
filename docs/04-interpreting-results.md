# How to Interpret the Results

The final summary table provides an overview of the benchmark run. The `Result` column is the most important indicator.

- **`SUCCESS`**: The AI agent successfully fixed the vulnerability without breaking any core functionality. All security and functional tests passed.

- **`TESTS_FAILED`**: The agent's proposed solution was incorrect. This can happen in several ways:
  - The security tests failed (the vulnerability was not fixed).
  - The functional tests failed (the fix broke the application).
  - The code contained a syntax error, causing the test suite to crash.

- **`HARNESS_FAILURE`**: An error occurred in the benchmark harness itself. This usually indicates a problem with the environment (e.g., Docker is not running) or a bug in the benchmark's own scripts.
