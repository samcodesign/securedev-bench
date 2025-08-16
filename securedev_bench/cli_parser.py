import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Optional

import questionary
from colorama import Fore, Style

from .console import error, info
from .discovery import discover_models, discover_providers, discover_tasks


def interactive_selection(
    args: argparse.Namespace,
    available_tasks: dict[str, list[str]],
    available_models: list[str],
    tasks_source_is_remote: bool,
) -> tuple[list[str], list[str], bool, bool, bool, Optional[str]]:
    """Decide tasks/models to run and interactive toggles; returns selections.

    Returns: (tasks_to_run, models_to_run, is_verbose, keep_temp_choice, save_artifacts_choice, artifacts_dir_choice)
    """
    if args.non_interactive:
        if not args.tasks or not args.models:
            info(
                Style.BRIGHT
                + Fore.RED
                + "Error: In non-interactive mode (-y), you must specify which tasks and models to run."
            )
            info(Fore.YELLOW + "Use --tasks <task1> ... and --models <model1> ...")
            info(Fore.YELLOW + "Use --list to see available options.")
            sys.exit(1)
        return args.tasks, args.models, args.verbose, False, False, None

    # Interactive mode
    info(Style.BRIGHT + Fore.GREEN + "\nWelcome to the SecureDev-Bench Interactive CLI!")
    models_to_run = questionary.checkbox(
        "Which models would you like to test?", choices=available_models
    ).ask()
    if not models_to_run:
        sys.exit(0)

    # Build task choices with variants
    task_choices = []
    for task_id, variants in available_tasks.items():
        if variants:
            for variant in variants:
                task_choices.append(f"{task_id}/{variant}")
        else:
            task_choices.append(task_id)

    tasks_to_run = questionary.checkbox(
        "Which tasks would you like to run?", choices=task_choices
    ).ask()
    if not tasks_to_run:
        sys.exit(0)

    is_verbose = questionary.confirm("Enable verbose (real-time) logging?", default=False).ask()

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

    return (
        tasks_to_run,
        models_to_run,
        is_verbose,
        keep_temp_choice,
        save_artifacts_choice,
        artifacts_dir_choice,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
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
        "--list-models", action="store_true", help="list all available models and exit."
    )
    info_group.add_argument(
        "--list-task-repo",
        help="list tasks from a private repository and exit. Use with --tasks-ref for specific branch.",
    )
    info_group.add_argument(
        "--list-task-dir",
        nargs="?",
        const="tasks",
        help="list tasks from a local directory and exit (default: tasks).",
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

    return parser


def handle_informational_flags(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    """Handle early informational flags that may exit the program.

    This function mirrors the previous inline handling of --help, --list-models,
    --list-task-repo and --list-task-dir.
    """
    if args.help:
        parser.print_help(sys.stderr)
        sys.exit(0)

    if args.list_models:
        provider_classes = discover_providers()
        available_models = discover_models(provider_classes)

        info(Style.BRIGHT + Fore.BLUE + "\nAvailable Models (based on your .env keys):")
        for model in available_models:
            info(f"  - {model}")
        sys.exit(0)

    if args.list_task_repo:
        # list tasks from a private repository
        if not args.tasks_ref:
            info(Fore.YELLOW + "Note: No --tasks-ref specified, using default branch.")
        list_cloned_dir = None
        try:
            info(Fore.CYAN + "Cloning tasks repository...")
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
            # Show subprocess output if console is verbose, otherwise capture it
            from .console import is_verbose

            if is_verbose():
                subprocess.run(clone_cmd, check=True, text=True)
            else:
                subprocess.run(clone_cmd, check=True, capture_output=True, text=True)

            available_tasks = discover_tasks(list_cloned_dir)

            info(Style.BRIGHT + Fore.BLUE + f"\nAvailable Tasks from {args.list_task_repo}:")
            for task_id, variants in available_tasks.items():
                if variants:
                    info(f"  - {task_id} (variants: {', '.join(variants)})")
                else:
                    info(f"  - {task_id}")

            shutil.rmtree(list_cloned_dir, ignore_errors=True)
            sys.exit(0)
        except subprocess.CalledProcessError as e:
            error(
                Style.BRIGHT + Fore.RED + "\nError: Failed to clone tasks repository for listing."
            )
            err_out = e.stderr or e.stdout or str(e)
            error(Fore.RED + err_out)
            if list_cloned_dir and os.path.isdir(list_cloned_dir):
                shutil.rmtree(list_cloned_dir, ignore_errors=True)
            sys.exit(1)
        except Exception as e:
            error(Style.BRIGHT + Fore.RED + f"\nUnexpected error during task discovery: {e}")
            if list_cloned_dir and os.path.isdir(list_cloned_dir):
                shutil.rmtree(list_cloned_dir, ignore_errors=True)
            sys.exit(1)

    if args.list_task_dir:
        tasks_dir = args.list_task_dir or "tasks"
        available_tasks = discover_tasks(tasks_dir)

        info(Style.BRIGHT + Fore.BLUE + f"\nAvailable Tasks from '{tasks_dir}':")
        for task_id, variants in available_tasks.items():
            if variants:
                info(f"  - {task_id} (variants: {', '.join(variants)})")
            else:
                info(f"  - {task_id}")
        sys.exit(0)
