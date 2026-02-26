import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=_ENV_PATH)


def _str(key: str, default: str) -> str:
    return (os.getenv(key) or default).strip()


def _int(key: str, default: int) -> int:
    return int(_str(key, str(default)) or str(default))


def _bool(key: str, default: bool) -> bool:
    raw = _str(key, str(default)).lower()
    return raw in ("1", "true", "yes", "on")


def _path_from_root(key: str, default: str) -> str:
    """Resolve path relative to project root so 'data/listings.txt' works from any cwd."""
    raw = _str(key, default)
    path = Path(raw)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return str(path.resolve())


# Pipeline
LISTINGS_FILE = _path_from_root("LISTINGS_FILE", "data/listings.txt")
LISTINGS_FILE_TEST = _path_from_root("LISTINGS_FILE_TEST", "data/listings_test.txt")
OUTPUT_FILE = _path_from_root("OUTPUT_FILE", "data/output.csv")
MAX_WORKERS = max(1, _int("MAX_WORKERS", 4))

# Extract: request and retries
REQUEST_TIMEOUT = _int("REQUEST_TIMEOUT", 30000)
MAX_RETRIES = _int("MAX_RETRIES", 3)
RETRY_WAIT_SECONDS = _int("RETRY_WAIT_SECONDS", 2)
PAGE_WAIT_MS = _int("PAGE_WAIT_MS", 3000)

USER_AGENT = _str(
    "USER_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
)
VIEWPORT_WIDTH = _int("VIEWPORT_WIDTH", 1920)
VIEWPORT_HEIGHT = _int("VIEWPORT_HEIGHT", 1080)
LOCALE = _str("LOCALE", "es-ES")
