import os
import shutil
import subprocess
import sys
import tempfile
from typing import Optional

from colorama import Fore, Style

from .console import error, info


def clone_tasks_repo(repo_url: str, ref: Optional[str] = None) -> str:
    """Clone a tasks repository to a temporary directory and return the path.

    Raises subprocess.CalledProcessError on failure.
    """
    cloned_dir = tempfile.mkdtemp(prefix="sdb_tasks_")
    clone_cmd = ["git", "clone", "--depth", "1"]
    if ref:
        clone_cmd += ["-b", ref]
    gh_token = os.environ.get("GH_TOKEN") or os.environ.get("TASKS_GIT_TOKEN")
    repo = repo_url
    if gh_token and repo.startswith("https://") and "@" not in repo.split("//", 1)[1]:
        proto, rest = repo.split("//", 1)
        repo = f"{proto}//{gh_token}@{rest}"
    clone_cmd += [repo, cloned_dir]
    from .console import is_verbose

    if is_verbose():
        subprocess.run(clone_cmd, check=True, text=True)
    else:
        subprocess.run(clone_cmd, check=True, capture_output=True, text=True)
    return cloned_dir


def prepare_tasks_source(args) -> tuple[str, Optional[str], bool]:
    """Return (tasks_root, cloned_tasks_dir, tasks_source_is_remote).

    Handles interactive prompts for choosing a source and cloning if necessary.
    """
    cloned_tasks_dir = None
    tasks_root = args.tasks_dir
    tasks_source_is_remote = False

    # Interactive selection of source
    if not args.non_interactive and not args.tasks_repo and args.tasks_dir == "tasks":
        q = __import__("questionary")
        source_choice = q.select(
            "Select tasks source",
            choices=[
                "Use local 'tasks' directory",
                "Specify local directory path",
                "Clone tasks repository (Git URL)",
            ],
        ).ask()

        if source_choice == "Specify local directory path":
            custom_dir = q.text("Enter path to tasks directory:", default="tasks").ask()
            tasks_root = custom_dir or "tasks"

        elif source_choice == "Clone tasks repository (Git URL)":
            repo_input = q.text("Enter Git URL (SSH or HTTPS):").ask()
            ref_input = q.text("Optional branch or tag (press Enter to skip):", default="").ask()
            if repo_input:
                try:
                    info(Fore.CYAN + "Cloning tasks repository...")
                    cloned_tasks_dir = clone_tasks_repo(repo_input, ref_input or None)
                    tasks_root = cloned_tasks_dir
                    tasks_source_is_remote = True
                except subprocess.CalledProcessError as e:
                    error(Style.BRIGHT + Fore.RED + "\nError: Failed to clone tasks repository.")
                    err_out = e.stderr or e.stdout or str(e)
                    error(Fore.RED + err_out)
                    if cloned_tasks_dir and os.path.isdir(cloned_tasks_dir):
                        shutil.rmtree(cloned_tasks_dir, ignore_errors=True)
                    sys.exit(1)

    # Non-interactive or explicit cloning
    if args.tasks_repo and (args.non_interactive or tasks_root == args.tasks_dir):
        try:
            info(Fore.CYAN + "Cloning tasks repository...")
            cloned_tasks_dir = clone_tasks_repo(args.tasks_repo, args.tasks_ref)
            tasks_root = cloned_tasks_dir
            tasks_source_is_remote = True
        except subprocess.CalledProcessError as e:
            error(Style.BRIGHT + Fore.RED + "\nError: Failed to clone tasks repository.")
            err_out = e.stderr or e.stdout or str(e)
            error(Fore.RED + err_out)
            if cloned_tasks_dir and os.path.isdir(cloned_tasks_dir):
                shutil.rmtree(cloned_tasks_dir, ignore_errors=True)
            sys.exit(1)

    return tasks_root, cloned_tasks_dir, tasks_source_is_remote
