"""Type hints for symbols injected into plugin module globals."""
from typing import Any, TypeVar, Callable, overload
from .base_plugin import ABCPlugin, Manager

__all__ = ['manager', 'validate_setup']

P = TypeVar('P', bound=ABCPlugin)

@overload
def validate_setup(func: Callable[[Manager[ABCPlugin]], P]) -> Callable[[Manager[ABCPlugin]], P]: ...
@overload
def validate_setup(func: object) -> object: ...

manager: Manager[ABCPlugin]
