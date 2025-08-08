import sys
import argparse
import questionary
import time
from .discovery import discover_tasks, discover_providers, discover_models
from .runner import run_task
from .reporting import save_reports, generate_markdown_report

def main():
    """
    Main entry point for the SecureDev-Bench CLI.
    This function discovers available tasks, providers, and models, then parses command-line arguments to determine
    whether to run in interactive or non-interactive mode. It allows users to list available tasks and models, select
    which tasks and models to run, and optionally enable verbose logging. The function executes the selected benchmarks,
    collects results, and prints a summary report.
    Command-line arguments:
        -h, --help: Show help message and exit.
        --list: List available tasks and models and exit.
        --tasks: Space-separated list of tasks to run.
        --models: Space-separated list of models to test.
        -v, --verbose: Enable verbose (real-time) logging.
        -y, --non-interactive: Run in non-interactive mode using defaults or provided flags.
    Returns:
        None
    """
    # Discover components
    available_tasks = discover_tasks()
    provider_classes = discover_providers()
    available_models = discover_models(provider_classes)

    # Set up the non-interactive parser
    parser = argparse.ArgumentParser(description="SecureDev-Bench: A benchmark for AI security agents.", add_help=False)
    parser.add_argument("-h", "--help", action="store_true", help="Show this help message and exit.")
    parser.add_argument("--list", action="store_true", help="List available tasks and models and exit.")
    parser.add_argument("--tasks", nargs='+', help="Space-separated list of tasks to run.")
    parser.add_argument("--models", nargs='+', help="Space-separated list of models to test.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose (real-time) logging.")
    parser.add_argument("-y", "--non-interactive", action="store_true", help="Run in non-interactive mode using defaults or provided flags.")
    
    args = parser.parse_args()

    # Handle help and list flags
    if args.help:
        parser.print_help()
        sys.exit(0)
        
    if args.list:
        print("Available Tasks:")
        for task in available_tasks: print(f"  - {task}")
        print("\nAvailable Models (based on your .env keys):")
        for model in available_models: print(f"  - {model}")
        sys.exit(0)

    # Determine run mode: Interactive or Non-Interactive
    if args.non_interactive:
        tasks_to_run = args.tasks or available_tasks
        models_to_run = args.models or available_models
        is_verbose = args.verbose
    else:
        print("\nWelcome to the SecureDev-Bench Interactive CLI!")
        if not available_tasks or not available_models:
            print("Error: No tasks or models available. Check your setup. Exiting.")
            sys.exit(1)
        
        models_to_run = questionary.checkbox("Which models would you like to test?", choices=available_models).ask()
        if not models_to_run: sys.exit(0)
        
        tasks_to_run = questionary.checkbox("Which tasks would you like to run?", choices=available_tasks).ask()
        if not tasks_to_run: sys.exit(0)
        
        is_verbose = questionary.confirm("Enable verbose (real-time) logging?", default=False).ask()

    # The Main Execution Loop
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

    # Final Reporting
    markdown_report = save_reports(all_results)
    print("\n--- Benchmark Summary ---")
    print(markdown_report)