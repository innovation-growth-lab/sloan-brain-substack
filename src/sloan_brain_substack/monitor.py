"""Newsletter monitoring service with database persistence."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .client import Newsletter as NewsletterClient
from .client import Auth
from .models import DatabaseManager
from .models import Newsletter as NewsletterModel
from .models import Post as PostModel


@dataclass
class MonitoringResult:
    """Result of a monitoring check."""

    newsletter_name: str
    newsletter_url: str
    new_posts: List[dict]
    total_posts_found: int
    check_time: datetime


class SubstackMonitor:
    """Monitors Substack newsletters and stores data in database."""

    def __init__(self, db_manager: DatabaseManager, auth: Optional[Auth] = None):
        """Initialize the monitor.

        Args:
            db_manager: Database manager instance
            auth: Optional authentication for accessing paywalled content
        """
        self.db_manager = db_manager
        self.auth = auth

    def add_newsletter(self, url: str, name: Optional[str] = None) -> NewsletterModel:
        """Add a newsletter to monitor.

        Args:
            url: Newsletter URL
            name: Optional custom name (will fetch from newsletter if not provided)

        Returns:
            Newsletter model instance
        """
        with self.db_manager.get_session() as session:
            # Check if newsletter already exists
            existing = session.execute(select(NewsletterModel).where(NewsletterModel.url == url)).scalar_one_or_none()

            if existing:
                return existing

            # Fetch newsletter info if name not provided
            if not name:
                try:
                    client = NewsletterClient(url, auth=self.auth)
                    # Try to get newsletter name from the client
                    # This might need adjustment based on the actual client API
                    name = getattr(client, "name", url.split("//")[1].split(".")[0])
                except Exception:
                    # Fallback to extracting from URL
                    name = url.split("//")[1].split(".")[0]

            # Create new newsletter
            newsletter = NewsletterModel(url=url, name=name, created_at=datetime.utcnow())

            session.add(newsletter)
            session.commit()
            session.refresh(newsletter)

            return newsletter

    def check_newsletter_updates(self, newsletter_url: str) -> MonitoringResult:
        """Check a specific newsletter for new posts.

        Args:
            newsletter_url: URL of the newsletter to check

        Returns:
            MonitoringResult with information about new posts found
        """
        with self.db_manager.get_session() as session:
            # Get newsletter from database
            newsletter = session.execute(
                select(NewsletterModel).where(NewsletterModel.url == newsletter_url)
            ).scalar_one_or_none()

            if not newsletter:
                raise ValueError(f"Newsletter {newsletter_url} not found in database. Add it first.")

            # Get existing post URLs from database
            existing_urls = set()
            existing_posts = (
                session.execute(select(PostModel.url).where(PostModel.newsletter_id == newsletter.id)).scalars().all()
            )
            existing_urls.update(existing_posts)

            # Fetch current posts from Substack
            try:
                client = NewsletterClient(newsletter_url, auth=self.auth)
                current_posts = client.get_posts(limit=50)  # Adjust limit as needed
            except Exception as e:
                raise RuntimeError(f"Failed to fetch posts from {newsletter_url}: {e}")

            # Find new posts
            new_posts = []
            for post_data in current_posts:
                post_url = getattr(post_data, "url", "")
                if post_url and post_url not in existing_urls:
                    # This is a new post
                    new_post = PostModel(
                        url=post_url,
                        title=getattr(post_data, "title", ""),
                        subtitle=getattr(post_data, "subtitle", None),
                        published_date=getattr(post_data, "post_date", datetime.utcnow()),
                        is_free=not getattr(post_data, "audience", "") == "paid",
                        post_id=str(getattr(post_data, "id", "")),
                        newsletter_id=newsletter.id,
                        created_at=datetime.utcnow(),
                    )

                    session.add(new_post)
                    new_posts.append({
                        "title": new_post.title,
                        "url": new_post.url,
                        "published_date": new_post.published_date,
                        "is_free": new_post.is_free,
                    })

            # Commit new posts
            if new_posts:
                session.commit()

            # Update newsletter's updated_at timestamp
            newsletter.updated_at = datetime.utcnow()
            session.commit()

            return MonitoringResult(
                newsletter_name=newsletter.name,
                newsletter_url=newsletter.url,
                new_posts=new_posts,
                total_posts_found=len(current_posts),
                check_time=datetime.utcnow(),
            )

    def check_all_newsletters(self) -> List[MonitoringResult]:
        """Check all newsletters in the database for updates.

        Returns:
            List of MonitoringResult objects
        """
        results = []

        with self.db_manager.get_session() as session:
            newsletters = session.execute(select(NewsletterModel)).scalars().all()

            for newsletter in newsletters:
                try:
                    result = self.check_newsletter_updates(newsletter.url)
                    results.append(result)
                except Exception as e:
                    # Log error but continue with other newsletters
                    print(f"Error checking {newsletter.name}: {e}")
                    results.append(
                        MonitoringResult(
                            newsletter_name=newsletter.name,
                            newsletter_url=newsletter.url,
                            new_posts=[],
                            total_posts_found=0,
                            check_time=datetime.utcnow(),
                        )
                    )

        return results

    def get_newsletter_stats(self, newsletter_url: str) -> dict:
        """Get statistics for a newsletter.

        Args:
            newsletter_url: URL of the newsletter

        Returns:
            Dictionary with newsletter statistics
        """
        with self.db_manager.get_session() as session:
            newsletter = session.execute(
                select(NewsletterModel).where(NewsletterModel.url == newsletter_url)
            ).scalar_one_or_none()

            if not newsletter:
                return {}

            total_posts = (
                session.execute(select(PostModel).where(PostModel.newsletter_id == newsletter.id)).scalars().all()
            )

            free_posts = [p for p in total_posts if p.is_free]
            paid_posts = [p for p in total_posts if not p.is_free]

            return {
                "name": newsletter.name,
                "url": newsletter.url,
                "total_posts": len(total_posts),
                "free_posts": len(free_posts),
                "paid_posts": len(paid_posts),
                "last_updated": newsletter.updated_at,
                "latest_post": max(total_posts, key=lambda p: p.published_date) if total_posts else None,
            }
