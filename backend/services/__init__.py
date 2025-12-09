from flask import blueprints as bp
from ._manager import manager

__all__ = [
	'blueprints'
]

def blueprints() -> list[bp.Blueprint]:
	return []
