"""Job enrichment (proposal + client brief)."""
from .client_brief import generate_client_brief
from .proposal import generate_proposal

__all__ = ["generate_client_brief", "generate_proposal"]
