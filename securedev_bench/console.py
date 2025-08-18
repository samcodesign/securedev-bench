import logging
import sys
from typing import Any

from colorama import Fore, Style
from colorama import init as colorama_init


def init_console():
    """Initialize colorama and basic logging configuration."""
    colorama_init(autoreset=True)
    # Basic logger to stderr
    logger = logging.getLogger("securedev_bench")
    if not logger.handlers:
        handler = logging.StreamHandler(stream=sys.stderr)
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def _logger():
    return logging.getLogger("securedev_bench")


def banner():
    """Print the ASCII banner to stderr."""
    try:
        # Import pyfiglet lazily to avoid heavy import at module load
        from pyfiglet import Figlet

        f = Figlet(font="ANSI_Shadow")
        b = f.renderText("SecureDev")
        _logger().info(Style.BRIGHT + Fore.MAGENTA + b)
    except Exception:
        _logger().info(Style.BRIGHT + Fore.MAGENTA + "SecureDev")
    _logger().info(Fore.YELLOW + "A benchmark for the modern AI security agent.")
    _logger().info(Fore.CYAN + "Initializing SecureDev-Bench CLI...")


def info(msg: Any):
    _logger().info(msg)


def success(msg: Any):
    _logger().info(Fore.GREEN + str(msg))


def warn(msg: Any):
    _logger().warning(Fore.YELLOW + str(msg))


def error(msg: Any):
    _logger().error(Fore.RED + str(msg))


def debug(msg: Any):
    _logger().debug(str(msg))


def set_level(level: int):
    """Set the logger level for the console logger."""
    _logger().setLevel(level)


def set_verbose():
    """Convenience helper to set logger to DEBUG."""
    set_level(logging.DEBUG)


def is_verbose() -> bool:
    """Return True if console logger is at DEBUG level or lower."""
    return _logger().isEnabledFor(logging.DEBUG)
