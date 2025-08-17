import importlib
import os
import pkgutil
from pathlib import Path

from providers.base_provider import BaseProvider  # <--- FIX 1: Import the class directly

from .console import info, warn


def discover_tasks(tasks_dir="tasks"):
    """
    Finds all valid task directories and their variants.

    Returns a dict where:
    - Keys are task IDs (e.g., 'task-001-hardcoded-key')
    - Values are lists of variant paths (e.g., ['var-01', 'var-02'] or [] if no variants)
    """
    # Accept either a direct tasks directory, or a repo root that contains a `tasks/` folder.
    path = Path(tasks_dir)
    if path.is_dir() and (path / "tasks").is_dir():
        path = path / "tasks"

    if not path.is_dir():
        return {}

    tasks = {}
    for d in os.listdir(path):
        task_path = path / d
        if not task_path.is_dir() or not d.startswith("task-"):
            continue

        # Check if this task has variants
        variants = []
        for subdir in task_path.iterdir():
            if subdir.is_dir() and subdir.name.startswith("var-"):
                variants.append(subdir.name)

        # If no variants found, this is a standard task (empty list)
        # If variants found, this is a variant-based task
        tasks[d] = sorted(variants) if variants else []

    return tasks


def get_task_path(task_id: str, variant: str = None, tasks_dir: str = "tasks") -> Path:
    """
    Gets the full path to a task or task variant.

    Args:
        task_id: The task directory name (e.g., 'task-001-hardcoded-key')
        variant: The variant name (e.g., 'var-01') or None for standard tasks
        tasks_dir: Root tasks directory

    Returns:
        Path to the task directory (with variant if specified)
    """
    # Handle case where caller passed a repository root that contains a `tasks/` folder
    path = Path(tasks_dir)
    if path.is_dir() and (path / "tasks").is_dir():
        path = path / "tasks"

    if variant:
        return path / task_id / variant
    return path / task_id


def discover_providers():
    """Dynamically imports all provider classes."""
    import providers

    provider_modules = pkgutil.iter_modules(providers.__path__, providers.__name__ + ".")
    provider_classes = {}
    for _, module_name, _ in provider_modules:
        module = importlib.import_module(module_name)
        for attribute_name in dir(module):
            attribute = getattr(module, attribute_name)
            # --- FIX 2: Use the directly imported BaseProvider class ---
            if (
                isinstance(attribute, type)
                and issubclass(attribute, BaseProvider)
                and attribute is not BaseProvider
            ):
                provider_name = attribute.__name__.replace("Provider", "").lower()
                provider_classes[provider_name] = attribute
    return provider_classes


def discover_models(provider_classes: dict, timeout_seconds: int = 10):
    """Checks API keys and asks each provider to list its available models.

    Each provider's `list_models` call is executed with a timeout to avoid hangs
    when a remote API is slow or unreachable. On timeout or error we skip that
    provider and continue.
    """
    from concurrent.futures import ThreadPoolExecutor, TimeoutError

    available_models = []
    for name, provider_class in provider_classes.items():
        api_key_env = f"{name.upper()}_API_KEY"
        api_key = os.environ.get(api_key_env)
        if not api_key:
            continue
        info(f"[Discovery]: Found API key for {name.upper()}, fetching models...")
        try:
            with ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(provider_class.list_models, api_key)
                models = fut.result(timeout=timeout_seconds)
        except TimeoutError:
            warn(f"Timeout while fetching models for provider {name}. Skipping.")
            models = []
        except Exception as e:
            warn(f"Failed to fetch models for provider {name}: {e}")
            models = []

        for model in models or []:
            available_models.append(f"{name}:{model}")

    return available_models
