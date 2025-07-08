"""
Base classes for application queries.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar


# Type variable for query results
TResult = TypeVar('TResult')


@dataclass(frozen=True)
class Query(ABC):
    """Base class for all queries."""
    pass


class QueryHandler(ABC, Generic[TResult]):
    """
    Base class for query handlers.
    
    Query handlers retrieve data without modifying state.
    """
    
    @abstractmethod
    async def handle(self, query: Query) -> TResult:
        """
        Handle the query and return a result.
        
        Args:
            query: The query to handle
            
        Returns:
            The result of handling the query
            
        Raises:
            QueryError: If the query cannot be handled
        """
        pass


class QueryError(Exception):
    """Base exception for query handling errors."""
    pass


class NotFoundError(QueryError):
    """Raised when a requested resource is not found."""
    pass


class UnauthorizedError(QueryError):
    """Raised when access to a resource is unauthorized."""
    pass