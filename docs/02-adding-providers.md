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

## Implementation details and conventions

To keep integrations consistent and discoverable by the benchmark, follow these conventions:

* Environment variable naming: use the provider's uppercase short name with `_API_KEY`. Examples:

```bash
GEMINI_API_KEY=xxxxx
OPENAI_API_KEY=xxxxx
```

* `list_models` contract: this should be a `@staticmethod` that accepts the API key and returns a list of model-name strings. The discovery code in the benchmark expects model names to be plain strings; when surfaced to the CLI they are shown as `provider:model_name` (the benchmark prefixes the provider name during discovery). Example signature:

```python
class ExampleProvider(BaseProvider):
    @staticmethod
    def list_models(api_key: str) -> list[str]:
        # return a list of model name strings, e.g. ['gpt-4', 'gpt-3.5']
        ...
```

* Minimal unit-test pattern: provide a small test that mocks network calls. This lets CI validate discovery without real keys.

```python
def test_list_models_monkeypatch(monkeypatch):
    # example: patch requests or the provider API client used by your provider
    monkeypatch.setattr(MyProviderClient, 'fetch_models', lambda key: ['m1', 'm2'])
    models = ExampleProvider.list_models('fake-key')
    assert models == ['m1', 'm2']
```

Update `.env.example` and `README.md` to show the expected variable names for your provider.
