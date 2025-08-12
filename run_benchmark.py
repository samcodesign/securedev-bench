#!/usr/bin/env python
import sys

from dotenv import load_dotenv

from securedev_bench.cli import main

if __name__ == "__main__":
    # Load environment variables from .env file at the very start
    load_dotenv()

    # Call the main function from our CLI module
    try:
        main()
    except KeyboardInterrupt:
        # Handle user cancellation gracefully
        print("\nBenchmark run cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        sys.exit(1)
