import sys
import argparse
import questionary
import time
from .discovery import discover_tasks, discover_providers, discover_models
from .runner import run_task
from .reporting import save_reports, generate_markdown_report

def main():
    """
    Entry point for the SecureDev-Bench CLI application.
    This function orchestrates the benchmarking process for AI security agents by:
    1. Discovering available tasks and models based on the user's environment and configuration.
    2. Parsing command-line arguments to determine operational mode and user preferences.
    3. Handling informational flags to list available tasks and models.
    4. Performing critical error checks to ensure required components are present.
    5. Determining which tasks and models to run, supporting both interactive and non-interactive modes.
    6. Executing the benchmark loop, running selected tasks against selected models.
    7. Reporting results and saving a summary in markdown format.
    Command-line arguments:
        --list              List available tasks and models, then exit.
        --tasks             Specify which tasks to run.
        --models            Specify which models to test.
        -v, --verbose       Enable verbose logging.
        -y, --non-interactive Run in non-interactive mode.
    Exits with status code 1 if no tasks or models are found.
    """

    # --- Step 1: Discover all available components ---
    print("Discovering available tasks and models...")
    available_tasks = discover_tasks()
    provider_classes = discover_providers()
    available_models = discover_models(provider_classes)

    # --- Step 2: Set up the command-line argument parser ---
    parser = argparse.ArgumentParser(
        description="SecureDev-Bench: A benchmark for AI security agents.",
        formatter_class=argparse.RawTextHelpFormatter # Improves help text formatting
    )
    parser.add_argument(
        "--list", action="store_true", 
        help="List available tasks and models (based on your .env keys) and exit."
    )
    parser.add_argument(
        "--tasks", nargs='+', 
        help="Run specific tasks. If not provided, all tasks will be run."
    )
    parser.add_argument(
        "--models", nargs='+', 
        help="Test specific models. If not provided, all available models will be tested."
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", 
        help="Enable verbose (real-time) logging for debugging."
    )
    parser.add_argument(
        "-y", "--non-interactive", action="store_true", 
        help="Run in non-interactive mode. Uses all available tasks/models unless specified otherwise."
    )
    args = parser.parse_args()

    # --- Step 3: Handle informational flags ---
    if args.list:
        print("\nAvailable Tasks:")
        for task in available_tasks: print(f"  - {task}")
        print("\nAvailable Models (based on your .env keys):")
        for model in available_models: print(f"  - {model}")
        sys.exit(0)

    # --- Step 4: CRITICAL ERROR HANDLING (This is the fix) ---
    # This check runs for both interactive and non-interactive modes.
    if not available_tasks:
        print("\nError: No task directories found in the 'tasks/' folder.")
        sys.exit(1)
    if not available_models:
        print("\nError: No models could be discovered.")
        print("Please check that your API keys are correctly set in your .env file.")
        sys.exit(1)

    # --- Step 5: Determine tasks and models to run ---
    tasks_to_run = []
    models_to_run = []

    if args.non_interactive:
        print("Running in non-interactive mode...")
        tasks_to_run = args.tasks or available_tasks
        models_to_run = args.models or available_models
        is_verbose = args.verbose
    else:
        # Interactive Mode
        print("\nWelcome to the SecureDev-Bench Interactive CLI!")
        models_to_run = questionary.checkbox("Which models would you like to test?", choices=available_models).ask()
        if not models_to_run: sys.exit(0)
        
        tasks_to_run = questionary.checkbox("Which tasks would you like to run?", choices=available_tasks).ask()
        if not tasks_to_run: sys.exit(0)
        
        is_verbose = questionary.confirm("Enable verbose (real-time) logging?", default=False).ask()

    # --- Step 6: The Main Execution Loop ---
    all_results = []
    start_time = time.time()
    print(f"\nStarting benchmark for {len(models_to_run)} model(s) against {len(tasks_to_run)} task(s)...")
    for model_spec in models_to_run:
        provider, model = model_spec.split(":")
        if not is_verbose: print(f"  - Testing model: {model_spec}")
        for task in tasks_to_run:
            result_data = run_task(task, provider, model, verbose=is_verbose)
            all_results.append(result_data)
    total_duration = time.time() - start_time
    print(f"\n✅ Benchmark complete. Total duration: {total_duration:.2f}s")

    # --- Step 7: Final Reporting ---
    markdown_report = save_reports(all_results)
    print("\n--- Benchmark Summary ---")
    print(markdown_report)