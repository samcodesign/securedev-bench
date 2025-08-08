import os
import importlib
import pkgutil
from pathlib import Path
from providers.base_provider import BaseProvider # <--- FIX 1: Import the class directly

def discover_tasks(tasks_dir="tasks"):
    """Finds all valid task directories."""
    if not os.path.isdir(tasks_dir):
        return []
    return sorted([d for d in os.listdir(tasks_dir) if os.path.isdir(Path(tasks_dir) / d) and d.startswith('task-')])

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
            if isinstance(attribute, type) and issubclass(attribute, BaseProvider) and attribute is not BaseProvider:
                provider_name = attribute.__name__.replace("Provider", "").lower()
                provider_classes[provider_name] = attribute
    return provider_classes

def discover_models(provider_classes: dict):
    """Checks API keys and asks each provider to list its available models."""
    available_models = []
    for name, provider_class in provider_classes.items():
        api_key_env = f"{name.upper()}_API_KEY"
        api_key = os.environ.get(api_key_env)
        if api_key:
            print(f"[Discovery]: Found API key for {name.upper()}, fetching models...")
            models = provider_class.list_models(api_key)
            for model in models:
                available_models.append(f"{name}:{model}")
    return available_models