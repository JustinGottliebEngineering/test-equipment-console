from __future__ import annotations

import pytest

from test_equipment_console.drivers.base import (
    InstrumentCommandError,
    InstrumentConnectionError,
)
from test_equipment_console.simulators.frequency_counter import (
    SimulatedFrequencyCounter,
)


def test_frequency_counter_starts_disconnected() -> None:
    counter = SimulatedFrequencyCounter()

    assert not counter.is_connected
    assert not counter.input_enabled
    assert counter.command_history == ()


def test_frequency_counter_connects_and_identifies() -> None:
    counter = SimulatedFrequencyCounter()
    counter.connect()

    identity = counter.identify()

    assert counter.is_connected
    assert identity.manufacturer == "OpenBench"
    assert identity.model == "FC-1000"
    assert identity.serial_number == "SIM-FC-0001"
    assert identity.firmware_version == "1.0"
    assert identity.display_name == "OpenBench FC-1000"


def test_frequency_counter_requires_connection() -> None:
    counter = SimulatedFrequencyCounter()

    with pytest.raises(
        InstrumentConnectionError,
        match="is not connected",
    ):
        counter.measure_frequency()


def test_frequency_counter_measures_enabled_input() -> None:
    counter = SimulatedFrequencyCounter(
        base_frequency_hz=10_000_000.0,
        noise_hz=1.0,
        seed=1,
    )
    counter.connect()
    counter.enable_input()

    measurement = counter.measure_frequency()

    assert measurement.target_hz == 10_000_000.0
    assert (
        9_999_999.0
        <= measurement.frequency_hz
        <= 10_000_001.0
    )
    assert measurement.error_hz == (
        measurement.frequency_hz
        - measurement.target_hz
    )
    assert measurement.error_ppm == pytest.approx(
        measurement.error_hz
        / measurement.target_hz
        * 1_000_000.0
    )


def test_frequency_counter_requires_enabled_input() -> None:
    counter = SimulatedFrequencyCounter()
    counter.connect()

    with pytest.raises(
        InstrumentCommandError,
        match="input is not enabled",
    ):
        counter.measure_frequency()


def test_frequency_counter_supports_forced_frequency() -> None:
    counter = SimulatedFrequencyCounter(
        noise_hz=0.0,
    )
    counter.connect()
    counter.enable_input()
    counter.force_frequency(9_999_950.0)

    measurement = counter.measure_frequency(
        target_hz=10_000_000.0,
    )

    assert measurement.frequency_hz == 9_999_950.0
    assert measurement.target_hz == 10_000_000.0
    assert measurement.error_hz == -50.0
    assert measurement.error_ppm == -5.0


def test_frequency_counter_clears_forced_frequency() -> None:
    counter = SimulatedFrequencyCounter(
        noise_hz=0.0,
    )
    counter.connect()
    counter.enable_input()
    counter.force_frequency(9_000_000.0)
    counter.force_frequency(None)

    measurement = counter.measure_frequency(
        target_hz=10_000_000.0,
    )

    assert measurement.frequency_hz == 10_000_000.0


def test_frequency_counter_rejects_invalid_forced_frequency() -> None:
    counter = SimulatedFrequencyCounter()
    counter.connect()

    with pytest.raises(
        InstrumentCommandError,
        match="greater than zero",
    ):
        counter.force_frequency(0.0)


def test_frequency_counter_rejects_invalid_target() -> None:
    counter = SimulatedFrequencyCounter()
    counter.connect()
    counter.enable_input()

    with pytest.raises(
        InstrumentCommandError,
        match="Target frequency",
    ):
        counter.measure_frequency(
            target_hz=0.0,
        )


def test_frequency_counter_supports_scpi_identity_query() -> None:
    counter = SimulatedFrequencyCounter()
    counter.connect()

    response = counter.query("  *idn?  ")

    assert response == (
        "OpenBench,FC-1000,SIM-FC-0001,1.0"
    )
    assert counter.command_history == (
        "*IDN?",
    )


def test_frequency_counter_supports_input_commands() -> None:
    counter = SimulatedFrequencyCounter()
    counter.connect()

    counter.write("input on")

    assert counter.input_enabled
    assert counter.query("input?") == "ON"

    counter.write("INPUT OFF")

    assert not counter.input_enabled
    assert counter.query("INPUT?") == "OFF"


def test_frequency_counter_supports_measurement_query() -> None:
    counter = SimulatedFrequencyCounter(
        base_frequency_hz=10_000_000.0,
        noise_hz=0.0,
    )
    counter.connect()
    counter.write("INPUT ON")

    response = counter.query(
        "MEASURE:FREQUENCY?"
    )

    assert response == "10000000.000000"


def test_frequency_counter_reset_clears_state() -> None:
    counter = SimulatedFrequencyCounter()
    counter.connect()
    counter.enable_input()
    counter.force_frequency(9_000_000.0)

    counter.write("*RST")

    assert not counter.input_enabled

    counter.enable_input()
    measurement = counter.measure_frequency(
        target_hz=10_000_000.0,
    )

    assert measurement.frequency_hz != 9_000_000.0


def test_frequency_counter_disconnect_clears_state() -> None:
    counter = SimulatedFrequencyCounter()
    counter.connect()
    counter.enable_input()
    counter.force_frequency(9_000_000.0)

    counter.disconnect()

    assert not counter.is_connected
    assert not counter.input_enabled

    counter.connect()
    counter.enable_input()

    measurement = counter.measure_frequency(
        target_hz=10_000_000.0,
    )

    assert measurement.frequency_hz != 9_000_000.0


def test_frequency_counter_rejects_unknown_write_command() -> None:
    counter = SimulatedFrequencyCounter()
    counter.connect()

    with pytest.raises(
        InstrumentCommandError,
        match="Unsupported frequency-counter command",
    ):
        counter.write("UNKNOWN")


def test_frequency_counter_rejects_unknown_query() -> None:
    counter = SimulatedFrequencyCounter()
    counter.connect()

    with pytest.raises(
        InstrumentCommandError,
        match="Unsupported frequency-counter query",
    ):
        counter.query("UNKNOWN?")


def test_frequency_counter_rejects_blank_command() -> None:
    counter = SimulatedFrequencyCounter()
    counter.connect()

    with pytest.raises(
        InstrumentCommandError,
        match="cannot be blank",
    ):
        counter.query("   ")


def test_frequency_counter_constructor_validation() -> None:
    with pytest.raises(
        ValueError,
        match="base_frequency_hz",
    ):
        SimulatedFrequencyCounter(
            base_frequency_hz=0.0,
        )

    with pytest.raises(
        ValueError,
        match="noise_hz",
    ):
        SimulatedFrequencyCounter(
            noise_hz=-1.0,
        )