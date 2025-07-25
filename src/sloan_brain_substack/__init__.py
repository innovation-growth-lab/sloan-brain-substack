"""Sloan Brain Substack: A library for monitoring Substack newsletters with database persistence."""

from .client import Auth, Newsletter, Post, User, Category
from .models import DatabaseManager
from .monitor import SubstackMonitor, MonitoringResult

__version__ = "0.1.0"
__all__ = [
    "Auth", 
    "Newsletter", 
    "Post", 
    "User", 
    "Category",
    "DatabaseManager",
    "SubstackMonitor", 
    "MonitoringResult"
] 