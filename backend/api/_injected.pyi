"""Type hints for symbols injected into API module globals."""
from typing import Any, TypeVar, Callable, overload
from ._base_api import ABCApi, Manager

__all__ = ['manager', 'validate_setup']

P = TypeVar('P', bound=ABCApi)

# Validator function - checks setup signature at type-check time only
@overload
def validate_setup(func: Callable[[Manager[ABCApi]], P]) -> Callable[[Manager[ABCApi]], P]: ...
@overload
def validate_setup(func: object) -> object: ...

manager: Manager[ABCApi]
require: Callable[[str], ABCApi]
