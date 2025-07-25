from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from .auth import Auth
from .constants import DEFAULT_HEADERS, DEFAULT_TIMEOUT


class Post:
    """A Substack post."""

    def __init__(self, url: str, auth: Auth = None) -> None:
        """Create a Post object.

        Args:
            url: The URL of the Substack post
            auth: Authentication handler for accessing paywalled content

        """
        self.url = url
        self.auth = auth
        parsed_url = urlparse(url)
        self.base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        path_parts = parsed_url.path.strip("/").split("/")
        # The slug is typically the last part of the path in Substack URLs
        self.slug = path_parts[-1] if path_parts else None

        self.endpoint = f"{self.base_url}/api/v1/posts/{self.slug}"
        self._post_data = None  # Cache for post data

    def __str__(self) -> str:
        """Return a string representation of the post."""
        return f"Post: {self.url}"

    def __repr__(self) -> str:
        """Return a string representation of the post."""
        return f"Post(url={self.url})"

    def _fetch_post_data(self, force_refresh: bool = False) -> dict[str, Any]:
        """Fetch the raw post data from the API and cache it.

        Args:
            force_refresh: Whether to force a refresh of the data, ignoring the cache

        Returns:
            dict[str, Any]: Full post metadata

        """
        if self._post_data is not None and not force_refresh:
            return self._post_data

        # Use authenticated session if available
        if self.auth and self.auth.authenticated:
            r = self.auth.get(self.endpoint, timeout=30)
        else:
            r = requests.get(self.endpoint, headers=DEFAULT_HEADERS, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()

        self._post_data = r.json()
        return self._post_data

    def get_metadata(self, force_refresh: bool = False) -> dict[str, Any]:
        """Get metadata for the post.

        Args:
            force_refresh: Whether to force a refresh of the data, ignoring the cache

        Returns:
            dict[str, Any]: Full post metadata

        """
        return self._fetch_post_data(force_refresh=force_refresh)

    def get_content(self, force_refresh: bool = False, raw_html: bool = False) -> str | None:
        """Get the content of the post as clean text or raw HTML.

        Args:
            force_refresh: Whether to force a refresh of the data, ignoring the cache
            raw_html: If True, return raw HTML; if False, return clean parsed text

        Returns:
            str | None: Content of the post, or None if not available

        """
        data = self._fetch_post_data(force_refresh=force_refresh)
        html_content = data.get("body_html")

        # Check if content is paywalled and we don't have auth
        if not html_content and data.get("audience") == "only_paid" and not self.auth:
            print("Warning: This post is paywalled. Provide authentication to access full content.")
            return None

        if not html_content:
            return None

        if raw_html:
            return html_content

        # Parse HTML and return clean text
        return self._parse_html_content(html_content)

    def _parse_html_content(self, html_content: str) -> str:
        """Parse HTML content into clean, readable text.

        Args:
            html_content: Raw HTML content

        Returns:
            str: Clean, formatted text

        """
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text and clean it up
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)

        return text

    def is_paywalled(self) -> bool:
        """Check if the post is paywalled.

        Returns:
        bool
            True if post is paywalled
        """
        data = self._fetch_post_data()
        return data.get("audience") == "only_paid"
