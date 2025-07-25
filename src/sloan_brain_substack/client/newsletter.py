from time import sleep
from typing import Any

import requests

from .auth import Auth
from .constants import DEFAULT_HEADERS, SUBSTACK_DOMAIN
from .post import Post
from .user import User


class Newsletter:
    """Newsletter class for interacting with Substack newsletters."""

    def __init__(self, url: str, auth: Auth = None) -> None:
        """Create a Newsletter object.

        Args:
            url: The URL of the Substack newsletter
            auth: Authentication handler for accessing paywalled content

        """
        self.url = url
        self.auth = auth

    def __str__(self) -> str:
        """Return a string representation of the newsletter."""
        return f"Newsletter: {self.url}"

    def __repr__(self) -> str:
        """Return a string representation of the newsletter."""
        return f"Newsletter(url={self.url})"

    def _make_request(self, endpoint: str, **kwargs: Any) -> requests.Response:
        """Make a GET request to the specified endpoint with authentication if needed.

        Args:
            endpoint: The API endpoint to request
            **kwargs: Additional parameters for the request

        Returns:
            requests.Response: The response object from the request

        """
        if self.auth and self.auth.authenticated:
            return self.auth.get(endpoint, **kwargs)
        else:
            return requests.get(endpoint, headers=DEFAULT_HEADERS, **kwargs)

    def _fetch_paginated_posts(
        self, params: dict[str, str], limit: int = None, page_size: int = 15
    ) -> list[dict[str, Any]]:
        """Helper method to fetch paginated posts with different query parameters.

        Args:
            params: Dictionary of query parameters to include in the API request
            limit: Maximum number of posts to return
            page_size: Number of posts to retrieve per page request

        Returns:
            list[dict[str, Any]]: List of post data dictionaries

        """
        results = []
        offset = 0
        batch_size = page_size  # The API default limit per request
        more_items = True

        while more_items:
            # Update params with current offset and batch size
            current_params = params.copy()
            current_params.update({"offset": str(offset), "limit": str(batch_size)})

            # Format query parameters
            query_string = "&".join([f"{k}={v}" for k, v in current_params.items()])
            endpoint = f"{self.url}/api/v1/archive?{query_string}"

            # Make the request
            response = self._make_request(endpoint, timeout=30)
            response.raise_for_status()

            items = response.json()
            if not items:
                break

            results.extend(items)

            # Update offset for next batch
            offset += batch_size

            # Check if we've reached the requested limit
            if limit and len(results) >= limit:
                results = results[:limit]
                more_items = False

            # Check if we got fewer items than requested (last page)
            if len(items) < batch_size:
                more_items = False

            # Be nice to the API
            sleep(0.5)

        # Instead of creating Post objects directly, return the URLs
        # The caller will create Post objects as needed
        return results

    def get_posts(self, sorting: str = "new", limit: int = None) -> list[Post]:
        """Get posts from the newsletter with specified sorting.

        Args:
            sorting: Sorting order for the posts ("new", "top", "pinned", or "community")
            limit: Maximum number of posts to return

        Returns:
            list[Post]: List of Post objects

        """
        params = {"sort": sorting}
        post_data = self._fetch_paginated_posts(params, limit)
        return [Post(item["canonical_url"], auth=self.auth) for item in post_data]

    def search_posts(self, query: str, limit: int = None) -> list[Post]:
        """Search posts in the newsletter with the given query.

        Args:
            query: Search query string
            limit: Maximum number of posts to return

        Returns:
            list[Post]: List of Post objects matching the search query

        """
        params = {"sort": "new", "search": query}
        post_data = self._fetch_paginated_posts(params, limit)
        return [Post(item["canonical_url"], auth=self.auth) for item in post_data]

    def get_podcasts(self, limit: int = None) -> list[Post]:
        """Get podcast posts from the newsletter.

        Args:
            limit: Maximum number of podcast posts to return

        Returns:
            list[Post]: List of Post objects representing podcast posts

        """
        params = {"sort": "new", "type": "podcast"}
        post_data = self._fetch_paginated_posts(params, limit)
        return [Post(item["canonical_url"], auth=self.auth) for item in post_data]

    def get_recommendations(self) -> list["Newsletter"]:
        """Get recommended publications for this newsletter.

        Returns:
            list[Newsletter]: List of recommended Newsletter objects

        """
        # First get any post to extract the publication ID
        posts = self.get_posts(limit=1)
        if not posts:
            return []

        publication_id = posts[0].get_metadata()["publication_id"]

        # Now get the recommendations
        endpoint = f"{self.url}/api/v1/recommendations/from/{publication_id}"
        response = self._make_request(endpoint, timeout=30)
        response.raise_for_status()

        recommendations = response.json()
        if not recommendations:
            return []

        recommended_newsletter_urls = []
        for rec in recommendations:
            recpub = rec["recommendedPublication"]
            if "custom_domain" in recpub and recpub["custom_domain"]:
                recommended_newsletter_urls.append(recpub["custom_domain"])
            else:
                recommended_newsletter_urls.append(f"{recpub['subdomain']}.{SUBSTACK_DOMAIN}")

        result = [Newsletter(url, auth=self.auth) for url in recommended_newsletter_urls]

        return result

    def get_authors(self) -> list[User]:
        """Get authors of the newsletter.

        Returns:
            list[User]: List of User objects representing the authors

        """
        endpoint = f"{self.url}/api/v1/publication/users/ranked?public=true"
        r = self._make_request(endpoint, timeout=30)
        r.raise_for_status()
        authors = r.json()
        return [User(author["handle"]) for author in authors]
