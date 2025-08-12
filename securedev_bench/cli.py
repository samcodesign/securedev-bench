import sys
import argparse
import questionary
import time
from colorama import init, Fore, Style
from .discovery import discover_tasks, discover_providers, discover_models
from .runner import run_task
from .reporting import save_reports
from pyfiglet import Figlet, FigletFont
import os



def display_banner():
    os.environ["PYFIGLET_FONT_DIR"] = "./fonts"
    f = Figlet(font="ANSI_Shadow")
    banner = f.renderText('SecureDev')
    print(Style.BRIGHT + Fore.MAGENTA + banner, file=sys.stderr)
    print(Fore.YELLOW + "A benchmark for the modern AI security agent.", file=sys.stderr)
    print(Fore.CYAN + "Initializing SecureDev-Bench CLI...", file=sys.stderr)


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
    init(autoreset=True)
    display_banner()
 
    # ---Discover all available components ---
    print(Fore.CYAN + "Discovering available tasks and models...", file=sys.stderr)
    available_tasks = discover_tasks()
    provider_classes = discover_providers()
    available_models = discover_models(provider_classes)

    # ---Set up the command-line argument parser ---
    parser = argparse.ArgumentParser(
        description="SecureDev-Bench: A benchmark for AI security agents.",
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False 
    )
    info_group = parser.add_argument_group('Informational Commands')
    info_group.add_argument("-h", "--help", action="store_true", help="Show this help message and exit.")
    info_group.add_argument("--list", action="store_true", help="List available tasks and models and exit.")

    run_group = parser.add_argument_group('Execution Control')
    run_group.add_argument("--tasks", nargs='+', help="REQUIRED in non-interactive mode. Space-separated list of tasks to run.")
    run_group.add_argument("--models", nargs='+', help="REQUIRED in non-interactive mode. Space-separated list of models to test.")
    run_group.add_argument("-v", "--verbose", action="store_true", help="Enable verbose (real-time) logging to stderr.")
    run_group.add_argument("-y", "--non-interactive", action="store_true", help="Run in non-interactive mode (requires --tasks and --models).")
    run_group.add_argument("--keep-temp", action="store_true", help="Keep the temporary working directory after each task run for debugging.")
    run_group.add_argument("--artifacts-dir", default="artifacts", help="Directory to store artifacts like modified app.py and report.json (default: artifacts).")
    run_group.add_argument("--no-artifacts", action="store_true", help="Do not save artifacts (overrides --artifacts-dir).")
    
    args = parser.parse_args()

    # ---Handle informational flags ---
    if args.help:
        parser.print_help(sys.stderr)
        sys.exit(0)  
        
    if args.list:
        print(Style.BRIGHT + Fore.BLUE + "\nAvailable Tasks:", file=sys.stderr)
        for task in available_tasks: print(f"  - {task}", file=sys.stderr)
        print(Style.BRIGHT + Fore.BLUE + "\nAvailable Models (based on your .env keys):", file=sys.stderr)
        for model in available_models: print(f"  - {model}", file=sys.stderr)
        sys.exit(0)

    # ---Error Handling ---
    if not available_tasks:
        print(Style.BRIGHT + Fore.RED + "\nError: No task directories found in the 'tasks/' folder.", file=sys.stderr)
        sys.exit(1)
    if not available_models:
        print(Style.BRIGHT + Fore.RED + "\nError: No models could be discovered. Check your .env file and API keys.", file=sys.stderr)
        sys.exit(1)

    # ---Determine tasks and models to run ---
    if args.non_interactive:
        if not args.tasks or not args.models:
            print(Style.BRIGHT + Fore.RED + "Error: In non-interactive mode (-y), you must specify which tasks and models to run.", file=sys.stderr)
            print(Fore.YELLOW + "Use --tasks <task1> ... and --models <model1> ...", file=sys.stderr)
            print(Fore.YELLOW + "Use --list to see available options.", file=sys.stderr)
            sys.exit(1)
        tasks_to_run = args.tasks
        models_to_run = args.models
        is_verbose = args.verbose
    else:
        # Interactive Mode
        print(Style.BRIGHT + Fore.GREEN + "\nWelcome to the SecureDev-Bench Interactive CLI!", file=sys.stderr)
        models_to_run = questionary.checkbox("Which models would you like to test?", choices=available_models).ask()
        if not models_to_run: sys.exit(0)
        tasks_to_run = questionary.checkbox("Which tasks would you like to run?", choices=available_tasks).ask()
        if not tasks_to_run: sys.exit(0)
        is_verbose = questionary.confirm("Enable verbose (real-time) logging?", default=False).ask()
        # New interactive toggles
        keep_temp_choice = questionary.confirm("Keep temporary directories after each run?", default=False).ask()
        save_artifacts_choice = questionary.confirm("Save artifacts (modified app.py and report.json)?", default=True).ask()
        artifacts_dir_choice = None
        if save_artifacts_choice:
            artifacts_dir_choice = questionary.text("Artifacts output directory:", default="artifacts").ask()

    # ---The Main Execution Loop ---
    all_results = []
    start_time = time.time()
    print(Style.BRIGHT + Fore.BLUE + f"\nStarting benchmark for {len(models_to_run)} model(s) against {len(tasks_to_run)} task(s)...", file=sys.stderr)
    for model_spec in models_to_run:
        provider, model = model_spec.split(":")
        if not is_verbose: print(Fore.YELLOW + f"  - Testing model: {model_spec}", file=sys.stderr)
        for task in tasks_to_run:
            result_data = run_task(
                task,
                provider,
                model,
                verbose=is_verbose,
                keep_temp=(args.keep_temp if args.non_interactive else keep_temp_choice),
                artifacts_dir=(args.artifacts_dir if args.non_interactive else (artifacts_dir_choice or "artifacts")),
                save_artifacts=(False if args.no_artifacts else (save_artifacts_choice if not args.non_interactive else True)),
            )
            all_results.append(result_data)
    total_duration = time.time() - start_time
    print(Fore.GREEN + f"\n✅ Benchmark complete. Total duration: {total_duration:.2f}s", file=sys.stderr)

    # ---Final Reporting ---
    markdown_report_for_console = save_reports(all_results)
    print(Style.BRIGHT + Fore.BLUE + "\n--- Benchmark Summary ---", file=sys.stderr)
    print(markdown_report_for_console)