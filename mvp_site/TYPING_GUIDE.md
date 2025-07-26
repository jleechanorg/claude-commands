# Python Typing Guide for WorldArchitect.AI

This guide documents the type annotation standards and practices for the WorldArchitect.AI codebase.

## Overview

We use Python's type hints (PEP 484) with a gradual typing approach to improve code quality, catch bugs early, and enhance developer experience.

## Type Checking Setup

### mypy Configuration

The project uses mypy for static type checking with configuration in `mvp_site/mypy.ini`:

```bash
# Run type checking
source venv/bin/activate
python -m mypy mvp_site --config-file mvp_site/mypy.ini
```

### Gradual Typing Strategy

We've adopted a gradual typing approach:
1. Start with critical modules (services, main application)
2. Add types to new code immediately
3. Type existing code when modifying
4. Increase strictness over time

## Core Type Definitions

### custom_types.py Module

Common types are defined in `mvp_site/custom_types.py`:

```python
# Firebase/Firestore data structures
CampaignData = TypedDict  # Campaign data structure
StateUpdate = TypedDict   # State update objects
EntityData = TypedDict    # Entity information
MissionData = TypedDict   # Mission/quest data

# Type aliases
UserId = str
CampaignId = str
EntityId = str

# JSON-compatible types
JsonValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JsonDict = Dict[str, JsonValue]
```

## Typing Patterns

### Flask Routes

```python
from flask import Response, Request
from .custom_types import ApiResponse, UserId, CampaignId

@app.route('/api/campaigns/<campaign_id>')
@check_token
def get_campaign(user_id: UserId, campaign_id: CampaignId) -> Union[Response, Tuple[Response, int]]:
    """Get a specific campaign."""
    ...
```

### Service Methods

```python
from typing import Optional, Dict, Any, List
from .custom_types import CampaignData, UserId, CampaignId

def get_campaign(self, user_id: UserId, campaign_id: CampaignId) -> Optional[CampaignData]:
    """Retrieve a campaign from Firestore."""
    ...
```

### Firebase/Firestore Operations

```python
from typing import TypedDict, Optional
from google.cloud import firestore

class UserData(TypedDict):
    name: str
    email: str
    created_at: datetime

def get_user(db: firestore.Client, user_id: str) -> Optional[UserData]:
    doc = db.collection('users').document(user_id).get()
    if doc.exists:
        return cast(UserData, doc.to_dict())
    return None
```

### Pydantic Models

Pydantic models are already typed by design:

```python
from pydantic import BaseModel
from typing import Optional, List

class CharacterModel(BaseModel):
    name: str
    level: int
    hp: Optional[int] = None
    abilities: List[str] = []
```

## Common Patterns

### Optional Values

```python
# Use Optional for nullable values
def find_entity(name: str) -> Optional[EntityData]:
    ...

# Modern syntax (Python 3.10+)
def find_entity(name: str) -> EntityData | None:
    ...
```

### Union Types

```python
# Multiple possible types
def process_value(val: Union[str, int, float]) -> str:
    ...

# Modern syntax
def process_value(val: str | int | float) -> str:
    ...
```

### Dictionaries and Lists

```python
# Specific dictionary structure
user_data: Dict[str, str] = {"name": "Alice", "email": "alice@example.com"}

# List of specific types
entity_list: List[EntityData] = []

# Mixed dictionaries
config: Dict[str, Any] = {"debug": True, "port": 8080}
```

### Callbacks and Decorators

```python
from typing import Callable, TypeVar, Any

F = TypeVar('F', bound=Callable[..., Any])

def log_exceptions(func: F) -> F:
    """Decorator that logs exceptions."""
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        ...
    return cast(F, wrapper)
```

## Type Checking in CI/CD

Add to your CI pipeline:

```yaml
- name: Type Check
  run: |
    source venv/bin/activate
    python -m mypy mvp_site --config-file mvp_site/mypy.ini
```

## Best Practices

1. **Be Specific**: Use specific types over `Any` when possible
2. **Use Type Aliases**: Create aliases for complex types
3. **Document Unclear Types**: Add comments for non-obvious type usage
4. **Gradual Adoption**: Don't try to type everything at once
5. **Test Type Annotations**: Ensure types match runtime behavior

## Migration Tips

When adding types to existing code:

1. Start with function signatures
2. Add types to class attributes
3. Type local variables only when unclear
4. Use `cast()` sparingly for type assertions
5. Run tests after adding types

## Type Stubs

Required type stubs are in `requirements.txt`:
- `types-flask` - Flask type stubs
- `types-requests` - Requests type stubs

## Resources

- [Python Type Hints Documentation](https://docs.python.org/3/library/typing.html)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/)
- [PEP 526 - Variable Annotations](https://www.python.org/dev/peps/pep-0526/)
