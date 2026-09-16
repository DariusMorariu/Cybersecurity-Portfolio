"""Abstract base publisher interface."""

from abc import ABC, abstractmethod
from src.core.models import CTIAnalysisResult


class BasePublisher(ABC):
    """Base interface for all CTI alert publishing channels."""

    @abstractmethod
    def publish(self, data: CTIAnalysisResult, dry_run: bool = False) -> bool:
        """Publish briefing data or simulate output if dry_run is True.

        Returns True on success, False otherwise.
        """
        pass
