from __future__ import annotations

from typing import Any

import pyvisa
import pytest

from test_equipment_console.drivers.base import (
    ConnectionState,
    InstrumentCommandError,
    InstrumentConnectionError,
)
from test_equipment_console.drivers.visa import (
    VisaInstrument,
)


class FakeVisaResource:
    def __init__(self) -> None:
        self.timeout: int | None = None
        self.read_termination: str | None = None
        self.write_termination: str | None = None
        self.closed = False

        self.writes: list[str] = []
        self.responses: dict[str, str] = {
            "*IDN?": "OpenBench,VM-100,SN-1001,2.5",
            "MEASURE?": "12.345",
        }

        self.write_error: Exception | None = None
        self.query_error: Exception | None = None
        self.close_error: Exception | None = None

    def write(self, command: str) -> None:
        if self.write_error is not None:
            raise self.write_error

        self.writes.append(command)

    def query(self, command: str) -> str:
        if self.query_error is not None:
            raise self.query_error

        return self.responses.get(
            command,
            "OK",
        )

    def close(self) -> None:
        if self.close_error is not None:
            raise self.close_error

        self.closed = True


class FakeResourceManager:
    def __init__(
        self,
        resource: FakeVisaResource,
    ) -> None:
        self.resource = resource
        self.closed = False
        self.opened_resource_name: str | None = None

        self.open_error: Exception | None = None
        self.close_error: Exception | None = None

    def open_resource(
        self,
        resource_name: str,
    ) -> FakeVisaResource:
        if self.open_error is not None:
            raise self.open_error

        self.opened_resource_name = resource_name
        return self.resource

    def close(self) -> None:
        if self.close_error is not None:
            raise self.close_error

        self.closed = True


def build_driver() -> VisaInstrument:
    return VisaInstrument(
        name="VISA Test Instrument",
        resource_name="GPIB0::10::INSTR",
        timeout_ms=2500,
        read_termination="\n",
        write_termination="\r\n",
    )


def install_fake_resource_manager(
    monkeypatch: pytest.MonkeyPatch,
    manager: FakeResourceManager,
) -> list[Any]:
    calls: list[Any] = []

    def fake_resource_manager(
        backend: str | None = None,
    ) -> FakeResourceManager:
        calls.append(backend)
        return manager

    monkeypatch.setattr(
        pyvisa,
        "ResourceManager",
        fake_resource_manager,
    )

    return calls


def test_visa_driver_starts_disconnected() -> None:
    instrument = build_driver()

    assert instrument.state == ConnectionState.DISCONNECTED
    assert not instrument.is_connected
    assert instrument.timeout_ms == 2500
    assert instrument.read_termination == "\n"
    assert instrument.write_termination == "\r\n"


def test_visa_driver_connects_and_configures_resource(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resource = FakeVisaResource()
    manager = FakeResourceManager(resource)

    calls = install_fake_resource_manager(
        monkeypatch,
        manager,
    )

    instrument = build_driver()
    instrument.connect()

    assert instrument.is_connected
    assert manager.opened_resource_name == (
        "GPIB0::10::INSTR"
    )
    assert resource.timeout == 2500
    assert resource.read_termination == "\n"
    assert resource.write_termination == "\r\n"
    assert calls == [None]


def test_visa_driver_uses_requested_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resource = FakeVisaResource()
    manager = FakeResourceManager(resource)

    calls = install_fake_resource_manager(
        monkeypatch,
        manager,
    )

    instrument = VisaInstrument(
        name="Backend Test Instrument",
        resource_name="TCPIP0::192.168.1.20::INSTR",
        backend="@py",
    )

    instrument.connect()

    assert calls == ["@py"]


def test_visa_driver_identifies_instrument(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resource = FakeVisaResource()
    manager = FakeResourceManager(resource)

    install_fake_resource_manager(
        monkeypatch,
        manager,
    )

    instrument = build_driver()
    instrument.connect()

    identity = instrument.identify()

    assert identity.manufacturer == "OpenBench"
    assert identity.model == "VM-100"
    assert identity.serial_number == "SN-1001"
    assert identity.firmware_version == "2.5"
    assert identity.display_name == "OpenBench VM-100"


def test_visa_driver_handles_short_identity_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resource = FakeVisaResource()
    resource.responses["*IDN?"] = "LegacyCorp,LC-50"

    manager = FakeResourceManager(resource)

    install_fake_resource_manager(
        monkeypatch,
        manager,
    )

    instrument = build_driver()
    instrument.connect()

    identity = instrument.identify()

    assert identity.manufacturer == "LegacyCorp"
    assert identity.model == "LC-50"
    assert identity.serial_number == "Unknown"
    assert identity.firmware_version == "Unknown"


def test_visa_driver_writes_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resource = FakeVisaResource()
    manager = FakeResourceManager(resource)

    install_fake_resource_manager(
        monkeypatch,
        manager,
    )

    instrument = build_driver()
    instrument.connect()

    instrument.write("  OUTPUT ON  ")

    assert resource.writes == [
        "OUTPUT ON",
    ]


def test_visa_driver_queries_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resource = FakeVisaResource()
    manager = FakeResourceManager(resource)

    install_fake_resource_manager(
        monkeypatch,
        manager,
    )

    instrument = build_driver()
    instrument.connect()

    response = instrument.query(
        "  MEASURE?  "
    )

    assert response == "12.345"


def test_visa_driver_rejects_blank_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resource = FakeVisaResource()
    manager = FakeResourceManager(resource)

    install_fake_resource_manager(
        monkeypatch,
        manager,
    )

    instrument = build_driver()
    instrument.connect()

    with pytest.raises(
        InstrumentCommandError,
        match="cannot be blank",
    ):
        instrument.write("   ")


def test_visa_driver_requires_connection() -> None:
    instrument = build_driver()

    with pytest.raises(
        InstrumentConnectionError,
        match="is not connected",
    ):
        instrument.query("*IDN?")


def test_visa_driver_wraps_open_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resource = FakeVisaResource()
    manager = FakeResourceManager(resource)

    manager.open_error = ValueError(
        "Resource is unavailable."
    )

    install_fake_resource_manager(
        monkeypatch,
        manager,
    )

    instrument = build_driver()

    with pytest.raises(
        InstrumentConnectionError,
        match="Could not open VISA resource",
    ):
        instrument.connect()

    assert instrument.state == ConnectionState.ERROR
    assert instrument.last_error is not None
    assert "Resource is unavailable" in instrument.last_error


def test_visa_driver_wraps_write_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resource = FakeVisaResource()
    resource.write_error = pyvisa.errors.VisaIOError(
        pyvisa.constants.StatusCode.error_timeout
    )

    manager = FakeResourceManager(resource)

    install_fake_resource_manager(
        monkeypatch,
        manager,
    )

    instrument = build_driver()
    instrument.connect()

    with pytest.raises(
        InstrumentCommandError,
        match="VISA write failed",
    ):
        instrument.write("OUTPUT ON")


def test_visa_driver_wraps_query_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resource = FakeVisaResource()
    resource.query_error = pyvisa.errors.VisaIOError(
        pyvisa.constants.StatusCode.error_timeout
    )

    manager = FakeResourceManager(resource)

    install_fake_resource_manager(
        monkeypatch,
        manager,
    )

    instrument = build_driver()
    instrument.connect()

    with pytest.raises(
        InstrumentCommandError,
        match="VISA query failed",
    ):
        instrument.query("MEASURE?")


def test_visa_driver_disconnects_cleanly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resource = FakeVisaResource()
    manager = FakeResourceManager(resource)

    install_fake_resource_manager(
        monkeypatch,
        manager,
    )

    instrument = build_driver()
    instrument.connect()
    instrument.disconnect()

    assert not instrument.is_connected
    assert resource.closed
    assert manager.closed


def test_visa_driver_wraps_resource_close_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resource = FakeVisaResource()
    resource.close_error = pyvisa.errors.VisaIOError(
        pyvisa.constants.StatusCode.error_system_error
    )

    manager = FakeResourceManager(resource)

    install_fake_resource_manager(
        monkeypatch,
        manager,
    )

    instrument = build_driver()
    instrument.connect()

    with pytest.raises(
        InstrumentConnectionError,
        match="Could not close VISA resource",
    ):
        instrument.disconnect()

    assert instrument.state == ConnectionState.ERROR
    assert manager.closed


def test_visa_driver_validates_timeout() -> None:
    with pytest.raises(
        ValueError,
        match="timeout_ms",
    ):
        VisaInstrument(
            name="Invalid Timeout",
            resource_name="GPIB0::10::INSTR",
            timeout_ms=0,
        )