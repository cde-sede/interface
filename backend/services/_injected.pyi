"""Type hints for symbols injected into service module globals."""
from typing import Any, TypeVar, Callable, overload
from ._base_service import ABCService
from ..manager import Manager

__all__ = ['manager', 'validate_setup']

P = TypeVar('P', bound=ABCService)

# Validator function - checks setup signature at type-check time only
@overload
def validate_setup(func: Callable[[Manager[ABCService]], P]) -> Callable[[Manager[ABCService]], P]: ...
@overload
def validate_setup(func: object) -> object: ...

manager: Manager[ABCService]
require: Callable[[str], ABCService]
