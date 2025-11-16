"""
Paper Survey Tool for InternAgent

This module provides a simple interface for conducting paper surveys by routing
queries to appropriate search functions. It wraps the multi-source search capabilities
and provides a clean API for the Survey Agent to use.
"""

import logging
from typing import Optional
from .literature_search import CitationManager

from .utils import parse_and_execute

logger = logging.getLogger(__name__)

class PaperSurvey:
    """
    Tool for searching scientific literature across multiple sources.

    This class provides a simplified interface for executing various types of
    literature queries including keyword searches, paper similarity searches,
    and reference retrieval. It routes queries to the appropriate backend
    functions in the utils module.
    """
    
    def __init__(self, 
                 max_results: int = 10,
                 sort: str = "relevance",
                 citation_manager: Optional[CitationManager] = None):
        """
        Initialize the literature search tool.
        
        Args:
            email: Email for API access (required for PubMed)
            api_keys: Dictionary of API keys for different sources
            citation_manager: Citation manager to use
        """

        # self.citation_manager = citation_manager or CitationManager()
        
        # Default search parameters
        self.max_results = max_results
        self.sort = sort # or "date"
        
        # Cache for search results
        self._cache = {}
   
    def query_route(self, query, max_results, **kwargs):
        
        return parse_and_execute(query, max_results, **kwargs)

