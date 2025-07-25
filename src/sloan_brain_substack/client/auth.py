import json
import os
from typing import Any

import requests

from .constants import DEFAULT_HEADERS


class Auth:
    """Handles authentication for Substack API requests."""

    def __init__(
        self,
        cookies_path: str,
    ) -> None:
        """Start a session with Substack.

        Args:
            cookies_path: Path to retrieve session cookies from

        """
        self.cookies_path = cookies_path
        self.session = requests.Session()
        self.authenticated = False

        # Set default headers
        self.session.headers.update(DEFAULT_HEADERS)
        self.session.headers.update({"Content-Type": "application/json"})

        # Try to load existing cookies
        if os.path.exists(self.cookies_path):
            self.load_cookies()
            self.authenticated = True
        else:
            print(f"Cookies file not found at {self.cookies_path}. Please log in.")
            self.authenticated = False
            self.session.cookies.clear()

    def load_cookies(self) -> bool:
        """Load cookies from file.

        Returns:
            True if cookies loaded successfully

        """
        try:
            with open(self.cookies_path, "r") as f:
                cookies = json.load(f)

            for cookie in cookies:
                self.session.cookies.set(
                    cookie["name"],
                    cookie["value"],
                    domain=cookie.get("domain"),
                    path=cookie.get("path", "/"),
                    secure=cookie.get("secure", False),
                )

            return True

        except Exception as e:
            print(f"Failed to load cookies: {str(e)}")
            return False

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        """Make a GET request. Optionally pass additional arguments to requests.get.

        Args:
            url: URL to request
            **kwargs: Additional arguments to pass to requests.get

        Returns:
            requests.Response: Response object

        """
        return self.session.get(url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        """Make a POST request. Optionally pass additional arguments to requests.post.

        Args:
            url: URL to request
            **kwargs: Additional arguments to pass to requests.post

        Returns:
            requests.Response: Response object

        """
        return self.session.post(url, **kwargs)
