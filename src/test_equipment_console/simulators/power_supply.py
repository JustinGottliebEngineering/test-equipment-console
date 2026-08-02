from __future__ import annotations

from dataclasses import dataclass
from random import Random

from test_equipment_console.drivers.base import (
    BaseInstrument,
    InstrumentCommandError,
    InstrumentIdentity,
)


@dataclass(frozen=True)
class PowerMeasurement:
    voltage_v: float
    current_a: float
    power_w: float
    output_enabled: bool


class SimulatedPowerSupply(BaseInstrument):
    """Simulated programmable DC power supply."""

    def __init__(
        self,
        *,
        name: str = "Simulated Power Supply",
        resource_name: str = "SIM::POWER_SUPPLY::1",
        maximum_voltage_v: float = 30.0,
        maximum_current_a: float = 5.0,
        load_resistance_ohms: float = 34.0,
        voltage_noise_v: float = 0.01,
        current_noise_a: float = 0.002,
        seed: int = 11,
    ) -> None:
        super().__init__(
            name=name,
            resource_name=resource_name,
        )

        if maximum_voltage_v <= 0:
            raise ValueError(
                "maximum_voltage_v must be greater than zero."
            )

        if maximum_current_a <= 0:
            raise ValueError(
                "maximum_current_a must be greater than zero."
            )

        if load_resistance_ohms <= 0:
            raise ValueError(
                "load_resistance_ohms must be greater than zero."
            )

        if voltage_noise_v < 0:
            raise ValueError(
                "voltage_noise_v cannot be negative."
            )

        if current_noise_a < 0:
            raise ValueError(
                "current_noise_a cannot be negative."
            )

        self.maximum_voltage_v = maximum_voltage_v
        self.maximum_current_a = maximum_current_a
        self.load_resistance_ohms = load_resistance_ohms
        self.voltage_noise_v = voltage_noise_v
        self.current_noise_a = current_noise_a

        self._random = Random(seed)
        self._voltage_setpoint_v = 0.0
        self._current_limit_a = maximum_current_a
        self._output_enabled = False
        self._forced_voltage_v: float | None = None
        self._forced_current_a: float | None = None
        self._command_history: list[str] = []

    @property
    def voltage_setpoint_v(self) -> float:
        return self._voltage_setpoint_v

    @property
    def current_limit_a(self) -> float:
        return self._current_limit_a

    @property
    def output_enabled(self) -> bool:
        return self._output_enabled

    @property
    def command_history(self) -> tuple[str, ...]:
        return tuple(self._command_history)

    def identify(self) -> InstrumentIdentity:
        self.require_connection()

        return InstrumentIdentity(
            manufacturer="OpenBench",
            model="PS-305",
            serial_number="SIM-PS-0001",
            firmware_version="1.0",
        )

    def configure(
        self,
        *,
        voltage_v: float,
        current_limit_a: float,
    ) -> None:
        self.require_connection()
        self.set_voltage(voltage_v)
        self.set_current_limit(current_limit_a)

    def set_voltage(
        self,
        voltage_v: float,
    ) -> None:
        self.require_connection()

        if not 0 <= voltage_v <= self.maximum_voltage_v:
            raise InstrumentCommandError(
                "Voltage must be between "
                f"0 and {self.maximum_voltage_v:g} V."
            )

        self._voltage_setpoint_v = voltage_v

    def set_current_limit(
        self,
        current_limit_a: float,
    ) -> None:
        self.require_connection()

        if not 0 < current_limit_a <= self.maximum_current_a:
            raise InstrumentCommandError(
                "Current limit must be greater than 0 and no more "
                f"than {self.maximum_current_a:g} A."
            )

        self._current_limit_a = current_limit_a

    def enable_output(self) -> None:
        self.require_connection()
        self._output_enabled = True

    def disable_output(self) -> None:
        self.require_connection()
        self._output_enabled = False

    def force_measurement(
        self,
        *,
        voltage_v: float | None = None,
        current_a: float | None = None,
    ) -> None:
        self.require_connection()

        if voltage_v is not None and voltage_v < 0:
            raise InstrumentCommandError(
                "Forced voltage cannot be negative."
            )

        if current_a is not None and current_a < 0:
            raise InstrumentCommandError(
                "Forced current cannot be negative."
            )

        self._forced_voltage_v = voltage_v
        self._forced_current_a = current_a

    def clear_forced_measurement(self) -> None:
        self.require_connection()
        self._forced_voltage_v = None
        self._forced_current_a = None

    def measure(self) -> PowerMeasurement:
        self.require_connection()

        if not self._output_enabled:
            return PowerMeasurement(
                voltage_v=0.0,
                current_a=0.0,
                power_w=0.0,
                output_enabled=False,
            )

        ideal_current_a = (
            self._voltage_setpoint_v
            / self.load_resistance_ohms
        )

        limited_current_a = min(
            ideal_current_a,
            self._current_limit_a,
        )

        current_limited = (
            ideal_current_a > self._current_limit_a
        )

        if current_limited:
            ideal_voltage_v = (
                self._current_limit_a
                * self.load_resistance_ohms
            )
        else:
            ideal_voltage_v = self._voltage_setpoint_v

        if self._forced_voltage_v is not None:
            measured_voltage_v = self._forced_voltage_v
        else:
            measured_voltage_v = ideal_voltage_v + (
                self._random.uniform(
                    -self.voltage_noise_v,
                    self.voltage_noise_v,
                )
            )

        if self._forced_current_a is not None:
            measured_current_a = self._forced_current_a
        else:
            measured_current_a = limited_current_a + (
                self._random.uniform(
                    -self.current_noise_a,
                    self.current_noise_a,
                )
            )

        measured_voltage_v = max(
            0.0,
            measured_voltage_v,
        )

        measured_current_a = max(
            0.0,
            measured_current_a,
        )

        return PowerMeasurement(
            voltage_v=measured_voltage_v,
            current_a=measured_current_a,
            power_w=(
                measured_voltage_v
                * measured_current_a
            ),
            output_enabled=True,
        )

    def write(self, command: str) -> None:
        self.require_connection()

        normalized = self._normalize_command(command)
        self._command_history.append(normalized)

        if normalized == "*RST":
            self._reset_state()
            return

        if normalized == "OUTPUT ON":
            self.enable_output()
            return

        if normalized == "OUTPUT OFF":
            self.disable_output()
            return

        if normalized == "VOLTAGE":
            raise InstrumentCommandError(
                "Missing numeric value for VOLTAGE."
            )

        if normalized.startswith("VOLTAGE "):
            value = self._parse_numeric_argument(
                normalized,
                prefix="VOLTAGE ",
            )
            self.set_voltage(value)
            return

        if normalized == "CURRENT":
            raise InstrumentCommandError(
                "Missing numeric value for CURRENT."
            )

        if normalized.startswith("CURRENT "):
            value = self._parse_numeric_argument(
                normalized,
                prefix="CURRENT ",
            )
            self.set_current_limit(value)
            return

        raise InstrumentCommandError(
            f"Unsupported power-supply command: {normalized}."
        )

    def query(self, command: str) -> str:
        self.require_connection()

        normalized = self._normalize_command(command)
        self._command_history.append(normalized)

        if normalized == "*IDN?":
            return self.identify().as_idn_response()

        if normalized == "VOLTAGE?":
            return f"{self._voltage_setpoint_v:.6f}"

        if normalized == "CURRENT?":
            return f"{self._current_limit_a:.6f}"

        if normalized == "OUTPUT?":
            return "ON" if self._output_enabled else "OFF"

        if normalized == "MEASURE:VOLTAGE?":
            measurement = self.measure()
            return f"{measurement.voltage_v:.6f}"

        if normalized == "MEASURE:CURRENT?":
            measurement = self.measure()
            return f"{measurement.current_a:.6f}"

        if normalized == "MEASURE:POWER?":
            measurement = self.measure()
            return f"{measurement.power_w:.6f}"

        raise InstrumentCommandError(
            f"Unsupported power-supply query: {normalized}."
        )

    def _connect(self) -> None:
        self._reset_state()
        self._command_history.clear()

    def _disconnect(self) -> None:
        self._output_enabled = False
        self._forced_voltage_v = None
        self._forced_current_a = None

    def _reset_state(self) -> None:
        self._voltage_setpoint_v = 0.0
        self._current_limit_a = self.maximum_current_a
        self._output_enabled = False
        self._forced_voltage_v = None
        self._forced_current_a = None

    @staticmethod
    def _normalize_command(command: str) -> str:
        normalized = command.strip().upper()

        if not normalized:
            raise InstrumentCommandError(
                "Instrument command cannot be blank."
            )

        return normalized

    @staticmethod
    def _parse_numeric_argument(
        command: str,
        *,
        prefix: str,
    ) -> float:
        value_text = command.removeprefix(
            prefix
        ).strip()

        if not value_text:
            raise InstrumentCommandError(
                f"Missing numeric value for {prefix.strip()}."
            )

        try:
            return float(value_text)
        except ValueError as exc:
            raise InstrumentCommandError(
                f"Invalid numeric value: {value_text}."
            ) from exc