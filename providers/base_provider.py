from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """Abstract base class for all AI model providers."""

    def __init__(self, api_key: str, model_name: str = None):
        if not api_key:
            raise ValueError(f"{self.__class__.__name__} requires an API key.")
        self.api_key = api_key
        self.model_name = model_name

    @abstractmethod
    def fix_code(self, vulnerable_code: str) -> str:
        """Takes a string of vulnerable code and returns the fixed code."""
        pass

    @staticmethod
    @abstractmethod
    def list_models(api_key: str) -> list[str]:
        """
        A static method that connects to the provider's API and returns a list
        of available model names that are suitable for code generation.
        """
        pass
