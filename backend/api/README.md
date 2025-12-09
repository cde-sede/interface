# API Modules

API modules implement Flask blueprints and handle interactions with the front-end.

## Purpose

APIs are the interface layer between the front-end and the backend logic. They define HTTP endpoints, handle requests/responses, and route to appropriate plugins.

## Structure

Each API module:
- Extends `ABCApi` from `_base_api.py`
- Implements a Flask `Blueprint`
- Uses the `@describe` decorator for automatic documentation
- Any `.py` file not starting with underscore is automatically discovered as a module
- Files starting with `_` are ignored (e.g., `_manager.py`, `_base_api.py`, `_injected.pyi`)

## Typical Flow

**Front-end → API → Plugin → Service**

APIs typically call plugins for business logic, which in turn may call services for external interactions.

## Example

```python
from .base_api import ABCApi, describe

class MyAPI(ABCApi):
    def __init__(self, manager, parent):
        self.bp = self.create_blueprint("my_api", parent=parent, url_prefix="/my")
        self.bp.add_url_rule("/endpoint", view_func=self.my_endpoint)

    @describe("Description of endpoint")
    def my_endpoint(self):
        return {"status": "ok"}
```
