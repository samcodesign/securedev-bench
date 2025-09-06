import shutil
import sys

from colorama import Fore, Style

# Reusable modules split from this file
from .cli_parser import build_parser, handle_informational_flags, interactive_selection
from .console import banner, error, info, init_console, set_verbose, success
from .discovery import discover_models, discover_providers, discover_tasks
from .executor import execute_benchmark
from .reporting import generate_console_report, save_reports
from .tasks_source import prepare_tasks_source

# `console.banner()` provides the banner now


def main():
    init_console()
    banner()

    parser = build_parser()
    args = parser.parse_args()

    # Wire verbosity to logger
    if getattr(args, "verbose", False):
        set_verbose()

    # Early informational handling (may exit)
    handle_informational_flags(args, parser)

    # Prepare tasks source (local dir or cloned repo)
    tasks_root, cloned_tasks_dir, tasks_source_is_remote = prepare_tasks_source(args)

    # Discover components
    info(Fore.CYAN + "Discovering available tasks and models...")
    available_tasks = discover_tasks(tasks_root)
    provider_classes = discover_providers()
    available_models = discover_models(provider_classes)

    # If model discovery returned nothing, retry with a longer timeout once.
    if not available_models:
        info(
            Fore.YELLOW
            + "No models found on first pass; retrying model discovery with extended timeout..."
        )
        # discover_models accepts an optional timeout_seconds arg
        try:
            available_models = discover_models(provider_classes, timeout_seconds=30)
        except Exception:
            available_models = []

    # Robust error handling
    if not available_tasks:
        error(
            Style.BRIGHT + Fore.RED + "\nError: No task directories found in the 'tasks/' folder."
        )
        sys.exit(1)
    if not available_models:
        error(
            Style.BRIGHT
            + Fore.RED
            + "\nError: No models could be discovered. Check your .env file and API keys."
        )
        sys.exit(1)

    # Determine tasks/models and interactive options
    (
        tasks_to_run,
        models_to_run,
        is_verbose,
        keep_temp_choice,
        save_artifacts_choice,
        artifacts_dir_choice,
        run_in_parallel,
        workers,
    ) = interactive_selection(args, available_tasks, available_models, tasks_source_is_remote)

    # Handle user cancellation or empty selections from interactive prompts
    if not models_to_run:
        info("No models selected or selection cancelled. Exiting.")
        sys.exit(0)
    if not tasks_to_run:
        info("No tasks selected or selection cancelled. Exiting.")
        sys.exit(0)

    # Execute benchmark
    all_results, total_duration = execute_benchmark(
        args,
        tasks_root,
        tasks_to_run,
        models_to_run,
        is_verbose,
        keep_temp_choice,
        save_artifacts_choice,
        artifacts_dir_choice,
        run_in_parallel=run_in_parallel,
        workers=workers,
    )

    success(Fore.GREEN + f"\n✅ Benchmark complete. Total duration: {total_duration:.2f}s")

    # Reporting
    save_reports(all_results)
    info(Style.BRIGHT + Fore.BLUE + "\n--- Benchmark Summary ---")
    print(generate_console_report(all_results))

    # Cleanup cloned tasks repo, if any
    if cloned_tasks_dir and not args.keep_temp:
        shutil.rmtree(cloned_tasks_dir, ignore_errors=True)


# helper modules now live in separate files (cli_parser.py, tasks_source.py, executor.py)
