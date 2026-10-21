"""LinxSci Scholar SDK and self-contained Agent Skill."""
from .scripts.scholar_client import Response, ScholarClient, ScholarError

__version__ = "0.3.0"
__all__ = ["Response", "ScholarClient", "ScholarError"]
