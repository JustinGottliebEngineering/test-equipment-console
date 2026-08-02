from __future__ import annotations

import pytest

from test_equipment_console.drivers.base import (
    InstrumentCommandError,
    InstrumentConnectionError,
)
from test_equipment_console.simulators.frequency_counter import (
    SimulatedFrequencyCounter,
)
from test_equipment_console.simulators.power_supply import (
    SimulatedPowerSupply,
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


def test_power_supply_starts_disconnected() -> None:
    supply = SimulatedPowerSupply()

    assert not supply.is_connected
    assert supply.voltage_setpoint_v == 0.0
    assert supply.current_limit_a == 5.0
    assert not supply.output_enabled
    assert supply.command_history == ()


def test_power_supply_connects_and_identifies() -> None:
    supply = SimulatedPowerSupply()
    supply.connect()

    identity = supply.identify()

    assert supply.is_connected
    assert identity.manufacturer == "OpenBench"
    assert identity.model == "PS-305"
    assert identity.serial_number == "SIM-PS-0001"
    assert identity.firmware_version == "1.0"
    assert identity.display_name == "OpenBench PS-305"


def test_power_supply_requires_connection() -> None:
    supply = SimulatedPowerSupply()

    with pytest.raises(
        InstrumentConnectionError,
        match="is not connected",
    ):
        supply.measure()


def test_power_supply_configures_voltage_and_current() -> None:
    supply = SimulatedPowerSupply()
    supply.connect()

    supply.configure(
        voltage_v=12.0,
        current_limit_a=1.5,
    )

    assert supply.voltage_setpoint_v == 12.0
    assert supply.current_limit_a == 1.5


def test_power_supply_rejects_voltage_above_limit() -> None:
    supply = SimulatedPowerSupply(
        maximum_voltage_v=30.0,
    )
    supply.connect()

    with pytest.raises(
        InstrumentCommandError,
        match="Voltage must be between",
    ):
        supply.set_voltage(31.0)


def test_power_supply_rejects_negative_voltage() -> None:
    supply = SimulatedPowerSupply()
    supply.connect()

    with pytest.raises(
        InstrumentCommandError,
        match="Voltage must be between",
    ):
        supply.set_voltage(-1.0)


def test_power_supply_rejects_invalid_current_limit() -> None:
    supply = SimulatedPowerSupply(
        maximum_current_a=5.0,
    )
    supply.connect()

    with pytest.raises(
        InstrumentCommandError,
        match="Current limit",
    ):
        supply.set_current_limit(0.0)

    with pytest.raises(
        InstrumentCommandError,
        match="Current limit",
    ):
        supply.set_current_limit(6.0)


def test_power_supply_measures_zero_when_output_is_disabled() -> None:
    supply = SimulatedPowerSupply(
        voltage_noise_v=0.0,
        current_noise_a=0.0,
    )
    supply.connect()
    supply.configure(
        voltage_v=12.0,
        current_limit_a=1.0,
    )

    measurement = supply.measure()

    assert measurement.voltage_v == 0.0
    assert measurement.current_a == 0.0
    assert measurement.power_w == 0.0
    assert not measurement.output_enabled


def test_power_supply_measures_enabled_output() -> None:
    supply = SimulatedPowerSupply(
        load_resistance_ohms=24.0,
        voltage_noise_v=0.0,
        current_noise_a=0.0,
    )
    supply.connect()
    supply.configure(
        voltage_v=12.0,
        current_limit_a=1.0,
    )
    supply.enable_output()

    measurement = supply.measure()

    assert measurement.voltage_v == 12.0
    assert measurement.current_a == 0.5
    assert measurement.power_w == 6.0
    assert measurement.output_enabled


def test_power_supply_applies_current_limit() -> None:
    supply = SimulatedPowerSupply(
        load_resistance_ohms=10.0,
        voltage_noise_v=0.0,
        current_noise_a=0.0,
    )
    supply.connect()
    supply.configure(
        voltage_v=12.0,
        current_limit_a=0.5,
    )
    supply.enable_output()

    measurement = supply.measure()

    assert measurement.current_a == 0.5
    assert measurement.voltage_v == 5.0
    assert measurement.power_w == 2.5


def test_power_supply_supports_forced_measurement() -> None:
    supply = SimulatedPowerSupply(
        voltage_noise_v=0.0,
        current_noise_a=0.0,
    )
    supply.connect()
    supply.configure(
        voltage_v=12.0,
        current_limit_a=1.0,
    )
    supply.enable_output()

    supply.force_measurement(
        voltage_v=11.75,
        current_a=0.42,
    )

    measurement = supply.measure()

    assert measurement.voltage_v == 11.75
    assert measurement.current_a == 0.42
    assert measurement.power_w == pytest.approx(
        4.935
    )


def test_power_supply_clears_forced_measurement() -> None:
    supply = SimulatedPowerSupply(
        load_resistance_ohms=24.0,
        voltage_noise_v=0.0,
        current_noise_a=0.0,
    )
    supply.connect()
    supply.configure(
        voltage_v=12.0,
        current_limit_a=1.0,
    )
    supply.enable_output()

    supply.force_measurement(
        voltage_v=9.0,
        current_a=0.2,
    )
    supply.clear_forced_measurement()

    measurement = supply.measure()

    assert measurement.voltage_v == 12.0
    assert measurement.current_a == 0.5


def test_power_supply_rejects_negative_forced_measurement() -> None:
    supply = SimulatedPowerSupply()
    supply.connect()

    with pytest.raises(
        InstrumentCommandError,
        match="Forced voltage cannot be negative",
    ):
        supply.force_measurement(
            voltage_v=-1.0,
        )

    with pytest.raises(
        InstrumentCommandError,
        match="Forced current cannot be negative",
    ):
        supply.force_measurement(
            current_a=-0.1,
        )


def test_power_supply_supports_scpi_identity_query() -> None:
    supply = SimulatedPowerSupply()
    supply.connect()

    response = supply.query("  *idn?  ")

    assert response == (
        "OpenBench,PS-305,SIM-PS-0001,1.0"
    )
    assert supply.command_history == (
        "*IDN?",
    )


def test_power_supply_supports_configuration_commands() -> None:
    supply = SimulatedPowerSupply()
    supply.connect()

    supply.write("voltage 12")
    supply.write("current 1.25")
    supply.write("output on")

    assert supply.voltage_setpoint_v == 12.0
    assert supply.current_limit_a == 1.25
    assert supply.output_enabled

    assert supply.query("voltage?") == "12.000000"
    assert supply.query("current?") == "1.250000"
    assert supply.query("output?") == "ON"


def test_power_supply_supports_measurement_queries() -> None:
    supply = SimulatedPowerSupply(
        load_resistance_ohms=24.0,
        voltage_noise_v=0.0,
        current_noise_a=0.0,
    )
    supply.connect()
    supply.write("VOLTAGE 12")
    supply.write("CURRENT 1")
    supply.write("OUTPUT ON")

    assert supply.query(
        "MEASURE:VOLTAGE?"
    ) == "12.000000"

    assert supply.query(
        "MEASURE:CURRENT?"
    ) == "0.500000"

    assert supply.query(
        "MEASURE:POWER?"
    ) == "6.000000"


def test_power_supply_reset_clears_state() -> None:
    supply = SimulatedPowerSupply()
    supply.connect()
    supply.configure(
        voltage_v=12.0,
        current_limit_a=1.0,
    )
    supply.enable_output()
    supply.force_measurement(
        voltage_v=11.0,
        current_a=0.4,
    )

    supply.write("*RST")

    assert supply.voltage_setpoint_v == 0.0
    assert supply.current_limit_a == 5.0
    assert not supply.output_enabled

    measurement = supply.measure()

    assert measurement.voltage_v == 0.0
    assert measurement.current_a == 0.0


def test_power_supply_disconnect_disables_output() -> None:
    supply = SimulatedPowerSupply()
    supply.connect()
    supply.configure(
        voltage_v=12.0,
        current_limit_a=1.0,
    )
    supply.enable_output()
    supply.force_measurement(
        voltage_v=11.0,
        current_a=0.4,
    )

    supply.disconnect()

    assert not supply.is_connected
    assert not supply.output_enabled

    supply.connect()

    assert supply.voltage_setpoint_v == 0.0
    assert supply.current_limit_a == 5.0
    assert not supply.output_enabled


def test_power_supply_rejects_unknown_write_command() -> None:
    supply = SimulatedPowerSupply()
    supply.connect()

    with pytest.raises(
        InstrumentCommandError,
        match="Unsupported power-supply command",
    ):
        supply.write("UNKNOWN")


def test_power_supply_rejects_unknown_query() -> None:
    supply = SimulatedPowerSupply()
    supply.connect()

    with pytest.raises(
        InstrumentCommandError,
        match="Unsupported power-supply query",
    ):
        supply.query("UNKNOWN?")


def test_power_supply_rejects_blank_command() -> None:
    supply = SimulatedPowerSupply()
    supply.connect()

    with pytest.raises(
        InstrumentCommandError,
        match="cannot be blank",
    ):
        supply.query("   ")


def test_power_supply_rejects_missing_numeric_argument() -> None:
    supply = SimulatedPowerSupply()
    supply.connect()

    with pytest.raises(
        InstrumentCommandError,
        match="Missing numeric value",
    ):
        supply.write("VOLTAGE ")


def test_power_supply_rejects_invalid_numeric_argument() -> None:
    supply = SimulatedPowerSupply()
    supply.connect()

    with pytest.raises(
        InstrumentCommandError,
        match="Invalid numeric value",
    ):
        supply.write("CURRENT ABC")


def test_power_supply_constructor_validation() -> None:
    with pytest.raises(
        ValueError,
        match="maximum_voltage_v",
    ):
        SimulatedPowerSupply(
            maximum_voltage_v=0.0,
        )

    with pytest.raises(
        ValueError,
        match="maximum_current_a",
    ):
        SimulatedPowerSupply(
            maximum_current_a=0.0,
        )

    with pytest.raises(
        ValueError,
        match="load_resistance_ohms",
    ):
        SimulatedPowerSupply(
            load_resistance_ohms=0.0,
        )

    with pytest.raises(
        ValueError,
        match="voltage_noise_v",
    ):
        SimulatedPowerSupply(
            voltage_noise_v=-0.1,
        )

    with pytest.raises(
        ValueError,
        match="current_noise_a",
    ):
        SimulatedPowerSupply(
            current_noise_a=-0.1,
        )