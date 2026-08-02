from __future__ import annotations

import pytest

from test_equipment_console.drivers.base import (
    BaseInstrument,
    ConnectionState,
    InstrumentConnectionError,
    InstrumentIdentity,
)


class DemoInstrument(BaseInstrument):
    def __init__(
        self,
        *,
        name: str = "Demo Instrument",
        resource_name: str = "SIM::DEMO",
        fail_connect: bool = False,
        fail_disconnect: bool = False,
    ) -> None:
        super().__init__(
            name=name,
            resource_name=resource_name,
        )

        self.fail_connect = fail_connect
        self.fail_disconnect = fail_disconnect
        self.commands: list[str] = []

    def identify(self) -> InstrumentIdentity:
        self.require_connection()

        return InstrumentIdentity(
            manufacturer="DEMO",
            model="MODEL-100",
            serial_number="SN-001",
            firmware_version="1.0",
        )

    def write(self, command: str) -> None:
        self.require_connection()
        self.commands.append(command)

    def query(self, command: str) -> str:
        self.require_connection()
        self.commands.append(command)

        if command == "*IDN?":
            return self.identify().as_idn_response()

        return "OK"

    def _connect(self) -> None:
        if self.fail_connect:
            raise RuntimeError(
                "Simulated connection failure."
            )

    def _disconnect(self) -> None:
        if self.fail_disconnect:
            raise RuntimeError(
                "Simulated disconnect failure."
            )


def test_instrument_starts_disconnected() -> None:
    instrument = DemoInstrument()

    assert instrument.state == ConnectionState.DISCONNECTED
    assert not instrument.is_connected
    assert instrument.last_error is None


def test_instrument_connects_and_disconnects() -> None:
    instrument = DemoInstrument()

    instrument.connect()

    assert instrument.state == ConnectionState.CONNECTED
    assert instrument.is_connected

    instrument.disconnect()

    assert instrument.state == ConnectionState.DISCONNECTED
    assert not instrument.is_connected


def test_instrument_requires_connection() -> None:
    instrument = DemoInstrument()

    with pytest.raises(
        InstrumentConnectionError,
        match="is not connected",
    ):
        instrument.query("*IDN?")


def test_instrument_identification_response() -> None:
    instrument = DemoInstrument()
    instrument.connect()

    identity = instrument.identify()

    assert identity.display_name == "DEMO MODEL-100"
    assert identity.as_idn_response() == (
        "DEMO,MODEL-100,SN-001,1.0"
    )


def test_instrument_records_commands() -> None:
    instrument = DemoInstrument()
    instrument.connect()

    instrument.write("RESET")
    response = instrument.query("STATUS?")

    assert response == "OK"
    assert instrument.commands == [
        "RESET",
        "STATUS?",
    ]


def test_connect_failure_sets_error_state() -> None:
    instrument = DemoInstrument(
        fail_connect=True,
    )

    with pytest.raises(
        InstrumentConnectionError,
        match="Failed to connect",
    ):
        instrument.connect()

    assert instrument.state == ConnectionState.ERROR
    assert instrument.last_error == (
        "Simulated connection failure."
    )


def test_disconnect_failure_sets_error_state() -> None:
    instrument = DemoInstrument(
        fail_disconnect=True,
    )
    instrument.connect()

    with pytest.raises(
        InstrumentConnectionError,
        match="Failed to disconnect",
    ):
        instrument.disconnect()

    assert instrument.state == ConnectionState.ERROR
    assert instrument.last_error == (
        "Simulated disconnect failure."
    )


def test_instrument_supports_context_manager() -> None:
    instrument = DemoInstrument()

    with instrument as active_instrument:
        assert active_instrument.is_connected

    assert not instrument.is_connected


def test_blank_instrument_name_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="name cannot be blank",
    ):
        DemoInstrument(
            name="",
        )


def test_blank_resource_name_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="resource name cannot be blank",
    ):
        DemoInstrument(
            resource_name="",
        )