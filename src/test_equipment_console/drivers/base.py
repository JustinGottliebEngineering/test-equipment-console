from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class ConnectionState(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class InstrumentError(RuntimeError):
    """Base exception for instrument communication failures."""


class InstrumentConnectionError(InstrumentError):
    """Raised when an instrument cannot connect or disconnect cleanly."""


class InstrumentCommandError(InstrumentError):
    """Raised when an instrument rejects or cannot execute a command."""


@dataclass(frozen=True)
class InstrumentIdentity:
    manufacturer: str
    model: str
    serial_number: str
    firmware_version: str

    @property
    def display_name(self) -> str:
        return f"{self.manufacturer} {self.model}"

    def as_idn_response(self) -> str:
        return ",".join(
            (
                self.manufacturer,
                self.model,
                self.serial_number,
                self.firmware_version,
            )
        )


class BaseInstrument(ABC):
    """Common interface for real and simulated test equipment."""

    def __init__(
        self,
        *,
        name: str,
        resource_name: str,
    ) -> None:
        normalized_name = name.strip()
        normalized_resource = resource_name.strip()

        if not normalized_name:
            raise ValueError(
                "Instrument name cannot be blank."
            )

        if not normalized_resource:
            raise ValueError(
                "Instrument resource name cannot be blank."
            )

        self.name = normalized_name
        self.resource_name = normalized_resource
        self._state = ConnectionState.DISCONNECTED
        self._last_error: str | None = None

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def is_connected(self) -> bool:
        return self._state == ConnectionState.CONNECTED

    @property
    def last_error(self) -> str | None:
        return self._last_error

    def connect(self) -> None:
        if self.is_connected:
            return

        self._state = ConnectionState.CONNECTING
        self._last_error = None

        try:
            self._connect()
        except Exception as exc:
            self._state = ConnectionState.ERROR
            self._last_error = str(exc)

            if isinstance(exc, InstrumentError):
                raise

            raise InstrumentConnectionError(
                f"Failed to connect to {self.name}: {exc}"
            ) from exc

        self._state = ConnectionState.CONNECTED

    def disconnect(self) -> None:
        if self._state == ConnectionState.DISCONNECTED:
            return

        try:
            self._disconnect()
        except Exception as exc:
            self._state = ConnectionState.ERROR
            self._last_error = str(exc)

            if isinstance(exc, InstrumentError):
                raise

            raise InstrumentConnectionError(
                f"Failed to disconnect from {self.name}: {exc}"
            ) from exc

        self._state = ConnectionState.DISCONNECTED
        self._last_error = None

    def require_connection(self) -> None:
        if not self.is_connected:
            raise InstrumentConnectionError(
                f"{self.name} is not connected."
            )

    @abstractmethod
    def identify(self) -> InstrumentIdentity:
        """Return the instrument identity."""

    @abstractmethod
    def write(self, command: str) -> None:
        """Send a command that does not return a response."""

    @abstractmethod
    def query(self, command: str) -> str:
        """Send a command and return its response."""

    @abstractmethod
    def _connect(self) -> None:
        """Open the instrument connection."""

    @abstractmethod
    def _disconnect(self) -> None:
        """Close the instrument connection."""

    def __enter__(self) -> BaseInstrument:
        self.connect()
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        self.disconnect()