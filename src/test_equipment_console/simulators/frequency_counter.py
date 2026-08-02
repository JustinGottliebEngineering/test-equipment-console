from __future__ import annotations

from dataclasses import dataclass
from random import Random

from test_equipment_console.drivers.base import (
    BaseInstrument,
    InstrumentCommandError,
    InstrumentIdentity,
)


@dataclass(frozen=True)
class FrequencyMeasurement:
    frequency_hz: float
    target_hz: float
    error_hz: float
    error_ppm: float


class SimulatedFrequencyCounter(BaseInstrument):
    """Simulated frequency counter with SCPI-style commands."""

    def __init__(
        self,
        *,
        name: str = "Simulated Frequency Counter",
        resource_name: str = "SIM::FREQ_COUNTER::1",
        base_frequency_hz: float = 10_000_000.0,
        noise_hz: float = 2.0,
        seed: int = 7,
    ) -> None:
        super().__init__(
            name=name,
            resource_name=resource_name,
        )

        if base_frequency_hz <= 0:
            raise ValueError(
                "base_frequency_hz must be greater than zero."
            )

        if noise_hz < 0:
            raise ValueError(
                "noise_hz cannot be negative."
            )

        self.base_frequency_hz = base_frequency_hz
        self.noise_hz = noise_hz

        self._random = Random(seed)
        self._input_enabled = False
        self._forced_frequency_hz: float | None = None
        self._command_history: list[str] = []

    @property
    def input_enabled(self) -> bool:
        return self._input_enabled

    @property
    def command_history(self) -> tuple[str, ...]:
        return tuple(self._command_history)

    def identify(self) -> InstrumentIdentity:
        self.require_connection()

        return InstrumentIdentity(
            manufacturer="OpenBench",
            model="FC-1000",
            serial_number="SIM-FC-0001",
            firmware_version="1.0",
        )

    def enable_input(self) -> None:
        self.require_connection()
        self._input_enabled = True

    def disable_input(self) -> None:
        self.require_connection()
        self._input_enabled = False

    def force_frequency(
        self,
        frequency_hz: float | None,
    ) -> None:
        self.require_connection()

        if frequency_hz is not None and frequency_hz <= 0:
            raise InstrumentCommandError(
                "Forced frequency must be greater than zero."
            )

        self._forced_frequency_hz = frequency_hz

    def measure_frequency(
        self,
        *,
        target_hz: float | None = None,
    ) -> FrequencyMeasurement:
        self.require_connection()

        if not self._input_enabled:
            raise InstrumentCommandError(
                "Frequency-counter input is not enabled."
            )

        target = (
            self.base_frequency_hz
            if target_hz is None
            else target_hz
        )

        if target <= 0:
            raise InstrumentCommandError(
                "Target frequency must be greater than zero."
            )

        if self._forced_frequency_hz is not None:
            measured = self._forced_frequency_hz
        else:
            measured = target + self._random.uniform(
                -self.noise_hz,
                self.noise_hz,
            )

        error_hz = measured - target
        error_ppm = (
            error_hz
            / target
            * 1_000_000.0
        )

        return FrequencyMeasurement(
            frequency_hz=measured,
            target_hz=target,
            error_hz=error_hz,
            error_ppm=error_ppm,
        )

    def write(self, command: str) -> None:
        self.require_connection()

        normalized = self._normalize_command(command)
        self._command_history.append(normalized)

        if normalized == "INPUT ON":
            self.enable_input()
            return

        if normalized == "INPUT OFF":
            self.disable_input()
            return

        if normalized == "*RST":
            self._input_enabled = False
            self._forced_frequency_hz = None
            return

        raise InstrumentCommandError(
            f"Unsupported frequency-counter command: {normalized}."
        )

    def query(self, command: str) -> str:
        self.require_connection()

        normalized = self._normalize_command(command)
        self._command_history.append(normalized)

        if normalized == "*IDN?":
            return self.identify().as_idn_response()

        if normalized == "INPUT?":
            return "ON" if self._input_enabled else "OFF"

        if normalized == "MEASURE:FREQUENCY?":
            measurement = self.measure_frequency()
            return f"{measurement.frequency_hz:.6f}"

        raise InstrumentCommandError(
            f"Unsupported frequency-counter query: {normalized}."
        )

    def _connect(self) -> None:
        self._input_enabled = False
        self._forced_frequency_hz = None
        self._command_history.clear()

    def _disconnect(self) -> None:
        self._input_enabled = False
        self._forced_frequency_hz = None

    @staticmethod
    def _normalize_command(command: str) -> str:
        normalized = command.strip().upper()

        if not normalized:
            raise InstrumentCommandError(
                "Instrument command cannot be blank."
            )

        return normalized