from flask import blueprints as bp
from .manager import manager

__all__ = [
	'blueprints'
]

def blueprints() -> list[bp.Blueprint]:
	return []
