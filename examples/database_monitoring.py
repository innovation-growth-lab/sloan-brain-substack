"""Example: Database-backed Substack monitoring with EC2 PostgreSQL."""

from sloan_brain_substack import DatabaseManager, SubstackMonitor, Auth

def setup_database_monitoring():
    """Example of setting up database-backed monitoring."""
    
    # Database connection string for EC2 PostgreSQL
    # Replace with your actual EC2 database credentials
    connection_string = "postgresql://username:password@your-ec2-instance:5432/substack_db"
    
    # Initialize database manager
    db_manager = DatabaseManager(connection_string)
    
    # Create tables if they don't exist
    db_manager.create_tables()
    
    # Optional: Set up authentication for paywalled content
    # auth = Auth(cookies_path="path/to/your/cookies.json")
    auth = None  # For now, just monitor free content
    
    # Initialize monitor
    monitor = SubstackMonitor(db_manager, auth=auth)
    
    return monitor, db_manager

def add_newsletters_to_monitor(monitor):
    """Add newsletters to the monitoring system."""
    
    newsletters = [
        "https://www.oneusefulthing.org",
        # Add more newsletter URLs here
    ]
    
    for url in newsletters:
        try:
            newsletter = monitor.add_newsletter(url)
            print(f"Added newsletter: {newsletter.name} ({newsletter.url})")
        except Exception as e:
            print(f"Failed to add {url}: {e}")

def check_for_updates(monitor):
    """Check all newsletters for new posts."""
    
    print("Checking for updates...")
    results = monitor.check_all_newsletters()
    
    total_new_posts = 0
    for result in results:
        if result.new_posts:
            print(f"\n📰 {result.newsletter_name}:")
            print(f"   Found {len(result.new_posts)} new post(s)")
            
            for post in result.new_posts:
                print(f"   • {post['title']}")
                print(f"     URL: {post['url']}")
                print(f"     Published: {post['published_date']}")
                print(f"     Free: {'Yes' if post['is_free'] else 'No'}")
                
            total_new_posts += len(result.new_posts)
        else:
            print(f"✓ {result.newsletter_name}: No new posts")
    
    print(f"\nTotal new posts found: {total_new_posts}")

def show_newsletter_stats(monitor, newsletter_url):
    """Show statistics for a specific newsletter."""
    
    stats = monitor.get_newsletter_stats(newsletter_url)
    
    if stats:
        print(f"\n📊 Statistics for {stats['name']}:")
        print(f"   Total posts: {stats['total_posts']}")
        print(f"   Free posts: {stats['free_posts']}")
        print(f"   Paid posts: {stats['paid_posts']}")
        print(f"   Last updated: {stats['last_updated']}")
        
        if stats['latest_post']:
            latest = stats['latest_post']
            print(f"   Latest post: {latest.title} ({latest.published_date})")
    else:
        print(f"No stats found for {newsletter_url}")

if __name__ == "__main__":
    # Set up the monitoring system
    monitor, db_manager = setup_database_monitoring()
    
    try:
        # Add newsletters to monitor
        add_newsletters_to_monitor(monitor)
        
        # Check for updates
        check_for_updates(monitor)
        
        # Show stats for One Useful Thing
        show_newsletter_stats(monitor, "https://www.oneusefulthing.org")
        
    finally:
        # Clean up database connection
        db_manager.close() 