"""Utility helpers: logging, trace id, and simple in-memory doc store.

This module centralizes small helpers used across the app.
"""
import logging
from typing import Dict, Optional

_DOC_STORE: Dict[str, dict] = {}


def setup_logging():
    """Configure basic structured JSON-like logging for the app."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s %(message)s')


def register_doc(doc: dict):
    """Register a document in the in-memory store for retrieval endpoints."""
    _DOC_STORE[doc["id"]] = doc


def get_doc(doc_id: str) -> Optional[dict]:
    return _DOC_STORE.get(doc_id)
