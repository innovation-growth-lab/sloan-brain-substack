# Sloan Brain Substack

A library for monitoring Substack newsletters with database persistence and session support.

## Installation

```bash
pip install -e .
```

## Usage

### Direct Newsletter Access

Access newsletter content directly without database storage:

```python
from sloan_brain_substack import Newsletter

newsletter = Newsletter("https://www.oneusefulthing.org")

# Fetch their posts
posts = newsletter.get_posts(limit=10)

# Identify the authors (substack username)
username = newsletter.get_authors()

# Get podcasts (lot's of mislabelled)
podcasts = newsletter.get_podcasts()

# Get recommendations
reccs = newsletter.get_recommendations()
```

### Authentication for Paywalled Content

To access content from newsletters you're subscribed to:

```python
from sloan_brain_substack import Newsletter, Auth

# Load session cookies from browser export
auth = Auth(cookies_path="cookies.json")

# Access newsletters
newsletter = Newsletter("https://paid-newsletter.substack.com", auth=auth)
```

### Work with a post
```python
post = Post(url="https://www.oneusefulthing.org/p/how-to-be-more-creative")

# Get post metadata
metadata = post.get_metadata()

# Get post bs4-parsed content
content = post.get_content()

# Check if it paywalled
is_paywalled = post.is_paywalled()
```

### Database-Backed Monitoring (WIP)

Store newsletter data in a PostgreSQL database and compare against existing data:

```python
from sloan_brain_substack import DatabaseManager, SubstackMonitor, Auth

# Set up database connection (PostgreSQL on EC2)
connection_string = "postgresql://user:password@your-ec2-instance:5432/substack_db"
db_manager = DatabaseManager(connection_string)
db_manager.create_tables()

# Initialise monitor
monitor = SubstackMonitor(db_manager)

# Add newsletters to monitor
monitor.add_newsletter("https://www.oneusefulthing.org")

# Check for new posts (compares against database, not time)
results = monitor.check_all_newsletters()

for result in results:
    if result.new_posts:
        print(f"New posts in {result.newsletter_name}: {len(result.new_posts)}")
        for post in result.new_posts:
            print(f"  - {post['title']}")
```


## Database Schema

The library uses SQLAlchemy with these models:

- `Newsletter`: Stores newsletter metadata (name, URL, description)
- `Post`: Stores individual posts with relationships to newsletters

## API Reference

### DatabaseManager

- `create_tables()` - Create database schema
- `get_session()` - Get SQLAlchemy session
- `close()` - Close database connection

### SubstackMonitor

- `add_newsletter(url, name=None)` - Add newsletter to monitoring
- `check_newsletter_updates(url)` - Check specific newsletter for new posts
- `check_all_newsletters()` - Check all monitored newsletters
- `get_newsletter_stats(url)` - Get statistics for a newsletter

### Direct Client Access

- `Newsletter` - Access newsletter posts and metadata
- `Post` - Access individual post content
- `User` - Access user profiles and subscriptions
- `Auth` - Handle authentication for paywalled content

## Dependencies

- httpx - HTTP client
- beautifulsoup4 - HTML parsing
- sqlalchemy - Database ORM
- psycopg2-binary - PostgreSQL adapter
- python>=3.13

## Development

```bash
pip install -e ".[dev]"
pytest
pre-commit run --all-files
```

## Credits

API endpoint identification based on work by [NHagar](https://github.com/NHagar).

## License

MIT License 