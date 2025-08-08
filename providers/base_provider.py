from abc import ABC, abstractmethod

class BaseProvider(ABC):
    """
    Abstract base class for all AI model providers.
    It ensures that every provider has a 'fix_code' method.
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError(f"{self.__class__.__name__} requires an API key.")
        self.api_key = api_key

    @abstractmethod
    def fix_code(self, vulnerable_code: str) -> str:
        """
        Takes a string of vulnerable code and returns the fixed code.
        This method must be implemented by all subclasses.
        """
        pass