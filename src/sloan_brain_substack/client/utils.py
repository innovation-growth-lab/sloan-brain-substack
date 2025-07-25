"""Utility functions for the Substack API client."""

from typing import Any

import requests

from .constants import DEFAULT_HEADERS, DEFAULT_TIMEOUT


def make_request(
    url: str, headers: dict[str, str] = None, timeout: int = DEFAULT_TIMEOUT, **kwargs: Any
) -> requests.Response:
    """Make a standardized GET request.

    Args:
        url: The URL to request
        headers: Optional custom headers (will be merged with defaults)
        timeout: Request timeout in seconds
        **kwargs: Additional arguments to pass to requests.get

    Returns:
        requests.Response: The response object

    Raises:
        requests.HTTPError: If the request was unsuccessful
    """
    request_headers = DEFAULT_HEADERS.copy()
    if headers:
        request_headers.update(headers)

    response = requests.get(url, headers=request_headers, timeout=timeout, **kwargs)
    response.raise_for_status()
    return response


def extract_subdomain_url(subdomain: str, domain: str = "substack.com") -> str:
    """Extract a full URL from a subdomain.

    Args:
        subdomain: The subdomain part
        domain: The base domain (defaults to substack.com)

    Returns:
        Full URL string
    """
    return f"https://{subdomain}.{domain}"
