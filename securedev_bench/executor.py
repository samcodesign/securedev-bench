import time
from typing import Optional

from colorama import Fore, Style

from .console import info
from .runner import run_task


def execute_benchmark(
    args,
    tasks_root: str,
    tasks_to_run: list[str],
    models_to_run: list[str],
    is_verbose: bool,
    keep_temp_choice: bool,
    save_artifacts_choice: bool,
    artifacts_dir_choice: Optional[str],
) -> tuple[list[dict], float]:
    """Run the benchmark loop and return (all_results, total_duration)."""
    all_results = []
    start_time = time.time()
    info(
        Style.BRIGHT
        + Fore.BLUE
        + f"\nStarting benchmark for {len(models_to_run)} model(s) against {len(tasks_to_run)} task(s)..."
    )
    for model_spec in models_to_run:
        provider, model = model_spec.split(":")
        if not is_verbose:
            info(Fore.YELLOW + f"  - Testing model: {model_spec}")
        for task in tasks_to_run:
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
                tasks_root=tasks_root,
            )
            all_results.append(result_data)

    total_duration = time.time() - start_time
    return all_results, total_duration
