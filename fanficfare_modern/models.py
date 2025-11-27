"""
Type-safe data models using Pydantic for validation and serialization.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class Rating(str, Enum):
    """Story content rating"""
    GENERAL = "General Audiences"
    TEEN = "Teen And Up Audiences"
    MATURE = "Mature"
    EXPLICIT = "Explicit"
    NOT_RATED = "Not Rated"


class Status(str, Enum):
    """Story completion status"""
    IN_PROGRESS = "In-Progress"
    COMPLETED = "Completed"
    HIATUS = "On Hiatus"
    ABANDONED = "Abandoned"


class Chapter(BaseModel):
    """A single chapter of a story"""
    number: int = Field(..., ge=1, description="Chapter number (1-indexed)")
    title: str = Field(..., min_length=1, description="Chapter title")
    url: str = Field(..., description="Chapter URL")
    content: Optional[str] = Field(None, description="HTML content of chapter")
    summary: Optional[str] = Field(None, description="Chapter summary/notes")
    word_count: Optional[int] = Field(None, ge=0)
    published: Optional[datetime] = None

    class Config:
        frozen = False  # Allow content to be added later


class Story(BaseModel):
    """Complete story metadata and content"""

    # Core identifiers
    story_id: str = Field(..., description="Unique ID on source site")
    title: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1)
    author_id: Optional[str] = None
    author_url: Optional[str] = None

    # Metadata
    summary: str = Field(default="", description="Story description")
    rating: Rating = Rating.NOT_RATED
    status: Status = Status.IN_PROGRESS
    language: str = Field(default="en", description="ISO language code")

    # Categories
    category: Optional[str] = None  # e.g., "Harry Potter", "Original Work"
    genre: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    characters: List[str] = Field(default_factory=list)
    relationships: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    # Chapters
    chapters: List[Chapter] = Field(default_factory=list)
    chapter_count: int = Field(default=0, ge=0)

    # Stats
    word_count: int = Field(default=0, ge=0)
    comments: Optional[int] = Field(None, ge=0)
    kudos: Optional[int] = Field(None, ge=0)
    bookmarks: Optional[int] = Field(None, ge=0)
    hits: Optional[int] = Field(None, ge=0)

    # Dates
    published: Optional[datetime] = None
    updated: Optional[datetime] = None
    completed: Optional[datetime] = None

    # Source info
    source_site: str = Field(..., description="Site domain (e.g., 'archiveofourown.org')")
    source_url: str = Field(..., description="Original story URL")

    # Media
    cover_url: Optional[str] = None
    cover_data: Optional[bytes] = None

    # Series info
    series_name: Optional[str] = None
    series_position: Optional[int] = None

    # Extra metadata (site-specific)
    extra: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('chapter_count', mode='before')
    @classmethod
    def compute_chapter_count(cls, v, info):
        """Auto-compute chapter count from chapters list"""
        if v == 0 and 'chapters' in info.data:
            return len(info.data['chapters'])
        return v

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }


class SiteConfig(BaseModel):
    """Configuration for a specific fanfiction site"""

    name: str = Field(..., description="Human-readable site name")
    domains: List[str] = Field(..., description="Accepted domain names")
    encoding: str = Field(default="utf-8")

    # Platform info
    platform: Optional[str] = Field(None, description="Platform type (efiction, xenforo, etc.)")
    platform_version: Optional[str] = None

    # URL patterns
    story_url_pattern: str = Field(..., description="Regex pattern for story URLs")
    story_url_template: Optional[str] = None

    # CSS/XPath selectors for extracting metadata
    selectors: Dict[str, Any] = Field(default_factory=dict)

    # Rate limiting
    rate_limit: Optional[float] = Field(None, description="Max requests per second")

    # Authentication
    requires_login: bool = False
    login_url: Optional[str] = None

    # Site-specific options
    options: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"  # Allow additional fields


class AdapterCapabilities(BaseModel):
    """What an adapter can do"""

    supports_metadata: bool = True
    supports_chapters: bool = True
    supports_images: bool = True
    supports_series: bool = False
    supports_search: bool = False
    supports_updates: bool = False  # Can check for new chapters

    requires_javascript: bool = False
    requires_authentication: bool = False
