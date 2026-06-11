"""Job enrichment (proposal / cover letter + client brief)."""
from .client_brief import generate_client_brief
from .proposal import generate_cover_letter, generate_proposal

__all__ = ["generate_client_brief", "generate_proposal", "generate_cover_letter"]
