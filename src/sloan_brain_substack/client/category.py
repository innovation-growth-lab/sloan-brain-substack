from typing import Any

import requests

from .constants import DEFAULT_HEADERS, DEFAULT_TIMEOUT, SUBSTACK_API_BASE
from .newsletter import Newsletter


def list_all_categories() -> list[tuple[str, int]]:
    """List all categories.

    Returns:
        list[tuple[str, int]]: List of tuples containing (category_name, category_id)

    """
    endpoint_cat = f"{SUBSTACK_API_BASE}/categories"
    r = requests.get(endpoint_cat, headers=DEFAULT_HEADERS, timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    categories = [(i["name"], i["id"]) for i in r.json()]
    return categories


class Category:
    """Top-level newsletter category."""

    def __init__(self, name: str = None, id: int = None) -> None:
        """Create a Category object.

        Args:
            name: The name of the category
            id: The ID of the category

        Raises:
            ValueError: If neither name nor id is provided, or if the provided
            name/id is not found
        """
        if name is None and id is None:
            raise ValueError("Either name or id must be provided")

        self.name = name
        self.id = id
        self._newsletters_data = None

        # Retrieve missing components
        if self.name and self.id is None:
            self._get_id_from_name()
        elif self.id and self.name is None:
            self._get_name_from_id()

    def __str__(self) -> str:
        """Return a string representation of the category."""
        return f"{self.name} ({self.id})"

    def __repr__(self) -> str:
        """Return a string representation of the category."""
        return f"Category(name={self.name}, id={self.id})"

    def _get_id_from_name(self) -> None:
        """Lookup category ID based on name."""
        categories = list_all_categories()
        for name, id in categories:
            if name == self.name:
                self.id = id
                return
        raise ValueError(f"Category name '{self.name}' not found")

    def _get_name_from_id(self) -> None:
        """Lookup category name based on ID."""
        categories = list_all_categories()
        for name, id in categories:
            if id == self.id:
                self.name = name
                return
        raise ValueError(f"Category ID {self.id} not found")

    def _fetch_newsletters_data(self, *, force_refresh: bool = False) -> list[dict[str, Any]]:
        """Fetch the raw newsletter data from the API and cache it.

        Args:
            force_refresh: Whether to force a refresh of the data, ignoring the cache

        Returns:
            list[dict[str, Any]]: Full newsletter metadata

        """
        if self._newsletters_data is not None and not force_refresh:
            return self._newsletters_data

        endpoint = f"{SUBSTACK_API_BASE}/category/public/{self.id}/all?page="

        all_newsletters = []
        page_num = 0
        more = True
        # endpoint doesn't return more than 21 pages [DAVID]
        while more and page_num <= 20:
            full_url = endpoint + str(page_num)
            r = requests.get(full_url, headers=DEFAULT_HEADERS, timeout=DEFAULT_TIMEOUT)
            r.raise_for_status()

            resp = r.json()
            newsletters = resp["publications"]
            all_newsletters.extend(newsletters)
            page_num += 1
            more = resp["more"]

        self._newsletters_data = all_newsletters
        return all_newsletters

    def get_newsletter_urls(self) -> list[str]:
        """Get only the URLs of newsletters in this category.

        Returns:
            list[str]: List of newsletter URLs

        """
        data = self._fetch_newsletters_data()

        return [item["base_url"] for item in data]

    def get_newsletters(self) -> list[Newsletter]:
        """Get Newsletter objects for all newsletters in this category.

        Returns:
            list[Newsletter]: List of Newsletter objects

        """
        urls = self.get_newsletter_urls()
        return [Newsletter(url) for url in urls]

    def get_newsletter_metadata(self) -> list[dict[str, Any]]:
        """Get full metadata for all newsletters in this category.

        Returns:
            list[dict[str, Any]]: List of newsletter metadata dictionaries

        """
        return self._fetch_newsletters_data()

    def refresh_data(self) -> None:
        """Force refresh of the newsletter data cache."""
        self._fetch_newsletters_data(force_refresh=True)
