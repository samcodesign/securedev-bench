import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from providers.gemini_provider import GeminiProvider

# from providers.openai_provider import OpenAIProvider

# Load environment variables from .env
load_dotenv()

SUPPORTED_PROVIDERS = {
    "gemini": GeminiProvider,
    # "openai": OpenAIProvider,
}


def get_api_key(provider_name: str) -> str:
    env_var_name = f"{provider_name.upper()}_API_KEY"
    api_key = os.environ.get(env_var_name)
    if not api_key:
        raise ValueError(f"API key not found. Please set {env_var_name} in your .env file.")
    return api_key


def main():
    parser = argparse.ArgumentParser(description="AI Security Agent")
    parser.add_argument("file_path", type=str, help="Path to the Python file to fix.")
    parser.add_argument(
        "--provider", type=str, default="gemini", choices=SUPPORTED_PROVIDERS.keys()
    )
    # --- NEW: Add an argument for the specific model name ---
    parser.add_argument(
        "--model", type=str, default=None, help="The specific model to use (e.g., gemini-1.5-pro)."
    )
    args = parser.parse_args()

    print(f"[Agent]: Using provider: {args.provider}, Model: {args.model or 'default'}")

    try:
        provider_class = SUPPORTED_PROVIDERS[args.provider]
        api_key = get_api_key(args.provider)

        # --- NEW: Pass the model name to the provider's constructor ---
        provider = provider_class(api_key=api_key, model_name=args.model)

        file_path = Path(args.file_path)
        vulnerable_code = file_path.read_text()
        corrected_code = provider.fix_code(vulnerable_code)

        print("[Agent]: Overwriting file with corrected code...")
        file_path.write_text(corrected_code)
        print("[Agent]: Fix complete.")

    except Exception as e:
        print(f"[Agent]: A critical error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
