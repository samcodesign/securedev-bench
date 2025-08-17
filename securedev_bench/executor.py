import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    run_in_parallel: bool = False,
    workers: int = 2,
) -> tuple[list[dict], float]:
    """Run the benchmark loop and return (all_results, total_duration).

    If run_in_parallel is True, tasks are dispatched to a ThreadPoolExecutor with the
    requested number of workers. Each (task, model) combination is a unit of work.
    """
    all_results: list[dict] = []
    start_time = time.time()
    info(
        Style.BRIGHT
        + Fore.BLUE
        + f"\nStarting benchmark for {len(models_to_run)} model(s) against {len(tasks_to_run)} task(s)..."
    )

    # Build the list of work units (task_id, variant, provider, model)
    work_units = []
    for model_spec in models_to_run:
        provider, model = model_spec.split(":")
        if not is_verbose:
            info(Fore.YELLOW + f"  - Testing model: {model_spec}")
        for task in tasks_to_run:
            if "/" in task:
                task_id, variant = task.split("/", 1)
            else:
                task_id, variant = task, None
            work_units.append((task_id, variant, provider, model))

    if run_in_parallel and workers > 1:
        info(Fore.CYAN + f"Running in parallel with {workers} workers...")
        with ThreadPoolExecutor(max_workers=workers) as ex:
            future_to_unit = {}
            for unit in work_units:
                task_id, variant, provider, model = unit
                future = ex.submit(
                    run_task,
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
                future_to_unit[future] = unit

            for fut in as_completed(future_to_unit):
                try:
                    res = fut.result()
                except Exception as e:
                    info(Fore.RED + f"Task raised exception: {e}")
                    continue
                all_results.append(res)
    else:
        # Sequential fallback
        for task_id, variant, provider, model in work_units:
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
