from flask import blueprints as bp
from .manager import manager

__all__ = [
	'blueprints',
	'manager'
]

def blueprints() -> list[bp.Blueprint]:
	return []
