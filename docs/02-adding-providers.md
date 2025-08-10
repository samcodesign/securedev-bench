# How to Add a New AI Provider

Integrating new AI models is crucial for making SecureDev Benchmark a comprehensive comparison/Benchmarking tool. The platform is designed to be easily extensible.

## 1. Create the Provider Module

In the `providers/` directory, create a new file named after your provider (e.g., `openai_provider.py`).

## 2. Implement the `BaseProvider` Interface

Your new provider class must inherit from `BaseProvider` (found in `providers/base_provider.py`). This is a contract that guarantees your provider will work with the benchmark engine.

You must implement two methods:

1. **`fix_code(self, vulnerable_code: str) -> str`**
    * This method receives the vulnerable code as a string.
    * It should connect to the provider's API, send the code for analysis, and get the proposed fix.
    * It must return the complete, corrected code as a string.
    * Crucially, it should include robust error handling. If the API call fails, it should `raise` the exception to stop the benchmark run with a clear error.

2. **`list_models(api_key: str) -> list[str]`**
    * This is a `staticmethod`.
    * It receives the relevant API key.
    * It should connect to the provider's API and query for a list of available models suitable for code generation.
    * It must return a list of model name strings (e.g., `['gpt-4-turbo', 'gpt-3.5-turbo']`).

## 3. Add a `.env` Variable

The benchmark automatically looks for API keys in the `.env` file using the pattern `PROVIDERNAME_API_KEY`. For an `OpenAIProvider`, it will look for `OPENAI_API_KEY`. Please document this in the main `README.md` and `.env.example`.

## 4. Submit a Pull Request

After implementing and testing your provider, open a pull request. We look forward to expanding the roster of testable models!
