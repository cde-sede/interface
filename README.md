# Proxmox Services Interface

A modular Flask + React application with a plugin-based architecture powered by a dynamic module manager framework.

## Architecture Overview

This project uses a custom **Manager** framework that enables dynamic module discovery, loading, and dependency injection. The backend is organized into three module categories:

- **APIs** - Flask Blueprint-based REST endpoints
- **Services** - Backend services (database, logging, etc.)
- **Plugins** - Extensible functionality modules

## Project Structure

```
.
├── backend/
│   ├── app.py              # Main Flask application
│   ├── manager.py          # Core Manager framework
│   ├── api/
│   │   ├── _manager.py     # API manager instance
│   │   ├── _base_api.py    # ABCApi base class with @describe decorator
│   │   └── *.py            # API modules (auto-discovered)
│   ├── services/
│   │   ├── _manager.py     # Services manager instance
│   │   └── *.py            # Service modules (auto-discovered)
│   ├── plugins/
│   │   ├── _manager.py     # Plugins manager instance
│   │   └── *.py            # Plugin modules (auto-discovered)
│   └── static/             # Built frontend files (generated)
└── frontend/               # React + Vite + TypeScript
    ├── src/
    ├── vite.config.ts
    └── package.json
```

## Manager Framework

The `Manager[T]` class provides automatic module discovery, lazy loading, and cross-manager module resolution.

### Key Features

- **Auto-discovery**: Automatically finds all `.py` files in a directory (excluding `_*.py`)
- **Lazy loading**: Modules are loaded only when accessed
- **Type-safe**: Generic type parameter ensures type consistency
- **Dependency injection**: Modules can access `manager`, `require()`, and custom dependencies
- **Cross-manager lookups**: Access modules from other managers using dot notation
- **Registry pattern**: All managers register themselves for cross-manager communication

### Creating a Manager

```python
from manager import Manager, ModuleLoadError

def checker(module):
    if not hasattr(module, 'setup'):
        raise ModuleLoadError("Module must have a setup() function")
    return module.setup()

manager = Manager[MyType](__name__, checker=checker)
```

### Module Loading

Each module file must:
1. Have a `setup()` function that returns an instance of the expected type
2. Can access injected variables: `manager`, `require()`, and `inject`

Example module:
```python
def setup():
    # Access the manager that loaded this module
    other_module = manager.get('other_module')

    # Cross-manager access
    service = manager.get('services.database')

    return MyModuleInstance()
```


### Loading order

In the backend application, by default, each manager loads every module in discovery order. This behavior may be machine dependant as it relies on pathlib.Path.iterdir which may have inconsistent sorting.

The application loads managers in reverse depth order:
1. Services
2. Plugins
3. APIs

Discover ordering may be bypassed using `require`, which is injected inside every loaded module, in the setup function.
But require is unable to interface with another plugin type, as it is manager bound.

### Accessing Modules

```python
# Load and get a module by name
instance = manager.get('module_name')

# Cross-manager access
service = manager.get('services.database')
plugin = manager.get('plugins.my_plugin')

# Access nested attributes
value = manager.get('module_name.attribute.nested')
```

## API Module System

APIs inherit from `ABCApi` and use Flask Blueprints. Each API must implement:
- `name` property - Module identifier
- `blueprint` property - Flask Blueprint instance

### The @describe Decorator

The `@describe` decorator provides automatic API documentation for endpoints:

```python
from ._base_api import ABCApi, describe

class MyAPI(ABCApi):
    def __init__(self):
        self.bp = self.create_blueprint("my_api", url_prefix="/api")
        self.bp.add_url_rule("/endpoint", view_func=self.my_endpoint)

    @describe(
        "Brief description of what this endpoint does",
        params={
            "param_name": {
                "type": "string",
                "required": True,
                "description": "Parameter description",
                "in": "query"  # or "path"
            }
        },
        method="GET"
    )
    def my_endpoint(self):
        """Detailed docstring about the endpoint implementation."""
        return {"result": "data"}
```

### Automatic /describe Endpoints

Every API blueprint automatically gets a `/describe` endpoint:

- `GET /api/my_api/describe` - List all documented endpoints
- `GET /api/my_api/describe?f=function_name` - Get specific endpoint documentation

The response includes:
- Function name
- Short description (from @describe)
- Full docstring
- Route pattern
- Parameters with types and descriptions
- HTTP method

### Blueprint Hierarchy

APIs can nest blueprints using the `create_blueprint()` method:

```python
self.bp = self.create_blueprint("sub_api", parent=parent_api, url_prefix="/v1")
```

This automatically registers the blueprint with its parent.

## Setup

### Backend Setup

1. Install Python dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

### Frontend Setup

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

## Development Mode

Run both servers separately for development with hot reload:

**Terminal 1 - Backend:**
```bash
cd backend
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Then open your browser to `http://localhost:5173`. The Vite dev server will proxy API requests to the Flask backend at `http://localhost:5000`.

## Production Mode

Build the frontend and serve it from Flask:

1. Build the frontend:
   ```bash
   cd frontend
   npm run build
   ```

2. Run the Flask server:
   ```bash
   cd backend
   python app.py
   ```

Then open your browser to `http://localhost:5000`. Flask will serve both the API endpoints and the static frontend files.

## Adding New Modules

### Adding an API Module

1. Create a new file in `backend/api/` (e.g., `my_api.py`)
2. Implement a class inheriting from `ABCApi`
3. Define a `setup()` function that returns an instance
4. The module will be auto-discovered and loaded on startup

### Adding a Service

1. Create a new file in `backend/services/` (e.g., `my_service.py`)
2. Implement your service class
3. Define a `setup()` function that returns an instance
4. Access from other modules via `manager.get('services.my_service')`

### Adding a Plugin

1. Create a new file in `backend/plugins/` (e.g., `my_plugin.py`)
2. Implement your plugin class
3. Define a `setup()` function that returns an instance
4. Access from other modules via `manager.get('plugins.my_plugin')`
