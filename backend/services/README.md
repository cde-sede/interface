# Service Modules

Service modules implement interactions with external processes, systems, and behaviors.

## Purpose

Services handle all external interactions such as:
- Database operations (db)
- File I/O operations
- Calls to microservices
- Third-party API integrations
- External process management

## Structure

Each service module:
- Extends `ABCService` from `_base_service.py`
- Encapsulates specific external interaction logic
- Any `.py` file not starting with underscore is automatically discovered as a module
- Files starting with `_` are ignored (e.g., `_manager.py`, `_base_service.py`, `_injected.pyi`)
- Provides clean interfaces for external operations

## Typical Flow

**API → Plugin → Service**

Services are the lowest layer in the architecture. They are typically called by plugins (or sometimes directly by APIs) when interaction with external systems is needed.

## Example

```python
from .base_service import ABCService

class DatabaseService(ABCService):
    def __init__(self):
        self.connection = self.connect_to_db()

    def query(self, sql):
        # Database interaction logic
        return results

    @property
    def name(self):
        return "database"
```
