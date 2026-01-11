from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InvalidLoanTransitionError(Exception):
    from_status: str
    to_status: str

    def __str__(self) -> str:  # pragma: no cover
        return f"Invalid loan status transition: {self.from_status} -> {self.to_status}"
