
"""Custom exceptions for the scraper module"""

class ScrapingError(Exception):
    """Base exception for scraping errors"""
    pass

class MetadataGenerationError(Exception):
    """Raised when metadata generation fails"""
    pass

class EmbeddingGenerationError(Exception):
    """Raised when embedding generation fails"""
    pass
