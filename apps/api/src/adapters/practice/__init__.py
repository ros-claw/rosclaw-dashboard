"""Practice store adapters."""

from adapters.practice.base import PracticeStoreAdapter
from adapters.practice.local_store import LocalPracticeStoreAdapter

__all__ = ["PracticeStoreAdapter", "LocalPracticeStoreAdapter"]
