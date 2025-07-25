"""Constants used across the Substack API client."""

# API Base URLs
SUBSTACK_BASE_URL = "https://substack.com"
SUBSTACK_API_BASE = f"{SUBSTACK_BASE_URL}/api/v1"

# Standard headers for all requests
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

# Request timeouts (in seconds)
DEFAULT_TIMEOUT = 30

# Substack domain pattern
SUBSTACK_DOMAIN = "substack.com"
