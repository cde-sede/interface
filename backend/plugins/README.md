# Plugin Modules

Plugin modules define modular behavior that varies depending on context or user actions.

## Purpose

Plugins encapsulate business logic and provide reusable functionality that can be composed in different ways. They act as the middle layer between APIs and services.

## Structure

Each plugin module:
- Extends `ABCPlugin` from `_base_plugin.py`
- Implements specific business logic or behavior
- Any `.py` file not starting with underscore is automatically discovered as a module
- Files starting with `_` are ignored (e.g., `_manager.py`, `_base_plugin.py`, `_injected.pyi`)
- Can be loaded dynamically by the plugin manager

## Typical Flow

**API → Plugin → Service**

Plugins are typically called by APIs to handle business logic, and they call services when they need to interact with external systems (databases, file systems, microservices, etc.).

## Example

```python
from .base_plugin import ABCPlugin

class MyPlugin(ABCPlugin):
    def process_data(self, data):
        # Business logic here
        # May call services for external interactions
        return processed_data

    @property
    def name(self):
        return "my_plugin"
```
