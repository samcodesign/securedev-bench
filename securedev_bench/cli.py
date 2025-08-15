import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time

import questionary
from colorama import Fore, Style, init
from pyfiglet import Figlet

from .discovery import discover_models, discover_providers, discover_tasks
from .reporting import save_reports
from .runner import run_task


def display_banner():
    os.environ["PYFIGLET_FONT_DIR"] = "./fonts"
    f = Figlet(font="ANSI_Shadow")
    banner = f.renderText("SecureDev")
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

    # ---Set up the command-line argument parser ---
    parser = argparse.ArgumentParser(
        description="SecureDev-Bench: A benchmark for AI security agents.",
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False,
    )
    info_group = parser.add_argument_group("Informational Commands")
    info_group.add_argument(
        "-h", "--help", action="store_true", help="Show this help message and exit."
    )
    info_group.add_argument(
        "--list-models", action="store_true", help="List all available models and exit."
    )
    info_group.add_argument(
        "--list-task-repo",
        help="List tasks from a private repository and exit. Use with --tasks-ref for specific branch.",
    )
    info_group.add_argument(
        "--list-task-dir",
        nargs="?",
        const="tasks",
        help="List tasks from a local directory and exit (default: tasks).",
    )

    run_group = parser.add_argument_group("Execution Control")
    run_group.add_argument(
        "--tasks",
        nargs="+",
        help="REQUIRED in non-interactive mode. Space-separated list of tasks to run.",
    )
    run_group.add_argument(
        "--models",
        nargs="+",
        help="REQUIRED in non-interactive mode. Space-separated list of models to test.",
    )
    run_group.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose (real-time) logging to stderr."
    )
    run_group.add_argument(
        "-y",
        "--non-interactive",
        action="store_true",
        help="Run in non-interactive mode (requires --tasks and --models).",
    )
    run_group.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep the temporary working directory after each task run for debugging.",
    )
    run_group.add_argument(
        "--tasks-dir",
        default="tasks",
        help="Path to a local tasks directory (default: tasks).",
    )
    run_group.add_argument(
        "--tasks-repo",
        help="Git URL of a tasks repository to clone (supports private repos via SSH or HTTPS with credentials).",
    )
    run_group.add_argument(
        "--tasks-ref",
        help="Optional git ref (branch or tag) to checkout when using --tasks-repo.",
    )
    run_group.add_argument(
        "--artifacts-dir",
        default="artifacts",
        help="Directory to store artifacts like modified app.py and report.json (default: artifacts).",
    )
    run_group.add_argument(
        "--no-artifacts",
        action="store_true",
        help="Do not save artifacts (overrides --artifacts-dir).",
    )

    args = parser.parse_args()

    # ---Early handle help/list to avoid prompting before exiting---
    if args.help:
        parser.print_help(sys.stderr)
        sys.exit(0)

    if args.list_models:
        # Just list models
        provider_classes = discover_providers()
        available_models = discover_models(provider_classes)

        print(
            Style.BRIGHT + Fore.BLUE + "\nAvailable Models (based on your .env keys):",
            file=sys.stderr,
        )
        for model in available_models:
            print(f"  - {model}", file=sys.stderr)
        sys.exit(0)

    if args.list_task_repo:
        # List tasks from a private repository
        if not args.tasks_ref:
            print(
                Fore.YELLOW + "Note: No --tasks-ref specified, using default branch.",
                file=sys.stderr,
            )

        try:
            print(Fore.CYAN + "Cloning tasks repository...", file=sys.stderr)
            list_cloned_dir = tempfile.mkdtemp(prefix="sdb_tasks_")
            clone_cmd = ["git", "clone", "--depth", "1"]
            if args.tasks_ref:
                clone_cmd += ["-b", args.tasks_ref]
            repo_url = args.list_task_repo
            gh_token = os.environ.get("GH_TOKEN") or os.environ.get("TASKS_GIT_TOKEN")
            if (
                gh_token
                and repo_url.startswith("https://")
                and "@" not in repo_url.split("//", 1)[1]
            ):
                proto, rest = repo_url.split("//", 1)
                repo_url = f"{proto}//{gh_token}@{rest}"
            clone_cmd += [repo_url, list_cloned_dir]
            subprocess.run(clone_cmd, check=True, capture_output=True, text=True)

            print(f"Debug: Cloned to {list_cloned_dir}", file=sys.stderr)
            print(f"Debug: Contents: {os.listdir(list_cloned_dir)}", file=sys.stderr)

            # Discover and list tasks from the cloned repo
            available_tasks = discover_tasks(list_cloned_dir)
            print(f"Debug: Found {len(available_tasks)} tasks", file=sys.stderr)

            print(
                Style.BRIGHT + Fore.BLUE + f"\nAvailable Tasks from {args.list_task_repo}:",
                file=sys.stderr,
            )
            for task_id, variants in available_tasks.items():
                if variants:
                    print(f"  - {task_id} (variants: {', '.join(variants)})", file=sys.stderr)
                else:
                    print(f"  - {task_id}", file=sys.stderr)

            shutil.rmtree(list_cloned_dir, ignore_errors=True)
            sys.exit(0)
        except subprocess.CalledProcessError as e:
            print(
                Style.BRIGHT + Fore.RED + "\nError: Failed to clone tasks repository for listing.",
                file=sys.stderr,
            )
            err_out = e.stderr or e.stdout or str(e)
            print(Fore.RED + err_out, file=sys.stderr)
            if list_cloned_dir and os.path.isdir(list_cloned_dir):
                shutil.rmtree(list_cloned_dir, ignore_errors=True)
            sys.exit(1)
        except Exception as e:
            print(
                Style.BRIGHT + Fore.RED + f"\nUnexpected error during task discovery: {e}",
                file=sys.stderr,
            )
            if list_cloned_dir and os.path.isdir(list_cloned_dir):
                shutil.rmtree(list_cloned_dir, ignore_errors=True)
            sys.exit(1)

    if args.list_task_dir:
        # List tasks from a local directory
        tasks_dir = args.list_task_dir or "tasks"
        available_tasks = discover_tasks(tasks_dir)

        print(Style.BRIGHT + Fore.BLUE + f"\nAvailable Tasks from '{tasks_dir}':", file=sys.stderr)
        for task_id, variants in available_tasks.items():
            if variants:
                print(f"  - {task_id} (variants: {', '.join(variants)})", file=sys.stderr)
            else:
                print(f"  - {task_id}", file=sys.stderr)
        sys.exit(0)

    # ---Prepare tasks root: local dir or a cloned repo---
    cloned_tasks_dir = None
    tasks_root = args.tasks_dir
    # Track whether the tasks source was cloned/remote (affects keep-temp prompt)
    tasks_source_is_remote = False

    # Interactive users can choose a tasks source if not explicitly provided
    if not args.non_interactive and not args.tasks_repo and args.tasks_dir == "tasks":
        source_choice = questionary.select(
            "Select tasks source",
            choices=[
                "Use local 'tasks' directory",
                "Specify local directory path",
                "Clone tasks repository (Git URL)",
            ],
        ).ask()

        if source_choice == "Specify local directory path":
            custom_dir = questionary.text("Enter path to tasks directory:", default="tasks").ask()
            tasks_root = custom_dir or "tasks"

        elif source_choice == "Clone tasks repository (Git URL)":
            repo_input = questionary.text("Enter Git URL (SSH or HTTPS):").ask()
            ref_input = questionary.text(
                "Optional branch or tag (press Enter to skip):", default=""
            ).ask()
            if repo_input:
                try:
                    print(Fore.CYAN + "Cloning tasks repository...", file=sys.stderr)
                    cloned_tasks_dir = tempfile.mkdtemp(prefix="sdb_tasks_")
                    clone_cmd = ["git", "clone", "--depth", "1"]
                    if ref_input:
                        clone_cmd += ["-b", ref_input]
                    repo_url = repo_input
                    gh_token = os.environ.get("GH_TOKEN") or os.environ.get("TASKS_GIT_TOKEN")
                    if (
                        gh_token
                        and repo_url.startswith("https://")
                        and "@" not in repo_url.split("//", 1)[1]
                    ):
                        proto, rest = repo_url.split("//", 1)
                        repo_url = f"{proto}//{gh_token}@{rest}"
                    clone_cmd += [repo_url, cloned_tasks_dir]
                    subprocess.run(clone_cmd, check=True, capture_output=True, text=True)
                    tasks_root = cloned_tasks_dir
                    tasks_source_is_remote = True
                except subprocess.CalledProcessError as e:
                    print(
                        Style.BRIGHT + Fore.RED + "\nError: Failed to clone tasks repository.",
                        file=sys.stderr,
                    )
                    err_out = e.stderr or e.stdout or str(e)
                    print(Fore.RED + err_out, file=sys.stderr)
                    if cloned_tasks_dir and os.path.isdir(cloned_tasks_dir):
                        shutil.rmtree(cloned_tasks_dir, ignore_errors=True)
                    sys.exit(1)

    # Non-interactive or explicitly provided repo cloning
    if args.tasks_repo and (args.non_interactive or tasks_root == args.tasks_dir):
        try:
            print(Fore.CYAN + "Cloning tasks repository...", file=sys.stderr)
            cloned_tasks_dir = tempfile.mkdtemp(prefix="sdb_tasks_")
            clone_cmd = ["git", "clone", "--depth", "1"]
            if args.tasks_ref:
                clone_cmd += ["-b", args.tasks_ref]
            # Support HTTPS with token if GH_TOKEN is provided and URL lacks credentials
            repo_url = args.tasks_repo
            gh_token = os.environ.get("GH_TOKEN") or os.environ.get("TASKS_GIT_TOKEN")
            if (
                gh_token
                and repo_url.startswith("https://")
                and "@" not in repo_url.split("//", 1)[1]
            ):
                # Insert token without logging it
                proto, rest = repo_url.split("//", 1)
                repo_url = f"{proto}//{gh_token}@{rest}"
            clone_cmd += [repo_url, cloned_tasks_dir]
            subprocess.run(clone_cmd, check=True, capture_output=True, text=True)
            tasks_root = cloned_tasks_dir
            tasks_source_is_remote = True
        except subprocess.CalledProcessError as e:
            print(
                Style.BRIGHT + Fore.RED + "\nError: Failed to clone tasks repository.",
                file=sys.stderr,
            )
            # Avoid printing full command if it may include credentials
            err_out = e.stderr or e.stdout or str(e)
            print(Fore.RED + err_out, file=sys.stderr)
            # Cleanup any partial dir
            if cloned_tasks_dir and os.path.isdir(cloned_tasks_dir):
                shutil.rmtree(cloned_tasks_dir, ignore_errors=True)
            sys.exit(1)

    # ---Discover all available components ---
    print(Fore.CYAN + "Discovering available tasks and models...", file=sys.stderr)
    available_tasks = discover_tasks(tasks_root)
    provider_classes = discover_providers()
    available_models = discover_models(provider_classes)

    # ---Handle informational flags ---
    # if args.help:
    #     parser.print_help(sys.stderr)
    #     sys.exit(0)

    # if args.list:
    #     print(Style.BRIGHT + Fore.BLUE + "\nAvailable Tasks:", file=sys.stderr)
    #     for task_id, variants in available_tasks.items():
    #         if variants:
    #             print(f"  - {task_id} (variants: {', '.join(variants)})", file=sys.stderr)
    #         else:
    #             print(f"  - {task_id}", file=sys.stderr)
    #     print(Style.BRIGHT + Fore.BLUE + "\nAvailable Models (based on your .env keys):", file=sys.stderr)
    #     for model in available_models: print(f"  - {model}", file=sys.stderr)
    #     sys.exit(0)

    # ---Robust Error Handling ---
    if not available_tasks:
        print(
            Style.BRIGHT + Fore.RED + "\nError: No task directories found in the 'tasks/' folder.",
            file=sys.stderr,
        )
        sys.exit(1)
    if not available_models:
        print(
            Style.BRIGHT
            + Fore.RED
            + "\nError: No models could be discovered. Check your .env file and API keys.",
            file=sys.stderr,
        )
        sys.exit(1)

    # ---Determine tasks and models to run ---
    if args.non_interactive:
        if not args.tasks or not args.models:
            print(
                Style.BRIGHT
                + Fore.RED
                + "Error: In non-interactive mode (-y), you must specify which tasks and models to run.",
                file=sys.stderr,
            )
            print(
                Fore.YELLOW + "Use --tasks <task1> ... and --models <model1> ...", file=sys.stderr
            )
            print(Fore.YELLOW + "Use --list to see available options.", file=sys.stderr)
            sys.exit(1)
        tasks_to_run = args.tasks
        models_to_run = args.models
        is_verbose = args.verbose
    else:
        # Interactive Mode
        print(
            Style.BRIGHT + Fore.GREEN + "\nWelcome to the SecureDev-Bench Interactive CLI!",
            file=sys.stderr,
        )
        models_to_run = questionary.checkbox(
            "Which models would you like to test?", choices=available_models
        ).ask()
        if not models_to_run:
            sys.exit(0)

        # Build task choices with variants
        task_choices = []
        for task_id, variants in available_tasks.items():
            if variants:
                # Task has variants - add each variant as a choice
                for variant in variants:
                    task_choices.append(f"{task_id}/{variant}")
            else:
                # Standard task - add as-is
                task_choices.append(task_id)

        tasks_to_run = questionary.checkbox(
            "Which tasks would you like to run?", choices=task_choices
        ).ask()
        if not tasks_to_run:
            sys.exit(0)
        is_verbose = questionary.confirm("Enable verbose (real-time) logging?", default=False).ask()
        # New interactive toggles
        # Only ask about keeping temporary directories when tasks were cloned (remote source).
        keep_temp_choice = False
        if tasks_source_is_remote:
            keep_temp_choice = questionary.confirm(
                "Keep temporary directories after each run?", default=False
            ).ask()
        save_artifacts_choice = questionary.confirm(
            "Save artifacts (modified app.py and report.json)?", default=True
        ).ask()
        artifacts_dir_choice = None
        if save_artifacts_choice:
            artifacts_dir_choice = questionary.text(
                "Artifacts output directory:", default="artifacts"
            ).ask()

    # ---The Main Execution Loop ---
    all_results = []
    start_time = time.time()
    print(
        Style.BRIGHT
        + Fore.BLUE
        + f"\nStarting benchmark for {len(models_to_run)} model(s) against {len(tasks_to_run)} task(s)...",
        file=sys.stderr,
    )
    for model_spec in models_to_run:
        provider, model = model_spec.split(":")
        if not is_verbose:
            print(Fore.YELLOW + f"  - Testing model: {model_spec}", file=sys.stderr)
        for task in tasks_to_run:
            # Parse task specification (may include variant)
            if "/" in task:
                task_id, variant = task.split("/", 1)
            else:
                task_id, variant = task, None

            result_data = run_task(
                task_id,
                provider,
                model,
                verbose=is_verbose,
                keep_temp=(args.keep_temp if args.non_interactive else keep_temp_choice),
                artifacts_dir=(
                    args.artifacts_dir
                    if args.non_interactive
                    else (artifacts_dir_choice or "artifacts")
                ),
                save_artifacts=(
                    False
                    if args.no_artifacts
                    else (save_artifacts_choice if not args.non_interactive else True)
                ),
                variant=variant,
                tasks_root=tasks_root,  # Pass tasks_root to the runner
            )
            all_results.append(result_data)
    total_duration = time.time() - start_time
    print(
        Fore.GREEN + f"\n✅ Benchmark complete. Total duration: {total_duration:.2f}s",
        file=sys.stderr,
    )

    # ---Final Reporting ---
    markdown_report_for_console = save_reports(all_results)
    print(Style.BRIGHT + Fore.BLUE + "\n--- Benchmark Summary ---", file=sys.stderr)
    # The final report to stdout is now colored for the console
    print(markdown_report_for_console)

    # ---Cleanup cloned tasks repo, if any---
    if cloned_tasks_dir and not args.keep_temp:
        shutil.rmtree(cloned_tasks_dir, ignore_errors=True)
