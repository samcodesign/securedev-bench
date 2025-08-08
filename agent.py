import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import our new provider classes
from providers.gemini_provider import GeminiProvider
# from providers.openai_provider import OpenAIProvider # You could add this later

# This dictionary makes the agent easily extensible.
# To add a new model, just add it here.
SUPPORTED_PROVIDERS = {
    "gemini": GeminiProvider,
    # "openai": OpenAIProvider,
}

def get_api_key(provider_name: str) -> str:
    """Gets the API key from environment variables based on the provider name."""
    env_var_name = f"{provider_name.upper()}_API_KEY"
    api_key = os.environ.get(env_var_name)
    if not api_key:
        raise ValueError(f"Please set the {env_var_name} environment variable.")
    return api_key

def main():
    """
    Main function to parse arguments, select a provider, and fix code.
    """
    parser = argparse.ArgumentParser(description="AI Security Agent")
    parser.add_argument("file_path", type=str, help="Path to the Python file to fix.")
    parser.add_argument(
        "--provider", 
        type=str, 
        default="gemini", 
        choices=SUPPORTED_PROVIDERS.keys(),
        help="The AI provider to use."
    )
    args = parser.parse_args()

    print(f"[Agent]: Using provider: {args.provider}")
    
    try:
        # 1. Select the provider class from our dictionary
        provider_class = SUPPORTED_PROVIDERS[args.provider]
        
        # 2. Get the correct API key for that provider
        api_key = get_api_key(args.provider)
        
        # 3. Instantiate the provider
        provider = provider_class(api_key=api_key)

        # 4. Read the vulnerable code
        file_path = Path(args.file_path)
        vulnerable_code = file_path.read_text()

        # 5. Ask the provider to fix the code
        corrected_code = provider.fix_code(vulnerable_code)

        # 6. Write the fix back to the file
        print(f"[Agent]: Overwriting file with corrected code from {args.provider}...")
        file_path.write_text(corrected_code)
        print("[Agent]: Fix complete.")

    except Exception as e:
        print(f"[Agent]: A critical error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()