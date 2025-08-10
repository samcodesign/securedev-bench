# Project Architecture

SecureDev is designed to be modular and maintainable. Here is a high-level overview of the project structure:

- **`run_benchmark.py`**: The main entry point for the application. Its only job is to load the environment and start the CLI.

- **`agent.py`**: The AI agent. It receives a file path and instructions from the benchmark runner. It loads the correct provider and asks it to fix the code.

- **`securedev_bench/`**: The core library for the benchmark.
  - **`cli.py`**: Handles all user interaction, including the interactive prompts (`questionary`) and non-interactive flags (`argparse`). This is the main orchestrator.
  - **`discovery.py`**: Contains all logic for dynamically finding available tasks and models.
  - **`runner.py`**: Contains the core engine for running a single benchmark task, including setting up the environment, running the agent, building and running Docker, and parsing results.
  - **`reporting.py`**: Contains all logic for generating the final Markdown and JSON report files.

- **`providers/`**: Contains the different AI model providers. Each provider is a module that knows how to communicate with a specific API (e.g., Gemini).

- **`tasks/`**: Contains the individual security challenges. Each task is a self-contained directory with everything needed to run the test.
