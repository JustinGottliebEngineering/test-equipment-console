from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class MeasurementRecord:
    """One timestamped measurement captured from an instrument."""

    timestamp: datetime
    instrument_name: str
    resource_name: str
    measurement_type: str
    value: float
    unit: str

    def __post_init__(self) -> None:
        if not self.instrument_name.strip():
            raise ValueError(
                "instrument_name cannot be blank."
            )

        if not self.resource_name.strip():
            raise ValueError(
                "resource_name cannot be blank."
            )

        if not self.measurement_type.strip():
            raise ValueError(
                "measurement_type cannot be blank."
            )

        if not self.unit.strip():
            raise ValueError(
                "unit cannot be blank."
            )

    @property
    def formatted_timestamp(self) -> str:
        return self.timestamp.strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )[:-3]

    @property
    def formatted_value(self) -> str:
        return f"{self.value:.6f}"

    def as_csv_row(self) -> dict[str, Any]:
        return {
            "timestamp": self.formatted_timestamp,
            "instrument": self.instrument_name,
            "resource": self.resource_name,
            "measurement_type": self.measurement_type,
            "value": self.formatted_value,
            "unit": self.unit,
        }