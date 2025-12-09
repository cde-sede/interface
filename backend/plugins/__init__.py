from flask import blueprints as bp
from ._manager import manager

__all__ = [
	'blueprints',
	'manager'
]

def blueprints() -> list[bp.Blueprint]:
	return []
