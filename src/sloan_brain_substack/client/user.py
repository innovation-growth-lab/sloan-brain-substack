import logging
from typing import Any
from urllib.parse import urlparse

import requests

from .constants import DEFAULT_HEADERS, DEFAULT_TIMEOUT, SUBSTACK_BASE_URL, SUBSTACK_DOMAIN

# Setup logger
logger = logging.getLogger(__name__)


def resolve_handle_redirect(old_handle: str, timeout: int = DEFAULT_TIMEOUT) -> str | None:
    """Resolve a potentially renamed Substack handle by following redirects.

    Args:
        old_handle: The original handle that may have been renamed
        timeout: Request timeout in seconds

    Returns:
        The new handle if renamed, None if no redirect or on error

    """
    try:
        # Make request to the public profile page with redirects enabled
        response = requests.get(
            f"{SUBSTACK_BASE_URL}/@{old_handle}",
            headers=DEFAULT_HEADERS,
            timeout=timeout,
            allow_redirects=True,
        )

        # If we got a successful response, check if we were redirected
        if response.status_code == 200:
            # Parse the final URL to extract the handle
            parsed_url = urlparse(response.url)
            path_parts = parsed_url.path.strip("/").split("/")

            # Check if this is a profile URL (starts with @)
            if path_parts and path_parts[0].startswith("@"):
                new_handle = path_parts[0][1:]  # Remove the @ prefix

                # Only return if it's actually different
                if new_handle and new_handle != old_handle:
                    logger.info(f"Handle redirect detected: {old_handle} -> {new_handle}")
                    return new_handle

        return None

    except requests.RequestException as e:
        logger.debug(f"Error resolving handle redirect for {old_handle}: {e}")
        return None


class User:
    """User class for interacting with Substack user profiles."""

    def __init__(self, username: str, follow_redirects: bool = True) -> None:
        """Create a User object.

        Args:
            username: The Substack username
            follow_redirects: Whether to follow redirects when a handle has been renamed (default: True)

        """
        self.username = username
        self.original_username = username  # Keep track of the original
        self.follow_redirects = follow_redirects
        self.endpoint = f"{SUBSTACK_BASE_URL}/api/v1/user/{username}/public_profile"
        self._user_data = None  # Cache for user data
        self._redirect_attempted = False  # Prevent infinite redirect loops

    def __str__(self) -> str:
        """Return a string representation of the user."""
        return f"User: {self.username}"

    def __repr__(self) -> str:
        """Return a string representation of the user."""
        return f"User(username={self.username})"

    def _update_handle(self, new_handle: str) -> None:
        """Update the user's handle and endpoint."""
        logger.info(f"Updating handle from {self.username} to {new_handle}")
        self.username = new_handle
        self.endpoint = f"{SUBSTACK_BASE_URL}/api/v1/user/{new_handle}/public_profile"

    def _fetch_user_data(self, force_refresh: bool = False) -> dict[str, Any]:
        """Fetch the raw user data from the API and cache it.

        Handles renamed accounts by following redirects when follow_redirects is True.

        Args:
            force_refresh: Whether to force a refresh of the data, ignoring the cache

        Returns:
            dict[str, Any]: Full user profile data

        Raises:
            requests.HTTPError: If the user cannot be found even after redirect attempts
        """
        if self._user_data is not None and not force_refresh:
            return self._user_data

        try:
            r = requests.get(self.endpoint, headers=DEFAULT_HEADERS, timeout=DEFAULT_TIMEOUT)
            r.raise_for_status()
            self._user_data = r.json()
            return self._user_data

        except requests.HTTPError as e:
            # Handle 404 errors if we should follow redirects
            if e.response.status_code == 404 and self.follow_redirects and not self._redirect_attempted:
                # Mark that we've attempted a redirect to prevent loops
                self._redirect_attempted = True

                # Try to resolve the redirect
                new_handle = resolve_handle_redirect(self.username)

                if new_handle:
                    # Update our state with the new handle
                    self._update_handle(new_handle)

                    # Try the request again with the new handle
                    try:
                        r = requests.get(self.endpoint, headers=DEFAULT_HEADERS, timeout=DEFAULT_TIMEOUT)
                        r.raise_for_status()
                        self._user_data = r.json()
                        return self._user_data
                    except requests.HTTPError:
                        # If it still fails, log and re-raise
                        logger.error(f"Failed to fetch user data even after redirect to {new_handle}")
                        raise
                else:
                    # No redirect found, this is a real 404
                    logger.debug(f"No redirect found for {self.username}, user may be deleted")

            # Re-raise the original error
            raise

    def get_raw_data(self, force_refresh: bool = False) -> dict[str, Any]:
        """Get the complete raw user data.

        Args:
            force_refresh: Whether to force a refresh of the data, ignoring the cache

        Returns:
            dict[str, Any]: Full user profile data

        """
        return self._fetch_user_data(force_refresh=force_refresh)

    @property
    def id(self) -> int:
        """Get the user's unique ID number.

        Returns:
            int: The user's ID

        """
        data = self._fetch_user_data()
        return data["id"]

    @property
    def name(self) -> str:
        """Get the user's name.

        Returns:
            str: The user's name

        """
        data = self._fetch_user_data()
        return data["name"]

    @property
    def profile_set_up_at(self) -> str:
        """Get the date when the user's profile was set up.

        Returns:
            str: Profile setup timestamp

        """
        data = self._fetch_user_data()
        return data["profile_set_up_at"]

    @property
    def was_redirected(self) -> bool:
        """Check if this user's handle was redirected from the original.

        Returns:
            bool: True if the handle was changed via redirect
        """
        return self.username != self.original_username

    def get_subscriptions(self) -> list[dict[str, Any]]:
        """Get newsletters the user has subscribed to.

        Returns:
            list[dict[str, Any]]: List of publications the user subscribes to with domain info
        """
        data = self._fetch_user_data()
        subscriptions = []

        for sub in data.get("subscriptions", []):
            pub = sub["publication"]
            domain = pub.get("custom_domain") or f"{pub['subdomain']}.{SUBSTACK_DOMAIN}"
            subscriptions.append({
                "publication_id": pub["id"],
                "publication_name": pub["name"],
                "domain": domain,
                "membership_state": sub["membership_state"],
            })

        return subscriptions
