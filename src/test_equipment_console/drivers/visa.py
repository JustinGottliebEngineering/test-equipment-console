from __future__ import annotations

from typing import Any

import pyvisa

from test_equipment_console.drivers.base import (
    BaseInstrument,
    InstrumentCommandError,
    InstrumentConnectionError,
    InstrumentIdentity,
)


class VisaInstrument(BaseInstrument):
    """Generic PyVISA-backed instrument driver."""

    def __init__(
        self,
        *,
        name: str,
        resource_name: str,
        timeout_ms: int = 5000,
        read_termination: str | None = "\n",
        write_termination: str | None = "\n",
        backend: str | None = None,
    ) -> None:
        super().__init__(
            name=name,
            resource_name=resource_name,
        )

        if timeout_ms <= 0:
            raise ValueError(
                "timeout_ms must be greater than zero."
            )

        self.timeout_ms = timeout_ms
        self.read_termination = read_termination
        self.write_termination = write_termination
        self.backend = backend

        self._resource_manager: pyvisa.ResourceManager | None = None
        self._resource: Any | None = None

    def identify(self) -> InstrumentIdentity:
        response = self.query("*IDN?")
        parts = [
            part.strip()
            for part in response.split(",")
        ]

        while len(parts) < 4:
            parts.append("Unknown")

        return InstrumentIdentity(
            manufacturer=parts[0] or "Unknown",
            model=parts[1] or "Unknown",
            serial_number=parts[2] or "Unknown",
            firmware_version=parts[3] or "Unknown",
        )

    def write(self, command: str) -> None:
        self.require_connection()

        normalized = self._validate_command(command)

        try:
            self._require_resource().write(normalized)
        except pyvisa.errors.VisaIOError as exc:
            raise InstrumentCommandError(
                f"VISA write failed for {self.name}: {exc}"
            ) from exc

    def query(self, command: str) -> str:
        self.require_connection()

        normalized = self._validate_command(command)

        try:
            response = self._require_resource().query(
                normalized
            )
        except pyvisa.errors.VisaIOError as exc:
            raise InstrumentCommandError(
                f"VISA query failed for {self.name}: {exc}"
            ) from exc

        return str(response).strip()

    def _connect(self) -> None:
        try:
            if self.backend:
                manager = pyvisa.ResourceManager(
                    self.backend
                )
            else:
                manager = pyvisa.ResourceManager()

            resource = manager.open_resource(
                self.resource_name
            )

            resource.timeout = self.timeout_ms
            resource.read_termination = (
                self.read_termination
            )
            resource.write_termination = (
                self.write_termination
            )

        except (
            pyvisa.errors.VisaIOError,
            OSError,
            ValueError,
        ) as exc:
            self._safe_close()
            raise InstrumentConnectionError(
                f"Could not open VISA resource "
                f"{self.resource_name}: {exc}"
            ) from exc

        self._resource_manager = manager
        self._resource = resource

    def _disconnect(self) -> None:
        close_error: Exception | None = None

        if self._resource is not None:
            try:
                self._resource.close()
            except (
                pyvisa.errors.VisaIOError,
                OSError,
            ) as exc:
                close_error = exc
            finally:
                self._resource = None

        if self._resource_manager is not None:
            try:
                self._resource_manager.close()
            except (
                pyvisa.errors.VisaIOError,
                OSError,
            ) as exc:
                if close_error is None:
                    close_error = exc
            finally:
                self._resource_manager = None

        if close_error is not None:
            raise InstrumentConnectionError(
                f"Could not close VISA resource "
                f"{self.resource_name}: {close_error}"
            ) from close_error

    def _safe_close(self) -> None:
        if self._resource is not None:
            try:
                self._resource.close()
            except Exception:
                pass
            finally:
                self._resource = None

        if self._resource_manager is not None:
            try:
                self._resource_manager.close()
            except Exception:
                pass
            finally:
                self._resource_manager = None

    def _require_resource(self) -> Any:
        if self._resource is None:
            raise InstrumentConnectionError(
                f"{self.name} does not have an open VISA resource."
            )

        return self._resource

    @staticmethod
    def _validate_command(command: str) -> str:
        normalized = command.strip()

        if not normalized:
            raise InstrumentCommandError(
                "Instrument command cannot be blank."
            )

        return normalized