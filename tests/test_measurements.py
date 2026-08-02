from __future__ import annotations

from datetime import datetime

import pytest

from test_equipment_console.measurements import (
    MeasurementRecord,
)


def test_measurement_record_formats_timestamp() -> None:
    record = MeasurementRecord(
        timestamp=datetime(
            2026,
            8,
            2,
            11,
            29,
            45,
            123456,
        ),
        instrument_name="Simulated Frequency Counter",
        resource_name="SIM::FREQ_COUNTER::1",
        measurement_type="Frequency",
        value=10_000_000.125,
        unit="Hz",
    )

    assert record.formatted_timestamp == (
        "2026-08-02 11:29:45.123"
    )


def test_measurement_record_formats_value() -> None:
    record = MeasurementRecord(
        timestamp=datetime(
            2026,
            8,
            2,
            11,
            29,
            45,
        ),
        instrument_name="Simulated Power Supply",
        resource_name="SIM::POWER_SUPPLY::1",
        measurement_type="Voltage",
        value=11.999048,
        unit="V",
    )

    assert record.formatted_value == "11.999048"


def test_measurement_record_returns_csv_row() -> None:
    record = MeasurementRecord(
        timestamp=datetime(
            2026,
            8,
            2,
            11,
            29,
            45,
            987654,
        ),
        instrument_name="Simulated Power Supply",
        resource_name="SIM::POWER_SUPPLY::1",
        measurement_type="Current",
        value=0.352804,
        unit="A",
    )

    assert record.as_csv_row() == {
        "timestamp": "2026-08-02 11:29:45.987",
        "instrument": "Simulated Power Supply",
        "resource": "SIM::POWER_SUPPLY::1",
        "measurement_type": "Current",
        "value": "0.352804",
        "unit": "A",
    }


@pytest.mark.parametrize(
    (
        "field_name",
        "field_value",
        "expected_message",
    ),
    (
        (
            "instrument_name",
            "",
            "instrument_name cannot be blank",
        ),
        (
            "resource_name",
            "   ",
            "resource_name cannot be blank",
        ),
        (
            "measurement_type",
            "",
            "measurement_type cannot be blank",
        ),
        (
            "unit",
            " ",
            "unit cannot be blank",
        ),
    ),
)
def test_measurement_record_rejects_blank_fields(
    field_name: str,
    field_value: str,
    expected_message: str,
) -> None:
    values = {
        "timestamp": datetime(
            2026,
            8,
            2,
            11,
            29,
            45,
        ),
        "instrument_name": "Instrument",
        "resource_name": "SIM::RESOURCE",
        "measurement_type": "Voltage",
        "value": 12.0,
        "unit": "V",
    }

    values[field_name] = field_value

    with pytest.raises(
        ValueError,
        match=expected_message,
    ):
        MeasurementRecord(**values)