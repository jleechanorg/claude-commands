"""
Base classes for application commands.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar


# Type variable for command results
TResult = TypeVar('TResult')


@dataclass(frozen=True)
class Command(ABC):
    """Base class for all commands."""
    pass


class CommandHandler(ABC, Generic[TResult]):
    """
    Base class for command handlers.
    
    Command handlers execute business operations by coordinating
    domain objects and infrastructure services.
    """
    
    @abstractmethod
    async def handle(self, command: Command) -> TResult:
        """
        Handle the command and return a result.
        
        Args:
            command: The command to handle
            
        Returns:
            The result of handling the command
            
        Raises:
            CommandError: If the command cannot be handled
        """
        pass


class CommandError(Exception):
    """Base exception for command handling errors."""
    pass


class ValidationError(CommandError):
    """Raised when command validation fails."""
    pass


class NotFoundError(CommandError):
    """Raised when a required resource is not found."""
    pass


class ConflictError(CommandError):
    """Raised when there's a conflict with existing state."""
    pass